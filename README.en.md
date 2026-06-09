[中文](README.md) | **English**

# SyberMem

A set of Claude Code / OpenCode skills for tracking project development history. It records changes, decisions, requirements, and bugs as structured files, so AI can recall project context across sessions.

## How It Works

Install the skills, run `/sybermem-init-project` in your project, use `/sybermem-record` after meaningful work, use `/sybermem-phase-analyze` to build or refresh `.sybermem/analysis/phase-index.md` from project history, use `/sybermem-phase-confirm` to confirm or adjust candidate phases, use `/sybermem-summary` to view the current-state panel for the most recently active confirmed phase (falling back to the weekly/monthly dynamic report if the analysis layer does not exist yet), and use `/sybermem-digest` when a meaningful phase ends and you want a durable summary stored in `.sybermem/digests/`. The phase index is a persistent project analysis artifact, not a final digest. At session start, AI reads `.sybermem/INDEX.md` to recall key conclusions from past work. In `auto` mode, the stop hook still writes a lightweight `change` trail automatically, but it may also emit a non-blocking suggestion that a change is important enough for `/sybermem-record`, or that a recent cluster of work may be ready for `/sybermem-digest`.

`/sybermem-summary` answers “what is the current state of this phase?”, while `/sybermem-digest` records “what did this phase ultimately conclude?”

## Recommended upgrade path

For an existing project, run `/sybermem-update`:

1. Refresh the globally installed SyberMem skills
2. Continue in the current project with `/sybermem-init-project`
3. Migrate legacy `ADR/` if needed
4. Check whether local `AGENTS.md` / `CLAUDE.md` files are stale and offer a refresh

## Upgrading from ADR/

If your project already uses `ADR/`, do not rename anything manually. The first run of `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, `/sybermem-digest`, `/sybermem-phase-analyze`, or `/sybermem-phase-confirm` automatically migrates the old `ADR/` directory to `.sybermem/`.

If both `.sybermem/` and `ADR/` exist, the system uses `.sybermem/` and warns that `ADR/` was ignored.

Refreshing global skills alone does not automatically refresh project-local `AGENTS.md` / `CLAUDE.md`, so after upgrading you should run `/sybermem-update` inside each target project.

Updating global skills does not automatically enable digest support inside every project. To use `/sybermem-digest` in a project, run `/sybermem-update` in that project first. This creates only the missing digest-related structure and does not silently overwrite project-owned files.

Existing projects also receive `.sybermem/analysis/phase-index.md` project by project through `/sybermem-update`.

If an older project still contains project-local copies such as `.claude/skills/sybermem-*`, Claude may load both the local and global copies and show duplicates in the `/` list. If you have adopted the global-install model, you can safely delete those old local copies.

If you want an existing project to receive the refreshed stop-hook nudge behavior, you still need to enter that project and run `/sybermem-update` there. Global skills update once, but local hook/template/instruction refresh still applies project by project.

If you previously encountered stop hook errors (file not found) when working in a subdirectory, running `/sybermem-update` fixes the issue. The updated hook automatically walks up to find the nearest ancestor with both `.sybermem/` and `.claude/settings.json` as the project root.

## Install

### One-liner (requires public repo)

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

### Clone and install

```bash
# macOS / Linux
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem && ./scripts/install.sh

# Windows (PowerShell)
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem; .\scripts\install.ps1
```

### Initialize a project

After the global install, open your project and run:

```text
/sybermem-init-project
```

This creates or refreshes:
- `.sybermem/`
- `.sybermem/digests/` (phase digest directory)
- `.sybermem/analysis/phase-index.md` (persistent phase analysis artifact)
- `.sybermem/hooks/record_change_on_stop.py` (default auto-change hook helper)
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json` (with the default SyberMem `auto` / `remind` mode)

It does not install another copy of the skills into the project.

See [INSTALL.md](INSTALL.md) for details.

## Skills

| Skill | What it does |
|-------|-------------|
| `/sybermem-init-project` | Create or refresh the `.sybermem/` directory structure in a project, scan an existing codebase, generate or refresh `CLAUDE.md` / `AGENTS.md`, and auto-migrate legacy `ADR/` on first run |
| `/sybermem-record` | Create a record from current session context. AI auto-detects the type and writes to `.sybermem/` |
| `/sybermem-summary` | Dynamically view the current-state panel for the most recently active confirmed phase; fall back to weekly/monthly reporting when the analysis layer is unavailable |
| `/sybermem-digest` | Create a durable phase digest from existing records, write it to `.sybermem/digests/`, and block duplicate compression of the same source records |
| `/sybermem-phase-analyze` | Build or refresh `.sybermem/analysis/phase-index.md` from full project history as a persistent phase analysis artifact |
| `/sybermem-phase-confirm` | Confirm, rename, or adjust candidate phases in `phase-index.md` so the project phase structure becomes explicit |
| `/sybermem-update` | Refresh the globally installed SyberMem skills, then continue with `/sybermem-init-project` in the current project |

## What gets created in your project

```
.sybermem/
├── INDEX.md          # Master index — AI reads Key Conclusions at session start
├── changes/          # Feature additions, modifications, deletions
├── decisions/        # Tech choices, architecture designs
├── requirements/     # User requirements, discussion outcomes
├── bugs/             # Bug analysis and fixes
├── digests/          # Phase digests
├── analysis/
│   └── phase-index.md            # Persistent project analysis artifact for candidate phases, confirmed phases, and analysis progress; not a final digest
├── hooks/
│   └── record_change_on_stop.py   # Default auto-change hook helper
└── templates/        # Record templates, including the digest template

CLAUDE.md             # Claude Code instructions (workflow rules)
AGENTS.md             # OpenCode instructions (same content)
.claude/settings.json # Project-level hook mode and stop hook
```

## Directory resolution rules

- `.sybermem/` is canonical.
- If `.sybermem/` already exists, use it.
- If only `ADR/` exists, the first run of `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, `/sybermem-digest`, `/sybermem-phase-analyze`, or `/sybermem-phase-confirm` automatically renames it to `.sybermem/`.
- If both `.sybermem/` and `ADR/` exist, use `.sybermem/` and warn that `ADR/` was ignored.

## Supported Platforms

| Platform | Global skills location | Project-level files |
|----------|------------------------|---------------------|
| Claude Code | `~/.claude/skills/` | `CLAUDE.md`, `.claude/settings.json`, `.sybermem/` |
| OpenCode | `~/.config/opencode/skills/` | `AGENTS.md`, `.claude/settings.json`, `.sybermem/` |

## Repo Structure

```
packages/claude-skills/               # Skill source for distribution inside the repo, not auto-loaded per project
├── sybermem-digest/
├── sybermem-init-project/
├── sybermem-phase-analyze/
├── sybermem-phase-confirm/
├── sybermem-record/
├── sybermem-summary/
└── sybermem-update/

scripts/                              # Install & update scripts
├── install-remote.sh / .ps1          # One-liner remote install
├── install.sh / .ps1                 # Local install
└── update.sh / .ps1                  # Update existing install

docs/zh/                              # Chinese documentation
```

## License

MIT
