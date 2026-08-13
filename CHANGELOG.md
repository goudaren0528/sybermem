# Changelog

## Unreleased

### Added
- Claude Code plugin skeleton (`.claude-plugin/`, `hooks/hooks.json`, `hooks/session-start`, `hooks/stop`)
- Plugin-facing `skills/` tree synced from `packages/claude-skills/`
- Gemini, Cursor, Codex, and Kimi platform entry files
- OpenCode install guide under `.opencode/INSTALL.md`
- Init, update, and install docs now include project-local `.sybermem/hooks/task_recall.py` distribution and explain that Claude `UserPromptSubmit` handles both record-intent capture and read-only task recall
- User Habit Memory visible reminders via `sybermem habit remind`, Claude managed prompt-hook reminders, and the `/sybermem-habit` skill
- Codex Phase 1 support: global installers copy SyberMem user skills to `~/.agents/skills`.
- Codex Phase 1.5 verification: health checks discover templates from the Codex user skill install, with package guards for the skill smoke path.
- OpenCode prompt-time recall and User Habit Memory reminders via supported `chat.message` + `experimental.chat.system.transform` hooks, with shared CLI recall/habit packets and visible markers.
- Codex Phase 2 User Habit Memory prompt reminders via a managed `UserPromptSubmit` hook that returns `hookSpecificOutput.additionalContext`; project recall, hidden auto-resume, background automation, prompt/agent handler runtimes, and `.codex/config.toml` remain unsupported.

### Changed
- `using-sybermem` now includes a `<SUBAGENT-STOP>` guard
- SessionStart bootstrap context now includes a short SyberMem skill catalog
- Codex plugin metadata and platform docs now describe user-skill support plus the bounded User Habit Memory hook, without claiming project recall or broad runtime automation.
- Public install docs now describe OpenCode and Codex prompt-time support accurately: OpenCode supports project recall plus habit reminders through its chat transform hooks, while Codex supports habit reminders only through `UserPromptSubmit` `additionalContext`.
