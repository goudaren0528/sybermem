# Changelog

## Unreleased

### Added
- Claude Code plugin skeleton (`.claude-plugin/`, `hooks/hooks.json`, `hooks/session-start`, `hooks/stop`)
- Plugin-facing `skills/` tree synced from `packages/claude-skills/`
- Gemini, Cursor, Codex, and Kimi platform entry files
- OpenCode install guide under `.opencode/INSTALL.md`
- Init, update, and install docs now include project-local `.sybermem/hooks/task_recall.py` distribution and explain that Claude `UserPromptSubmit` handles both record-intent capture and read-only task recall
- User Habit Memory visible reminders via `sybermem habit remind`, Claude managed prompt-hook reminders, and the `/sybermem-habit` skill
- Codex Phase 1 support: global installers now copy SyberMem user skills to `~/.agents/skills`, with `.codex/INSTALL.md` documenting the skills-only boundary
- Codex Phase 1.5 verification: health checks now discover templates from the Codex user skill install, with package guards and docs for the skills-only smoke path

### Changed
- `using-sybermem` now includes a `<SUBAGENT-STOP>` guard
- SessionStart bootstrap context now includes a short SyberMem skill catalog
- Public install docs now spell out the OpenCode limitation: no documented automatic prompt-time `UserPromptSubmit` injection, manual `/sybermem-search` and supported compaction only
- Codex plugin metadata and platform docs now describe user-skill support instead of metadata-only status, without hook or runtime automation claims
