# Changelog

## [0.2.0] - 2026-07-27

### Added
- `HIPPOCAMPUS_HOME` environment variable to override data storage directory (for sandbox environments)

### Fixed
- Replaced emoji characters (`💡🌙💎`) in `context_injection()` with ASCII-safe markers `[A][D][P]` to fix `UnicodeEncodeError` on Windows GBK consoles
- Added `UnicodeEncodeError` fallback in CLI `context` command for cross-platform encoding safety

### Changed
- Corrected module path from `hippocampus.hippocampus.engine` to `hippocampus.engine` in all documentation
- Updated dependency docs from `sentence-transformers` to `fastembed` (matching requirements.txt)

## [0.1.0] - 2026-07-26

### Added
- Initial release: three-layer memory architecture (Active/Dormant/Permastore)
- `consolidate`, `retrieve`, `context`, `maintain`, `stats` commands
- Semantic embedding via fastembed (BAAI/bge-small-en-v1.5)
- Ebbinghaus-style forgetting curve
- Context-aware wake mechanism for dormant memories
- SQLite-backed persistent storage
