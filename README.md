# SyberMem

A set of Claude Code / OpenCode skills for tracking project development history. Records changes, decisions, requirements, and bugs as structured files, so AI can recall project context across sessions.

## How It Works

Install the skills, run `/init-project` in your project, then use `/record` after completing meaningful work. AI auto-detects the record type and writes a structured file to the `ADR/` directory. At session start, AI reads `ADR/INDEX.md` to recall key conclusions from past work.

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
| `/init-project` | Create `ADR/` directory structure in a project, scan existing codebase, generate `CLAUDE.md` / `AGENTS.md` |
| `/record` | Create a record from current session context. AI auto-detects type: change, decision, requirement, or bug |
| `/summary` | Generate weekly or monthly progress report from existing records and git history |

## What gets created in your project

```
ADR/
├── INDEX.md          # Master index — AI reads Key Conclusions at session start
├── changes/          # Feature additions, modifications, deletions
├── decisions/        # Tech choices, architecture designs
├── requirements/     # User requirements, discussion outcomes
├── bugs/             # Bug analysis and fixes
└── templates/        # Record templates

CLAUDE.md             # Claude Code instructions (workflow rules)
AGENTS.md             # OpenCode instructions (same content)
```

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
