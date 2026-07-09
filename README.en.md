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
- phase digests / theme digests
- relations and supersession (`implements`, `fixes`, `related`, `superseded_by`)
- project-level summary / search / link

### Hub
- project registry
- workspace search
- project status
- portfolio view

### Team
- team init
- team publish
- team overview
- team management summary
- Team Project Summary
- full phase / theme digest history sync

## Install

### Claude Code plugin install (recommended)

```bash
claude --plugin-dir .
```

This is the recommended path for Claude Code users who want hooks and skills managed through the plugin runtime.

### Claude Code / OpenCode script install (compatibility mode)

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

### OpenCode

OpenCode can also use SyberMem through its plugin/runtime path. See [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

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
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json`

Where:
- `auto` = lightweight `change` trail + reminders
- `remind` = reminders only, with no automatic `change` trail

## Daily Usage

### Project owner
- `/sybermem-record` — record a meaningful round of work
- `/sybermem-summary` — inspect current project state
- `/sybermem-digest` — capture a stable phase conclusion
- `/sybermem-theme-digest` — capture a cross-phase topic conclusion
- `/sybermem-team-publish` — publish the current project into Team memory

### Manager / management agent
- `/sybermem-team-summary` — generate the Team management summary
- read `dashboards/current-overview.md` / `latest-management-summary.md`

### If you're unsure what to do next
- `/using-sybermem` — inspect the current state and get the recommended command

## Team Workflow

The recommended Team workflow today is:

1. record and digest work inside each project
2. publish the project into the Team repo with `/sybermem-team-publish`
3. let Team overview rebuild automatically
4. generate a management summary with `/sybermem-team-summary`
5. drill into digest history when more detail is needed

In other words:

```text
skim status
read digest history for detail
```

### Team support available today
- **Phase A**: `sybermem team init` — create the Team repo skeleton, write `team.yaml`, and bind the Git remote
- **Phase B**: `sybermem publish status` — publish `project.md` + a Team Project Summary style `current-status.md` + `meta.json`
- **Phase C**: automatically rebuild `dashboards/current-overview.md` after each `publish status`
- **Phase D**: remember Team association so `publish status` no longer needs `--team-path` every time
- **Phase E**: `sybermem team summary` — generate a low-cost management summary (markdown + json)
- **Phase F**: sync the full phase / theme digest history into the Team repo
- **Team Skills**: `/sybermem-team-publish` and `/sybermem-team-summary`

> `sybermem publish status` is the single Team publication entrypoint. You do not need separate team-push/bootstrap commands; the system fills in low-risk prerequisites during publish and asks for confirmation before high-impact actions.

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

## Compatibility

- `.sybermem/` is the canonical project data directory
- if a project still uses legacy `ADR/`, first use will migrate it automatically to `.sybermem/`
- for deeper upgrade and compatibility notes, see `INSTALL.md`

## More Docs

- [INSTALL.md](INSTALL.md)
- [`docs/superpowers/specs/`](docs/superpowers/specs/)
- [`docs/zh/`](docs/zh/)

## License

MIT
