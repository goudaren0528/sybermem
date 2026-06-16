---
name: sybermem-digest
description: Use when creating a durable phase digest from existing SyberMem records, with source coverage and duplicate protection.
---

# sybermem-digest Skill

Create a durable phase digest in `.sybermem/digests/` so future project understanding does not require re-reading every raw record.

In this skill, the artifact is a phase digest. The required `## Stage Digests` heading in `INDEX.md` is the index section name that lists these phase digests.

## Core Invariants

- **No digest without explicit source coverage.**
- **No candidate phase is used as a digest source until it has been confirmed (confirmation may be automatic).**

<HARD-GATE>
Do NOT create a digest file unless ALL of the following are true:
1. An explicit `source_records` list has been built from real `.sybermem/` record files
2. The source set has been normalized and compared against existing digests (no exact duplicates, partial overlaps warned)
3. The phase is confirmed (auto-confirmation counts) or explicit source records were provided by the user

If any of these is false, STOP. Do not write the digest file.
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

## Preconditions

Before creating a digest, verify all of the following:

- `.sybermem/digests/` exists
- `.sybermem/INDEX.md` contains a `## Stage Digests` section
- `.sybermem/INDEX.md` contains the exact insertion anchor `<!-- add new digest records here -->` within that section
- `.sybermem/templates/digest-template.md` exists

If any of these are missing, explain that digest support has not been enabled in this project yet and ask the user to run `/sybermem-update`.

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply Step 0 directory resolution rules above
2. **Verify preconditions** — `.sybermem/digests/` exists, `INDEX.md` has `## Stage Digests` with `<!-- add new digest records here -->`, `.sybermem/templates/digest-template.md` exists. If any missing, ask user to run `/sybermem-update`.
3. **Determine digest input mode**:
   - If explicit source records specified → use them directly, skip phase-index dependency
   - If no explicit source records:
     - If `.sybermem/analysis/phase-index.md` does not exist → REQUIRED: run `/sybermem-phase-analyze` first, then continue
     - If phase-index exists with confirmed phases → digest **all** confirmed phases without existing digests (batch mode)
     - If only candidate phases → auto-confirm all, then digest all in batch

### Batch mode (default when no explicit source records)

When multiple confirmed phases exist and no explicit source records were provided, create a digest for **each** confirmed phase that does not already have an existing digest with the same source coverage. Process them in chronological order by phase coverage dates. Skip any phase whose raw source records are incomplete or missing.

For each phase, run Steps 4–10 independently. This is the normal batch path — do not stop after the first phase and ask the user which one to digest next.

4. **Identify the phase scope** — use current session context, explicit source records, or the resolved phase-index. If fewer than 2 relevant source records for a given phase, skip that phase (batch) or refuse (single-phase).
5. **Select source records** — build an explicit `source_records` list from existing `.sybermem/changes/`, `decisions/`, `requirements/`, and `bugs/` records.
6. **Normalize and compare coverage** — normalize source list (project-relative paths, sorted, deduplicated). Compare against existing digests:
   - **Exact duplicate** → do not create, return existing digest path
   - **Partial overlap** → warn, recommend extending existing digest, only continue if user confirms
7. **Generate metadata** — set `type: digest`, `kind: phase`, `date`, `number`, `title`, `status: completed` (default), `source_records`, `coverage.from/to`, `fingerprint`
8. **Write the digest file** — path: `.sybermem/digests/{YYYY-MM-DD}-{NNN}-{title}.md`. Use `.sybermem/templates/digest-template.md`.
9. **Update INDEX.md** — insert row above `<!-- add new digest records here -->` in `## Stage Digests` table: `| NNN | YYYY-MM-DD | Title | <status> | X records | [link](digests/file.md) |`
10. **Preserve Key Conclusions signal quality** — do not add to `## Key Conclusions` by default. Only add if the digest introduces a truly global project conclusion.

## Error Handling

- Missing digest capability structure → ask user to run `/sybermem-update`
- No meaningful phase boundary → refuse and explain
- Fewer than 2 source records → refuse and explain
- Exact duplicate source set → refuse and point to the existing digest
- Partial overlap without explicit confirmation → stop after warning

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:

- Creating a digest without listing explicit source records
- Using a candidate phase as a digest source without first confirming it (auto-confirmation counts)
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
