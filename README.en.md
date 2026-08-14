[中文](README.md) | **English**

# SyberMem

SyberMem is a project and team engineering-memory system for AI coding workflows. It stores context, decisions, rationale, and phase conclusions as local Markdown so the next session does not have to rebuild project history from scratch.

## Why It Exists

AI agents can move quickly inside one context window, but cross-session work often loses three important signals:

- why a design was chosen
- which problems were already found or fixed
- what the safest next step is now

SyberMem preserves those signals through structured records, derived indexes, phase/theme digests, and bounded read-only resume views. Data lives in the project's `.sybermem/` directory, so humans and AI agents can inspect it directly without relying on a black-box service.

## Quick Start

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

Then open a target project:

```text
/sybermem-init-project
/sybermem-record
/sybermem-resume
```

The usual loop is: initialize the project, record meaningful work after a session, then start the next session with `/sybermem-resume` to see the current phase, recent progress, risks, recommended next action, confidence, and freshness.

## What a Memory Record Looks Like

`/sybermem-record` writes Markdown records under `.sybermem/changes/`, `.sybermem/decisions/`, `.sybermem/requirements/`, or `.sybermem/bugs/`:

```markdown
---
type: change
record_id: change-6a3ab8a0e44e4c41843b66bde8b7134a
date: 2026-08-07
title: UUID-backed record IDs and derived project index
key_conclusion: Use UUID record IDs and a derived INDEX so parallel records merge safely
topics: [architecture, collaboration, quality]
implements: [requirement-002]
---

## Change Content
...

## Reason
...

## Impact Scope
...
```

`.sybermem/INDEX.md` is derived from canonical records and acts as the navigation and session-start key-conclusion layer. Long-term compression lives in phase digests and theme digests.

## Current Capabilities

### Project Memory

- structured records: `change` / `decision` / `requirement` / `bug`
- UUID-backed `record_id` values, with legacy numeric record IDs still readable
- derived `.sybermem/INDEX.md` from canonical records
- phase digests and theme digests for phase/topic compression
- record relations: `implements` / `fixes` / `related` / `superseded_by`
- read-only resume: `/sybermem-resume` and `sybermem resume`
- memory stats: `sybermem project memory-stats` prints 7d/30d terminal tables by default, and `--format json` emits structured stats for `/sybermem-summary`
- project search: `/sybermem-search` and `sybermem search`
- next-step guidance: `/using-sybermem` and `sybermem next-step`

### Workspace / Hub

- project registry
- workspace SQLite FTS5 search index: `sybermem index build`
- workspace search with project, type, and status filters
- recovery guidance for missing, incompatible, or stale indexes
- portfolio view: `sybermem portfolio`

### Team Memory

- Team repo initialization: `sybermem team init`
- read-only publish preview: `sybermem publish status --preview`
- publish with a reviewed preview hash to avoid stale writes
- automatic Team overview rebuilds
- Team management summary: `sybermem team summary`
- phase/theme digest history sync into the Team repo
- matching skills: `/sybermem-team-publish`, `/sybermem-team-summary`

### User Habit Memory

- user-level habit storage: `~/.sybermem/user-habits/`, or `SYBERMEM_HOME/user-habits/` in tests/custom environments
- explicit capture: `sybermem habit add --type workflow --applies-to planning "Prefer plans before implementation"`
- review and governance: `sybermem habit list`, `search`, `pause`, and `delete`
- visible reminders: `sybermem habit remind --context planning --format markdown` and `/sybermem-habit`
- manual/compaction injection: `sybermem habit inject --context planning --format markdown`
- conservative gates: only active, high-confidence, directly relevant, non-excluded habits are injected, with a maximum of three
- habits are not stored in project `.sybermem/` records and are not published to Team memory by default

## CLI vs Skill Boundaries

SyberMem has two execution paths with different reliability properties:

| Path | Representative capabilities | Notes |
|---|---|---|
| CLI / Core | `sybermem resume`, `search`, `next-step`, `portfolio`, `index build`, `project index build/check`, `project memory-stats`, `record id`, `habit add/list/search/pause/delete/remind/inject`, `team init/summary`, `publish status`, `project uninstall` | Programmatic and scriptable; best for deterministic queries and publication flows |
| Skill orchestration | `/sybermem-record`, `/sybermem-habit`, `/sybermem-link`, `/sybermem-digest`, `/sybermem-theme-digest`, `/sybermem-phase-analyze`, `/sybermem-phase-confirm` | AI edits `.sybermem/` Markdown or invokes user-level habit CLI according to skill instructions; best for work that requires judgment and synthesis |

`sybermem record id --type <change|decision|requirement|bug>` only mints a canonical record ID. Full record creation still happens through `/sybermem-record`.

## Platform Support

For the detailed capability matrix, see the [SyberMem Feature Map](docs/feature_map.md); this section keeps only the common platform summary.

| Platform | Support level | Notes |
|---|---|---|
| Claude Code | Full integration | plugin metadata, skills, SessionStart / Stop / UserPromptSubmit hooks |
| OpenCode | Supported integration | skills + TypeScript plugin; session lifecycle, prompt-time project recall, User Habit Memory reminders, record-intent metadata, and recall debug logging on supported plugin/chat transform seams |
| Codex | Partial runtime + skills | user-level skills at `~/.agents/skills`, plus managed `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` hooks for bounded startup context, prompt-time recall, habit reminders, record-intent capture, Stop record nudges, and compact re-seed markers; still no hidden auto-resume, background automation, or agent runtime |

Claude Code managed projects can use `UserPromptSubmit` for bounded reminders when prompts look like reusable preferences or when prompt-approved habits match; existing projects need `/sybermem-update` to refresh the hook. OpenCode uses `chat.message` + `experimental.chat.system.transform` for per-prompt high-signal project recall and injects User Habit Memory reminders into the same turn's system prompt; `chat.message` also writes bounded `.sybermem/.record-intent.json` and `.sybermem/.recall-debug.jsonl` metadata without storing raw prompt text. `⭐`/`💡` still mark visible recall, while habit reminders stay conservative, only active, high-confidence, directly relevant, prompt-ok-when-supported items, with bounded output and fail-open behavior. Codex now installs `~/.codex/hooks/sybermem_session_start.py`, `sybermem_user_prompt.py`, `sybermem_stop.py`, and `sybermem_post_compact.py` and merges them into `~/.codex/hooks.json` under `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact`. `SessionStart` and `UserPromptSubmit` use `hookSpecificOutput.additionalContext` for bounded startup context, prompt-time project recall, and User Habit Memory reminders. `UserPromptSubmit` also writes bounded `.sybermem/.record-intent.json` metadata for explicit record requests without storing raw prompt text; `Stop` provides a loop-safe record nudge; `PostCompact` writes a compact re-seed marker only. Codex still does not support hidden auto-resume, background automation, prompt or agent handler runtimes, and it does not install `.codex/config.toml`. See [`.codex/INSTALL.md`](.codex/INSTALL.md) for Codex details and [`.opencode/INSTALL.md`](.opencode/INSTALL.md) for OpenCode details.

## Install and Upgrade

### One-Line Install

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

This refreshes user-level Claude Code skills, OpenCode skills, Codex skills (`~/.agents/skills`), the OpenCode plugin, the Codex `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` hooks, and the CLI / Core runtime. The installer creates a fixed CLI launcher at `$HOME/.claude/sybermem/cli/sybermem` on macOS / Linux and `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd` on Windows. SyberMem's OpenCode plugin, Codex hooks, and CLI-using skills prefer this fixed launcher when a subprocess cannot resolve bare `sybermem`; install scripts do not modify persistent PATH by default.

### Local Plugin Validation

```bash
claude --plugin-dir .
```

Use this from a repository checkout to validate the Claude Code plugin, hooks, and skills locally.

### Upgrade Order

1. Re-run the global install / update command first.
2. Open each existing project and run `/sybermem-update`.
3. For new projects, run `/sybermem-init-project`.

The global refresh updates user-level runtime, Claude/OpenCode/Codex skills, the OpenCode plugin, and the Codex user-level hooks. Project-local `.sybermem/`, hooks, templates, and instruction files are refreshed by `/sybermem-update`. `/sybermem-update` now calls `sybermem project refresh --format json` first for scriptable project-local refresh, falling back to agent-orchestrated `/sybermem-init-project` only when the CLI is missing, exits nonzero, or emits invalid JSON. Codex health checks treat `~/.agents/skills/sybermem-init-project/project-files` as one template source, so the Codex install path participates in project freshness checks. Old users who need the new OpenCode habit-reminder, record-intent metadata, or recall debug logging path should re-run the global install/update first to refresh `~/.config/opencode/plugins/sybermem.ts`, then run `/sybermem-update` in the project. The same order applies to fixes for the CLI launcher, OpenCode plugin, Codex hook, or skill instructions.

## Initialize a Project

Run this in the target project:

```text
/sybermem-init-project
```

It creates or refreshes:

- `.sybermem/`
- `.sybermem/digests/`
- `.sybermem/theme-digests/`
- `.sybermem/analysis/phase-index.md`
- `.sybermem/project.yaml`
- `.sybermem/hooks/`
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json`

If a project already has custom `.claude/settings.json` content, SyberMem patches only recognized managed entries and does not overwrite unrelated hooks, env, or instructions.

## Daily Usage

### Project Owner

- `/sybermem-resume`: get a bounded read-only resume view
- `/sybermem-record`: record a meaningful round of work
- `/sybermem-search`: search historical records
- `/sybermem-habit`: add, review, pause, delete, or remind user-level habits
- `/sybermem-summary`: inspect current project state
- `/sybermem-digest`: capture a stable phase conclusion
- `/sybermem-theme-digest`: capture a cross-phase topic conclusion
- `/sybermem-team-publish`: preview, review, then publish into Team memory

### Manager / Management Agent

- `/sybermem-team-summary`: generate the Team management summary
- read `dashboards/current-overview.md` and `latest-management-summary.md` in the Team repo

### When Unsure What To Do Next

- `/sybermem-resume` (slash skill): restore current context first
- `/using-sybermem` (slash skill): inspect state and get the recommended command
- `sybermem next-step` (terminal CLI command, **not** a slash command — there is no `/sybermem-next-step`): get next-step guidance directly; `/using-sybermem` calls it internally, and it shares the same router as `/sybermem-resume`, so they agree

## Indexing and Search

- `.sybermem/INDEX.md` is a derived project navigation file rebuilt by `sybermem project index build` and checked by `sybermem project index check`.
- `sybermem project memory-stats` renders 7d/30d tables for record counts, type distribution, recall events, injected/abstained counts, and recall rate; `--format json` is available for skills and automation. Recall metrics come only from `.sybermem/.recall-debug.jsonl`; a missing log means stats are unavailable, not that recall activity was zero.
- `sybermem index build` builds the workspace SQLite FTS5 index for cross-project search.
- Project search defaults to lexical matching and scoring over parsed Markdown records; use the workspace index for cross-project search.
- Optional `SYBERMEM_SEMANTIC_RECALL=1` enables a local char n-gram recall supplement for explicit search. It does not automatically inject recall into every prompt.

## Team Workflow

Recommended path:

1. Keep recording and digesting inside each project.
2. Generate a read-only preview with `/sybermem-team-publish` or `sybermem publish status --preview --format json`.
3. Review source revision, source hash, freshness, conflicts, and review-required state.
4. Publish with the reviewed preview hash.
5. Let Team overview rebuild automatically.
6. Generate a management summary with `/sybermem-team-summary` or `sybermem team summary`.
7. Drill into full digest history when details are needed.

## Repository Structure

```text
.claude-plugin/                      # Claude Code plugin metadata and marketplace manifest
hooks/                               # Claude Code hook declarations and delegators
skills/                              # Plugin-facing skills tree
packages/claude-skills/              # Skill source for distribution
packages/core/                       # Core memory / Team publication logic
packages/cli/                        # sybermem CLI
packages/opencode-plugin/            # OpenCode plugin
.codex-plugin/                       # Codex marketplace/entry metadata
.codex/                              # Codex install notes and bounded habit hook
scripts/                             # Install, update, uninstall, and package-check scripts
```

## Uninstall

### Project-Level Uninstall

```text
sybermem project uninstall
```

This deactivates SyberMem runtime management in the project while preserving `.sybermem/` history and removing only managed hook / env / instruction-block content where possible.

### Global Uninstall

```bash
# Windows (PowerShell)
.\scripts\uninstall.ps1

# macOS / Linux
./scripts/uninstall.sh
```

Global uninstall removes user-level skills, CLI, launchers, and the OpenCode plugin. It does not delete `.sybermem/` history from any project.

## Compatibility

- `.sybermem/` is the current canonical project data directory.
- If a project still uses legacy `ADR/`, the first relevant SyberMem workflow migrates it to `.sybermem/`.
- Claude prompt-time recall applies to managed Claude hooks; OpenCode uses `chat.message` + `experimental.chat.system.transform` for high-signal project recall and conservative User Habit Memory reminders, and `chat.message` writes prompt-free record-intent and recall debug metadata; Codex uses `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` for bounded startup context, prompt-time recall, habit reminders, record-intent capture, loop-safe record nudges, and compact re-seed markers, but still does not claim hidden auto-resume, background automation, or direct compaction prompt injection.
- For more installation, upgrade, and compatibility details, see [INSTALL.md](INSTALL.md).

## License

MIT
