# Changelog

## Unreleased

## 0.2.0 - 2026-08-26

### Added
- Latest phase-digest Core Conclusions are now injected as model-visible context on all three hosts: OpenCode at startup/compaction, and Claude Code and Codex at `SessionStart` (via each host's session-start hook). `sybermem digest latest` remains the single source, and `sybermem project memory-stats` reports the digest injection lane.
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
- OpenCode injection visibility now emits one bounded post-injection summary after recall, habit, or project norm content actually lands in the model-visible prompt; candidate capture still raises a separate scope-aware `💡` toast, and startup context keeps its separate one-shot notice.
- User-habit awareness surface: `sybermem habit awareness` and the OpenCode first-turn startup context report active-habit counts, type distribution, and a pending-candidate flag (counts only, never habit statements, no duplication of prompt-time reminders).
- Scoped uninstall: `sybermem uninstall --scope project|global` and `/sybermem-uninstall` separate project-level deactivation from global removal, ask when natural-language scope is unclear, and preserve project `.sybermem/` histories.
- Remote-version awareness for OpenCode: `session.created` reads a local cache (`~/.claude/sybermem/.remote-version-cache.json`) and, when stale (>24h), kicks off a fire-and-forget 3s-timeout fetch of `main/VERSION`; when the published version exceeds the installed one it raises a distinct `remote-outdated` toast telling the user to re-run the install script. Fully fail-open, never blocks the hot path, and honors a `SYBERMEM_NO_REMOTE_CHECK=1` kill switch. This is separate from the existing project-behind-installed `/sybermem-update` nudge.

### Fixed
- OpenCode injection toasts fired in the same tick (e.g. `session.idle` nudge + recall-health + digest-backlog, or the first system-transform's startup + prompt-memory) no longer clobber each other: toasts now drain through a serial FIFO queue with a minimum on-screen gap, so each simultaneous SyberMem signal is actually perceptible. `throttledToast` keeps its per-key 30s dedup and the two direct toast callers were rerouted through the queue.

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
- Managed uninstall manifest now separates active `skills` from `retired_skills`, while the remover still cleans both so old users shed retired Team skills on update/uninstall.

