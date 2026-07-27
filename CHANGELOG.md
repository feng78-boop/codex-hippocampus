# Changelog

## [0.3.1] - 2026-07-27

### Added
- **AUTO-PILOT MODE**: SKILL.md now mandates non-negotiable session protocol. Agent MUST run `context` at session start, consolidate autonomously during conversation, without user prompting. Replaces the old "activation phrase" model where user had to say "let me remember."
- **Known Limitations** section in SKILL.md documenting cross-agent isolation, manual pip install requirement, sandbox write restrictions, and context timing constraint.

### Fixed
- Changed all command examples from `python3` to `python` for cross-platform compatibility (Windows does not have `python3` alias).
- Removed misleading "Activation phrase: let me remember" from description — auto-pilot makes this obsolete.
- Removed `numpy` from docs install command (`pip install fastembed` is sufficient; numpy is a transitive dependency).

### Lessons Learned (2026-07-27 Codex Session)
- SKILL.md previously treated memory protocol as "suggestions" — the agent could skip them. MANDATORY language with AUTO-PILOT table makes compliance non-optional.
- First-install UX is broken: skill installer copies files but does not run `pip install fastembed`. User hits `ModuleNotFoundError` on first use without clear guidance.
- `HIPPOCAMPUS_HOME` env var caused confusion when set in process scope but user thought it was persistent. Standard path `~/.codex/hippocampus/global/` is the recommended default.
- Cross-agent memory (Codex ↔ WorkBuddy) is an unsolved architectural gap. Each agent builds independent memory stores.

## [0.3.0] - 2026-07-27

### Added
- `local` memory scope — stores data in `.hippocampus/` within the project directory
- Interactive `setup.py` installer with scope selection (global/local)

### Changed
- Default scope remains `global` (backward compatible)

## [0.2.0] - 2026-07-27

### Added
- `HIPPOCAMPUS_HOME` environment variable to override data storage directory

### Fixed
- Replaced emoji characters in `context_injection()` with ASCII-safe markers `[A][D][P]` to fix `UnicodeEncodeError` on Windows GBK consoles
- Added `UnicodeEncodeError` fallback in CLI `context` command for cross-platform encoding safety

### Changed
- Corrected module path from `hippocampus.hippocampus.engine` to `hippocampus.engine` in all documentation
- Updated dependency docs from `sentence-transformers` to `fastembed`

## [0.1.0] - 2026-07-26

### Added
- Initial release: three-layer memory architecture
- SQLite-backed persistent storage
- Semantic embedding via fastembed
- Ebbinghaus-style forgetting curve
