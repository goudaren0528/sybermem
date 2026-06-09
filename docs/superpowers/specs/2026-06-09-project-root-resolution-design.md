# SyberMem Project Root Resolution Design

Date: 2026-06-09
Status: Proposed

## Overview

SyberMem currently assumes that the AI's current working directory is the project root. All skills, the stop hook, and the directory resolution rules operate on relative paths from `cwd`.

This assumption breaks when:
- the user opens a subdirectory of the actual project (e.g., `D:\erp-lite\web` instead of `D:\erp-lite`)
- the user works inside a monorepo subfolder
- the user switches between directories within the same project during a session

When this happens:
- the stop hook cannot find `.sybermem/hooks/record_change_on_stop.py` because the relative path resolves against the wrong directory
- `/sybermem-init-project` may create a duplicate `.sybermem/` inside a subdirectory instead of recognizing the parent project
- `/sybermem-record`, `/sybermem-digest`, `/sybermem-phase-analyze`, and `/sybermem-summary` all read from and write to the wrong `.sybermem/` or fail to find one at all
- project memory gets fragmented across nested `.sybermem/` directories

This spec introduces a project root resolution layer that all SyberMem skills and the stop hook must use before any other operation.

## Goals

- Define a deterministic algorithm for resolving the SyberMem project root from any subdirectory
- Prevent accidental creation of nested `.sybermem/` directories inside subdirectories of an existing SyberMem project
- Make the stop hook reliable regardless of which subdirectory the session's `cwd` happens to be
- Keep the resolution logic simple, predictable, and explainable to users
- Preserve backward compatibility for projects where `cwd` is already the correct project root

## Non-Goals

- Do not support multiple independent SyberMem projects nested inside each other in v1
- Do not introduce a project registry or global project index
- Do not change the `.sybermem/` directory structure itself
- Do not require users to manually configure the project root

## Resolution Algorithm

### Core rule

From the current working directory, walk upward through parent directories. The SyberMem project root is the **nearest ancestor directory** (including `cwd` itself) that contains **both**:

1. `.sybermem/` directory
2. `.claude/settings.json` file

### Why both signals

Using `.sybermem/` alone would match any directory that happens to have a `.sybermem/` folder, even if it was created accidentally or is an unrelated artifact.

Using `.claude/settings.json` alone would match Claude Code project roots that have nothing to do with SyberMem.

Requiring both ensures the resolved root is genuinely a SyberMem-initialized project.

### Walk-up behavior

```text
Starting from: cwd
Check: does cwd contain both .sybermem/ AND .claude/settings.json?
  Yes → cwd is the project root. Stop.
  No  → move to parent directory. Repeat.

Stop conditions:
  - Found a directory with both markers → that is the project root
  - Reached filesystem root without finding both markers → no SyberMem project root found
```

### Boundary: filesystem root

If the walk reaches the filesystem root (`/` on Unix, drive root on Windows) without finding both markers, the resolution fails. The skill or hook should then behave as if no SyberMem project exists and either:
- prompt the user to run `/sybermem-init-project` (for skills)
- exit silently with code 0 (for the stop hook)

### Boundary: git repository root

As an optional additional guard, the walk-up may stop at the git repository root (the directory containing `.git/`). This prevents accidentally resolving to an unrelated parent project outside the current repository.

If the git root is reached without finding both markers, treat it the same as reaching the filesystem root.

## Where Resolution Must Be Applied

### All SyberMem skills

Every SyberMem skill must resolve the project root before doing any other work. This replaces the current assumption that `cwd` is the project root.

Affected skills:
- `/sybermem-init-project`
- `/sybermem-update`
- `/sybermem-record`
- `/sybermem-summary`
- `/sybermem-digest`
- `/sybermem-phase-analyze`
- `/sybermem-phase-confirm`

Each skill's "Directory Resolution Rules" section must be updated to include the walk-up algorithm before the existing `.sybermem/` vs `ADR/` checks.

### The stop hook

The stop hook (`record_change_on_stop.py`) currently uses `Path.cwd()` as the project root. It must be updated to walk up from `cwd` and find the nearest directory with both `.sybermem/` and `.claude/settings.json`.

This is the most critical fix because the stop hook runs automatically and cannot ask the user for clarification.

### `/sybermem-init-project` anti-nesting guard

When `/sybermem-init-project` runs in a subdirectory, it must first check whether a parent directory is already a SyberMem project root. If so:
- do NOT create a new `.sybermem/` in the current subdirectory
- instead, inform the user that the project root was found at `<parent-path>`
- offer to operate on that parent root instead
- only create a new `.sybermem/` if the user explicitly confirms they want a separate nested project (rare edge case)

## Resolution Result

When resolution succeeds, the result should be an absolute path to the project root directory. All subsequent operations in that skill/hook invocation should use this resolved root as their base, not `cwd`.

For example:
- `INDEX_PATH = resolved_root / ".sybermem" / "INDEX.md"`
- `CHANGES_DIR = resolved_root / ".sybermem" / "changes"`
- `NUDGE_STATE_PATH = resolved_root / ".sybermem" / ".auto-nudge-state.json"`

## Impact on the Stop Hook

The stop hook is the most sensitive consumer because:
- it runs automatically on every session stop
- it cannot prompt the user
- it uses relative paths internally

### Required changes

1. Replace `ROOT = Path.cwd()` with a walk-up resolution function
2. If resolution fails (no SyberMem root found), exit silently with code 0
3. If resolution succeeds, use the resolved root for all path construction
4. Git-status commands should still run from the original `cwd` (so they see the right workspace changes), but record files should be written to the resolved project root's `.sybermem/`

### Edge case: git changed files vs project root

The stop hook collects changed files using `git diff` etc. These commands should continue to run from `cwd` so they capture the actual workspace state. But the generated change record should be written to `resolved_root/.sybermem/changes/`, and `resolved_root/.sybermem/INDEX.md` should be updated.

This means the hook needs to distinguish between:
- **git context directory**: where `git` commands run (original `cwd`)
- **sybermem project root**: where `.sybermem/` records are stored (resolved root)

## Impact on Skills

### Common pattern

Every skill should begin with:

```text
Step 0: Resolve project root

Walk up from the current working directory to find the nearest ancestor
containing both .sybermem/ and .claude/settings.json.

If found: use that directory as the project root for all subsequent steps.
If not found: prompt the user to run /sybermem-init-project.
```

This replaces the current "Directory Resolution Rules" which only check `cwd`.

### `/sybermem-init-project` special behavior

When the walk-up finds an existing SyberMem root above `cwd`:
- warn the user that a parent project root already exists
- ask whether they want to operate on the parent root or create a new nested project
- default to operating on the parent root
- only create nested `.sybermem/` on explicit user confirmation

### All other skills

When the walk-up finds the project root:
- use it transparently
- optionally inform the user: "Using SyberMem project root at `<resolved-path>`"
- proceed with normal skill flow against the resolved root

## Upgrade and Compatibility

### Existing projects where cwd = project root

No behavior change. The walk-up resolves immediately at `cwd` and everything works as before.

### Existing projects accessed from a subdirectory

The walk-up finds the parent project root. Skills and the stop hook now work correctly without requiring the user to `cd` to the project root first.

### Projects that already have nested `.sybermem/` directories

If a subdirectory already has its own `.sybermem/` and `.claude/settings.json`, the walk-up will resolve to that subdirectory (since it is the nearest match). This preserves intentional nested project setups without breaking them.

### Rollout

This change should be distributed through the standard two-layer model:
1. Global skill update (new skill definitions with walk-up logic)
2. Project-local `/sybermem-update` (refreshes the stop hook with walk-up logic)

## Acceptance Criteria

1. From any subdirectory of a SyberMem project, all skills resolve to the correct project root.
2. The stop hook resolves to the correct project root and does not fail with file-not-found errors when run from a subdirectory.
3. `/sybermem-init-project` warns when run from a subdirectory of an existing SyberMem project and does not create a nested `.sybermem/` by default.
4. The resolution algorithm is deterministic: same directory structure always produces the same resolved root.
5. If no SyberMem root is found, skills prompt for initialization and the stop hook exits silently.
6. Existing projects where `cwd` is already the project root see no behavior change.
7. The walk-up stops at the filesystem root or git repository root, whichever comes first.

## Risks

### Risk: unexpected parent resolution

A subdirectory might resolve to a parent project the user did not intend. 

Mitigation: the git-root boundary prevents walking outside the current repository, and skills can optionally display the resolved root path so the user notices if it is wrong.

### Risk: intentional nested projects break

If a user genuinely wants independent SyberMem projects nested inside each other, the walk-up might resolve to the wrong one.

Mitigation: the walk-up resolves to the nearest match, which should be the innermost project. If both the child and parent have `.sybermem/` + `.claude/settings.json`, the child wins.

### Risk: stop hook performance

Walking up the directory tree adds a small number of filesystem existence checks.

Mitigation: the walk is bounded by directory depth (typically < 10 levels) and each check is two `os.path.exists()` calls. This is negligible.

## Recommendation

Project root resolution is a foundational fix that should be implemented before further capability additions. Without it, every new skill and every hook enhancement inherits the same subdirectory fragility.

In one sentence:

**SyberMem should walk up from `cwd` to find the nearest ancestor with both `.sybermem/` and `.claude/settings.json`, use that as the canonical project root for all operations, and refuse to create nested `.sybermem/` directories unless the user explicitly requests it.**
