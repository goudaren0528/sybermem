---
name: sybermem-update
description: Use when refreshing installed SyberMem skills in an existing project, especially after upgrading SyberMem or when local project instructions may be stale.
---

# sybermem-update Skill

**Announce at start:** "I'm using the sybermem-update skill to refresh global skills and re-check this project."

Refresh the installed SyberMem skills, then re-check the current project with the deterministic `sybermem project refresh --format json` CLI path. Fall back to `/sybermem-init-project` orchestration only when the CLI is unavailable, broken, or does not emit valid JSON.

## Quick guide (for humans)

> Plain-language overview for people. **Not** the execution contract — the
> `<HARD-GATE>`, `## When to Use`, and `## Flow` sections below are authoritative
> and win on any conflict.

**What it does:** one maintenance command — refreshes the globally installed
SyberMem skills, then runs the project-local refresh through Core/CLI so this
project picks up the newest managed-file behavior quickly and deterministically.

**When to run:** after upgrading SyberMem, or when the project still shows old
`ADR/` wording or stale managed files.

**What you get:** up-to-date global skills plus a JSON-backed project re-check
that creates, refreshes, or migrates only the local files that actually need to
change (and says so explicitly when nothing needs changing). If the CLI path is
unhealthy, the skill uses the older agent-guided `/sybermem-init-project` path
as a recovery fallback.

## Core Invariant

- **No behavior change is complete unless `/sybermem-update` can carry an existing managed project to that behavior in operational terms: by running `sybermem project refresh --format json` first, parsing its managed-file report, and then creating, refreshing, or migrating only the files that actually need a project-local change. If the CLI path is unavailable or invalid, fall back to `/sybermem-init-project`; if the new behavior is classification-only or otherwise requires no project-local file change, the update flow must say so explicitly.**

<HARD-GATE>
Do NOT declare the upgrade complete without running the managed-file propagation check.
Do NOT skip the project-local follow-up after updating global skills: run CLI refresh first, or run `/sybermem-init-project` only as fallback.
Do NOT leave the old direct-hook command in `.claude/settings.json` when the launcher should have replaced it.
</HARD-GATE>

## When to Use

- You upgraded SyberMem and want the current project to pick up the newest behavior
- The project still answers with old `ADR/` or generic `/init-project` wording
- You want one maintenance command instead of updating globally and then running project init separately

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

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

### Step 2: Run CLI-first project refresh in the current project

After the global refresh completes, resolve a SyberMem CLI command and run project refresh. Before running SyberMem CLI commands, resolve a command variable first. On Windows PowerShell, prefer `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd` and store the chosen command in `$SyberMemCli`; on Unix, prefer `$HOME/.claude/sybermem/cli/sybermem` and store the chosen command in `"$SYBERMEM_CLI"`. If the fixed launcher is unavailable, fall back to bare `sybermem`. Do not modify persistent PATH automatically. Command examples below use `$SyberMemCli` / `"$SYBERMEM_CLI"`.

1. Prefer bare `sybermem`.
2. If bare `sybermem` is unavailable, try the fixed launcher:
   - Windows PowerShell: `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd`
   - macOS / Linux: `$HOME/.claude/sybermem/cli/sybermem`
3. Run:

```bash
$SYBERMEM_CLI project refresh --format json
```

```powershell
& $SyberMemCli project refresh --format json
```

The command is the primary project-local update path. It is responsible for:
- classifying managed files as fresh, missing, stale, custom, or preserved
- creating missing project-managed files from templates
- refreshing stale SyberMem-managed hooks/templates with backups
- inserting or replacing the marker-bounded `using-sybermem` protocol block in managed instruction files without overwriting custom content
- surgically repairing `.claude/settings.json` SyberMem hook/env entries while preserving unrelated custom hooks, env, and instructions
- creating `.sybermem/project.yaml` when missing
- emitting valid JSON with `overall`, `files`, `actions_needed`, `actions_applied`, `actions_skipped`, and `preserved_custom`

If the CLI exits successfully and emits valid JSON, summarize that JSON and **do not** run `/sybermem-init-project`. The project-local refresh is complete when the report is `fresh` or `updated` and any applied/skipped/preserved actions are reported to the user.

### Step 3: Fall back only when CLI refresh is unavailable or invalid

**REQUIRED FALLBACK SUB-SKILL:** Run `/sybermem-init-project` only if the CLI path is unusable.

Fallback triggers are limited to:
- bare `sybermem` and the fixed launcher are both missing or not executable
- `sybermem project refresh --format json` exits nonzero
- stdout is empty, non-JSON, or missing the required report keys
- CLI refresh is missing, broken, or emits invalid JSON

Do not fall back merely because the CLI report says it changed files or preserved custom files. Those are successful outcomes.

The fallback step is responsible for the same managed-file propagation semantics when Core/CLI cannot run:
- migrating legacy `ADR/` to `.sybermem/`
- checking whether local `AGENTS.md` / `CLAUDE.md` are stale, including pre-digest SyberMem-managed files that still need the digest-aware guidance refresh
- enabling digest support by creating `.sybermem/digests/`, creating the digest template, and inserting the `Phase Digests` section when missing
- enabling analysis support by creating `.sybermem/analysis/` and `.sybermem/analysis/phase-index.md` from the starter template when missing
- creating or refreshing the default project-level `.claude/settings.json`, `.sybermem/hooks/record_change_on_stop.py`, and `.sybermem/hooks/user_prompt.py` (the merged UserPromptSubmit hook), keeping `.sybermem/hooks/detect_record_intent.py` and `.sybermem/hooks/task_recall.py` as the backward-compatible modules `user_prompt.py` reuses, when the project uses the SyberMem-managed hook template
- migrating a legacy dual-hook `.claude/settings.json` (separate `detect_record_intent.py` + `task_recall.py` UserPromptSubmit entries) to the single merged `user_prompt.py` entry, surgically and preserving unrelated custom hooks
- ensuring the global stop hook launcher exists at `~/.claude/sybermem/launch_record_change_on_stop.py`
- enabling the root-resolving stop-hook launcher by creating `.sybermem/hooks/launch_record_change_on_stop.py` when missing
- auto-migrating existing projects from old relative Stop hook commands to the global absolute launcher command
- applying that migration even when `.claude/settings.json` is otherwise custom, as long as the old Stop hook command is recognizably SyberMem-managed
- repairing missing or stale SyberMem-managed `UserPromptSubmit` hook wiring so the same hook performs both natural-language record-intent capture and read-only task recall
- applying that `UserPromptSubmit` repair surgically even when `.claude/settings.json` is otherwise custom, without overwriting unrelated custom hooks, env, or instructions
- inserting or refreshing the marker-bounded `using-sybermem` session-entry protocol block in managed instruction files
- ensuring existing projects receive both the marker-bounded `using-sybermem` protocol block and the visible `/using-sybermem` skill after upgrade
- refreshing stale SyberMem-managed project instructions with backups
- leaving custom project instructions and custom hook settings alone unless the user approves replacement

The protocol block gives automatic session-entry guidance; the visible `/using-sybermem` skill gives a manual diagnostic entrypoint.

Every new managed behavior introduced by SyberMem must explicitly say whether `sybermem project refresh --format json` changes any project-local files at all. If it does, name the exact files that are created, refreshed, or migrated. If it does not, say that the behavior is classification-only or otherwise has no project-local file action. Update `docs/feature_map.md` in the same feature change when platform support claims change.

Current behavior note: `sybermem project memory-stats` and the `/sybermem-summary` Memory Health / Recall Stats panel require refreshed global CLI/Core and skill instructions only. They do not create, refresh, or migrate any project-local managed files through `sybermem project refresh --format json`; the command reads existing `.sybermem/` records and optional `.sybermem/.recall-debug.jsonl` metadata.

### Managed-file propagation check

Before declaring an upgrade complete, verify for the current project:
- which local files need the new behavior
- whether each file is missing, fresh, stale SyberMem-managed, or custom
- whether stale SyberMem-managed files will be backed up before replacement
- whether custom files will be preserved unless the user explicitly approves replacement
- whether the `using-sybermem` protocol block was inserted or refreshed non-destructively when applicable
- whether recognized old SyberMem Stop hook commands were surgically replaced with the global launcher path when present in otherwise custom settings files.
- whether recognized SyberMem-managed `UserPromptSubmit` entries were added or repaired surgically when missing or stale, while leaving unrelated custom hooks, env, and instructions untouched.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:

- Declaring the upgrade complete without running `sybermem project refresh --format json` or the documented fallback
- Skipping the project-local follow-up step after updating global skills
- Running `/sybermem-init-project` even though CLI refresh succeeded with valid JSON
- Leaving the old direct-hook command in `.claude/settings.json` when the launcher should have replaced it
- Claiming a behavior change is shipped when project-local files have not been created or refreshed

**All of these mean: go back to Step 2 and re-run the init-project flow.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Global skills updated, so the project is updated too" | Project-local files (hooks, settings.json, CLAUDE.md) don't update automatically. Run CLI refresh. |
| "CLI refresh changed files, so I should also run init-project" | Changed files are a successful CLI outcome. Fall back only for missing/broken/non-JSON CLI failures. |
| "I already ran update last week" | Skills may have been updated since then. Each update is idempotent and fast with the health check. |

## Terminal State

This skill is complete when:
- global skills have been refreshed
- `sybermem project refresh --format json` succeeded with valid JSON, or `/sybermem-init-project` fallback ran because CLI refresh was unavailable or invalid
- all managed files are classified, created, refreshed, or preserved as appropriate
- the user has been told what was updated

## Safety Rules

- Do not silently overwrite custom project instruction files.
- Do not skip the project-local follow-up step.
- Do not use agent orchestration when CLI refresh succeeded with valid JSON.
- If the update command fails, stop and report the failure instead of pretending the project was refreshed.
- Do not silently enable digest support by overwriting user-owned files; only create missing digest capability structure.
- Do not rewrite unrelated custom settings; only surgically replace recognized old SyberMem Stop hook commands.
- Do not rewrite unrelated custom settings; only surgically add or repair recognized SyberMem-managed `UserPromptSubmit` entries.
- Do not rewrite the rest of `CLAUDE.md` / `AGENTS.md` when the `using-sybermem` markers already exist; only refresh the bounded protocol block.

## Integration

**Fallback sub-skills:**
- **sybermem-init-project** — Called only when CLI-first project refresh is missing, broken, or emits invalid JSON

**Related skills:**
- **sybermem-record** — Available after update
- **sybermem-summary** — Available after update
