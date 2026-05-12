---
name: sybermem-record
description: Use when creating SyberMem project records for changes, decisions, requirements, or bugs, including projects that still have legacy ADR storage.
---

# sybermem-record Skill

Unified SyberMem record entry point. AI auto-detects the record type from context.

## Directory Resolution Rules

Resolve the project data directory before reading or writing records:

1. If `.sybermem/` exists, use it.
2. If only `ADR/` exists, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If both `.sybermem/` and `ADR/` exist, use `.sybermem/`, warn that `ADR/` was ignored, and do not auto-merge them.
4. If neither exists, prompt the user to run `/sybermem-init-project` first.

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

Use `packages/claude-skills/sybermem-record/templates/{type}.md` as the content template.

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
