---
name: sybermem-update
description: Use when refreshing installed SyberMem skills in an existing project, especially after upgrading SyberMem or when local project instructions may be stale.
---

# sybermem-update Skill

**Announce at start:** "I'm using the sybermem-update skill to refresh global skills and re-check this project."

Refresh the installed SyberMem skills, then re-check the explicitly confirmed project with `sybermem project refresh --root "<confirmed-target>" --format json`. If the CLI is unusable, stop and offer separately authorized recovery.

## Quick guide (for humans)

> Plain-language overview for people. **Not** the execution contract — the
> `<HARD-GATE>`, `## When to Use`, and `## Flow` sections below are authoritative
> and win on any conflict.

**What it does:** one maintenance command — refreshes the globally installed
SyberMem skills, then runs the project-local refresh through Core/CLI so this
project picks up the newest managed-file behavior quickly and deterministically.

**When to run:** after upgrading SyberMem, or when the project still has stale
managed files.

**What you get:** up-to-date global skills plus a JSON-backed project re-check
that creates, refreshes, or migrates only the local files that actually need to
change (and says so explicitly when nothing needs changing). If the CLI path is
unhealthy, stop to inspect state and offer `/sybermem-init-project` in a new session
as a recovery option.

## Core Invariant

- **No behavior change is complete unless `/sybermem-update` can propagate it to the confirmed project through explicit-root CLI refresh and a verified report. If the CLI is unusable, stop and explain recovery; if the behavior needs no project-local file change, say so explicitly.**

<HARD-GATE>
Do NOT declare the upgrade complete without running the managed-file propagation check.
Do NOT skip the project-local follow-up after updating global skills: run explicit-root CLI refresh after scope confirmation, or report why setup is deferred.
Do NOT leave the old direct-hook command in `.claude/settings.json` when the launcher should have replaced it.
</HARD-GATE>

## When to Use

- You upgraded SyberMem and want the current project to pick up the newest behavior
- The project still answers with stale managed-file wording
- You want one maintenance command instead of updating globally and then running project init separately

## Directory Resolution

Nested-project approval does not bypass CLI safety checks: `--root` rejects target
or ancestor symlink/reparse points, a target inside an ancestor Git worktree unless
it has its own independent repository, and an unconfirmed Git boundary. Core may
otherwise run `git rm --cached` against an ancestor index. On rejection, stop;
never fall back to no-argument refresh. Not every nested directory is supported.
The explicit branch rejects nonempty `GIT_*` environment overrides and unavailable
Git or an unknown boundary; Git probes use a fixed locale (`C`) and strictly recognize
non-repository results. An independent repository at the target is allowed, an
ancestor-worktree subdirectory is rejected. `--root` is a static exact-target check,
not an OS sandbox or a race-safety/full-chain-redaction guarantee. Real refresh
validation requires VM/OS isolation and has not yet been performed.
Normalize the user-confirmed target to an absolute path before running the command;
show that normalized path and reconfirm if it differs from the intended scope.
Compare returned `root` using that same normalized target. These checks do not prove
model consumption. Only `doctor --runtime` and `project refresh --root` are
authorized interface additions in this change.

Resolve project root by walking up from cwd to find `.sybermem/` + (`.sybermem/project.yaml` OR `.claude/settings.json`).
First confirm the target existing directory with the user; cwd alone is not authorization.
If a SyberMem ancestor exists, ask whether the user wants an independent nested
project or the parent. Do not silently choose either. Explicit `--root` uses exactly
that existing directory: no upward resolution, implicit mkdir, or fallback.
Legacy `sybermem project refresh --format json` keeps ancestor resolution and exits 1
if no root resolves; changing HOME does not prevent the physical ancestor search.
Legacy `sybermem project init` provides identity for an existing resolved root,
not a full fresh-project initialization.

## Flow

### Step 1: Explain the update command before running it

Tell the user which command you are about to run.

Choose the update path in this order:

1. **Local clone available**
   - If the current working directory is the SyberMem repo and contains the install/update scripts, use the local update script.
   - Bash shell: `./scripts/update.sh`
   - Windows OpenCode or `cmd.exe`: `python scripts/update.py`
   - PowerShell shell: `./scripts/update.ps1`

2. **Any other project**
   - Use the remote install script to refresh the globally installed skills.
   - Bash shell: `curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash`
   - Windows OpenCode or `cmd.exe`: `python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.py').read())"`
   - PowerShell shell: `irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex`

On Windows OpenCode, prefer the Python commands above. They do not spawn
`powershell.exe`; the remote script downloads and extracts the repository with
Python's standard library before running the shared installer. Existing
PowerShell and shell paths remain supported.

The remote install path is also the update path for globally installed skills.

### Step 2: Run CLI-first project refresh in the current project

After the global refresh completes, resolve a SyberMem CLI command and run project refresh. Before running SyberMem CLI commands, resolve a command variable first. On Windows `cmd.exe` or OpenCode, prefer `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd`; in Windows PowerShell prefer `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd` and store the chosen command in `$SyberMemCli`; on Unix, prefer `$HOME/.claude/sybermem/cli/sybermem` and store the chosen command in `"$SYBERMEM_CLI"`. If the fixed launcher is unavailable, fall back to bare `sybermem`. Do not modify persistent PATH automatically. Command examples below use `$SyberMemCli` / `"$SYBERMEM_CLI"`.

Verify the resolved launcher with `project refresh --help` and confirm `--root`
support. If an older CLI rejects `--root`, stop and recommend upgrading or using the
skill in a new session; never downgrade to a no-argument refresh. Skills installed
in this session are not hot-loaded. With scope confirmed, run:

```bash
"$SYBERMEM_CLI" project refresh --root "<confirmed-target>" --format json
```

```powershell
& $SyberMemCli project refresh --root "<confirmed-target>" --format json
```

```cmd
"%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd" project refresh --root "<confirmed-target>" --format json
```

The command is the primary project-local update path. It is responsible for:
- classifying managed files as fresh, missing, stale, custom, or preserved
- creating missing project-managed files from templates
- refreshing stale SyberMem-managed hooks/templates with backups
- removing any legacy SyberMem protocol block from `CLAUDE.md` / `AGENTS.md` (whole file when purely SyberMem-managed, otherwise only the block) without overwriting custom content
- adding or refreshing the marker-bounded SyberMem `.gitignore` block for git projects (ignores machine-local runtime/scripts and local derived `.sybermem/INDEX.md`; keeps records committable; skipped for non-git projects) without overwriting unrelated ignore rules
- surgically repairing `.claude/settings.json` SyberMem hook/env entries while preserving unrelated custom hooks, env, and instructions
- creating `.sybermem/project.yaml` when missing
- emitting valid JSON with `overall`, `files`, `actions_needed`, `actions_applied`, `actions_skipped`, and `preserved_custom`

Require exit 0, valid JSON, returned `root` matching the authorized target, and
`overall` equal to `fresh` or `updated`. Summarize actual applied/skipped/preserved
actions and **do not** run `/sybermem-init-project` after success. Failure may leave
partial writes; do not blindly retry. A wrong root or failed overall is not success.

### Step 3: Fall back only when CLI refresh is unavailable or invalid

**RECOVERY BOUNDARY:** Stop on an unusable CLI or failed report; explain possible
partial writes and inspect the confirmed scope before any separately authorized
recovery. Offer `/sybermem-init-project` in a new session when necessary; newly
installed skills are not hot-loaded. Never silently retry with no `--root`.

Fallback triggers are limited to:
- bare `sybermem` and the fixed launcher are both missing or not executable
- explicit-root project refresh exits nonzero or returns a wrong root/failed overall
- stdout is empty, non-JSON, or missing the required report keys
- CLI refresh is missing, broken, or emits invalid JSON

Do not fall back merely because the CLI report says it changed files or preserved custom files. Those are successful outcomes.

The fallback step is responsible for the same managed-file propagation semantics when Core/CLI cannot run:
- checking whether local `AGENTS.md` / `CLAUDE.md` still carry a legacy SyberMem protocol block that must be removed
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
- removing any legacy SyberMem protocol block from `CLAUDE.md` / `AGENTS.md` (whole file when purely SyberMem-managed, otherwise only the block) without overwriting custom content
- ensuring existing projects receive the visible `/using-sybermem` skill after upgrade
- refreshing stale SyberMem-managed project instructions with backups
- leaving custom project instructions and custom hook settings alone unless the user approves replacement

The visible `/using-sybermem` skill gives a manual diagnostic entrypoint; no instruction-file injection is needed.

Every new managed behavior introduced by SyberMem must explicitly say whether `sybermem project refresh --format json` changes any project-local files at all. If it does, name the exact files that are created, refreshed, or migrated. If it does not, say that the behavior is classification-only or otherwise has no project-local file action. Update `docs/feature_map.md` in the same feature change when platform support claims change.

Current behavior note: `sybermem project memory-stats` and the `/sybermem-summary` Memory Health / Recall Stats panel require refreshed global CLI/Core and skill instructions only. They do not create, refresh, or migrate any project-local managed files through `sybermem project refresh --format json`; the command reads existing `.sybermem/` records, optional `.sybermem/.recall-debug.jsonl` recall-frequency metadata, optional `.sybermem/.recall-outcomes.jsonl` recall-precision metadata (used for the `low_relevance` verdict), and optional `.sybermem/.memory-usage.jsonl` OpenCode actual-injection metadata. These files are runtime logs, never scaffolded managed files.

Current behavior note: OpenCode observability requires refreshed global CLI/Core and the OpenCode plugin selected by the host major: V1 standalone `sybermem-v1.ts` → `~/.config/opencode/plugins/sybermem.ts`, or V2 complete `dist-v2` directory → `~/.config/opencode/sybermem-v2/` with one directory plugin entry. Migration must not dual-load both. An unknown version without `--opencode-major 1|2` / `SYBERMEM_OPENCODE_MAJOR` skips OpenCode plugin deployment. Verify separately: (1) installer result and deployed file SHA-256 vs built sources; (2) reload and inspect host loader; (3) run a real matching prompt and confirm recall/usage and V2 companion TUI toast. File/hash checks alone cannot prove model injection or visible toast. V2 usage journals describe outgoing-request injection rather than provider acceptance; V2 has not restored V1's background remote-version refresh. These features do not change project-local managed files through `sybermem project refresh --format json`; runtime logs are created only during use.

Current behavior note: `sybermem project phase analyze` (used by `/sybermem-phase-analyze`, which `/sybermem-digest` triggers when the phase index is missing or stale) requires refreshed global CLI/Core and skill instructions. `sybermem project refresh --format json` does not itself rewrite the phase index, but running `/sybermem-phase-analyze` DOES change the project-local file `.sybermem/analysis/phase-index.md` (it persists confirmed phases + coverage map). This is expected and is the whole point of making phase analysis durable rather than a hand-written step.

### Managed-file propagation check

Before declaring an upgrade complete, verify for the current project:
- which local files need the new behavior
- whether each file is missing, fresh, stale SyberMem-managed, or custom
- whether stale SyberMem-managed files will be backed up before replacement
- whether custom files will be preserved unless the user explicitly approves replacement
- whether any legacy SyberMem protocol block was removed from `CLAUDE.md` / `AGENTS.md` non-destructively when present
- whether recognized old SyberMem Stop hook commands were surgically replaced with the global launcher path when present in otherwise custom settings files.
- whether recognized SyberMem-managed `UserPromptSubmit` entries were added or repaired surgically when missing or stale, while leaving unrelated custom hooks, env, and instructions untouched.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:

- Declaring the upgrade complete without running `sybermem project refresh --format json` or the documented fallback
- Skipping the project-local follow-up step after updating global skills
- Running `/sybermem-init-project` even though CLI refresh succeeded with valid JSON
- Leaving the old direct-hook command in `.claude/settings.json` when the launcher should have replaced it
- Claiming a behavior change is shipped when project-local files have not been created or refreshed

**All of these mean: stop, inspect state and reconfirm scope before recovery.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Global skills updated, so the project is updated too" | Project-local files (hooks, settings.json, CLAUDE.md) don't update automatically. Run CLI refresh. |
| "CLI refresh changed files, so I should also run init-project" | Changed files are a successful CLI outcome. Fall back only for missing/broken/non-JSON CLI failures. |
| "I already ran update last week" | Skills may have been updated since then. Each update is idempotent and fast with the health check. |

## Terminal State

This skill is complete when:
- global skills have been refreshed
- explicit-root refresh succeeded with verified root/overall, or the failure/deferred recovery was honestly reported
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
- Do not rewrite the rest of `CLAUDE.md` / `AGENTS.md` when removing a legacy `using-sybermem` protocol block; remove only the bounded block (or the whole file when purely SyberMem-managed).

## Integration

**Fallback sub-skills:**
- **sybermem-init-project** — Called only when CLI-first project refresh is missing, broken, or emits invalid JSON

**Related skills:**
- **sybermem-record** — Available after update
- **sybermem-summary** — Available after update
