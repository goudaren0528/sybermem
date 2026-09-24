# Changelog

## Unreleased

## 0.7.0 - 2026-09-24

### Added
- OpenCode V2 ships separate server and TUI companion bundles alongside an independent V1 compatibility plugin; upgrades transactionally replace managed artifacts to prevent double loading.

### Changed
- Claude Code's four hooks now dispatch through one absolute, fail-open launcher with safer migration and health diagnostics; Claude Code 2.1.139 is the minimum for these managed exec hooks.

### Known limitations
- V2 cannot append legacy reply-body markers; feedback uses TUI toasts and read-only summaries instead. Background remote-version refresh has not been restored. Real-model and TUI end-to-end acceptance was not exercised for this release.

## 0.6.0 - 2026-09-08

### Changed
- `/sybermem-record` is now the single entry point for creating, supplementing, or correcting project memory. It can update the five supported relations on existing records with source-only, idempotent, conflict-safe behavior while preserving the existing create-record and norm-crystallization paths.
- `/using-sybermem` now has a thin default orientation path: it resolves the project root, reports a compact installation/project state, routes through the canonical `sybermem next-step --format json`, and presents exactly one recommended command without running any downstream action. The hook/anchor/legacy-protocol health checklist and the CLI-unavailable fallback decision graph are retained in full, but moved into an explicitly read-only "Advanced diagnostics" section used only when CLI routing is unavailable or a health signal is unhealthy.
- Skill discovery is now tiered for progressive disclosure instead of presenting a flat surface: `README.md`, `README.en.md`, `INSTALL.md`, and `docs/feature_map.md` lead with seven Core entrypoints (`using-sybermem`, `sybermem-init-project`, `sybermem-record`, `sybermem-resume`, `sybermem-search`, `sybermem-digest`, `sybermem-habit`) and then present six advanced/lifecycle entrypoints (`sybermem-install`, `sybermem-update`, `sybermem-uninstall`, `sybermem-summary`, `sybermem-phase-analyze`, `sybermem-theme-digest`). Every Skill stays fully supported and directly invocable — the tier reflects frequency, never deprecation — and no Skill was merged or retired to achieve it.

### Removed
- Retired the redundant top-level `/sybermem-link` skill. Existing relation frontmatter and search behavior remain compatible; global install/update removes old copies from Claude Code, OpenCode, and Codex skill homes, and relation updates now use `/sybermem-record`.

## 0.5.0 - 2026-09-07

### Added
- Project INDEX generation is now complete and deterministic from canonical records and digests: `sybermem project index build` regenerates Key Conclusions, Archived Conclusions, phase/theme digest navigation, record tables, Usage, and Topic Index without depending on a previously committed INDEX. Digest-covered conclusions are derived into Archived Conclusions, including both block-list and inline `source_records` formats.

### Changed
- `.sybermem/INDEX.md` is now a machine-local, Git-ignored derived artifact for every project. Teams share canonical record and digest files only; each machine rebuilds INDEX locally, eliminating derived-file diff and merge-conflict noise.
- Project identity now uses `.sybermem/project.yaml` (with `.claude/settings.json` compatibility) instead of INDEX existence across Core, OpenCode, Claude Code, Codex, and global launchers. Portfolio, workspace indexing, search, startup context, and health checks continue to work when INDEX is absent.
- `sybermem project refresh` automatically migrates an already-tracked INDEX with a guarded `git rm --cached`: the working file is preserved, no commit or force operation is performed, failures remain retryable, and repeated refreshes are idempotent.

## 0.4.2 - 2026-09-07

### Added
- Claude Code now produces recall-outcome evidence: a fail-open `Stop` hook (`recall_outcome_on_stop.py`) reconciles the record IDs injected during a session against the files actually edited (via `git diff`), and writes the same `.recall-outcomes.jsonl` and `.memory-usage.jsonl` `session_outcome` rows that `sybermem project memory-stats` already reads from Codex and OpenCode. Claude also now journals per-turn injected record IDs (previously missing), so recall relevance/precision can populate on Claude-Code-driven projects instead of staying permanently null.

### Fixed
- Habit candidate capture no longer fires on non-preferences that merely contain a durable-word trigger: project-specific branch/PR conventions, analysis/summary/"propose general norms" requests, and information-seeking or complaint questions are now rejected in both the OpenCode prefilter and the authoritative Core classifier, while explicit first-person preferences (including polite-question and cross-project PR/branch workflows) are still captured. Persisted stale false-positive candidates are pruned non-destructively on read (only when their bounded summary positively matches a known false-positive shape and no longer classifies), so upgrading users stop seeing spurious habit-candidate reminders without losing legitimate pending candidates.

## 0.4.1 - 2026-09-01

### Added
- New `sybermem-install` skill: a first-time installer entrypoint that lets a new user install the complete SyberMem system from inside an agent conversation. It is a thin orchestration layer that runs the official remote install script (landing skills for all three hosts, Codex hooks, Claude launchers, the CLI runtime, the OpenCode plugin, and the version marker), then verifies each host plus the shared CLI is ready, and initializes the current project via the CLI-first `sybermem project refresh` path (since freshly-installed skills are not hot-loaded in the current session). It is a fully managed skill distributed by every install/update path alongside the other SyberMem skills.

## 0.4.0 - 2026-09-01

### Added
- User Habit Memory now has read-only prompt-time diagnostics: `sybermem habit test --context <text>` explains active/evaluated/selected counts, pending candidates, and per-habit score/floor/reason decisions, while `sybermem habit explain --id <habit-id> --context <text>` focuses on a single habit.

### Changed
- Prompt-time habit reminders now reuse the same evaluator as the diagnostic commands, keeping dry-run decisions and real model-visible reminder selection aligned without lowering the conservative habit injection gate.

## 0.3.0 - 2026-09-01

### Added
- Codex now writes metadata-only recall/memory observability rows for prompt-time recall, startup context, and best-effort `SessionEnd` edit alignment, so `sybermem project memory-stats` can report Codex recall/lane activity alongside OpenCode.
- Codex prompt-time memory injection now has explicit visibility markers with lane counts and record IDs, plus a default-on env-gated `systemMessage` summary for clients that surface hook messages.

### Changed
- Codex installers now register `SessionEnd`, copy the shared observability helper, use `statusMessage` for hook visibility, and keep managed uninstall/guard manifests in sync with the expanded hook set.
- Project gitignore management now ignores `.sybermem/.memory-usage.jsonl` so local runtime memory-usage journals do not enter Git.

## 0.2.4 - 2026-08-27

### Fixed
- Habit candidate capture no longer fires on one-off requests that merely contain a preference-shaped word: bare "我希望" (a generic "I want you to …" request) now only counts as a durable preference when paired with a standing-time word (以后/每次/默认/一律/总是), and "默认" must be followed by a verb (默认用/先/都) so a plain noun usage like "指定默认调用的模型" is not captured. This closes a class of noisy pending candidates left after the 0.2.3 discussion/task filter while still capturing genuine preferences like "我希望以后都用中文回复".

## 0.2.3 - 2026-08-27

### Fixed
- Habit candidate capture now requires explicit durable preference phrasing and ignores habit-system discussion, delegated research/review prompts, and one-off project task wording, reducing noisy pending candidates while preserving confirmation-first habit memory.

## 0.2.2 - 2026-08-27

### Added
- Recall search now includes machine-readable scoring explanations, including matched fields and score breakdowns, so CLI users can understand why a memory was retrieved.
- Recall health now reports `low_measurability` when records are missing enough `related_files` anchors to evaluate edit alignment reliably.
- Project search can expand strong direct record/relation hits through one-hop typed relations (`implements`, `fixes`, `related`, `supersedes`, `superseded_by`) with bounded provenance.

### Changed
- Prompt-time recall remains conservative while allowing capped relation-expanded rows only behind high-signal seeds; weak keyword, topic, and semantic-only matches still abstain from injection.
- CLI JSON/text recall surfaces now expose relation expansion provenance without bloating prompt-time Markdown packets.

## 0.2.1 - 2026-08-26

### Added
- User Habit candidates now carry a bounded, secret/injection-filtered `summary` of the triggering prompt (≤160 chars, mirroring the record-intent summary contract) plus a stable `candidate_id`, so `/sybermem-habit` can propose a normalized statement from your own words instead of having only a type/scope with no content.
- Habit candidates are stored as a bounded list (most recent 5, 10-day expiry, deduped by summary) instead of a single overwritable entry, so a stale unrelated candidate can no longer mask the one you want to confirm. New CLI: `sybermem habit intent-discard <candidate-id>` discards one candidate; `sybermem habit intent-clear` now clears all. `habit intent-status --format json` returns `{count, candidates[], candidate}` (newest first) and `habit awareness` reports `pending_count`. The legacy single-object candidate file is still read for backward compatibility.
- The `sybermem-habit` skill now opens with a default status view (active habits + pending candidates with relative age and summary) and supports one-step confirm-from-summary and single-candidate discard.
- Pending habit candidates are now surfaced across all three hosts on a durable, non-throttled surface: OpenCode injects a model-visible "Habit Candidate" reminder (once per candidate set per session) and startup context, and Claude Code and Codex add a pending-candidate line at `SessionStart`, all from the single `habit awareness` source of truth.

### Fixed
- Habit injection could stay silent forever: the candidate-confirmation reminder was only shown via a one-shot throttled toast (swallowed after its first fire) and was not surfaced on Claude Code or Codex at all, so users never confirmed a candidate and no active habit was ever created. Reminders are now durable and cross-host.
- Unified the user-habit home: the launcher no longer forces `SYBERMEM_HOME` to the install-managed `~/.claude/sybermem/cli`, so a habit added via a bare `sybermem` and one added via the launcher no longer land in two divergent stores (which made habits silently invisible to host injection). Core now treats the documented `~/.sybermem` as canonical and performs a one-time, non-destructive import of any habit data (habits, pending candidate, injection log) left in the legacy home, guarded so a cleared candidate is never re-imported and the legacy source is preserved.
- OpenCode startup context no longer skips habit awareness / pending-candidate for projects that have no key conclusions, digest, or norms (previously an early return dropped it).

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

