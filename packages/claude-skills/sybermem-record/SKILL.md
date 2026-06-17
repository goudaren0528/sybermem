---
name: sybermem-record
description: Use when creating SyberMem project records for changes, decisions, requirements, or bugs, including projects that still have legacy ADR storage.
---

# sybermem-record Skill

**Announce at start:** "I'm using the sybermem-record skill to create a project record."

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

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

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
7. **Write back key conclusion** — insert a one-line core conclusion above `<!-- add new conclusions here -->` in `## Key Conclusions`. Format: `- [type-NNN] #topic1 #topic2 — description (date)`. Must include both **what changed** and **why**. Choose 1-3 topic tags from existing tags in the `## Topic Index` section, or create new ones if needed.
8. **Update Topic Index** — if the `## Topic Index` section exists in INDEX.md, add the new record ID to each relevant topic line. If a topic doesn't exist yet, add a new line for it.

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

## Verification

After completing Steps 5-7, verify:
1. **File path check:** Does the record file path match `.sybermem/{type}/{YYYY-MM-DD}-{NNN}-{title}.md`?
2. **INDEX row check:** Is the new row in the correct type table (not a different table)?
3. **Key Conclusion quality:** Does the conclusion line contain both *what changed* AND *why*? Does it include `#topic` tags? If missing, add them.
4a. **Topic Index updated:** Are the record's topics reflected in the `## Topic Index` section?
4. **Number uniqueness:** Is the NNN unique within its directory?

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Inserting a table row without first creating the record file
- Writing a Key Conclusion that only says "what" without "why"
- Creating a record for formatting-only or comment-only changes
- Using number 001 without checking the directory for existing records
- Auto-detecting type as "change" when the context clearly describes a decision or requirement

**All of these mean: go back to the relevant step and re-verify.**

## When NOT to Record

- Simple formatting adjustments or comment edits
- Config tweaks with no functional impact
- WIP or draft work
