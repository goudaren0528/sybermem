[中文](README.md) | **English**

# SyberMem

A set of Claude Code / OpenCode skills for tracking project development history. It records changes, decisions, requirements, and bugs as structured files, so AI can recall project context across sessions.

## How It Works

Install the skills, run `/init-project` in your project, then use `/record` after completing meaningful work. AI auto-detects the record type and writes a structured file to the `.sybermem/` directory. At session start, AI reads `.sybermem/INDEX.md` to recall key conclusions from past work.

## Upgrading from ADR/

If your project already uses `ADR/`, upgrading the skills is enough. Do not rename anything manually. The first run of `/init-project`, `/record`, or `/summary` automatically migrates the old `ADR/` directory to `.sybermem/`.

If both `.sybermem/` and `ADR/` exist, the system uses `.sybermem/` and warns that `ADR/` was ignored.

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
| `/init-project` | Create the `.sybermem/` directory structure in a project, scan an existing codebase, generate `CLAUDE.md` / `AGENTS.md`, and auto-migrate legacy `ADR/` on first run |
| `/record` | Create a record from current session context. AI auto-detects the type and writes to `.sybermem/` |
| `/summary` | Generate a weekly or monthly progress report from `.sybermem/` records and git history; legacy `ADR/` auto-migrates on first use |

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
- If only `ADR/` exists, the first run of `/init-project`, `/record`, or `/summary` automatically renames it to `.sybermem/`.
- If both `.sybermem/` and `ADR/` exist, use `.sybermem/` and warn that `ADR/` was ignored.

## Supported Platforms

| Platform | Skills location | Project instructions |
|----------|----------------|---------------------|
| Claude Code | `~/.claude/skills/` or `.claude/skills/` | `CLAUDE.md` |
| OpenCode | `~/.config/opencode/skills/` or `.claude/skills/` | `AGENTS.md` |

## Repo Structure

```
.claude/skills/               # The skills (what gets installed)
├── init-project/SKILL.md
├── record/
│   ├── SKILL.md
│   └── templates/
└── summary/SKILL.md

scripts/                       # Install & update scripts
├── install-remote.sh / .ps1   # One-liner remote install
├── install.sh / .ps1          # Local install
└── update.sh / .ps1           # Update existing install

docs/zh/                       # Chinese documentation
```

## License

MIT
