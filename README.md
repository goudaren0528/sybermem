# ADR Record System

A lightweight Architecture Decision Record (ADR) system for Claude Code and OpenCode projects.

## Features

- **Unified record entry** — AI auto-detects record type (change/decision/requirement/bug)
- **Project initialization** — Auto-detects new or existing projects, creates ADR directory structure
- **Progress reports** — Generate weekly or monthly reports on demand

## Supported Platforms

| Platform | Project-level skills | User-level skills | Project instructions |
|----------|---------------------|-------------------|---------------------|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | `CLAUDE.md` |
| OpenCode | `.claude/skills/` (compatible) | `~/.config/opencode/skills/` | `AGENTS.md` |

## Project Structure

```
.claude/skills/                  # Project-level Skills (shared across platforms)
├── init-project/SKILL.md
├── record/
│   ├── SKILL.md
│   └── templates/
└── summary/SKILL.md

ADR/                             # Project records (created by /init-project)
├── INDEX.md
├── changes/ decisions/ requirements/ bugs/
└── templates/

CLAUDE.md                        # Claude Code project instructions
AGENTS.md                        # OpenCode project instructions
```

## Quick Start

### One-liner install (recommended)

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

Then go to your project and run `/init-project`.

### Other install options

See [INSTALL.md](INSTALL.md) for project-level install and clone-based install.

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/init-project` | Initialize ADR directory structure, detect project type |
| `/record` | Create a record, AI auto-detects type |
| `/summary` | Generate weekly (default) or monthly report |

## Record Types

| Type | Directory | Trigger |
|------|-----------|---------|
| Feature change | `ADR/changes/` | Add/modify/delete features |
| Technical decision | `ADR/decisions/` | Tech selection, architecture design |
| Requirement | `ADR/requirements/` | User requirements, discussion outcomes |
| Bug fix | `ADR/bugs/` | Fix bugs, troubleshoot issues |

## Chinese Documentation

Chinese versions of all files are available in `docs/zh/` for reference.

## License

MIT
