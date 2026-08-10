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
requirement / bug), auto-picking the type from context, then fills canonical
frontmatter fields for `record_id`, `key_conclusion`, and `topics`. Project
`INDEX.md` content is derived later with the CLI, not hand-edited.

**When to run:** after a meaningful piece of work whose reason and impact are
worth preserving across sessions — not for formatting-only or trivial edits.

**What you get:** a new file under `.sybermem/<type>/`, plus a rebuilt and
checked derived project `INDEX.md`. Legacy numeric records stay supported for
reading and indexing, but new records use generated canonical IDs.

## Core Invariant

- **No record is complete until the canonical record file exists, its generated frontmatter is present, and derived project INDEX build/check pass.**

<HARD-GATE>
Do NOT claim a record is complete unless ALL three actions have been executed and verified:
1. The record file exists on disk at the correct path
2. The file frontmatter includes generated `record_id`, `key_conclusion`, and `topics`
3. `sybermem project index build` and `sybermem project index check` both succeed

If any of these three is missing, the record is incomplete. Go back and finish it.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Choose a path: fast vs full

Once write intent is clear (the user explicitly wants the record created now), pick a path:

- **Fast path (default for a single, unambiguous record).** When the record type is
  obvious from context and all required fields can be filled from the current session,
  do it in one shot without per-item back-and-forth: auto-detect the type, generate the
  metadata, infer relations, write the file, and build/check the index. Do **not** stop
  to ask the user to confirm the type, each relation, or the wording unless something is
  genuinely ambiguous. Announce what you recorded once, at the end (path + type + key
  conclusion), so the user can correct if needed.
- **Full path (for ambiguous or high-stakes records).** Use the step-by-step flow below
  when the type is unclear, multiple records might be warranted, it is a `decision` with
  real trade-offs, or the user asked to review before writing. Here you classify and
  confirm before persisting.

Both paths obey the same `<HARD-GATE>` and `## Verification`: a record is complete only
when the file exists with generated `record_id`/`key_conclusion`/`topics` and
`sybermem project index build` + `check` both pass. Fast path removes *confirmation
friction*, never the completion guarantees.

## Flow

The steps below are the **full path**. On the fast path, execute the same steps 4-11
in one pass from context, skipping the interactive confirmations in steps 2-3 and the
per-relation prompt in step 7 (still infer and write relations, just don't ask).

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

Suggestion and planning are side-effect-free. They may inspect existing records to avoid duplicate/no-op writes, but they must not create files, run project index writes, or store raw prompt payloads. Duplicate/no-op candidates should route to review existing memory rather than writing another record.

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

5. **Generate canonical metadata** — call the core helper contract `generate_record_id(type)` to get `record_id`. Do not invent UUID strings manually. Also generate a one-line `key_conclusion` that states both **what changed** and **why**, and choose 1-3 `topics` tags. Existing legacy numeric records remain valid for reading and indexing, but new records use the generated `record_id` path and frontmatter.
6. **Collect information** — extract from the current session. Only ask the user when key information is missing.

Required sections:
- **change**: change content, reason, impact scope
- **decision**: context, considered options, final decision
- **requirement**: source, content, conclusion
- **bug**: description, root cause, solution

6a. **Optional: declare trust metadata explicitly** — trust fields are normally *inferred* (source_kind from path, authority from source, lifecycle from status/relations). You MAY additionally set explicit frontmatter to override inference when the author's intent differs from what inference would produce:
   - `authority: authoritative | summarized | evidence` — e.g. mark a low-signal note as `evidence` so automatic recall deprioritizes it.
   - `lifecycle: active | resolved | superseded | archived | conflicted` — e.g. pin a record `archived` without waiting on INDEX-derived detection.
   Only recognized values take effect; an unknown value is ignored and inference applies. Omit these fields unless you specifically need to override — inference is the default and is correct for the vast majority of records.

7. **Infer relations (propose, don't force)** — from the current session context, infer whether this record relates to an existing record. Look for:
   - a requirement or decision this change/work implements → propose `implements`
   - a bug this work fixes → propose `fixes`
   - a record discussed in the same session with no clear causality → propose `related`

   On the **full path**, propose to the user, e.g. "This change appears to implement requirement-002. Add `implements: [requirement-002]`?" and only write the relation if the user confirms. On the **fast path**, when the relation is clear from context, write the inferred relation directly and mention it in the final summary (the user can correct). Either way, relation values must be existing record IDs; if there is no clear relation, skip silently. This never blocks the core record steps below.

8. **Create file** — path: `.sybermem/{type}/{YYYY-MM-DD}-{record_id}-{slug}.md`. Use `templates/{type}.md` as the content template and fill the canonical frontmatter fields exactly as `record_id`, `key_conclusion`, and `topics`.
9. **Build derived project INDEX** — run `sybermem project index build` after the record file is written. Do not hand-edit `.sybermem/INDEX.md`, Key Conclusions, topic tables, or per-type tables.
10. **Check derived project INDEX** — run `sybermem project index check` and treat any failure as blocking.
11. **Clear record intent state** — if `.sybermem/.record-intent.json` exists, delete it after a successful record write and successful project index build/check. A real manual record completes the earlier reminder loop, so the intent file must not survive afterward.

## Error Handling

- `.sybermem/` doesn't exist after resolution → prompt to initialize the project with `/sybermem-init-project`
- `generate_record_id(type)` unavailable or project index build/check fails → stop and fix the underlying environment instead of inventing IDs or editing INDEX by hand
- Required field missing → ask the user to provide it

## Terminal State

This skill is complete when:
- the record file is created
- the file contains generated `record_id`, `key_conclusion`, and `topics`
- `sybermem project index build` succeeds
- `sybermem project index check` succeeds
- the user has been told the record path

## Verification

After completing Steps 6-10, verify:
1. **File path check:** Does the record file path match `.sybermem/{type}/{YYYY-MM-DD}-{record_id}-{slug}.md`?
2. **Canonical frontmatter check:** Are `record_id`, `key_conclusion`, and `topics` present with those exact field names?
3. **ID source check:** Was `record_id` obtained from `generate_record_id(type)` instead of manual UUID invention?
4. **Key conclusion quality:** Does `key_conclusion` contain both *what changed* and *why*?
5. **Topic quality:** Does `topics` contain the intended 1-3 topic tags for derived indexing?
6. **Derived INDEX build check:** Did `sybermem project index build` succeed without manual INDEX edits?
7. **Derived INDEX integrity check:** Did `sybermem project index check` succeed?
8. **Legacy compatibility check:** Were existing legacy numeric records left untouched and still treated as supported historical inputs?
9. **Relation validity:** If any `implements`/`fixes`/`related` field was written, does each referenced ID correspond to an existing record?

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Hand-editing `.sybermem/INDEX.md`, Key Conclusions, topic tables, or per-type record tables
- Writing a `key_conclusion` that only says "what" without "why"
- Creating a record for formatting-only or comment-only changes
- Allocating a new numeric record number for a fresh record
- Inventing a UUID string instead of using `generate_record_id(type)`
- Writing a new record without `record_id`, `key_conclusion`, or `topics`
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
| "I'll just edit INDEX.md directly, it's faster" | INDEX is derived output now. The canonical source is the record file plus `sybermem project index build/check`. |

## When NOT to Record

- Simple formatting adjustments or comment edits
- Config tweaks with no functional impact
- WIP or draft work

## Integration

**Related skills:**
- **sybermem-phase-analyze** — Run to refresh the phase index after creating records
- **sybermem-digest** — Use when a phase has enough records for a durable summary
