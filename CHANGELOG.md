# Changelog

## Unreleased

### Added
- Claude Code plugin skeleton (`.claude-plugin/`, `hooks/hooks.json`, `hooks/session-start`, `hooks/stop`)
- Plugin-facing `skills/` tree synced from `packages/claude-skills/`
- Gemini, Cursor, Codex, and Kimi platform entry files
- OpenCode install guide under `.opencode/INSTALL.md`

### Changed
- `using-sybermem` now includes a `<SUBAGENT-STOP>` guard
- SessionStart bootstrap context now includes a short SyberMem skill catalog
