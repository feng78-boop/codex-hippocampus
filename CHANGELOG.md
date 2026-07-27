# Changelog

### Known Limitations

- **Codex Sandbox**: The default global path (`~/.codex/hippocampus/global/`) is outside sandbox writable roots. Add `HIPPOCAMPUS_HOME` to `config.toml` `[shell_environment_policy.set]` as a permanent fix. See README for details.

- **Codex Sandbox**: The default global path (`~/.codex/hippocampus/global/`) is outside sandbox writable roots. Use `HIPPOCAMPUS_HOME` environment variable pointing to a workspace path, or switch to `HIPPOCAMPUS_SCOPE=local` for sandbox environments.

## [0.3.0] - 2026-07-27

### Added
- `local` memory scope — stores data in `.hippocampus/` within the project directory
- Interactive `setup.py` installer with scope selection (global/local)

### Changed
- Default scope remains `global` (backward compatible)

## [0.2.0] - 2026-07-27
 - 2026-07-27

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
