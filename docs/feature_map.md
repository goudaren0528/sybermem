# SyberMem Feature Map

Last updated: 2026-08-27 (recall accuracy Phase 1: key_conclusion/path-aware ranking, JSON explanations, low_measurability health; OpenCode memory injection observability, Edit Alignment semantics, project binding-norm subsystem)

This is the source-of-truth feature map for SyberMem project capabilities and
platform support claims. Public READMEs and platform install docs should stay
consistent with this file.

## Support Legend

| Label | Meaning |
|---|---|
| Full | Real platform runtime, hook, plugin, or CLI support exists and the capability can run automatically where described. |
| Partial | Real support exists, but only for a narrower sub-capability. |
| Manual | User or agent must explicitly invoke a skill or CLI command. |
| Metadata | Only manifest, entry-file, or documentation support exists; no runtime wiring is installed. |
| Unsupported | Not implemented and must not be claimed as supported. |

## Platform Summary

| Platform | Current Level | Mechanism | Current Conclusion |
|---|---|---|---|
| Claude Code | Full | `.claude-plugin` plus `SessionStart`, `UserPromptSubmit`, and `Stop` hooks | Full baseline platform for prompt-time recall, record intent, habit reminders, startup context, and stop-time nudges. |
| OpenCode | Full for supported seams | TypeScript plugin with `session.created`, `session.idle`, `chat.message`, `experimental.chat.system.transform`, and `experimental.session.compacting` | Real runtime integration. OpenCode now supports prompt-time project recall, bounded User Habit Memory reminders, record-intent metadata capture, and recall debug logging through supported plugin seams. |
| Codex | Partial runtime plus skills | User skills under `~/.agents/skills` plus managed `.codex/hooks/session_start.py`, `.codex/hooks/user_prompt.py`, `.codex/hooks/stop.py`, and `.codex/hooks/post_compact.py` registered under supported Codex hook events | Not skills-only anymore. Codex supports bounded startup project context, prompt-time project recall, User Habit Memory reminders, record-intent capture, loop-safe Stop record nudges, and compact re-seed markers through supported Codex seams. |
| Gemini | Metadata | `gemini-extension.json` and `GEMINI.md` | Entry/manifest support only. No SyberMem runtime hooks or installer-managed Gemini integration. |
| Cursor | Metadata | `.cursor-plugin/plugin.json` | Manifest support only. No SyberMem runtime hooks or installer-managed Cursor integration. |
| Kimi | Metadata | `.kimi-plugin/plugin.json` | Manifest support only. No SyberMem runtime hooks or installer-managed Kimi integration. |

## Capability Matrix

| Capability | Claude Code | OpenCode | Codex | Gemini | Cursor | Kimi |
|---|---|---|---|---|---|---|
| User-level skills | Full: plugin/user skills | Full: copied to `~/.config/opencode/skills` | Full: copied to `~/.agents/skills` | Metadata/entry only | Metadata only | Metadata only |
| CLI/Core access | Full | Full; plugin and CLI-using skills prefer the fixed launcher | Full when invoked manually or from skills; hook also prefers fixed launcher | Manual only if `sybermem` is installed | Manual only if `sybermem` is installed | Manual only if `sybermem` is installed |
| Project memory records | Full via `.sybermem/` | Full via the same project `.sybermem/` | Full via manual skills/CLI | Manual only | Manual only | Manual only |
| Project init/update | Full: `/sybermem-init-project`, CLI-first `/sybermem-update` using `sybermem project refresh --format json` | Full through skills; project update uses the same CLI-first refresh | Full through user skills; project update uses the same CLI-first refresh | Manual/entry guidance only | Manual/entry guidance only | Manual/entry guidance only |
| Session-start project context | Full: `SessionStart` hook | Full model-visible: `session.created` toast plus a one-shot first-turn startup context injected via `experimental.chat.system.transform` | Partial runtime: managed `SessionStart` hook emits `sybermem context session --format markdown` through `hookSpecificOutput.additionalContext` | Unsupported | Unsupported | Unsupported |
| Stop/idle change nudge | Full: `Stop` hook | Full on OpenCode seam: `session.idle` record/digest nudges and bounded auto-trail journal | Partial runtime: managed `Stop` hook emits one bounded record nudge and respects `stop_hook_active` loop prevention | Unsupported | Unsupported | Unsupported |
| Prompt-time project recall | Full: `UserPromptSubmit` task recall | Full on OpenCode seam: `chat.message` plus `experimental.chat.system.transform` | Partial runtime: managed `UserPromptSubmit` hook delegates to `sybermem context recall --query <prompt>` and injects only high-signal recall hints | Unsupported | Unsupported | Unsupported |
| Prompt-time recall markers | Full: `⭐` important and `💡` ordinary recall hints | Full: same markers injected on qualifying prompts | Full for qualifying Codex recall output: same shared CLI recall markdown | Unsupported | Unsupported | Unsupported |
| Prompt-time recall observability log | Full where Claude prompt hook logs recall injection/abstention | Full on OpenCode seam: `.sybermem/.recall-debug.jsonl` appends bounded inject/abstain metadata without prompt text | Unsupported | Unsupported | Unsupported | Unsupported |
| Memory injection observability log | Unsupported | Full on OpenCode seam: bounded `.sybermem/.memory-usage.jsonl` per-turn and `session_outcome` rows for memory that actually reached the model-visible prompt | Unsupported in this phase | Unsupported | Unsupported | Unsupported |
| Recall-health self-feedback | Manual via `sybermem project memory-stats` | Full: `session.idle` surfaces a throttled advisory when recent recall is `low_signal`, `low_relevance`, or `low_measurability`, derived from the same `recall_health` verdict | Manual via `sybermem project memory-stats` | Manual only | Manual only | Manual only |
| Edit-aware auto-trail signals | Unsupported | Full on OpenCode seam: `file.edited` / `todo.updated` / `tool.execute.after` accumulate per-session edit focus, todo-batch completion, and test/build signals so record nudges carry a semantic `trigger_reason` instead of raw file counts | Unsupported | Unsupported | Unsupported | Unsupported |
| Recall relevance feedback | Manual via `sybermem project memory-stats` precision | Full on OpenCode seam: `session.idle` flushes a bounded `.recall-outcomes.jsonl` measuring whether injected records' `related_files` were edited, feeding a precision-backed `low_relevance` verdict distinct from `low_signal` | Manual via `sybermem project memory-stats` precision | Manual only | Manual only | Manual only |
| In-session injection visibility | N/A (Claude injects into visible `UserPromptSubmit` context) | Full on OpenCode seam: throttled SEPARATE toasts at `experimental.chat.system.transform` time — `⭐` recall, `🧠` applied habit, `📏` applied project norm — plus a scope-aware `💡` toast when a prompt looks like a reusable preference/norm but no habit matched (`habit_preference_candidate`) | Partial runtime: injected `additionalContext` starts with an ASCII SyberMem Codex marker; no OpenCode-style TUI toast or default Windows desktop toast is claimed | Unsupported | Unsupported | Unsupported |
| Prompt-time User Habit Memory reminder | Full: managed `UserPromptSubmit` hook | Full on OpenCode seam: same chat transform path as recall; habits added via `/sybermem-habit` are prompt-ok-when-supported by DEFAULT (perceptible without extra flags), matched with CJK-aware weighted relevance | Partial runtime: composed into the same managed `UserPromptSubmit` `additionalContext` packet as recall | Unsupported | Unsupported | Unsupported |
| Session-start project constitution (binding norms) | Full: `SessionStart` injects the bounded active-global-norm constitution | Full on OpenCode seam: `experimental.chat.system.transform` startup packet leads with the constitution | Partial runtime: `SessionStart` appends the constitution to `additionalContext` | Unsupported | Unsupported | Unsupported |
| Prompt-time scoped project norms | Full: `UserPromptSubmit` adds scope-matched norms | Full on OpenCode seam: `chat.message` -> system transform adds a `## Relevant Project Norms` packet | Partial runtime: `UserPromptSubmit` appends a scoped-norm section | Unsupported | Unsupported | Unsupported |
| Digest backlog / staleness heads-up | Full: `SessionStart` surfaces stale-digest and undigested-backlog nudges | Full on OpenCode seam: `session.idle` emits a throttled `⭐` backlog toast; startup/compaction surface stale-digest headers | Partial runtime: `SessionStart` appends a backlog heads-up line | Unsupported | Unsupported | Unsupported |
| Prompt-time record-intent capture | Full: `UserPromptSubmit` captures explicit record intent into `.record-intent.json` | Full on OpenCode seam: `chat.message` writes bounded classifier metadata to `.sybermem/.record-intent.json` for explicit write classifications | Partial runtime: managed `UserPromptSubmit` writes bounded classifier metadata to `.sybermem/.record-intent.json` for explicit write classifications | Unsupported | Unsupported | Unsupported |
| Compaction carry-forward | Full through Claude-managed context/hook flow where available | Full: `experimental.session.compacting` injects session context, phase info, the project constitution, the latest digest's conclusions, digest heads-up, next-step, and habit inject output | Partial approximation: managed `PostCompact` writes a compact marker and `SessionStart` with source `compact` re-seeds bounded session context; no direct compaction prompt injection | Unsupported | Unsupported | Unsupported |
| Manual resume/search/record/habit | Full | Full | Full via installed skills and CLI | Manual only | Manual only | Manual only |
| Cross-project portfolio | Full via CLI (`sybermem portfolio`) | Full via CLI | Full via CLI | Manual CLI only | Manual CLI only | Manual CLI only |
| Hidden auto-resume | Not claimed as hidden behavior | Unsupported | Unsupported | Unsupported | Unsupported | Unsupported |
| Background automation | Claude managed hook scope only | OpenCode plugin lifecycle scope only; no hidden background worker | Unsupported | Unsupported | Unsupported | Unsupported |
| `.codex/config.toml` management | Not applicable | Not applicable | Unsupported by SyberMem installers; Codex can load inline hooks from config.toml, but SyberMem manages `hooks.json` only | Not applicable | Not applicable | Not applicable |
| Installer coverage | Full: Claude skills, CLI/Core, global launchers | Full: OpenCode skills and plugin | Full: Codex skills, SessionStart/UserPromptSubmit/Stop/PostCompact hooks, hooks.json merge | Version/manifest only | Version/manifest only | Version/manifest only |
| Integrity guards | Full packaging and hook guards | OpenCode plugin route, source/bundle, metadata privacy, update wiring, and fixed-launcher guards | Codex skill distribution, managed hook wiring, honesty, and no-config guards | Version consistency | Version consistency | Version consistency |

## Project/Core Feature Map

| Feature Area | Status | Main Entrypoints | Notes |
|---|---|---|---|
| Project Memory | Full | `.sybermem/changes`, `.sybermem/decisions`, `.sybermem/requirements`, `.sybermem/bugs`, `.sybermem/norms` | Canonical Markdown records with UUID-backed `record_id`, relation fields (`implements`/`fixes`/`related`/`superseded_by`/`crystallized_from`), source/trust metadata, and legacy ID compatibility. `norm` is a first-class binding-rule record type (see Project Norms). |
| Derived Project Index | Full | `sybermem project index build`, `sybermem project index check` | `.sybermem/INDEX.md` is generated from canonical records and can be mechanically checked. |
| Phase Index | Full | `sybermem project phase analyze`, `sybermem project coverage-hash`, `/sybermem-phase-analyze` | Deterministic phase persistence with agent semantic grouping as the primary path: `phase analyze --from-json <file>` validates and atomically writes an agent-produced grouping (confirmed phases + coverage map + `status: analyzed`) to `.sybermem/analysis/phase-index.md`, so analysis is never silently lost. Mechanical `phase analyze` (month+topic buckets) is only a fallback when no agent grouping is available. `coverage-hash` resolves a phase's covered records to real paths (by frontmatter `record_id:`) and returns the `coverage_hash` `/sybermem-digest` stores. This is the one Project-memory capability that DOES change a project-local file (`phase-index.md`); the skills fall back to agent orchestration only when the CLI is missing, broken, or emits invalid JSON. |
| Project Refresh | Full | `sybermem project refresh --format json`, `/sybermem-update` | Deterministic project-local managed-file propagation for `.sybermem/`, hooks, templates, `.claude/settings.json`, and `project.yaml`, plus removal of any legacy SyberMem protocol block from `CLAUDE.md` / `AGENTS.md`; `/sybermem-update` falls back to agent orchestration only when CLI refresh is unavailable or invalid. |
| Scoped Uninstall | Full | `sybermem uninstall --scope project|global`, `/sybermem-uninstall` | Top-level CLI separates project deactivation from global removal. Project scope preserves `.sybermem/` history and deactivates current-project runtime wiring; global scope requires `--yes` and removes managed user-level skills/hooks/plugin/CLI while leaving every project `.sybermem/` history untouched. The skill is the natural-language router and asks when scope is ambiguous. |
| Instruction files (`CLAUDE.md`/`AGENTS.md`) | No injection | `sybermem project refresh --format json`, `check_project_health.py` | SyberMem no longer creates or injects a session protocol into instruction files. Capabilities are delivered by hooks/plugin reading `.sybermem/` directly, not by these files. init/update only MIGRATES old projects: a legacy `SYBERMEM_SESSION_PROTOCOL` block is removed (whole file deleted with `.bak` when purely SyberMem-managed, otherwise only the block is stripped and user content preserved). Fresh projects get no instruction file. |
| Project Memory Stats | Full | `sybermem project memory-stats`, `sybermem project memory-stats --format json`, `/sybermem-summary` | Deterministic 7d/30d memory and recall observability plus a `recall_health` verdict (`healthy`/`low_signal`/`low_relevance`/`low_measurability`/`no_activity`/`no_log`) with an Edit Alignment proxy. Text mode prints terminal tables for recall events, Edit Alignment, and Memory injection turns/items/chars, avg chars/turn, p95 chars/turn, plus 30d lane distribution; JSON mode feeds `/sybermem-summary` and host advisories. Recall frequency is backed by `.sybermem/.recall-debug.jsonl`; Edit Alignment and memory-injection stats are backed by OpenCode `.recall-outcomes.jsonl` and `.memory-usage.jsonl`. A missing log means unavailable, not zero activity. |
| Recall Relevance | Full | `sybermem project record-files`, `.sybermem/.recall-outcomes.jsonl`, `.sybermem/.memory-usage.jsonl`, OpenCode `file.edited`/`todo.updated`/`tool.execute.after` | Edit-aware relevance: injected records whose declared `related_files` were edited count as hits; precision below a floor (with a minimum sample size) yields a `low_relevance` verdict distinct from frequency-based `low_signal`. Records without a `related_files` anchor are excluded from the precision denominator rather than counted as misses, surfaced as unmeasurable, and can produce `low_measurability` when enough edit evidence exists. |
| Resume | Full | `/sybermem-resume`, `sybermem resume --mode fast|standard|deep` | Read-only restart brief with phase, progress, risks, confidence, freshness, and next action. |
| Search | Full | `/sybermem-search`, `sybermem search` | Supports project/workspace search, record-id/topic/keyword/relation matching, `key_conclusion` first-class scoring, capped `related_files` path/module boosting, successor guidance, conflict notes, and stale-index warnings. |
| High-signal Recall | Full | Claude `UserPromptSubmit`, OpenCode `chat.message`/transform, Codex `UserPromptSubmit`, `sybermem context recall` | Automatic only on Claude/OpenCode/Codex supported prompt seams. Uses stricter gate than explicit search; Phase 1 improves ranking/explainability without lowering the high-signal threshold. `context recall --format json` exposes matched fields and score breakdowns, while Markdown stays compact for prompt injection. |
| Workspace/Hub | Full | `sybermem index build`, workspace `sybermem search`, `sybermem portfolio` | SQLite FTS5 workspace index with project/type/status filters and stale-index detection. |
| Digest Governance | Full | `/sybermem-digest`, `/sybermem-theme-digest`, `sybermem digest status`, `sybermem digest latest` | Phase/theme digests with coverage hash and current/stale/unknown verdicts. `digest status --format json` also carries a `backlog` object (uncovered records + days since last digest) so a project that keeps recording but never digests gets a proactive nudge; the old "no digest yet" next-step gate now uses a digest-specific record threshold. `digest latest` returns the newest phase digest's Core Conclusions so digest content is injected into startup/compaction, not just recalled. |
| Digest Feedback (effect) | Full | OpenCode startup/compaction, `session.idle`, Claude/Codex `SessionStart`, `sybermem project memory-stats` | Digest results have model-visible effect on multiple lanes: digests are in the search/recall corpus (with `related_digest` continuity links + stale conflict notes); the latest digest's conclusions are injected at OpenCode startup/compaction; memory-stats shows digest coverage; all three hosts nudge when >=5 records are uncovered by any digest. |
| Cross-project portfolio | Full | `sybermem portfolio` | Read-only aggregate over the Hub registry: each registered project's phase, open bugs/requirements, digest coverage, and latest record date. No separate Team repo or publish pipeline. Collaboration is via Git-shared `.sybermem/`; the earlier standalone Team publication subsystem was removed (redundant for single-repo Git sharing). |
| User Habit Memory | Full | `/sybermem-habit`, `sybermem habit add/list/search/pause/delete/remind/inject/intent/intent-status/intent-clear/awareness` | User-owned storage under `~/.sybermem/user-habits` or `SYBERMEM_HOME/user-habits`; not project memory. `add` now defaults `injection_policy=prompt_ok_when_supported`, so a confirmed habit is perceptible at prompt time (🧠) on supported hosts without extra flags; relevance uses CJK-aware weighted matching (an `applies_to` tag match is a strong boost, otherwise >=2 distinct multi-char statement overlaps), so Chinese contexts match while unrelated habits stay silent. |
| Habit intent capture | Full (candidate-only) | `sybermem habit intent`, OpenCode `chat.message`, `~/.sybermem/.habit-intent.json` | Passively classifies a reusable-preference prompt into a candidate-only intent written to the user-level intent file. NEVER creates an active habit and never persists secrets/injection text; `/sybermem-habit` turns a pending candidate into a habit only after user confirmation, then clears it. The keyword prefilter is a cheap hot-path guard, not the decision. |
| Project Norms (binding rules) | Full | `.sybermem/norms/`, `sybermem norms list/nominate/doctor`, `/sybermem-record` (crystallize), `/sybermem-link crystallized-from` | First-class binding-rule subsystem, distinct from user habits and ordinary decisions. A `norm` record carries `scope` (`global` / `topic:x` / `path:x` / `tool:x`), an imperative `statement`, `authority: authoritative`, and reuses the existing lifecycle + supersede machinery. Two feedback lanes: the always-on bounded **constitution** (active GLOBAL norms, <=5, injected once per session) and **scoped recall** (non-global norms matched by scope tag or >=2 strong statement overlaps, without lowering the recall gate). `norms list --scope global\|scoped\|all --context <text> --format json` is the single source of truth all hosts consume. |
| Norm identification | Full (confirmation-first) | `/sybermem-record` closing step (explicit crystallization), `sybermem norms nominate`, `/sybermem-digest` + `/sybermem-theme-digest` closing steps (emergent) | Two pipelines, both confirmation-first and never auto-promote. Explicit: mark a binding rule at record/closeout time -> crystallize a `norm` (with `crystallized_from` provenance). Emergent: `norms nominate` deterministically finds imperative constraints recurring across >=3 distinct decision/requirement records (not already covered by an active norm) and surfaces them at digest/theme time for one-step confirmation. |
| Norm governance | Full (advisory) | `sybermem norms doctor`, `sybermem project memory-stats` | `norms doctor` flags 2+ active norms in the same scope with overlapping statements (likely contradiction/duplication) and exits non-zero for CI gating; it never edits or deactivates. memory-stats shows norm coverage (active count, global/scoped split, constitution budget usage). |
| Semantic norm nomination (agent judgment) | Skill-orchestrated | `/sybermem-habit`, `/sybermem-record`, `/sybermem-digest` | Beyond the deterministic `norms nominate` detector, the Agent judges whether a statement is a reusable preference or a standing norm — including phrasing with no trigger word. Personal/cross-project preference → user habit; binding project rule → crystallize a `norm`; ordinary non-binding convention → `decision`/`requirement` record. Batched, one-step-confirm, confirmation-first (L1), never mid-flow, dropped on decline. |
| Habit awareness surface | Full | `sybermem habit awareness`, OpenCode startup context, `habit_awareness_summary` | Surfaces habit PRESENCE (active count, type distribution, latest confirmation, pending-candidate flag) in the first-turn startup context and stats without exposing habit statements on the hot path or duplicating prompt-time reminders. |
| Context Helpers | Full | `sybermem context session|prompt|recall|habit` | Shared host-neutral context contract. OpenCode/Codex automation reuses the same conservative CLI behavior where supported. |
| Record Authoring | Skill-orchestrated | `/sybermem-record`; CLI helper `sybermem record id --type ...` | CLI mints IDs and validates indexes; full record writing remains skill workflow. |
| Version / Update notification | Full | `sybermem version`, `sybermem doctor`, `~/.claude/sybermem/VERSION` marker, `.sybermem/project.yaml` `sybermem_version` | Installers write an installed-version marker; `sybermem project refresh` stamps the project's `sybermem_version`. Session-start compares them and, when a project trails the installed SyberMem, surfaces a fail-open, throttled `⭐ run /sybermem-update` nudge (OpenCode `session.created` toast; Claude/Codex `SessionStart` additionalContext). `sybermem doctor` reports installed vs project version on demand. Fail-safe: unknown/empty versions never nag. |
| Distribution/Verification | Full | install/update scripts, `scripts/check-plugin-package.py`, pytest package integrity tests | Installers refresh Claude/OpenCode/Codex skills, OpenCode plugin, Codex hook, CLI/Core runtime, fixed launchers, and guards. |

## OpenCode Detail

| Capability | Status | Mechanism | Boundary |
|---|---|---|---|
| Skills | Full | `~/.config/opencode/skills` | Refreshed by global install/update. |
| Plugin | Full | `~/.config/opencode/plugins/sybermem.ts` | Refreshed by global install/update. |
| Project update | Full | `/sybermem-update` -> `sybermem project refresh --format json` | CLI-first project-local refresh; falls back to `/sybermem-init-project` only if CLI refresh is missing, broken, or non-JSON. |
| Session-start context | Full model-visible | `session.created` + `experimental.chat.system.transform` | `session.created` toasts loaded conclusions and stashes a one-shot startup packet that the first system transform prepends. The packet LEADS with the project constitution (binding global norms), then key conclusions, phase, the latest digest's Core Conclusions, stale/digest heads-up, and next-step. Startup no longer bails when INDEX conclusions are empty if a constitution or digest is available. Habits are excluded (the same first prompt already triggers prompt-time habit injection). Hidden auto-resume is still unsupported. |
| Idle nudge | Full | `session.idle` | Mirrors Claude Stop follow-up thresholds using OpenCode lifecycle seam; also emits a throttled recall-health advisory when recent recall is `low_signal`, `low_relevance`, or `low_measurability` and a throttled `⭐` digest-backlog toast when >=5 records are uncovered by any digest. Record nudges now carry a semantic `trigger_reason` (tests passed / todo batch done / edit focus) derived from edit-aware signals, falling back to the existing file-count heuristic. |
| Edit-aware activity signals | Full | `file.edited`, `todo.updated`, `tool.execute.after` | Per-session in-memory accumulation of edit frequency (edit focus), completed todo batches, and passing-test/clean-build signals. Events only mutate in-memory state; the computation and disk write happen at `session.idle`. No hidden background worker. Payload shapes are read defensively and any missing field degrades to "no signal". |
| Recall relevance feedback | Full | `session.idle` -> `sybermem project record-files` -> `.sybermem/.recall-outcomes.jsonl` | Injected records this session are matched against edited files via their declared `related_files`; a bounded per-session outcome (injected / hit / precision / hit+miss ids) is appended, feeding the precision-backed `low_relevance` verdict. Fail-open and prompt-text-free. |
| Memory injection observability | Full | `experimental.chat.system.transform`, `session.idle`, `.sybermem/.memory-usage.jsonl`, `sybermem project memory-stats` | OpenCode-first telemetry only in this phase. After model-visible injection succeeds, SyberMem appends one bounded per-turn metadata row. At idle it appends one bounded `session_outcome` row with memory/edit/todo/tool/Edit Alignment evidence. No raw prompt text or full injected memory text is persisted. |
| Prompt-time project recall | Full | `chat.message` -> `sybermem context recall` -> `experimental.chat.system.transform` | Same-turn system prompt injection; only high-signal recall qualifies. |
| Prompt-time habit reminder | Full | `chat.message` -> `sybermem context habit --delivery prompt-time` -> system transform | Bounded, fail-open, active/high-confidence/directly relevant/prompt-ok habits only (prompt-ok is now the default policy). |
| Session-start constitution | Full | `session.created` + first `experimental.chat.system.transform` -> `sybermem norms list --scope global` | Injects the bounded active-global-norm constitution once per session, leading the startup packet, so binding norms govern the session regardless of prompt relevance. Fail-open. |
| Prompt-time scoped norms | Full | `chat.message` -> `sybermem norms list --scope scoped --context <prompt>` -> system transform | Adds a `## Relevant Project Norms` packet for scope-matched non-global norms; a distinct `📏` toast fires when applied. Global norms are excluded here (delivered by the constitution). |
| Digest-conclusion injection | Full | `session.created`/compacting -> `sybermem digest latest` | The newest phase digest's Core Conclusions are injected into startup and compaction context, so digest content reaches the model directly (not only via recall). |
| Digest-backlog advisory | Full | `session.idle` -> `sybermem digest status --format json` | Emits one throttled, fail-open `⭐` toast when >=5 records are uncovered by any digest (with age note); reuses the same governance JSON as the stale-digest check. |
| Habit intent capture | Full (candidate-only) | `chat.message` -> `sybermem habit intent --prompt` | Passively classifies a reusable-preference prompt into a candidate written to the user-level `~/.sybermem/.habit-intent.json`; never an active habit, never persists secrets/injection text. |
| Habit awareness in startup | Full | `session.created` + first `experimental.chat.system.transform` -> `sybermem habit awareness` | Adds a bounded "User Habits" line (active count + pending-candidate flag only, never statements) so habits are visible on the first turn without duplicating prompt-time reminders. |
| Compaction carry-forward | Full | `experimental.session.compacting` | Includes session context, the project constitution, the latest digest's Core Conclusions, phase/status, digest heads-up, next-step, and compaction habit inject. |
| Record-intent capture | Full | `chat.message` | Writes `.sybermem/.record-intent.json` only for explicit `change` / `decision` / `requirement` / `bug` write intent metadata; raw prompt text is never persisted. |
| Recall debug log | Full | `chat.message` | Appends bounded `.sybermem/.recall-debug.jsonl` inject/abstain entries with source, timestamp, record IDs, match classes, and reason codes only; raw prompt text is never persisted. |
| Recall-health advisory | Full | `session.idle` -> `sybermem project memory-stats --format json` | Reads the `recall_health` verdict and emits one throttled, fail-open toast only when recent recall is `low_signal`, `low_relevance`, or `low_measurability`; `healthy`/`no_activity`/`no_log` stay silent. |
| Injection visibility toasts | Full | `chat.message` + `experimental.chat.system.transform` | Throttled and fail-open visibility: a scope-aware `💡` candidate toast remains distinct, startup context keeps its one-shot `⭐` notice, and successful prompt-time recall/habit/norm injection emits one combined bounded summary after model-visible insertion with total items, total chars, and non-zero lane counts. Never block or spam the prompt flow. |
| Opt-in reply marker | Full (default OFF) | `experimental.text.complete`, env `SYBERMEM_REPLY_MARKER` | When enabled, prepends ONE line (`> SyberMem: 本轮参考了 ⭐N 条记忆 · 🧠M 条习惯`) to the FIRST assistant text part of a turn that actually received injected recall/habit context — a guaranteed, model-independent visibility signal. OFF by default because the seam is experimental and the marker persists in message history. Only fires when material was injected; marks once per assistant message. |

### OpenCode Research Notes And Next Work

Current OpenCode plugin docs expose a broad TypeScript plugin surface: `event`,
`chat.message`, `chat.params`, `tool.execute.before`, `tool.execute.after`,
`shell.env`, custom `tool` registration, `session.*`, `message.*`, `file.edited`,
`todo.updated`, `tui.*`, and experimental `chat.system.transform` /
`session.compacting`. SyberMem currently uses the highest-value memory seams:
prompt-time system transform, idle lifecycle nudges, startup toast signals, and
compaction context.

Next OpenCode candidates, in priority order:

1. Broaden edit-aware signals beyond git-diff trails (e.g. `file.edited` sequence
   ordering) to pre-fill richer auto-trail entries, still without hidden workers.
2. Use accumulated recall-precision history to auto-tune the high-signal recall
   gate, deprioritizing record types that are consistently injected but never edited.

Recently shipped: model-visible first-turn startup context via `session.created` +
`experimental.chat.system.transform`; a `session.idle` recall-health advisory
derived from `sybermem project memory-stats` `recall_health`; edit-aware auto-trail
signals (`file.edited` / `todo.updated` / `tool.execute.after`) that give record
nudges a semantic `trigger_reason`; and an edit-aware recall relevance feedback loop
(`.sybermem/.recall-outcomes.jsonl` + precision-backed `low_relevance`).

## Codex Detail

| Capability | Status | Mechanism | Boundary |
|---|---|---|---|
| User skills | Full | `~/.agents/skills` | Same SyberMem skill set as other hosts when Codex loads user skills. |
| Project setup/update | Full manual | `/sybermem-init-project`, CLI-first `/sybermem-update` | Refreshes `.sybermem/` and removes any legacy SyberMem protocol block from `AGENTS.md` via `sybermem project refresh --format json` before any agent fallback; no Codex project runtime required. |
| Session-start project context | Partial runtime | `.codex/hooks/session_start.py` registered under `SessionStart` | Emits shared `sybermem context session --format markdown` only when available, prefixed with `## SyberMem Codex Startup`; fail-open and bounded. |
| Habit prompt reminder | Partial runtime | `.codex/hooks/user_prompt.py` registered under `UserPromptSubmit` | Composed with recall in one `hookSpecificOutput.additionalContext` packet, prefixed with `## SyberMem Codex Context` when anything is injected; only bounded `## User Habit Reminder` output qualifies. |
| Session-start constitution | Partial runtime | `.codex/hooks/session_start.py` -> `sybermem norms list --scope global` | Appends the bounded active-global-norm constitution to `additionalContext`; fail-open + timeout-bounded. |
| Prompt-time scoped norms | Partial runtime | `UserPromptSubmit` -> `sybermem norms list --scope scoped --context <prompt>` | Appends a `## Relevant Project Norms` section for scope-matched non-global norms. |
| Digest-backlog heads-up | Partial runtime | `.codex/hooks/session_start.py` -> `sybermem digest status --format json` | Appends a bounded "N records not covered by any digest" line when >=5 records are uncovered. |
| Project memory prompt recall | Partial runtime | `UserPromptSubmit` -> `sybermem context recall --query <prompt>` | Uses shared high-signal recall gate and `⭐`/`💡` markers inside the recall section; qualifying packets also start with a SyberMem Codex summary marker. Abstentions emit no context. |
| Record-intent capture | Partial runtime | `UserPromptSubmit` -> Core `classify_record_intent` | Writes only bounded classifier metadata to `.sybermem/.record-intent.json`; raw prompt text is not persisted. |
| Stop nudge | Partial runtime | `.codex/hooks/stop.py` registered under `Stop` | Emits a bounded `/sybermem-record` continuation nudge only once per changed-file fingerprint and returns nothing when `stop_hook_active` is true. |
| Compact re-seed | Partial approximation | `.codex/hooks/post_compact.py` registered under `PostCompact` plus `SessionStart` source `compact` | `PostCompact` writes `.sybermem/.codex-compact-marker.json` only; later `SessionStart` re-seeds normal session context. No direct compaction prompt injection. |
| Session lifecycle hooks | Partial runtime | Managed `SessionStart`, `Stop`, and `PostCompact`; researched `SessionEnd`, `PreCompact` are available in Codex | SyberMem currently uses only bounded command hooks; hidden auto-resume and background workers are still unsupported. |
| Hidden auto-resume | Unsupported | None | Must not be claimed. |
| Background automation | Unsupported | None | Must not be claimed. |
| `.codex/config.toml` | Unsupported | None | Installers and guards must not create it. |

### Codex Research Notes And Next Work

Current Codex docs and source expose command hooks for `SessionStart`,
`UserPromptSubmit`, `Stop`, `SessionEnd`, `PreToolUse`, `PostToolUse`,
`PermissionRequest`, `PreCompact`, `PostCompact`, `SubagentStart`, and
`SubagentStop`. `SessionStart` and `UserPromptSubmit` support
`hookSpecificOutput.additionalContext`, which is the supported seam SyberMem uses
for startup context, prompt-time recall, scoped norms, and habit reminders. The
managed Codex hooks add model-visible ASCII SyberMem markers inside that same
`additionalContext` payload; SyberMem does not claim a Codex TUI toast API or
install default Windows desktop notifications. SyberMem now uses `Stop` only for
bounded record nudges with `stop_hook_active` loop prevention.
`PreCompact` and `PostCompact` exist, but their output schema has no
`hookSpecificOutput`, so SyberMem uses `PostCompact` only as a marker for a later
`SessionStart` re-seed and cannot directly inject compaction context the way
OpenCode can.

Next Codex candidates, in priority order:

1. Expand the Codex `Stop` hook from record nudges to digest nudges once a shared
   host-neutral digest/changed-file classifier exists.
2. Consider `PostToolUse` feedback only for narrowly scoped memory hygiene, after
   verifying current Codex additionalContext support for that event in the target
   release.
3. Keep installer management on `~/.codex/hooks.json`; do not create or require
   `.codex/config.toml` unless there is a deliberate future decision.

## Explicit Unsupported Claims

All bullets below are unsupported claims. These statements are stale or wrong and
should not appear in current public docs:

- Unsupported claim: OpenCode is manual-only for prompt-time recall.
- Unsupported claim: OpenCode supports only compaction-time habit injection.
- Unsupported claim: OpenCode lacks prompt-time User Habit Memory reminders.
- Unsupported claim: Codex is skills-only.
- Unsupported claim: Codex supports hidden auto-resume, background automation, prompt/agent handler runtimes, or SyberMem-managed `.codex/config.toml`.
- Unsupported claim: Gemini, Cursor, or Kimi have SyberMem runtime integration beyond metadata/entry manifests.
