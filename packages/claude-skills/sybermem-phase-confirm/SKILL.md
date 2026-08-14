---
name: sybermem-phase-confirm
description: Use when explicitly confirming, renaming, adjusting, or rejecting candidate phases in the project phase index.
---

# sybermem-phase-confirm Skill

**Announce at start:** "I'm using the sybermem-phase-confirm skill to update the phase index."

Adjust, rename, reject, or re-scope phases in `.sybermem/analysis/phase-index.md`, or change a phase's lifecycle. This is an optional refinement step: `/sybermem-phase-analyze` already deterministically persists confirmed phases via `sybermem project phase analyze`, so confirmation is no longer required before downstream skills like `/sybermem-digest`.

For a bulk deterministic rewrite of the whole phase set (for example when you have a higher-quality semantic grouping), prefer the CLI: write the grouping as JSON `{ "phases": [ { "title": "...", "covered_records": ["change-001", ...] } ] }` and run `sybermem project phase confirm --from-json <file>`. Core validates every covered record exists and is covered by exactly one phase, then atomically rewrites the phase index. Use the in-place Markdown edits below for small, targeted adjustments (rename one phase, change one lifecycle, move a few records).

## Core Invariant

- **Phase edits stay within the existing `## Phase Candidates`, `## Confirmed Phases`, and `## Coverage Map` sections; never add a second `## Coverage Map` heading.**

<HARD-GATE>
Do NOT auto-create digests during confirmation. Confirmation only updates the phase index.
Do NOT add a second `## Coverage Map` heading. Edit only within existing sections.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Preconditions

Before confirmation, verify:
- `.sybermem/analysis/phase-index.md` exists
- the file contains at least one candidate phase or confirmed phase

If the phase index is missing or still `not_yet_analyzed`, run `/sybermem-phase-analyze` first (which persists a phase structure via the CLI); do not ask the user to run `/sybermem-update` just for this.

## Flow

### Step 1: Read the phase index

Read current:
- analysis progress
- candidate phases
- confirmed phases
- coverage map

### Step 2: Ask the user which candidate to act on when needed

Read and operate on candidate/phase blocks using the shared canonical shapes:

```md
### Candidate: <candidate_title>
- candidate_id: candidate-phase-<NNN>
- status: proposed
- covered_records:
  - <category>-NNN
  - <category>-NNN
- rationale: <short human-readable grouping rationale>
- proposed_at: <YYYY-MM-DD>
```

```md
### Phase: <phase_title>
- phase_id: phase-<NNN>
- source_candidate_id: candidate-phase-<NNN>
- status: confirmed
- lifecycle: active
- covered_records:
  - <category>-NNN
  - <category>-NNN
- confirmed_at: <YYYY-MM-DD>
- notes: <optional short note>
```

**Lifecycle management:** Users can also change a confirmed phase's lifecycle:
- `lifecycle: active` — current work (default for new phases)
- `lifecycle: completed` — work is done; add `completed_at: YYYY-MM-DD`
- `lifecycle: archived` — digested and no longer active

When changing lifecycle to `completed`, always add the `completed_at` date field.

Support these explicit actions:
- confirm candidate as phase
- rename candidate or phase
- adjust covered records
- reject candidate

### Step 3: Update the file conservatively

Use an in-place section-edit pattern:
- edit only the content inside the existing `## Phase Candidates`, `## Confirmed Phases`, and `## Coverage Map` sections
- never add a second `## Coverage Map` heading during confirmation
- when confirming the first phase, replace the placeholder comment under `## Confirmed Phases` with the canonical confirmed phase block instead of leaving the comment behind

Then apply the confirmation update:
- move confirmed candidates into `## Confirmed Phases` using the canonical confirmed phase block
- keep confirmation date visible
- remove or rewrite candidate entries as needed
- preserve `candidate-phase-<NNN>` and `phase-<NNN>` ID formats for stable references
- set `source_candidate_id` when a candidate is confirmed
- update coverage mappings to match the confirmed phase by replacing the placeholder comment or editing existing mapping lines in place

Confirmed phases are the canonical phase objects that future `/sybermem-summary` and `/sybermem-digest` should prefer over candidate proposals.

Do not auto-create digests.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Auto-creating a digest during the confirmation flow
- Adding a second `## Coverage Map` heading instead of editing within the existing one
- Removing an existing confirmed phase without the user explicitly requesting it
- Confirming a candidate without setting `source_candidate_id` to trace lineage

**All of these mean: go back to the relevant step and re-verify.**

## Terminal State

This skill is complete when:
- the user's requested confirmation/rename/adjustment/rejection has been applied to `phase-index.md`
- the coverage map has been updated to reflect the new phase structure
- no digest has been auto-created
- the user has been told what changed

## Integration

**Related skills:**
- **sybermem-phase-analyze** — Upstream: must run before confirming phases
- **sybermem-digest** — Downstream: create digests after confirming phases
- **sybermem-update** — Run if phase-index.md is missing
