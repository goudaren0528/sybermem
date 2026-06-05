---
name: sybermem-digest
description: Use when creating a durable phase digest from existing SyberMem records, with source coverage and duplicate protection.
---

# sybermem-digest Skill

Create a durable phase digest in `.sybermem/digests/` so future project understanding does not require re-reading every raw record.

## Directory Resolution Rules

Resolve the project data directory before reading or writing digests:

1. If `.sybermem/` exists, use it.
2. If only `ADR/` exists, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If both `.sybermem/` and `ADR/` exist, use `.sybermem/`, warn that `ADR/` was ignored, and do not auto-merge them.
4. If neither exists, prompt the user to run `/sybermem-init-project` first.

## Preconditions

Before creating a digest, verify all of the following:

- `.sybermem/digests/` exists
- `.sybermem/INDEX.md` contains a `## Stage Digests` section
- `.sybermem/templates/digest-template.md` exists

If any of these are missing, explain that digest support has not been enabled in this project yet and ask the user to run `/sybermem-update`.

## Flow

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

`| NNN | YYYY-MM-DD | Title | completed | X records | [link](digests/file.md) |`

### Step 7: Preserve `Key Conclusions` signal quality

Do not add a new line to `## Key Conclusions` by default.
Only add one if the digest introduces a truly global project conclusion.

## Error Handling

- Missing digest capability structure → ask user to run `/sybermem-update`
- No meaningful phase boundary → refuse and explain
- Fewer than 2 source records → refuse and explain
- Exact duplicate source set → refuse and point to the existing digest
- Partial overlap without explicit confirmation → stop after warning

## When NOT to Create a Digest

- The work is still in progress and not phase-bounded
- The source material is too small to be worth compressing
- The proposed digest would only repeat an existing digest with the same source records
