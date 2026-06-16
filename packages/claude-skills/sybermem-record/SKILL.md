---
name: sybermem-record
description: Use when creating SyberMem project records for changes, decisions, requirements, or bugs, including projects that still have legacy ADR storage.
---

# sybermem-record Skill

Unified SyberMem record entry point. AI auto-detects the record type from context.

## Core Invariant

- **No record is complete until the file is created, the correct table row is inserted, and the Key Conclusion is updated.**

<HARD-GATE>
Do NOT claim a record is complete unless ALL three actions have been executed and verified:
1. The record file exists on disk at the correct path
2. The INDEX.md table row has been inserted above the correct `<!-- add new records here -->` marker
3. The Key Conclusion line has been inserted above `<!-- add new conclusions here -->`

If any of these three is missing, the record is incomplete. Go back and finish it.
</HARD-GATE>

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

You MUST complete these steps in order:

1. **Resolve project root** — apply Step 0 directory resolution rules above
2. **Determine record type** — auto-detect from current work context:

| Signal | Type | Directory |
|--------|------|-----------|
| Add/modify/delete feature code | change | `.sybermem/changes/` |
| Tech selection, architecture design, multi-option evaluation | decision | `.sybermem/decisions/` |
| User raises requirement, discusses feature direction | requirement | `.sybermem/requirements/` |
| Fix bug, troubleshoot issue | bug | `.sybermem/bugs/` |

When uncertain, ask the user to choose.

3. **Get next number** — check `.sybermem/{type}/` directory, find max number, +1. Empty directory → 001. Format: 001, 002, 003...
4. **Collect information** — extract from the current session. Only ask the user when key information is missing.

Required sections:
- **change**: change content, reason, impact scope
- **decision**: context, considered options, final decision
- **requirement**: source, content, conclusion
- **bug**: description, root cause, solution

5. **Create file** — path: `.sybermem/{type}/{YYYY-MM-DD}-{NNN}-{title}.md`. Use `templates/{type}.md` as the content template.
6. **Update INDEX.md table** — insert a new row above the `<!-- add new records here -->` comment in the corresponding table.
7. **Write back key conclusion** — insert a one-line core conclusion above `<!-- add new conclusions here -->` in `## Key Conclusions`. Must include both **what changed** and **why**.

## Error Handling

- `.sybermem/INDEX.md` doesn't exist after resolution → prompt to initialize the project with `/sybermem-init-project`
- Number conflict → auto-increment
- Required field missing → ask the user to provide it

## Terminal State

This skill is complete when:
- the record file is created
- the correct INDEX.md table row is inserted
- the Key Conclusion line is updated
- the user has been told the record path

## When NOT to Record

- Simple formatting adjustments or comment edits
- Config tweaks with no functional impact
- WIP or draft work
