# Installation Guide

## Upgrading existing ADR/ projects

If a project already uses `ADR/`, do not rename directories manually. The first run of `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, `/sybermem-digest`, `/sybermem-phase-analyze`, or `/sybermem-phase-confirm` automatically migrates `ADR/` to `.sybermem/`.

If both `.sybermem/` and `ADR/` exist, the skills use `.sybermem/` and warn that the legacy `ADR/` directory was ignored.

Refreshing global skills alone does not automatically refresh project-local `AGENTS.md` / `CLAUDE.md`. After upgrading, open each target project and run `/sybermem-update`.

Updating global skills does not automatically enable digest support inside every project. To use `/sybermem-digest` in a project, run `/sybermem-update` in that project first. This creates only the missing digest-related structure and does not silently overwrite project-owned files.

Updating global skills once refreshes the shared slash commands, but existing projects still receive stop-hook behavior changes project by project. To give a specific project the refreshed hook/template/instruction behavior, run `/sybermem-update` inside that project.

Existing projects also receive `.sybermem/analysis/phase-index.md` project by project through `/sybermem-update`.

If the same source records have already been compressed into an existing digest, `/sybermem-digest` must point to the existing digest instead of creating a duplicate.

If an older project still contains project-local copies such as `.claude/skills/sybermem-*`, Claude may load both the local and global copies and show duplicates in the `/` list. Once you have switched to the global-install model, those old project-local copies can be deleted.

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

After install, open your target project and run `/sybermem-init-project`.
That step will also create the default project-level `.claude/settings.json` for SyberMem `auto` / `remind` mode and the default `.sybermem/hooks/record_change_on_stop.py` helper for automatic `change` records.

## Option 2: Clone and install

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

## Subdirectory Hook Fix

For existing users who experienced stop hook errors when working in project subdirectories: running `/sybermem-update` in the project refreshes the hook with automatic project root resolution. The updated hook finds the correct `.sybermem/` directory even when your working directory is a subdirectory of the project root.

## Verify Installation

Type `/sybermem-init-project` or `/sybermem-update` in Claude Code or OpenCode. If the project gets the `.sybermem/` directory structure, reports that an existing `ADR/` directory will be auto-migrated, or offers to refresh stale `AGENTS.md` / `CLAUDE.md`, the installation was successful.
