---
name: hippocampus
description: "Brain-inspired persistent memory for Codex. AUTO-PILOT: runs context at every session start, consolidates autonomously. Three-layer storage, never deletes."
---

# HIPPOCAMPUS PROTOCOL — NON-NEGOTIABLE

**Every Codex session MUST follow this protocol. No exceptions. The user does NOT need to request it.**

1. **Session START**: Before ANY other action, run `python -m hippocampus.engine context "<topic>"` with topic from user first message. Internalize the output.
2. **During session**: Consolidate autonomously when user teaches, corrects, or expresses strong emotion.
3. **Session END**: Consolidate 3-5 key takeaways before yielding.
4. **Weekly**: Run `python -m hippocampus.engine maintain`.

---

## What it is

A local, persistent memory engine for Codex that mimics how human memory works:

| Human Brain | Hippocampus |
|---|---|
| Working Memory (Prefrontal Cortex) | Current session context |
| Importance Scoring (Amygdala) | Emotion-weighted importance |
| Memory Consolidation (Hippocampus) | Active → Dormant → Permastore |
| Long-term Storage (Neocortex) | Local vector database |
| Context-aware Recall | Semantic wake mechanism |
| Forgetting Curve (Ebbinghaus) | Decay weights, never delete |

---

## AUTO-PILOT MODE (DEFAULT)

Hippocampus operates AUTOMATICALLY. The agent must:

| Trigger | Action |
|---|---|
| Every session start | Run `context` with topic from user first message |
| User teaches/corrects agent | Run `consolidate` with emotion 0.5-0.8 |
| User shows strong emotion | Run `consolidate` with emotion 0.7-0.9 |
| Agent makes a mistake | Run `consolidate` with emotion 0.7+, topic "agent-behavior" |
| Session ending | Run `consolidate` for 3-5 key takeaways |

The user should NEVER need to say "let me remember" or "remember this." Memory is automatic.

## Manual Triggers (backup)

If auto-pilot missed something, user can still say "let me remember" to force manual consolidation.

## Core Principles

1. **Never delete**, only decay retrieval weights
2. **Context triggers recall** — not keyword search
3. **Emotion creates permanence** — what matters sticks (>0.8 = permastore, never decays)
4. **Spaced repetition** — retrieved memories strengthen

## Commands

All commands use `python` (works on both Windows and Unix; `python3` is Unix-only).

### consolidate — Create a memory
```bash
python -m hippocampus.engine consolidate "<content>" --emotion <0-1> --topic "<topic>" --tags tag1 tag2
```
- `--emotion`: 0.0 (neutral) to 1.0 (highly emotional). >0.8 = permastore (never decays).
- `--topic`: subject area
- `--tags`: freeform tags for context encoding

### retrieve — Search memories
```bash
python -m hippocampus.engine retrieve "<query>" --top 5
```

### context — Session context injection (MANDATORY)
```bash
python -m hippocampus.engine context "<current topic>"
```
**MANDATORY at session start.** Injects relevant memories into the conversation.

### maintain — Daily maintenance
```bash
python -m hippocampus.engine maintain
```

### stats — Memory statistics
```bash
python -m hippocampus.engine stats
```

## Session Protocol (MANDATORY)

### At session START:
1. **IMMEDIATELY** run `context` — before answering user, before any analysis
2. Extract topic from user first message
3. Read and internalize the output

### During session:
1. User preference/correction → `consolidate` (emotion 0.5-0.8)
2. Agent mistake discovered → `consolidate` (emotion 0.7+)
3. Strong user emotion → `consolidate` (emotion 0.7-0.9)
4. Use `--emotion 0.81+` for permanent memories that should never decay

### At session END:
1. Consolidate 3-5 key takeaways from the conversation
2. Run `maintain` weekly

## Installation

```bash
pip install fastembed
```

No external API keys needed. Embeddings run locally via ONNX (~80MB model download on first use).

## Storage

By default, memories are stored at `~/.codex/hippocampus/global/memories.db` — one brain across all projects.

Override with environment variables if needed:
- `HIPPOCAMPUS_SCOPE=project` — per-project isolation
- `HIPPOCAMPUS_HOME=/path` — custom data directory

## Known Limitations

1. **No cross-agent memory sharing**: Codex and WorkBuddy each have independent memory. Hippocampus memories are agent-local.
2. **First-install requires manual pip**: The skill installer copies files but does not auto-run `pip install fastembed`. Users must run this manually.
3. **Sandbox may block writes**: In restricted sandbox modes, the data directory must be added to writable roots, or set `HIPPOCAMPUS_HOME` to a writable path.
4. **Context must run at session start**: The auto-pilot protocol depends on the agent following the SKILL.md. If the agent skips step 1, memories from prior sessions won't be injected.
