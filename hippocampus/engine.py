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
    emotion_score: float = 0.5          # 0-1, amygdala-style emotional weight
    importance: float = 0.5             # composite importance
    retrieval_count: int = 0
    last_retrieved: Optional[str] = None  # ISO timestamp
    encoding_snapshot: dict = field(default_factory=dict)
    layer: str = "active"               # active | dormant | permastore
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
                (memory_id, content, content_embedding, context_embedding,
                 emotion_score, importance, retrieval_count, last_retrieved,
                 encoding_snapshot, layer, created_at)
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
        results = []
        for r in rows:
            mem = MemoryFragment(
                memory_id=r[0], content=r[1],
                content_embedding=json.loads(r[2]) if r[2] else None,
                context_embedding=json.loads(r[3]) if r[3] else None,
                emotion_score=r[4], importance=r[5],
                retrieval_count=r[6], last_retrieved=r[7],
                encoding_snapshot=json.loads(r[8]) if r[8] else {},
                layer=r[9], created_at=r[10]
            )
            results.append(mem)
        return results

    def load_by_layer(self, layer: str) -> list[MemoryFragment]:
        all_mem = self.load_all()
        return [m for m in all_mem if m.layer == layer]

    def get_meta(self, key: str, default=None):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_meta(self, key: str, value):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
            conn.commit()

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE layer='active'"
            ).fetchone()[0]
            dormant = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE layer='dormant'"
            ).fetchone()[0]
            permastore = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE layer='permastore'"
            ).fetchone()[0]
        return {
            "total": total,
            "active": active,
            "dormant": dormant,
            "permastore": permastore,
        }


# ---------------------------------------------------------------------------
# Embedding provider
# ---------------------------------------------------------------------------

class EmbeddingProvider:
    """Local embedding model using sentence-transformers."""

    def __init__(self):
        self._model = None
        self._dim = None

    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            # all-MiniLM-L6-v2: 384-dim, ~80MB, runs on CPU, fast
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._dim = 384

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        self._ensure_model()
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()

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
    High-emotion and frequently-retrieved memories resist decay.
    """

    # Decay half-life in days (how fast weight drops to 0.5)
    DEFAULT_HALF_LIFE = 7.0          # active memories
    DORMANT_HALF_LIFE = 3.0          # dormant memories decay faster
    PERMASTORE_FLOOR = 0.3           # permastore never drops below this

    def decay_factor(
        self,
        mem: MemoryFragment,
        current_time: Optional[datetime] = None,
    ) -> float:
        """Return a multiplier (0-1) for retrieval weight after time decay."""
        if mem.layer == "permastore":
            return max(self.PERMASTORE_FLOOR, 1.0)

        if mem.created_at is None:
            return 1.0

        now = current_time or datetime.now(timezone.utc)
        created = datetime.fromisoformat(mem.created_at)
        days_elapsed = (now - created).total_seconds() / 86400.0

        half_life = self.DEFAULT_HALF_LIFE if mem.layer == "active" else self.DORMANT_HALF_LIFE

        # Override: frequently retrieved memories have longer half-life
        adjusted_half_life = half_life * (1 + mem.retrieval_count * 0.5)

        # Override: high-emotion memories resist decay
        adjusted_half_life *= (1 + mem.emotion_score * 2.0)

        # Exponential decay: weight = 0.5 ^ (t / half_life)
        decay = 0.5 ** (days_elapsed / max(adjusted_half_life, 0.1))
        return max(decay, 0.01)  # never zero — never fully forgotten


# ---------------------------------------------------------------------------
# Core Hippocampus Engine
# ---------------------------------------------------------------------------

class Hippocampus:
    """Brain-inspired persistent memory engine for Codex."""

    def __init__(
        self,
        data_dir: str = None,
    ):
        if data_dir is None:
            # Default: ~/.codex/hippocampus/ per project
            cwd = os.getcwd()
            project_hash = str(abs(hash(cwd)))[:8]
            data_dir = os.path.join(
                os.path.expanduser("~/.codex/hippocampus"),
                project_hash
            )

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
        """Encode a new memory fragment after each meaningful exchange."""
        # Generate embeddings
        content_emb = self.embedder.embed([content])[0]

        # Build context embedding from snapshot
        ctx_parts = []
        if encoding_context:
            ctx_parts.append(encoding_context.get("project", ""))
            ctx_parts.append(encoding_context.get("topic", ""))
            ctx_parts.append(encoding_context.get("mood", ""))
        if topic_tags:
            ctx_parts.extend(topic_tags)
        ctx_text = " ".join(filter(None, ctx_parts))
        context_emb = self.embedder.embed([ctx_text])[0] if ctx_text.strip() else content_emb

        # Determine importance
        importance = self._calculate_importance(
            emotion_score=emotion_score,
            content=content
        )

        # Determine layer
        layer = "permastore" if emotion_score > 0.8 else "active"

        mem = MemoryFragment(
            content=content,
            content_embedding=content_emb,
            context_embedding=context_emb,
            emotion_score=emotion_score,
            importance=importance,
            encoding_snapshot={
                "project": (encoding_context or {}).get("project", ""),
                "topic": (encoding_context or {}).get("topic", ""),
                "mood": (encoding_context or {}).get("mood", ""),
                "tags": topic_tags or [],
            },
            layer=layer,
        )
        self.store.save(mem)
        return mem

    def _calculate_importance(self, emotion_score: float, content: str) -> float:
        """Importance = weighted mix of emotion + content signals."""
        # Base on emotion
        base = emotion_score * 0.6
        # Length bonus: more substantive content = slightly more important
        length_bonus = min(len(content) / 500.0, 0.3)
        return min(base + length_bonus, 1.0)

    # ---- Retrieval (with Wake mechanism) ----

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        include_dormant: bool = True,
    ) -> list[MemoryFragment]:
        """Search memories by semantic similarity, including waking dormant ones."""
        query_emb = self.embedder.embed([query])[0]
        all_mem = self.store.load_all()

        if not all_mem:
            return []

        scored = []
        now = datetime.now(timezone.utc)

        for mem in all_mem:
            # Compute semantic similarity to query
            if mem.content_embedding:
                content_sim = self._cosine_sim(query_emb, mem.content_embedding)
            else:
                content_sim = 0.0

            # Compute context similarity (wake mechanism)
            if mem.context_embedding:
                context_sim = self._cosine_sim(query_emb, mem.context_embedding)
            else:
                context_sim = 0.0

            # Wake threshold: context similarity can wake dormant memories
            wake_bonus = 0.0
            if mem.layer == "dormant" and context_sim > 0.6:
                wake_bonus = 0.3  # significant boost to dormant memory
                # Mark as retrieved (spaced repetition effect)
                mem.retrieval_count += 1
                mem.last_retrieved = now.isoformat()
                self.store.save(mem)

            # Apply forgetting curve decay
            decay = self.forgetting.decay_factor(mem, current_time=now)

            # Final score
            final_score = (content_sim * 0.5 + context_sim * 0.3 + wake_bonus) * decay

            # Skip dormant with very low scores
            if mem.layer == "dormant" and not include_dormant:
                if final_score < 0.1:
                    continue

            scored.append((mem, final_score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Update retrieval stats for top results
        for mem, _ in scored[:top_k]:
            mem.retrieval_count += 1
            mem.last_retrieved = now.isoformat()
            self.store.save(mem)

        return [m for m, _ in scored[:top_k]]

    def _cosine_sim(self, a: list[float], b: list[float]) -> float:
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    # ---- Layer Management ----

    def run_maintenance(self):
        """Periodic maintenance: move inactive memories to dormant layer.

        Called daily (or on session end).  Like sleep consolidation.
        """
        all_mem = self.store.load_all()
        now = datetime.now(timezone.utc)
        changes = 0

        for mem in all_mem:
            if mem.layer == "permastore":
                continue  # never touch permastore

            created = datetime.fromisoformat(mem.created_at)
            days_elapsed = (now - created).total_seconds() / 86400.0

            # Active → Dormant after 14 days without retrieval
            if mem.layer == "active" and days_elapsed > 14 and mem.retrieval_count == 0:
                mem.layer = "dormant"
                self.store.save(mem)
                changes += 1

            # Merge similar dormant memories
            if mem.layer == "dormant" and days_elapsed > 30:
                # Compress content to summary
                if len(mem.content) > 500:
                    mem.content = self._summarize(mem.content)
                    self.store.save(mem)
                    changes += 1

        return changes

    def _summarize(self, content: str, max_len: int = 300) -> str:
        """Simple extractive summarization."""
        sentences = content.replace("!", ".").replace("?", ".").split(".")
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if len(sentences) <= 2:
            return content[:max_len]
        # Keep first and key sentences
        summary = sentences[0]
        for s in sentences[1:]:
            if len(summary) + len(s) < max_len:
                summary += ". " + s
        return summary[:max_len] + "..."

    # ---- Session integration ----

    def context_injection(self, current_topic: str, max_tokens: int = 800) -> str:
        """Generate context to inject at session start.

        Retrieves and wakes relevant memories, producing a compact
        context block for the current conversation.
        """
        memories = self.retrieve(current_topic, top_k=5)
        if not memories:
            return ""

        lines = ["[海马体 - 相关记忆:]"]
        for mem in memories:
            layer_emoji = {"active": "💡", "dormant": "🌙", "permastore": "💎"}
            emoji = layer_emoji.get(mem.layer, "")
            truncated = mem.content[:150].replace("\n", " ")
            lines.append(f"  {emoji} [{mem.memory_id}] {truncated}")

        result = "\n".join(lines)
        # Rough token estimate: 1 token ≈ 4 chars
        while len(result) > max_tokens * 4:
            lines.pop()
            result = "\n".join(lines)

        return result

    # ---- Stats ----

    def stats(self) -> dict:
        return self.store.stats()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Hippocampus - Brain-like Memory for Codex")
    sub = parser.add_subparsers(dest="command")

    # consolidate
    p_cons = sub.add_parser("consolidate", help="Encode a new memory")
    p_cons.add_argument("content", help="Memory content")
    p_cons.add_argument("--emotion", type=float, default=0.5)
    p_cons.add_argument("--topic", default="")
    p_cons.add_argument("--tags", nargs="*", default=[])

    # retrieve
    p_ret = sub.add_parser("retrieve", help="Search memories")
    p_ret.add_argument("query", help="Search query")
    p_ret.add_argument("--top", type=int, default=5)

    # context
    p_ctx = sub.add_parser("context", help="Generate context injection")
    p_ctx.add_argument("topic", help="Current topic")

    # maintain
    sub.add_parser("maintain", help="Run memory maintenance")

    # stats
    sub.add_parser("stats", help="Show memory stats")

    args = parser.parse_args()

    hp = Hippocampus()

    if args.command == "consolidate":
        mem = hp.consolidate(
            args.content,
            emotion_score=args.emotion,
            encoding_context={"topic": args.topic},
            topic_tags=args.tags,
        )
        print(f"Memory encoded: {mem.memory_id} (layer={mem.layer})")

    elif args.command == "retrieve":
        results = hp.retrieve(args.query, top_k=args.top)
        for m in results:
            print(f"[{m.layer[:1].upper()}][{m.memory_id}] {m.content[:200]}")

    elif args.command == "context":
        ctx = hp.context_injection(args.topic)
        print(ctx)

    elif args.command == "maintain":
        changes = hp.run_maintenance()
        print(f"Maintenance complete: {changes} changes")

    elif args.command == "stats":
        print(json.dumps(hp.stats(), indent=2))


if __name__ == "__main__":
    main()
