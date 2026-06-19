---
name: sybermem-link
description: Use when establishing or adding a relationship between two existing SyberMem records, such as marking that a change implements a requirement or fixes a bug.
---

# sybermem-link Skill

**Announce at start:** "I'm using the sybermem-link skill to relate two project records."

Add a forward relation between two existing SyberMem records by editing the SOURCE record's frontmatter. Relations are forward-only.

## Core Invariant

- **Only the source record's frontmatter is modified. The target record is never touched.**

<HARD-GATE>
Do NOT modify the target record. Relations are stored forward-only on the source.
Do NOT create either record. Both must already exist; verify with a file-system tool.
Do NOT add a relation type other than implements, fixes, or related.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Usage

```
/sybermem-link <source-id> <relation> <target-id>
/sybermem-link change-008 implements requirement-002
/sybermem-link bug-001 related change-003
```

`<relation>` must be one of: `implements`, `fixes`, `related`.

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply directory resolution rules above.
2. **Parse arguments** — `<source-id> <relation> <target-id>`. If `<relation>` is not one of `implements`/`fixes`/`related`, stop and tell the user the valid relations.
3. **Verify both records exist** — use a file-system tool to find the source and target record files under the real SyberMem record directories (`.sybermem/changes/`, `.sybermem/decisions/`, `.sybermem/requirements/`, `.sybermem/bugs/`). Match the requested record IDs against the actual filenames (`YYYY-MM-DD-NNN-title.md`). If either does not exist, stop and report which one is missing.
4. **Read the source record** — load its frontmatter.
5. **Append the relation** — in the source record's frontmatter, add `<target-id>` to the `<relation>` field. If the field does not exist, create it as a list. If `<target-id>` is already present, skip (no duplicate).
6. **Write the source record only** — save the source file. Do NOT modify the target.
7. **Report** — tell the user which record and field were updated.

## Relation Semantics

| Relation | Meaning | Typical direction |
|---|---|---|
| `implements` | source implements the target requirement/decision | change → requirement / decision |
| `fixes` | source fixes the target bug | change / bug → bug |
| `related` | weak association, no clear causality | any → any |

## Error Handling

- Source or target record does not exist → stop, name the missing one.
- Invalid relation type → stop, list valid relations.
- Relation already present → report no-op, do not duplicate.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Editing the target record's frontmatter (relations are forward-only)
- Creating a record that does not exist instead of stopping
- Writing a relation type other than implements/fixes/related
- Duplicating a relation that is already present

**All of these mean: go back to the relevant step and re-verify.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll also add the reverse on the target for convenience" | Forward-only. Reverse is computed at query time by /sybermem-search. |
| "The target probably exists, I'll skip verification" | Verify with a file-system tool. A dangling relation is a defect. |
| "related is close enough for everything" | Use implements/fixes when the causality is clear. |

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
