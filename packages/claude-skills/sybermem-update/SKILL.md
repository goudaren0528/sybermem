---
name: sybermem-update
description: Use when refreshing installed SyberMem skills in an existing project, especially after upgrading SyberMem or when local project instructions may be stale.
---

# sybermem-update Skill

Refresh the installed SyberMem skills, then re-check the current project with `/sybermem-init-project`.

## When to Use

- You upgraded SyberMem and want the current project to pick up the newest behavior
- The project still answers with old `ADR/` or generic `/init-project` wording
- You want one maintenance command instead of updating globally and then running project init separately

## Flow

### Step 1: Explain the update command before running it

Tell the user which command you are about to run.

Choose the update path in this order:

1. **Local clone available**
   - If the current working directory is the SyberMem repo and contains the install/update scripts, use the local update script.
   - Bash shell: `./scripts/update.sh`
   - PowerShell shell: `./scripts/update.ps1`

2. **Any other project**
   - Use the remote install script to refresh the globally installed skills.
   - Bash shell: `curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash`
   - PowerShell shell: `irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex`

The remote install path is also the update path for globally installed skills.

### Step 2: Run `/sybermem-init-project` in the current project

After the global refresh completes, continue with the same project by applying the `/sybermem-init-project` flow.

That second step is responsible for:
- migrating legacy `ADR/` to `.sybermem/`
- checking whether local `AGENTS.md` / `CLAUDE.md` are stale
- enabling digest support by creating `.sybermem/digests/`, creating the digest template, and inserting the `Stage Digests` section when missing
- creating or refreshing the default project-level `.claude/settings.json` and `.sybermem/hooks/record_change_on_stop.py` when the project uses the SyberMem-managed hook template
- refreshing stale SyberMem-managed project instructions with backups
- leaving custom project instructions and custom hook settings alone unless the user approves replacement

## Safety Rules

- Do not silently overwrite custom project instruction files.
- Do not skip the `/sybermem-init-project` follow-up step.
- If the update command fails, stop and report the failure instead of pretending the project was refreshed.
- Do not silently enable digest support by overwriting user-owned files; only create missing digest capability structure.
