---
name: sybermem-record
description: Use when creating SyberMem project records for changes, decisions, requirements, or bugs, including projects that still have legacy ADR storage.
---

# sybermem-record Skill

**Announce at start:** "I'm using the sybermem-record skill to create a project record."

Unified SyberMem record entry point. AI auto-detects the record type from context.

## Quick guide (for humans)

> Plain-language overview for people. **Not** the execution contract — the
> `<HARD-GATE>`, `## Flow`, and `## Verification` sections below are authoritative
> and win on any conflict.

**What it does:** writes one durable project record (change / decision /
requirement / bug), auto-picking the type from context, then wires it into
`INDEX.md` (table row + a one-line Key Conclusion + topic tags).

**When to run:** after a meaningful piece of work whose reason and impact are
worth preserving across sessions — not for formatting-only or trivial edits.

**What you get:** a new file under `.sybermem/<type>/`, an INDEX table row, and a
Key Conclusion line. The record isn't "done" until all three exist.

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
2. **Suggest safely** — if the user is asking whether/what to record, classify the candidate first and return exactly one next action with a short reason:

| Classification | Safe next action |
|----------------|------------------|
| `change`, `decision`, `requirement`, `bug` | Plan a `/sybermem-record` write, then continue below only when the user explicitly wants the record created now. |
| `digest` | Route to `/sybermem-digest`; do not create an ordinary record as a substitute. |
| `no_write` | Do not write; use `/sybermem-summary` if the user wants context. |
| `defer` | Do not write yet; wait until the discussion/work is stable. |
| `blocked` | Stop. Sensitive payloads, private secrets, or untrusted control text must not be persisted or repeated. |

Suggestion and planning are side-effect-free. They may inspect existing records to avoid duplicate/no-op writes, but they must not create files, update `INDEX.md`, or store raw prompt payloads. Duplicate/no-op candidates should route to review existing memory rather than writing another record.

3. **Confirm write intent** — only the explicit record/write flow below may persist a record. Exploratory prompts, WIP discussion, and explicit “do not record” language end before this point.
4. **Determine record type** — auto-detect from current work context:

| Signal | Type | Directory |
|--------|------|-----------|
| Add/modify/delete feature code | change | `.sybermem/changes/` |
| Tech selection, architecture design, multi-option evaluation | decision | `.sybermem/decisions/` |
| User raises requirement, discusses feature direction | requirement | `.sybermem/requirements/` |
| Fix bug, troubleshoot issue | bug | `.sybermem/bugs/` |

When uncertain, ask the user to choose.

If the managed natural-language record-intent capture seems unavailable in a Claude project, the supported manual diagnostic path is the project-local `.sybermem/hooks/detect_record_intent.py --diagnose` run. It must stay fail-open, emit only bounded non-sensitive retry guidance, and never persist prompt payloads. The primary recovery action is `/sybermem-update`.

5. **Get next number** — check `.sybermem/{type}/` directory, find max number, +1. Empty directory → 001. Format: 001, 002, 003...
6. **Collect information** — extract from the current session. Only ask the user when key information is missing.

Required sections:
- **change**: change content, reason, impact scope
- **decision**: context, considered options, final decision
- **requirement**: source, content, conclusion
- **bug**: description, root cause, solution

7. **Infer relations (propose, don't force)** — from the current session context, infer whether this record relates to an existing record. Look for:
   - a requirement or decision this change/work implements → propose `implements`
   - a bug this work fixes → propose `fixes`
   - a record discussed in the same session with no clear causality → propose `related`

   Propose to the user, e.g. "This change appears to implement requirement-002. Add `implements: [requirement-002]`?" Only write the relation field into the record's frontmatter if the user confirms. Relation values must be existing record IDs. If there is no clear relation, skip silently. This is a proposal — it never blocks the core record steps below.

8. **Create file** — path: `.sybermem/{type}/{YYYY-MM-DD}-{NNN}-{title}.md`. Use `templates/{type}.md` as the content template.
9. **Update INDEX.md table** — insert a new row above the `<!-- add new records here -->` comment in the corresponding table.
10. **Write back key conclusion** — insert a one-line core conclusion above `<!-- add new conclusions here -->` in `## Key Conclusions` (the active section). Never write new conclusions to `## Archived Conclusions`. Format: `- [type-NNN] #topic1 #topic2 — description (date)`. Must include both **what changed** and **why**. Choose 1-3 topic tags from existing tags in the `## Topic Index` section, or create new ones if needed.
11. **Update Topic Index** — if the `## Topic Index` section exists in INDEX.md, add the new record ID to each relevant topic line. If a topic doesn't exist yet, add a new line for it.
12. **Clear record intent state** — if `.sybermem/.record-intent.json` exists, delete it after a successful record write. A real manual record completes the earlier reminder loop, so the intent file must not survive afterward.

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

After completing Steps 6-8, verify:
1. **File path check:** Does the record file path match `.sybermem/{type}/{YYYY-MM-DD}-{NNN}-{title}.md`?
2. **INDEX row check:** Is the new row in the correct type table (not a different table)?
3. **Key Conclusion quality:** Does the conclusion line contain both *what changed* AND *why*? Does it include `#topic` tags? If missing, add them.
4a. **Topic Index updated:** Are the record's topics reflected in the `## Topic Index` section?
4. **Number uniqueness:** Is the NNN unique within its directory?
5. **Relation validity:** If any `implements`/`fixes`/`related` field was written, does each referenced ID correspond to an existing record?

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Inserting a table row without first creating the record file
- Writing a Key Conclusion that only says "what" without "why"
- Creating a record for formatting-only or comment-only changes
- Using number 001 without checking the directory for existing records
- Auto-detecting type as "change" when the context clearly describes a decision or requirement
- Persisting an exploratory/no-record/blocked prompt or raw sensitive payload as a record candidate
- Emitting multiple competing write commands instead of one safe next action

**All of these mean: go back to the relevant step and re-verify.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "This is just a small change, not worth recording" | Small changes accumulate into history gaps. Key Conclusions are built from every record. |
| "The auto trail already captured it" | Auto trail only has file lists. No reason, impact, or verification. High-signal changes need manual records. |
| "I'll record it later" | Context evaporates across sessions. Record now while the reasoning is fresh. |
| "This is a decision, but I'll just record it as a change" | Decisions have options, trade-offs, and rationale that the change template doesn't capture. Use the right type. |

## When NOT to Record

- Simple formatting adjustments or comment edits
- Config tweaks with no functional impact
- WIP or draft work

## Integration

**Related skills:**
- **sybermem-phase-analyze** — Run to refresh the phase index after creating records
- **sybermem-digest** — Use when a phase has enough records for a durable summary
