---
name: sybermem-update
description: Use when refreshing installed SyberMem skills in an existing project, especially after upgrading SyberMem or when local project instructions may be stale.
---

# sybermem-update Skill

Refresh the installed SyberMem skills, then re-check the current project with `/sybermem-init-project`.

## Core Invariant

- **No behavior change is complete unless `/sybermem-update` can carry an existing managed project to that behavior in operational terms: by re-running the project check, classifying each relevant local managed file, and then creating, refreshing, or migrating only the files that actually need a project-local change. If the new behavior is classification-only or otherwise requires no project-local file change, the update flow must say so explicitly.**

<HARD-GATE>
Do NOT declare the upgrade complete without running the managed-file propagation check.
Do NOT skip the `/sybermem-init-project` follow-up step after updating global skills.
Do NOT leave the old direct-hook command in `.claude/settings.json` when the launcher should have replaced it.
</HARD-GATE>

## When to Use

- You upgraded SyberMem and want the current project to pick up the newest behavior
- The project still answers with old `ADR/` or generic `/init-project` wording
- You want one maintenance command instead of updating globally and then running project init separately

## Directory Resolution Rules

### Step 0: Resolve project root

Before any other operation, walk up from the current working directory to find the nearest ancestor directory (including cwd itself) that contains **both** `.sybermem/` **and** `.claude/settings.json`.

- If found: use that directory as the project root for all subsequent steps. Inform the user if the resolved root differs from cwd: "Using SyberMem project root at `<resolved-path>`".
- If not found (reached git repository root or filesystem root without a match): prompt the user to run `/sybermem-init-project`.

After resolving the project root, apply legacy directory checks against the resolved root:
1. If the resolved root has `.sybermem/`, use it.
2. If the resolved root has only `ADR/`, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If the resolved root has both `.sybermem/` and `ADR/`, use `.sybermem/`, warn that `ADR/` was ignored.

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
- checking whether local `AGENTS.md` / `CLAUDE.md` are stale, including pre-digest SyberMem-managed files that still need the digest-aware guidance refresh
- enabling digest support by creating `.sybermem/digests/`, creating the digest template, and inserting the `Stage Digests` section when missing
- enabling analysis support by creating `.sybermem/analysis/` and `.sybermem/analysis/phase-index.md` from the starter template when missing
- creating or refreshing the default project-level `.claude/settings.json` and `.sybermem/hooks/record_change_on_stop.py` when the project uses the SyberMem-managed hook template
- ensuring the global stop hook launcher exists at `~/.claude/sybermem/launch_record_change_on_stop.py`
- enabling the root-resolving stop-hook launcher by creating `.sybermem/hooks/launch_record_change_on_stop.py` when missing
- auto-migrating existing projects from old relative Stop hook commands to the global absolute launcher command
- applying that migration even when `.claude/settings.json` is otherwise custom, as long as the old Stop hook command is recognizably SyberMem-managed
- inserting or refreshing the marker-bounded `using-sybermem` session-entry protocol block in managed instruction files
- ensuring existing projects receive both the marker-bounded `using-sybermem` protocol block and the visible `/using-sybermem` skill after upgrade
- refreshing stale SyberMem-managed project instructions with backups
- leaving custom project instructions and custom hook settings alone unless the user approves replacement

The protocol block gives automatic session-entry guidance; the visible `/using-sybermem` skill gives a manual diagnostic entrypoint.

Every new managed behavior introduced by SyberMem must explicitly say whether `/sybermem-update` changes any project-local files at all. If it does, name the exact files that are created, refreshed, or migrated. If it does not, say that the behavior is classification-only or otherwise has no project-local file action.

### Managed-file propagation check

Before declaring an upgrade complete, verify for the current project:
- which local files need the new behavior
- whether each file is missing, fresh, stale SyberMem-managed, or custom
- whether stale SyberMem-managed files will be backed up before replacement
- whether custom files will be preserved unless the user explicitly approves replacement
- whether the `using-sybermem` protocol block was inserted or refreshed non-destructively when applicable
- whether recognized old SyberMem Stop hook commands were surgically replaced with the global launcher path when present in otherwise custom settings files.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:

- Declaring the upgrade complete without running the managed-file propagation check
- Skipping the `/sybermem-init-project` follow-up step after updating global skills
- Leaving the old direct-hook command in `.claude/settings.json` when the launcher should have replaced it
- Claiming a behavior change is shipped when project-local files have not been created or refreshed

**All of these mean: go back to Step 2 and re-run the init-project flow.**

## Terminal State

This skill is complete when:
- global skills have been refreshed
- the `/sybermem-init-project` follow-up has run on the current project
- all managed files are classified, created, refreshed, or preserved as appropriate
- the user has been told what was updated

## Safety Rules

- Do not silently overwrite custom project instruction files.
- Do not skip the `/sybermem-init-project` follow-up step.
- If the update command fails, stop and report the failure instead of pretending the project was refreshed.
- Do not silently enable digest support by overwriting user-owned files; only create missing digest capability structure.
- Do not rewrite unrelated custom settings; only surgically replace recognized old SyberMem Stop hook commands.
- Do not rewrite the rest of `CLAUDE.md` / `AGENTS.md` when the `using-sybermem` markers already exist; only refresh the bounded protocol block.
