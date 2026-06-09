---
name: sybermem-digest
description: Use when creating a durable phase digest from existing SyberMem records, with source coverage and duplicate protection.
---

# sybermem-digest Skill

Create a durable phase digest in `.sybermem/digests/` so future project understanding does not require re-reading every raw record.

In this skill, the artifact is a phase digest. The required `## Stage Digests` heading in `INDEX.md` is the index section name that lists these phase digests.

## Core Invariants

- **No digest without explicit source coverage.**
- **No candidate phase is canonical until explicitly confirmed.**

## Directory Resolution Rules

### Step 0: Resolve project root

Before any other operation, walk up from the current working directory to find the nearest ancestor directory (including cwd itself) that contains **both** `.sybermem/` **and** `.claude/settings.json`.

- If found: use that directory as the project root for all subsequent steps. Inform the user if the resolved root differs from cwd: "Using SyberMem project root at `<resolved-path>`".
- If not found (reached git repository root or filesystem root without a match): prompt the user to run `/sybermem-init-project`.

After resolving the project root, apply legacy directory checks against the resolved root:
1. If the resolved root has `.sybermem/`, use it.
2. If the resolved root has only `ADR/`, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If the resolved root has both `.sybermem/` and `ADR/`, use `.sybermem/`, warn that `ADR/` was ignored.

## Preconditions

Before creating a digest, verify all of the following:

- `.sybermem/digests/` exists
- `.sybermem/INDEX.md` contains a `## Stage Digests` section
- `.sybermem/INDEX.md` contains the exact insertion anchor `<!-- add new digest records here -->` within that section
- `.sybermem/templates/digest-template.md` exists

If any of these are missing, explain that digest support has not been enabled in this project yet and ask the user to run `/sybermem-update`.

## Flow

- If `.sybermem/analysis/phase-index.md` exists, prefer a confirmed phase as the digest source. If only a candidate phase exists, ask the user to confirm or adjust it first instead of silently treating it as canonical.

### Step 1: Identify the phase scope

Use current session context and existing `.sybermem/` records to determine whether there is a meaningful completed or clearly bounded phase to compress.

If there is no meaningful phase boundary or fewer than 2 relevant source records, refuse to create a digest and explain why.

### Step 2: Select source records

Build an explicit `source_records` list from existing `.sybermem/changes/`, `decisions/`, `requirements/`, and `bugs/` records.

The digest must not be created unless the source set is explicit enough to:
- list coverage
- compare against existing digests
- guide future drill-down reading

### Step 3: Normalize and compare coverage

Normalize the `source_records` list by:
- converting to project-relative paths
- sorting ascending
- removing duplicates

Then compare the normalized list against existing digest files in `.sybermem/digests/`.

#### Exact duplicate rule

If an existing digest has the exact same normalized source set:
- do not create a new digest
- return the existing digest path
- tell the user this phase is already compressed

#### Partial overlap rule

If an existing digest overlaps partially with the proposed source set:
- show the overlapping records
- warn that a partial coverage overlap exists
- recommend extending the existing digest instead of creating a sibling overlap
- only continue if the user explicitly confirms they want a broader enclosing digest

### Step 4: Generate metadata

Set:
- `type: digest`
- `kind: phase`
- `date: YYYY-MM-DD`
- `number: NNN` within `.sybermem/digests/`
- `title: <phase title>`
- `status: completed` by default unless the user explicitly wants `active`
- `source_records: [...]`
- `coverage.from` and `coverage.to` from the earliest and latest source record dates
- `fingerprint` from the normalized source set

Carry the chosen `status` value through consistently into both the digest frontmatter and the `INDEX.md` row.

### Step 5: Write the digest file

Path:

`.sybermem/digests/{YYYY-MM-DD}-{NNN}-{title}.md`

Use `.sybermem/templates/digest-template.md` and fill in:
- Phase Scope
- Core Conclusions
- Key Decisions and Changes
- Current State
- Recommended Next Reads
- Source Coverage

### Step 6: Update `INDEX.md`

Insert a new row above `<!-- add new digest records here -->` in the `## Stage Digests` table.

Use this format:

`| NNN | YYYY-MM-DD | Title | <status> | X records | [link](digests/file.md) |`

Use the same status selected in Step 4.

### Step 7: Preserve `Key Conclusions` signal quality

Do not add a new line to `## Key Conclusions` by default.
Only add one if the digest introduces a truly global project conclusion.

- `/sybermem-digest` is the durable phase conclusion artifact. If the user wants the current state of an active confirmed phase, prefer `/sybermem-summary` instead.

## Error Handling

- Missing digest capability structure → ask user to run `/sybermem-update`
- No meaningful phase boundary → refuse and explain
- Fewer than 2 source records → refuse and explain
- Exact duplicate source set → refuse and point to the existing digest
- Partial overlap without explicit confirmation → stop after warning

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:

- Creating a digest without listing explicit source records
- Treating a candidate phase as canonical without explicit user confirmation
- Generating a second digest for the exact same source set
- Skipping the overlap warning when source records partially overlap with an existing digest
- Writing a digest that reads like a current-state summary instead of a durable conclusion

**All of these mean: go back to Step 2 and re-verify source coverage and phase status.**

## Terminal State

This skill is complete when:
- the digest file is written to `.sybermem/digests/`
- the `INDEX.md` Stage Digests table has a new row
- the source records are explicitly listed in the digest
- the user has been shown the digest path and coverage

## When NOT to Create a Digest

- The work is still in progress and not phase-bounded
- The source material is too small to be worth compressing
- The proposed digest would only repeat an existing digest with the same source records
