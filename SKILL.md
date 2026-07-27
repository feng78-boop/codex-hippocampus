---
name: hippocampus
description: "Brain-inspired persistent memory for Codex. Three-layer storage, never deletes, context-aware wake mechanism. Remembers like a human brain — stores everything, retrieves by association. Activation phrase: 'let me remember'."
---

# Hippocampus — Brain-Inspired Memory System

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

## Core Principles

1. **Never delete**, only decay retrieval weights
2. **Context triggers recall** — not keyword search
3. **Emotion creates permanence** — what matters sticks
4. **Spaced repetition** — retrieved memories strengthen

## When to Use

Use the `consolidate` command whenever any of these happen:
- The user expresses a preference or opinion about how you work
- The user explicitly teaches you something new
- The user corrects your approach
- The user shares a strong emotional reaction (excitement, frustration, surprise)
- At the end of each session, consolidate key learnings

Use the `context` command at the start of each new session to inject relevant memories.

## Commands

### consolidate — Create a memory
```
python3 -m hippocampus.engine consolidate "<memory content>" --emotion <0-1> --topic "<topic>" --tags tag1 tag2
```
- `--emotion`: 0.0 (neutral) to 1.0 (highly emotional). Memories with >0.8 go to permastore.
- `--topic`: the subject area
- `--tags`: freeform tags for context encoding

### retrieve — Search memories
```
python3 -m hippocampus.engine retrieve "<query>" --top 5
```

### context — Generate session context injection
```
python3 -m hippocampus.engine context "<current topic>"
```
Run this at session start. Injects relevant memories into the conversation.

### maintain — Run daily maintenance (consolidation, forgetting)
```
python3 -m hippocampus.engine maintain
```

### stats — View memory statistics
```
python3 -m hippocampus.engine stats
```

## Session Protocol

### At session START:
1. Run `context` with the user's first message topic
2. Inject the output into your understanding of the user

### During session:
1. When user expresses preferences, corrections, or emotions → `consolidate`
2. Use `--emotion 0.7+` for strong reactions, `0.3-0.5` for mild preferences

### At session END:
1. Consolidate 3-5 key takeaways from the conversation
2. Run `maintain` weekly

## Installation

```bash
pip install fastembed numpy
```

### Sandbox / Custom Data Directory

Set `HIPPOCAMPUS_HOME` to override the default data storage path:

```bash
export HIPPOCAMPUS_HOME=/path/to/writable/dir   # Linux/macOS
set HIPPOCAMPUS_HOME=C:\path\to\writable\dir   # Windows
```


No external API keys needed. All embeddings run locally via `all-MiniLM-L6-v2` (~80MB model).
