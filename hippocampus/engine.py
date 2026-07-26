"""Hippocampus - a brain-inspired local memory engine for Codex.

Three-layer memory architecture:
  - Active:   frequently retrieved, high retrieval weight
  - Dormant:  low retrieval weight, compressed, never deleted
  - Permastore: high-emotion memories, permanently retrievable

Key principles:
  - Never delete, only decay retrieval weights
  - Context-aware wake: encoded-context vectors trigger dormant memories
  - Emotion-weighted importance scoring
  - Ebbinghaus-style forgetting curve
  - GLOBAL by default: one brain across all projects, fused from day one.
    Set HIPPOCAMPUS_SCOPE=project for per-project isolation.
"""

import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class MemoryFragment:
    content: str
    content_embedding: Optional[list[float]] = None
    context_embedding: Optional[list[float]] = None
    emotion_score: float = 0.5
    importance: float = 0.5
    retrieval_count: int = 0
    last_retrieved: Optional[str] = None
    encoding_snapshot: dict = field(default_factory=dict)
    layer: str = "active"
    memory_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Persistent store (SQLite)
# ---------------------------------------------------------------------------

class MemoryStore:
    """SQLite-backed persistent store for memory metadata."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    content_embedding TEXT,
                    context_embedding TEXT,
                    emotion_score REAL DEFAULT 0.5,
                    importance REAL DEFAULT 0.5,
                    retrieval_count INTEGER DEFAULT 0,
                    last_retrieved TEXT,
                    encoding_snapshot TEXT DEFAULT '{}',
                    layer TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def save(self, mem: MemoryFragment):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memories
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mem.memory_id, mem.content,
                json.dumps(mem.content_embedding) if mem.content_embedding else None,
                json.dumps(mem.context_embedding) if mem.context_embedding else None,
                mem.emotion_score, mem.importance, mem.retrieval_count,
                mem.last_retrieved, json.dumps(mem.encoding_snapshot),
                mem.layer, mem.created_at
            ))
            conn.commit()

    def load_all(self) -> list[MemoryFragment]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY importance DESC"
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def _row_to_memory(self, r) -> MemoryFragment:
        return MemoryFragment(
            memory_id=r[0], content=r[1],
            content_embedding=json.loads(r[2]) if r[2] else None,
            context_embedding=json.loads(r[3]) if r[3] else None,
            emotion_score=r[4], importance=r[5],
            retrieval_count=r[6], last_retrieved=r[7],
            encoding_snapshot=json.loads(r[8]) if r[8] else {},
            layer=r[9], created_at=r[10]
        )

    def load_by_layer(self, layer: str) -> list[MemoryFragment]:
        return [m for m in self.load_all() if m.layer == layer]

    def stats(self) -> dict:
        all_m = self.load_all()
        return {
            "total": len(all_m),
            "active": sum(1 for m in all_m if m.layer == "active"),
            "dormant": sum(1 for m in all_m if m.layer == "dormant"),
            "permastore": sum(1 for m in all_m if m.layer == "permastore"),
        }


# ---------------------------------------------------------------------------
# Embedding provider
# ---------------------------------------------------------------------------

class EmbeddingProvider:
    """Local embedding model using fastembed (ONNX runtime)."""

    def __init__(self):
        self._model = None
        self._dim = None

    def _ensure_model(self):
        if self._model is None:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            self._dim = 384

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._ensure_model()
        vectors = list(self._model.embed(texts))
        result = []
        for v in vectors:
            norm = np.linalg.norm(v)
            result.append((v / norm).tolist() if norm > 0 else v.tolist())
        return result

    @property
    def dim(self) -> int:
        self._ensure_model()
        return self._dim


# ---------------------------------------------------------------------------
# Forgetting curve
# ---------------------------------------------------------------------------

class ForgettingCurve:
    """Ebbinghaus-inspired forgetting curve.

    Never deletes — only decays retrieval weight.
    """

    DEFAULT_HALF_LIFE = 7.0
    DORMANT_HALF_LIFE = 3.0
    PERMASTORE_FLOOR = 0.3

    def decay_factor(
        self, mem: MemoryFragment,
        current_time: Optional[datetime] = None,
    ) -> float:
        if mem.layer == "permastore":
            return max(self.PERMASTORE_FLOOR, 1.0)
        if mem.created_at is None:
            return 1.0

        now = current_time or datetime.now(timezone.utc)
        created = datetime.fromisoformat(mem.created_at)
        days_elapsed = (now - created).total_seconds() / 86400.0

        half_life = self.DEFAULT_HALF_LIFE if mem.layer == "active" else self.DORMANT_HALF_LIFE
        half_life *= (1 + mem.retrieval_count * 0.5)
        half_life *= (1 + mem.emotion_score * 2.0)

        decay = 0.5 ** (days_elapsed / max(half_life, 0.1))
        return max(decay, 0.01)


# ---------------------------------------------------------------------------
# Core Hippocampus Engine (GLOBAL by default)
# ---------------------------------------------------------------------------

class Hippocampus:
    """Brain-inspired persistent memory engine for Codex.

    GLOBAL scope by default — one brain across all projects.
    Set HIPPOCAMPUS_SCOPE=project for per-project isolation.
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            scope = os.environ.get("HIPPOCAMPUS_SCOPE", "global")
            base = os.path.join(os.path.expanduser("~"), ".codex", "hippocampus")
            if scope == "project":
                cwd_hash = str(abs(hash(os.getcwd())))[:8]
                data_dir = os.path.join(base, "projects", cwd_hash)
            else:
                data_dir = os.path.join(base, "global")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        db_path = str(self.data_dir / "memories.db")
        self.store = MemoryStore(db_path)
        self.embedder = EmbeddingProvider()
        self.forgetting = ForgettingCurve()

    # ---- Memory Consolidation ----

    def consolidate(
        self,
        content: str,
        emotion_score: float = 0.5,
        encoding_context: Optional[dict] = None,
        topic_tags: Optional[list[str]] = None,
    ) -> MemoryFragment:
        content_emb = self.embedder.embed([content])[0]

        ctx_parts = []
        if encoding_context:
            ctx_parts.append(encoding_context.get("project", ""))
            ctx_parts.append(encoding_context.get("topic", ""))
            ctx_parts.append(encoding_context.get("mood", ""))
        if topic_tags:
            ctx_parts.extend(topic_tags)
        ctx_text = " ".join(filter(None, ctx_parts))
        context_emb = self.embedder.embed([ctx_text])[0] if ctx_text.strip() else content_emb

        importance = min(emotion_score * 0.6 + min(len(content) / 500.0, 0.3), 1.0)
        layer = "permastore" if emotion_score > 0.8 else "active"

        mem = MemoryFragment(
            content=content,
            content_embedding=content_emb,
            context_embedding=context_emb,
            emotion_score=emotion_score,
            importance=importance,
            encoding_snapshot={
                "project": (encoding_context or {}).get("project", os.getcwd()),
                "topic": (encoding_context or {}).get("topic", ""),
                "mood": (encoding_context or {}).get("mood", ""),
                "tags": topic_tags or [],
            },
            layer=layer,
        )
        self.store.save(mem)
        return mem

    # ---- Retrieval with Wake mechanism ----

    def retrieve(
        self, query: str, top_k: int = 5, include_dormant: bool = True,
    ) -> list[MemoryFragment]:
        query_emb = self.embedder.embed([query])[0]
        all_mem = self.store.load_all()
        if not all_mem:
            return []

        scored = []
        now = datetime.now(timezone.utc)

        for mem in all_mem:
            content_sim = self._cosine_sim(query_emb, mem.content_embedding) if mem.content_embedding else 0.0
            context_sim = self._cosine_sim(query_emb, mem.context_embedding) if mem.context_embedding else 0.0

            wake_bonus = 0.0
            if mem.layer == "dormant" and context_sim > 0.6:
                wake_bonus = 0.3
                mem.retrieval_count += 1
                mem.last_retrieved = now.isoformat()
                self.store.save(mem)

            decay = self.forgetting.decay_factor(mem, current_time=now)
            final_score = (content_sim * 0.5 + context_sim * 0.3 + wake_bonus) * decay

            if mem.layer == "dormant" and not include_dormant and final_score < 0.1:
                continue

            scored.append((mem, final_score))

        scored.sort(key=lambda x: x[1], reverse=True)

        for mem, _ in scored[:top_k]:
            mem.retrieval_count += 1
            mem.last_retrieved = now.isoformat()
            self.store.save(mem)

        return [m for m, _ in scored[:top_k]]

    def _cosine_sim(self, a, b) -> float:
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    # ---- Maintenance ----

    def run_maintenance(self):
        all_mem = self.store.load_all()
        now = datetime.now(timezone.utc)
        changes = 0

        for mem in all_mem:
            if mem.layer == "permastore":
                continue
            created = datetime.fromisoformat(mem.created_at)
            days = (now - created).total_seconds() / 86400.0

            if mem.layer == "active" and days > 14 and mem.retrieval_count == 0:
                mem.layer = "dormant"
                self.store.save(mem)
                changes += 1
            elif mem.layer == "dormant" and days > 30 and len(mem.content) > 500:
                mem.content = self._summarize(mem.content)
                self.store.save(mem)
                changes += 1

        return changes

    def _summarize(self, content: str, max_len: int = 300) -> str:
        sentences = [s.strip() for s in content.replace("!", ".").replace("?", ".").split(".") if len(s.strip()) > 10]
        if len(sentences) <= 2:
            return content[:max_len]
        result = sentences[0]
        for s in sentences[1:]:
            if len(result) + len(s) < max_len:
                result += ". " + s
        return result[:max_len] + "..."

    # ---- Session context ----

    def context_injection(self, current_topic: str, max_tokens: int = 800) -> str:
        memories = self.retrieve(current_topic, top_k=5)
        if not memories:
            return ""

        lines = ["[海马体 - 相关记忆:]"]
        for mem in memories:
            emoji = {"active": "💡", "dormant": "🌙", "permastore": "💎"}.get(mem.layer, "")
            truncated = mem.content[:150].replace("\n", " ")
            lines.append(f"  {emoji} [{mem.memory_id}] {truncated}")

        result = "\n".join(lines)
        while len(result) > max_tokens * 4:
            lines.pop()
            result = "\n".join(lines)
        return result

    def stats(self) -> dict:
        return self.store.stats()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Codex-Hippocampus: Brain-like Memory")
    sub = parser.add_subparsers(dest="command")

    p_cons = sub.add_parser("consolidate")
    p_cons.add_argument("content")
    p_cons.add_argument("--emotion", type=float, default=0.5)
    p_cons.add_argument("--topic", default="")
    p_cons.add_argument("--tags", nargs="*", default=[])

    p_ret = sub.add_parser("retrieve")
    p_ret.add_argument("query")
    p_ret.add_argument("--top", type=int, default=5)

    p_ctx = sub.add_parser("context")
    p_ctx.add_argument("topic")

    sub.add_parser("maintain")
    sub.add_parser("stats")

    args = parser.parse_args()
    hp = Hippocampus()

    if args.command == "consolidate":
        mem = hp.consolidate(args.content, emotion_score=args.emotion,
                             encoding_context={"topic": args.topic}, topic_tags=args.tags)
        print(f"Memory encoded: {mem.memory_id} (layer={mem.layer})")

    elif args.command == "retrieve":
        for m in hp.retrieve(args.query, top_k=args.top):
            print(f"[{m.layer[:1].upper()}][{m.memory_id}] {m.content[:200]}")

    elif args.command == "context":
        print(hp.context_injection(args.topic))

    elif args.command == "maintain":
        changes = hp.run_maintenance()
        print(f"Maintenance: {changes} changes")

    elif args.command == "stats":
        print(json.dumps(hp.stats(), indent=2))


if __name__ == "__main__":
    main()
