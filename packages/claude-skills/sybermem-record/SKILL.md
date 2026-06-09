---
name: sybermem-record
description: Use when creating SyberMem project records for changes, decisions, requirements, or bugs, including projects that still have legacy ADR storage.
---

# sybermem-record Skill

Unified SyberMem record entry point. AI auto-detects the record type from context.

## Core Invariant

- **No record is complete until the file is created, the correct table row is inserted, and the Key Conclusion is updated.**

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

### Step 1: Determine record type

Auto-detect from current work context:

| Signal | Type | Directory |
|--------|------|-----------|
| Add/modify/delete feature code | change | `.sybermem/changes/` |
| Tech selection, architecture design, multi-option evaluation | decision | `.sybermem/decisions/` |
| User raises requirement, discusses feature direction | requirement | `.sybermem/requirements/` |
| Fix bug, troubleshoot issue | bug | `.sybermem/bugs/` |

When uncertain, ask the user to choose.

### Step 2: Get next number

```
Check .sybermem/{type}/ directory → find max number → +1
Empty directory → 001
Format: 001, 002, 003...
```

### Step 3: Collect information

Extract from the current session. Only ask the user when key information is missing.

Required sections:
- **change**: change content, reason, impact scope
- **decision**: context, considered options, final decision
- **requirement**: source, content, conclusion
- **bug**: description, root cause, solution

### Step 4: Create file

Path: `.sybermem/{type}/{YYYY-MM-DD}-{NNN}-{title}.md`

Use `templates/{type}.md` as the content template.

### Step 5: Update INDEX.md table

Insert a new row above the `<!-- add new records here -->` comment in the corresponding table in `.sybermem/INDEX.md`.

### Step 6: Write back key conclusion

Insert a one-line core conclusion above the `<!-- add new conclusions here -->` comment in `.sybermem/INDEX.md` `## Key Conclusions`.

The conclusion must include both **what changed** and **why**.

## Error Handling

- `.sybermem/INDEX.md` doesn't exist after resolution → prompt to initialize the project with `/sybermem-init-project`
- Number conflict → auto-increment
- Required field missing → ask the user to provide it

## When NOT to Record

- Simple formatting adjustments or comment edits
- Config tweaks with no functional impact
- WIP or draft work
