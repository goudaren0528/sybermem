---
name: using-sybermem
description: Use when you want a visible SyberMem entrypoint that diagnoses the current project root, loaded SyberMem layers, and the recommended next workflow command.
---

# using-sybermem Skill

`using-sybermem` is the visible advisory entrypoint for the SyberMem system. It does not replace concrete skills like `record`, `summary`, `digest`, or `phase-analyze`. It reports the current project's SyberMem state and tells the user what the correct next command is.

## Core Invariant

- **`using-sybermem` reports and routes; it does not silently perform downstream business actions.**

<HARD-GATE>
Do NOT auto-run `phase-analyze`, `record`, `summary`, or `digest` without telling the user.
Do NOT treat candidate phases as canonical.
Do NOT ignore the resolved root and answer from the wrong directory context.
</HARD-GATE>

## Directory Resolution Rules

### Step 0: Resolve project root

Before any other operation, walk up from the current working directory to find the nearest ancestor directory (including cwd itself) that contains **both** `.sybermem/` **and** `.claude/settings.json`.

- If found: use that directory as the project root for all subsequent steps. Inform the user if the resolved root differs from cwd.
- If not found (reached git repository root or filesystem root without a match): prompt the user to run `/sybermem-init-project`.

After resolving the project root, apply legacy directory checks against the resolved root:
1. If the resolved root has `.sybermem/`, use it.
2. If the resolved root has only `ADR/`, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If the resolved root has both `.sybermem/` and `ADR/`, use `.sybermem/`, warn that `ADR/` was ignored.

## Flow

### Step 1: Report current SyberMem state

At minimum, report:
- resolved project root
- whether `.sybermem/INDEX.md` exists
- whether `.sybermem/digests/` exists
- whether `.sybermem/analysis/phase-index.md` exists
- whether the `using-sybermem` session protocol block is present in instruction files when relevant

### Step 2: Report current routing behavior

Explain what would currently happen if the user runs:
- `/sybermem-summary`
- `/sybermem-digest`
- `/sybermem-phase-analyze`
- `/sybermem-record`
- `/sybermem-update`

### Step 3: Recommend the next command

Recommend the most appropriate next SyberMem command based on the current state.
Examples:
- if no phase index exists and the user wants phase-aware workflows → recommend `/sybermem-phase-analyze`
- if a candidate phase exists but no confirmed phase exists → recommend `/sybermem-phase-confirm`
- if important work is happening and only a lightweight trail exists → recommend `/sybermem-record`
- if the project appears partially upgraded → recommend `/sybermem-update`

## Output Style

Return a short advisory report, for example:

```md
## SyberMem Status
- Project root: ...
- Index: present / missing
- Digests: present / missing
- Phase index: present / missing

## Current routing
- summary: ...
- digest: ...
- analyze: ...
- record: ...
- update: ...

## Recommended next step
- ...
```

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Auto-running `phase-analyze`, `record`, `summary`, or `digest` without telling the user
- Treating candidate phases as canonical
- Ignoring the resolved root and answering from the wrong directory context

## Terminal State

This skill is complete when:
- the current SyberMem state has been reported
- the routing implications for the main SyberMem commands have been explained
- a recommended next command has been given
