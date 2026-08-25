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
- Edit-aware recall relevance feedback for OpenCode: `file.edited` / `todo.updated` / `tool.execute.after` accumulate per-session edit focus, todo-batch completion, and test/build signals; `session.idle` matches injected records against edited files (via each record's `related_files`) into a bounded `.sybermem/.recall-outcomes.jsonl`, feeding a precision-backed `low_relevance` recall-health verdict distinct from frequency-based `low_signal`. Record nudges carry a semantic `trigger_reason`, and the `session.idle` advisory now surfaces both `low_signal` and `low_relevance`.
- `sybermem project record-files --ids <a,b> --format json` maps record ids to their declared `related_files`, keeping Markdown parsing in Core for the OpenCode relevance loop.
- `sybermem project memory-stats` now reports a recall precision column/field and the `low_relevance` verdict, backed by `.sybermem/.recall-outcomes.jsonl`.
- Candidate-only User Habit Memory intent capture: OpenCode `chat.message` classifies reusable-preference prompts and calls `sybermem habit intent --prompt`, writing a candidate to the user-level `~/.sybermem/.habit-intent.json`. It never creates an active habit and never persists secrets/injection text; `/sybermem-habit` confirms a pending candidate into a habit in one step and then clears it. New CLI: `sybermem habit intent`, `intent-status`, `intent-clear`, `awareness`.
- Distinct habit injection visibility on OpenCode: applied user habits now get their own `🧠` toast, separate from the recall `⭐` toast, and a captured candidate raises a `💡` toast.
- User-habit awareness surface: `sybermem habit awareness` and the OpenCode first-turn startup context report active-habit counts, type distribution, and a pending-candidate flag (counts only, never habit statements, no duplication of prompt-time reminders).

### Removed (breaking)
- The standalone **Team memory** publication subsystem has been removed. Removed CLI: `sybermem team init`, `sybermem team summary`, `sybermem publish status`. Removed skills: `/sybermem-team-publish`, `/sybermem-team-summary`. Removed core modules: `team`, `team_summary`, `publish`, `publish_bootstrap`, `publish_render`, `publish_sources`.
  - **Breaking API change:** `sybermem project status` (`project_status()`) no longer returns a `publication` object.
  - **Rationale:** for a single team sharing one repo's `.sybermem/` via Git, Team mode targeted a multi-repo manager persona that does not exist; its only unique value (a cross-repo management projection) is now served by the read-only `sybermem portfolio` (Hub-registry based, no separate Team repo, no publish pipeline, no preview hash).
  - **Data safety:** your `.sybermem/` history and any external Team Git repositories are never deleted or modified. Existing `team:` blocks in `.sybermem/project.yaml` are inert and ignored. Upgrading (global install/update + `/sybermem-update`) cleans the retired Team skills from installs via the retired-skill cleanup contract.
  - **Migration:** collaborate via Git-shared `.sybermem/` as before; use `sybermem portfolio` for a cross-project view. External Team repositories remain readable and user-owned but receive no further SyberMem updates.

### Changed
- `using-sybermem` now includes a `<SUBAGENT-STOP>` guard
- SessionStart bootstrap context now includes a short SyberMem skill catalog
- Codex plugin metadata and platform docs now describe user-skill support plus bounded managed hooks; hidden auto-resume and broad runtime automation remain unsupported.
- Public install docs now describe OpenCode and Codex prompt-time support accurately: OpenCode supports project recall plus habit reminders through its chat transform hooks, while Codex supports startup context through `SessionStart` and prompt recall/habit reminders through `UserPromptSubmit` `additionalContext`.
- OpenCode plugin source is split under `packages/opencode-plugin/src/` and bundled back to `packages/opencode-plugin/sybermem.ts` for installer compatibility.
