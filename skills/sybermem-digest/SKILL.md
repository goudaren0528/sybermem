---
name: sybermem-digest
description: Use when creating a durable phase digest from existing SyberMem records, with source coverage and duplicate protection.
---

# sybermem-digest Skill

**Announce at start:** "I'm using the sybermem-digest skill to create a durable phase digest."

Create a durable phase digest in `.sybermem/digests/` so future project understanding does not require re-reading every raw record.

In this skill, the artifact is a phase digest. The required `## Phase Digests` heading in `INDEX.md` is the index section name that lists these phase digests.

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

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`.

## Preconditions

Before creating a digest, verify all of the following:

- `.sybermem/digests/` exists
- `.sybermem/INDEX.md` contains a `## Phase Digests` section
- `.sybermem/INDEX.md` contains the exact insertion anchor `<!-- add new digest records here -->` within that section
- `.sybermem/templates/digest-template.md` exists

If any of these are missing, explain that digest support has not been enabled in this project yet and ask the user to run `/sybermem-update`.

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply Step 0 directory resolution rules above
2. **Verify preconditions** — `.sybermem/digests/` exists, `INDEX.md` has `## Phase Digests` with `<!-- add new digest records here -->`, `.sybermem/templates/digest-template.md` exists. If any missing, ask user to run `/sybermem-update`.
3. **Determine digest input mode**:
   - If explicit source records specified → use them directly, skip phase-index dependency
   - If no explicit source records:
     - If `.sybermem/analysis/phase-index.md` does not exist or is stale → **RUN `/sybermem-phase-analyze` first** (see Step 3b), then continue
     - If phase-index exists with confirmed phases → digest **all** confirmed phases without existing digests (batch mode)
     - If only candidate phases → auto-confirm all, then digest all in batch

### 3b. Digest drives phase analysis (agent semantic grouping)

When a phase index is missing or out of date, `/sybermem-digest` **triggers** `/sybermem-phase-analyze` rather than blocking. Phase grouping is an agent judgement: read the full `.sybermem/` record history and produce a **semantic** grouping (`{ "phases": [ { "title": "...", "covered_records": ["change-001", ...] } ] }`), then persist it with `sybermem project phase analyze --from-json <file>`. Mechanical grouping (`sybermem project phase analyze` without `--from-json`) is only a fallback when agent grouping is unavailable. Resolve record ids to files by each record's frontmatter `record_id:`, never by filename.

### Batch mode (default when no explicit source records)

When multiple confirmed phases exist and no explicit source records were provided, create a digest for **each** confirmed phase that does not already have an existing digest with the same source coverage. Prefer phases with `lifecycle: completed` first, then `lifecycle: active` if no completed phases remain undigested. Skip phases with `lifecycle: archived` (they already have digests). Process in chronological order by phase coverage dates. Skip any phase whose raw source records are incomplete or missing. Phases missing a `lifecycle` field are treated as `active`.

For each phase, run Steps 4–10 independently. This is the normal batch path — do not stop after the first phase and ask the user which one to digest next.

4. **Identify the phase scope** — use current session context, explicit source records, or the resolved phase-index. If fewer than 2 relevant source records for a given phase, skip that phase (batch) or refuse (single-phase).
5. **Select source records** — build an explicit `source_records` list from existing `.sybermem/changes/`, `decisions/`, `requirements/`, and `bugs/` records.
6. **Normalize and compare coverage** — normalize source list (project-relative paths, sorted, deduplicated). Compare against existing digests:
   - **Exact duplicate** → do not create, return existing digest path
   - **Partial overlap** → warn, recommend extending existing digest, only continue if user confirms
7. **Generate metadata** — set `type: digest`, `kind: phase`, `date`, `number`, `title`, `status: completed` (default), `source_records`, `coverage.from/to`, and `coverage_hash` (see Step 7a)
7a. **Compute `coverage_hash`** — this is a **required, deterministic** field that lets SyberMem mechanically detect when a digest has gone stale because its source records later changed. Compute it with the CLI so the value always matches what the freshness check recomputes:
   - Resolve the `source_records` project-relative paths for the phase: run `sybermem project coverage-hash --phase-id phase-NNN --format json`, which resolves the phase's covered record ids to real file paths (via frontmatter `record_id:`, never filename) and returns `{"source_records": [...], "coverage_hash": "..."}`. Use the returned `coverage_hash`.
   - If your `source_records` differ from the phase's covered set (e.g. explicit sources), pass them directly: `sybermem project coverage-hash --source-records "changes/x.md,bugs/y.md" --format json`.
   - If the CLI is unavailable, fall back to core semantics: for each project-relative path in `source_records`, sorted ascending, take the file's current bytes' SHA-256 hex (literal `<missing>` if absent), build `"{rel_path}:{sha256}"` lines, join with `\n`, and SHA-256 the UTF-8 bytes — but **prefer the CLI** so the value always matches `sybermem_core.digest_coverage.compute_coverage_hash`.
8. **Write the digest file** — path: `.sybermem/digests/{YYYY-MM-DD}-{NNN}-{title}.md`. Use `.sybermem/templates/digest-template.md`. Fill `coverage_hash` with the value from Step 7a (never leave the `{{coverage_hash}}` placeholder). Write `## Core Conclusions` as concise, standalone, source-aware durable facts. They are the compressed hot-path signal and may be injected into model-visible startup or compaction context, so each conclusion should still make sense when read alone.
9. **Update INDEX.md** — insert row above `<!-- add new digest records here -->` in `## Phase Digests` table: `| NNN | YYYY-MM-DD | Title | <status> | X records | [link](digests/file.md) |`
10. **Preserve Key Conclusions signal quality** — do not add to `## Key Conclusions` by default. Only add if the digest introduces a truly global project conclusion.
11. **Archive source record conclusions** — after writing the digest, move the Key Conclusions of the source records to `## Archived Conclusions` in INDEX.md. Append `[compressed in digest-NNN]` to each archived line. This keeps Key Conclusions focused on current undigested work. Only move conclusions whose record ID is in the `source_records` list; leave other conclusions untouched.

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
- Writing `## Core Conclusions` as vague notes, open questions, or claims not grounded in the listed `source_records`
- Leaving the `{{coverage_hash}}` placeholder unfilled, inventing a hash, or computing it over anything other than the exact `source_records` set (this silently defeats stale-digest detection)

**All of these mean: go back to Step 2 and re-verify source coverage and phase status.**

## Optional closing step: surface a fixable norm

A digest is a natural moment to notice conventions worth fixing down. After the
digest is written, check for **recurring binding constraints** that should be
crystallized into project norms.

First, ask the CLI for emergent nominations (deterministic recurrence detection over
decision/requirement records): `sybermem norms nominate --format json`. Each nomination
carries `occurrences`, `evidence` (source record ids), and a representative `sample`.
Also do your own semantic look-back for constraints the token detector may have missed.

If a recurring binding rule stands out, offer (once, batched) to capture it — never auto-write:

- Personal / cross-project preference → offer a **user habit** (`/sybermem-habit`).
- Recurring binding project rule → offer to **crystallize a `norm`** via `/sybermem-record`
  (see that skill's "Crystallizing a project norm"), citing the nomination `evidence`.
- Ordinary non-binding convention → an ordinary `decision`/`requirement` record is enough.

Rules: only when it recurs and you are confident; one batched offer, one-step to accept;
decline or silence → drop it. Confirmation-first (L1). Skip entirely when nothing recurs.

## Terminal State

This skill is complete when:
- the digest file is written to `.sybermem/digests/`
- the `INDEX.md` Phase Digests table has a new row
- the source records are explicitly listed in the digest
- the user has been shown the digest path and coverage

## When NOT to Create a Digest

- The work is still in progress and not phase-bounded
- The source material is too small to be worth compressing
- The proposed digest would only repeat an existing digest with the same source records

## Integration

**Required sub-skills:**
- **sybermem-phase-analyze** — Required when phase index is missing or stale; digest triggers it to produce agent semantic grouping

**Related skills:**
- **sybermem-update** — Run first if project is missing digest capability
