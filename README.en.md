[中文](README.md) | **English**

# SyberMem

SyberMem is an AI-oriented project and team engineering-memory system.

It helps you store:
- project progress
- technical decisions
- phase-level conclusions
- team-facing summaries

as structured memory so project owners, managers, and management agents can keep consuming those signals across sessions.

## Current Capabilities

### Project
- structured records (`change` / `decision` / `requirement` / `bug`)
- persistent phase index
- user-invoked, bounded, read-only `/sybermem-resume`
- phase digests / theme digests
- relations and supersession (`implements`, `fixes`, `related`, `superseded_by`)
- project-level summary / search / link with source-aware trust fields

### Hub
- project registry
- workspace search
- safe guidance for missing or stale workspace indexes
- project status
- portfolio view

### Team
- team init
- Team publish preview, review, and publish-with-hash flow
- team overview
- team management summary
- Team Project Summary
- full phase / theme digest history sync

## Platform support levels

Integration completeness varies by platform. Choose based on the actual level:

| Platform | Support level | Notes |
|---|---|---|
| **Claude Code** | Full | plugin manifest + marketplace + hooks fully wired, validated by `claude plugins validate` |
| **OpenCode** | Full | real TypeScript runtime (`packages/opencode-plugin/sybermem.ts`), script install |
| **Gemini** | Entry integration | `gemini-extension.json` + `GEMINI.md` entry; no deep runtime validation |
| **Codex / Cursor / Kimi** | Metadata placeholder | unified manifest metadata only; no platform runtime hook yet |

> Codex / Cursor / Kimi are metadata placeholders today — they do not yet ship a platform-specific runtime integration.

## Install

### One-line install (recommended for users)

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

The most intuitive path — no clone needed. One command refreshes Claude Code / OpenCode skills, the OpenCode plugin, and the CLI / Core runtime.

### Claude Code plugin install (developers / local validation)

```bash
claude --plugin-dir .
```

Best for loading hooks and skills as a plugin directly inside a local checkout for development or validation.

### OpenCode

OpenCode can also use SyberMem through its plugin/runtime path. See [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

The documented limitation still applies: OpenCode does not expose a documented per-prompt automatic injection callback, so SyberMem does not claim or register unsupported `UserPromptSubmit` prompt injection there. On OpenCode, explicit historical recall is still manual through `/sybermem-search`, while automatic carry-forward is limited to the supported compaction flow.

`/sybermem-resume` is also available manually on OpenCode, but it stays a read-only restart view. It does not auto-run the suggested action, and it does not claim hidden auto-resume, background execution, or unsupported prompt-time injection.

### Install and upgrade order

1. Refresh the global install first.
   - The install scripts refresh Claude Code skills, OpenCode skills, the OpenCode plugin, and the CLI/Core runtime.
   - Re-running the remote install command is a supported global runtime refresh.
2. Then open each target project and run `/sybermem-update`.
   - That is the project-local repair step for managed hooks, templates, instruction files, and managed settings patches.
3. If the project is not initialized yet, run `/sybermem-init-project`.

In short, global first, then project-local. Existing projects do not pick up new managed behavior from a global refresh alone.

## Initialize a Project

Inside your project directory, run:

```text
/sybermem-init-project
```

This creates or refreshes:
- `.sybermem/`
- `.sybermem/digests/`
- `.sybermem/theme-digests/`
- `.sybermem/analysis/phase-index.md`
- `.sybermem/project.yaml`
- `.sybermem/hooks/record_change_on_stop.py`
- `.sybermem/hooks/detect_record_intent.py`
- `.sybermem/hooks/task_recall.py`
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json`

Where:
- `auto` = lightweight `change` trail + reminders
- `remind` = reminders only, with no automatic `change` trail
- the default Claude `UserPromptSubmit` hook handles both natural-language record-intent capture and read-only task recall
- if a project already has a custom `.claude/settings.json`, SyberMem applies only surgical patches to recognized managed entries and does not overwrite unrelated custom hooks, env, or instructions

## Daily Usage

### Project owner
- `/sybermem-resume` — rebuild the current project context from natural language with a bounded, read-only restart brief
- `/sybermem-record` — record a meaningful round of work
- `/sybermem-summary` — inspect current project state
- `/sybermem-digest` — capture a stable phase conclusion
- `/sybermem-theme-digest` — capture a cross-phase topic conclusion
- `/sybermem-team-publish` — preview, review, then publish the current project into Team memory with the preview hash

### Manager / management agent
- `/sybermem-team-summary` — generate the Team management summary
- read `dashboards/current-overview.md` / `latest-management-summary.md`

### If you're unsure what to do next
- `/sybermem-resume` — get the read-only restart brief before choosing whether to run the next step
- `/using-sybermem` — inspect the current state and get the recommended command

## Commands vs Skill orchestration

SyberMem capabilities run through two execution paths with different reliability. Know which is which:

| Category | Capabilities | How it runs | Characteristics |
|---|---|---|---|
| **CLI commands** (program-verified) | `sybermem resume` / `search` / `project status` / `portfolio` / `team init` / `team summary` / `publish status` | Executed directly by the `sybermem` CLI + core | Deterministic, scriptable, stable output |
| **Skill orchestration** (AI-executed) | `/sybermem-record` / `/sybermem-link` / `/sybermem-digest` / `/sybermem-theme-digest` / `/sybermem-phase-analyze` / `/sybermem-phase-confirm` | The AI edits `.sybermem/` markdown per skill instructions | Depends on AI judgement, not a deterministic command |

- `sybermem resume` now provides a **programmatic** restart brief (`--mode fast|standard|deep`, `--format text|json`) alongside the natural-language `/sybermem-resume` skill.
- record / link / digest and similar are skill orchestration: they have no CLI command and rely on the AI following skill instructions to edit markdown records, so their reliability depends on the AI doing so correctly.

## Resume and trust UX

`/sybermem-resume` is the natural-language-first restart entrypoint for requests like "resume this project", "what was I doing", or "what should I do next".

- `fast`: a short restart brief with the current phase, recent progress, top risk, next action, and the reason for that recommendation
- `standard`: the default handoff, with a bit more trust context such as digest coverage or the most important unresolved question
- `deep`: still bounded, but points you to the right records or digests for follow-up instead of auto-reading full history

The restart brief should show current phase, recent progress, risks, next action, confidence, freshness, and reason.

`/sybermem-resume` is read-only. It never auto-executes the suggested action, and it never writes records, digests, or settings. Trust fields should make it clear whether the result is grounded in a current authoritative record, a digest, or lower-confidence supporting evidence. It uses the existing resume, status, search, and next-step path, not a second memory store.

When you need explicit historical evidence, run `/sybermem-search`. Project search and workspace search aim to surface authority, lifecycle, freshness, and successor guidance clearly. Workspace search depends on a `sybermem index build` cache. If that index is missing, stale, or FTS falls back, the system should guide recovery safely instead of inventing recall.

## Team Workflow

The recommended Team workflow today is:

1. record and digest work inside each project
2. generate a read-only preview with `/sybermem-team-publish`
3. review source revision, source hash, freshness, conflicts, and review-required state
4. publish with the reviewed preview hash
5. let Team overview rebuild automatically
6. generate a management summary with `/sybermem-team-summary`
7. drill into digest history when more detail is needed

In other words:

```text
skim status
read digest history for detail
```

### Team support available today
- **Phase A**: `sybermem team init` — create the Team repo skeleton, write `team.yaml`, and bind the Git remote
- **Phase B**: `sybermem publish status --preview --format json` — generate a read-only preview for review
- **Phase C**: `sybermem publish status --preview-source-hash <source_hash> --format json` — perform the actual publish from the reviewed preview
- **Phase D**: automatically rebuild `dashboards/current-overview.md` after each `publish status`
- **Phase E**: remember Team association so `publish status` no longer needs `--team-path` every time
- **Phase F**: `sybermem team summary` — generate a low-cost management summary (markdown + json)
- **Phase G**: sync the full phase / theme digest history into the Team repo
- **Team Skills**: `/sybermem-team-publish` and `/sybermem-team-summary`

> The safe Team publish path is preview → review → publish with hash. The preview is read-only. If publish returns `stale_preview`, generate a fresh preview before publishing again.

## Modes and Reminders

- `auto` = lightweight automatic `change` trail + reminders
- `remind` = reminders only, no automatic `change` trail
- If you explicitly say something like “remind me to record this round when it’s done”, SyberMem can remember that intent and remind you to run `/sybermem-record` at the right time.

## Workflow Router

SyberMem now recommends the next step using this priority order:

```text
record > digest > team-publish
```

This reduces the “what should I do next?” friction after a round of work.

## Repo Structure

```text
.claude-plugin/                      # Claude Code plugin metadata and marketplace manifest
hooks/                               # Claude Code hook declarations and delegators
skills/                              # Plugin-facing skills tree
packages/claude-skills/              # Skill source for distribution
packages/core/                       # Core memory / Team publication logic
packages/cli/                        # sybermem CLI
scripts/                             # Install, update, and packaging scripts
```

## Uninstall

SyberMem supports two layers of uninstall:

### Project-level uninstall (preserve history, deactivate runtime)

```text
sybermem project uninstall
```

- preserves `.sybermem/` history
- only removes SyberMem hooks / env from `.claude/settings.json`
- only removes the SyberMem protocol block from `CLAUDE.md` / `AGENTS.md`
- user's own content is never destroyed
- can be re-enabled later by running `/sybermem-update`

### Global uninstall (remove global runtime, preserve project history)

```bash
# Windows (PowerShell)
.\scripts\uninstall.ps1

# macOS / Linux
./scripts/uninstall.sh
```

- removes global skills / CLI / launcher / OpenCode plugin
- does not delete any `.sybermem/` history inside projects

## Compatibility

- `.sybermem/` is the canonical project data directory
- if a project still uses legacy `ADR/`, first use will migrate it automatically to `.sybermem/`
- Claude-specific `UserPromptSubmit` repair applies only to managed Claude hooks. OpenCode does not support, and SyberMem does not claim, the same prompt-time injection model there.
- for deeper upgrade and compatibility notes, see `INSTALL.md`

## License

MIT
