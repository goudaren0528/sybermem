# Changelog

## Unreleased

### Added
- Claude Code plugin skeleton (`.claude-plugin/`, `hooks/hooks.json`, `hooks/session-start`, `hooks/stop`)
- Plugin-facing `skills/` tree synced from `packages/claude-skills/`
- Gemini, Cursor, Codex, and Kimi platform entry files
- OpenCode install guide under `.opencode/INSTALL.md`
- Init, update, and install docs now include project-local `.sybermem/hooks/task_recall.py` distribution and explain that Claude `UserPromptSubmit` handles both record-intent capture and read-only task recall
- User Habit Memory visible reminders via `sybermem habit remind`, Claude managed prompt-hook reminders, and the `/sybermem-habit` skill
- Codex user-skill support: global installers copy SyberMem user skills to `~/.agents/skills`.
- Codex verification: health checks discover templates from the Codex user skill install, with package guards for the skill smoke path.
- OpenCode prompt-time recall and User Habit Memory reminders via supported `chat.message` + `experimental.chat.system.transform` hooks, with shared CLI recall/habit packets and visible markers.
- OpenCode prompt-time record-intent metadata capture and bounded recall debug logging via `chat.message`, both prompt-free and installed through the existing single-file plugin target.
- Codex bounded `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` runtime support: startup context, prompt-time project recall, User Habit Memory reminders, record-intent capture, loop-safe Stop record nudges, and compact re-seed markers; hidden auto-resume, background automation, prompt/agent handler runtimes, direct compaction prompt injection, and SyberMem-managed `.codex/config.toml` remain unsupported.

### Changed
- `using-sybermem` now includes a `<SUBAGENT-STOP>` guard
- SessionStart bootstrap context now includes a short SyberMem skill catalog
- Codex plugin metadata and platform docs now describe user-skill support plus bounded managed hooks, without claiming hidden auto-resume or broad runtime automation.
- Public install docs now describe OpenCode and Codex prompt-time support accurately: OpenCode supports project recall plus habit reminders through its chat transform hooks, while Codex supports startup context through `SessionStart` and prompt recall/habit reminders through `UserPromptSubmit` `additionalContext`.
- OpenCode plugin source is split under `packages/opencode-plugin/src/` and bundled back to `packages/opencode-plugin/sybermem.ts` for installer compatibility.
