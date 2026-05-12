# Installation Guide

## Upgrading existing ADR/ projects

If a project already uses `ADR/`, do not rename directories manually. The first run of `/sybermem-init-project`, `/sybermem-record`, or `/sybermem-summary` automatically migrates `ADR/` to `.sybermem/`.

If both `.sybermem/` and `ADR/` exist, the skills use `.sybermem/` and warn that the legacy `ADR/` directory was ignored.

Refreshing global skills alone does not automatically refresh project-local `AGENTS.md` / `CLAUDE.md`. After upgrading, open each target project and run `/sybermem-update`.

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

After install, go to your project and run `/sybermem-update`.

## Option 2: Project-level install

Copy files directly into a project, no global install needed.

1. Copy `.claude/skills/` directory to the target project
2. Copy `CLAUDE.md` (Claude Code) or `AGENTS.md` (OpenCode) to the project root
3. Run `/sybermem-init-project`

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

Re-run the one-liner install command — it refreshes the globally installed skills with the latest version.

After the global refresh, open the target project and run `/sybermem-update`.

### Clone-based update

```bash
# macOS / Linux
cd sybermem && git pull && ./scripts/update.sh
```

```powershell
# Windows (PowerShell)
cd sybermem; git pull; .\scripts\update.ps1
```

After the script finishes, open the target project and run `/sybermem-update`.

## Verify Installation

Type `/sybermem-init-project` or `/sybermem-update` in Claude Code or OpenCode. If the project gets the `.sybermem/` directory structure, reports that an existing `ADR/` directory will be auto-migrated, or offers to refresh stale `AGENTS.md` / `CLAUDE.md`, the installation was successful.
