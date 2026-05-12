# Installation Guide

## Upgrading existing ADR/ projects

If a project already uses `ADR/`, upgrading the skills is enough. Do not rename directories manually. The first run of `/init-project`, `/record`, or `/summary` automatically migrates `ADR/` to `.sybermem/`.

If both `.sybermem/` and `ADR/` exist, the skills use `.sybermem/` and warn that the legacy `ADR/` directory was ignored.

## Option 1: One-liner install (recommended)

No clone needed — downloads directly from GitHub.

### macOS / Linux

```bash
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

After install, go to your project and run `/init-project`.

## Option 2: Project-level install

Copy files directly into a project, no global install needed.

1. Copy `.claude/skills/` directory to the target project
2. Copy `CLAUDE.md` (Claude Code) or `AGENTS.md` (OpenCode) to the project root
3. Run `/init-project`

## Option 3: Clone and install

Clone the repo, then run the local install script.

```bash
# macOS / Linux
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem && ./scripts/install.sh
```

```powershell
# Windows (PowerShell)
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem; .\scripts\install.ps1
```

## Update

### One-liner update

Re-run the one-liner install command — it overwrites existing skills with the latest version.

### Clone-based update

```bash
# macOS / Linux
cd sybermem && git pull && ./scripts/update.sh
```

```powershell
# Windows (PowerShell)
cd sybermem; git pull; .\scripts\update.ps1
```

## Verify Installation

Type `/init-project` in Claude Code or OpenCode. If it prompts to create the `.sybermem/` directory structure, or reports that an existing `ADR/` directory will be auto-migrated, the installation was successful.
