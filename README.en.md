[中文](README.md) | **English**

# SyberMem

A set of Claude Code / OpenCode skills for tracking project development history. It records changes, decisions, requirements, and bugs as structured files, so AI can recall project context across sessions.

## How It Works

Install the skills, run `/sybermem-init-project` in your project, then use `/sybermem-record` after completing meaningful work. AI auto-detects the record type and writes a structured file to the `.sybermem/` directory. At session start, AI reads `.sybermem/INDEX.md` to recall key conclusions from past work.

## Recommended upgrade path

For an existing project, run `/sybermem-update`:

1. Refresh the globally installed SyberMem skills
2. Continue in the current project with `/sybermem-init-project`
3. Migrate legacy `ADR/` if needed
4. Check whether local `AGENTS.md` / `CLAUDE.md` files are stale and offer a refresh

## Upgrading from ADR/

If your project already uses `ADR/`, do not rename anything manually. The first run of `/sybermem-init-project`, `/sybermem-record`, or `/sybermem-summary` automatically migrates the old `ADR/` directory to `.sybermem/`.

If both `.sybermem/` and `ADR/` exist, the system uses `.sybermem/` and warns that `ADR/` was ignored.

Refreshing global skills alone does not automatically refresh project-local `AGENTS.md` / `CLAUDE.md`, so after upgrading you should run `/sybermem-update` inside each target project.

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

### Copy into a project

Copy `.claude/skills/` and `CLAUDE.md` (or `AGENTS.md`) to your project root.

See [INSTALL.md](INSTALL.md) for details.

## Skills

| Skill | What it does |
|-------|-------------|
| `/sybermem-init-project` | Create or refresh the `.sybermem/` directory structure in a project, scan an existing codebase, generate or refresh `CLAUDE.md` / `AGENTS.md`, and auto-migrate legacy `ADR/` on first run |
| `/sybermem-record` | Create a record from current session context. AI auto-detects the type and writes to `.sybermem/` |
| `/sybermem-summary` | Generate a weekly or monthly progress report from `.sybermem/` records and git history; legacy `ADR/` auto-migrates on first use |
| `/sybermem-update` | Refresh the globally installed SyberMem skills, then continue with `/sybermem-init-project` in the current project |

## What gets created in your project

```
.sybermem/
├── INDEX.md          # Master index — AI reads Key Conclusions at session start
├── changes/          # Feature additions, modifications, deletions
├── decisions/        # Tech choices, architecture designs
├── requirements/     # User requirements, discussion outcomes
├── bugs/             # Bug analysis and fixes
└── templates/        # Record templates

CLAUDE.md             # Claude Code instructions (workflow rules)
AGENTS.md             # OpenCode instructions (same content)
```

## Directory resolution rules

- `.sybermem/` is canonical.
- If `.sybermem/` already exists, use it.
- If only `ADR/` exists, the first run of `/sybermem-init-project`, `/sybermem-record`, or `/sybermem-summary` automatically renames it to `.sybermem/`.
- If both `.sybermem/` and `ADR/` exist, use `.sybermem/` and warn that `ADR/` was ignored.

## Supported Platforms

| Platform | Skills location | Project instructions |
|----------|----------------|---------------------|
| Claude Code | `~/.claude/skills/` or `.claude/skills/` | `CLAUDE.md` |
| OpenCode | `~/.config/opencode/skills/` or `.claude/skills/` | `AGENTS.md` |

## Repo Structure

```
.claude/skills/                     # The skills (what gets installed)
├── sybermem-init-project/
│   ├── SKILL.md
│   └── project-files/
├── sybermem-record/
│   ├── SKILL.md
│   └── templates/
├── sybermem-summary/
│   └── SKILL.md
└── sybermem-update/
    └── SKILL.md

scripts/                             # Install & update scripts
├── install-remote.sh / .ps1         # One-liner remote install
├── install.sh / .ps1                # Local install
└── update.sh / .ps1                 # Update existing install

docs/zh/                             # Chinese documentation
```

## License

MIT
