---
name: sybermem-link
description: Use when establishing or adding a relationship between two existing SyberMem records, such as marking that a change implements a requirement, fixes a bug, or marking that one decision/requirement was superseded by another.
---

# sybermem-link Skill

**Announce at start:** "I'm using the sybermem-link skill to relate two project records."

Add a forward relation between two existing SyberMem records by editing the SOURCE record's frontmatter. Relations are forward-only.

## Core Invariant

- **Only the source-side state is modified. The target record is never touched. For `superseded-by`, this may also move the source conclusion in `.sybermem/INDEX.md` from `## Key Conclusions` to `## Archived Conclusions`.**

<HARD-GATE>
Do NOT modify the target record. Relations are stored forward-only on the source.
Do NOT create either record. Both must already exist; verify with a file-system tool.
Do NOT add a relation type other than implements, fixes, related, or superseded-by.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`.

## Usage

```
/sybermem-link <source-id> <relation> <target-id>
/sybermem-link change-008 implements requirement-002
/sybermem-link bug-001 related change-003
/sybermem-link decision-003 superseded-by decision-007
```

`<relation>` must be one of: `implements`, `fixes`, `related`, `superseded-by`, `crystallized-from`.

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply directory resolution rules above.
2. **Parse arguments** — `<source-id> <relation> <target-id>`. If `<relation>` is not one of `implements`/`fixes`/`related`/`superseded-by`/`crystallized-from`, stop and tell the user the valid relations.
3. **Verify both records exist** — use a file-system tool to find the source and target record files under the real SyberMem record directories (`.sybermem/changes/`, `.sybermem/decisions/`, `.sybermem/requirements/`, `.sybermem/bugs/`, `.sybermem/norms/`). Match the requested record IDs against the actual filenames (`YYYY-MM-DD-NNN-title.md`). If either does not exist, stop and report which one is missing.
4. **Read the source record** — load its frontmatter.
5. **Apply the relation behavior**
   - For `implements`/`fixes`/`related`/`crystallized-from`, append `<target-id>` to the matching frontmatter list field (`crystallized_from` for `crystallized-from`). If the field does not exist, create it as a list. If `<target-id>` is already present, skip (no duplicate). `crystallized-from` is used on a `norm` record to point at the decision/requirement it was crystallized from.
   - For `superseded-by`, write `superseded_by: <target-id>` in the source frontmatter. If the field already exists with the same value, skip. If it exists with a different value, warn and ask before overwriting.
6. **Apply the archive side-effect for `superseded-by`** — move the source conclusion from `## Key Conclusions` to `## Archived Conclusions`, appending `[superseded by <target-id>]`. If it is already archived with the same suffix, skip.
7. **Write the source-side updates only** — save the source file and any required source-side conclusion move in `.sybermem/INDEX.md`. Do NOT modify the target record.
8. **Report** — tell the user which source record fields were updated and whether the source conclusion was archived.

## Relation Semantics

| Relation | Meaning | Typical direction |
|---|---|---|
| `implements` | source implements the target requirement/decision | change → requirement / decision |
| `fixes` | source fixes the target bug | change / bug → bug |
| `related` | weak association, no clear causality | any → any |
| `superseded-by` | source decision/requirement has been replaced by the target decision/requirement | older decision / requirement → newer decision / requirement |

## Error Handling

- Source or target record does not exist → stop, name the missing one.
- Invalid relation type → stop, list valid relations.
- Relation already present → report no-op, do not duplicate.
- Source and target IDs are the same → stop.
- `superseded-by` would overwrite an existing different `superseded_by` value → ask before overwriting.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Editing the target record's frontmatter (relations are forward-only)
- Creating a record that does not exist instead of stopping
- Writing a relation type other than implements/fixes/related/superseded-by
- Duplicating a relation that is already present
- Deleting the source conclusion from `## Key Conclusions` instead of archiving it in `## Archived Conclusions`

**All of these mean: go back to the relevant step and re-verify.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll also add the reverse on the target for convenience" | Forward-only. Reverse is computed at query time by /sybermem-search. |
| "The target probably exists, I'll skip verification" | Verify with a file-system tool. A dangling relation is a defect. |
| "related is close enough for everything" | Use implements/fixes when the causality is clear. |
| "I can delete the old conclusion because the replacement exists now" | Do not delete the old conclusion. Archive it in `## Archived Conclusions` with a `[superseded by <target-id>]` suffix so historical retrieval still works. |

## Terminal State

This skill is complete when:
- both records were verified to exist
- the source record's relation field was updated (or confirmed already present)
- the target record was left untouched
- the user was told what changed

## Integration

**Related skills:**
- **sybermem-record** — also proposes relations at record-creation time
- **sybermem-search** — surfaces forward relations and computes reverse references
