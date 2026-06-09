---
name: sybermem-phase-analyze
description: Use when building or incrementally refreshing the project phase index from full SyberMem records and related git context.
---

# sybermem-phase-analyze Skill

Analyze the project's full `.sybermem/` record history, update `.sybermem/analysis/phase-index.md`, and propose candidate phases without auto-confirming them.

## Core Invariants

- **Phase analysis proposes structure; it does not canonize it.**
- **No re-analysis may append contradictory duplicate candidates blindly.**

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

Before analysis, verify all of the following:
- `.sybermem/analysis/phase-index.md` exists
- `.sybermem/INDEX.md` exists
- at least one raw record exists in `changes/`, `decisions/`, `requirements/`, or `bugs/`

If the phase index is missing, ask the user to run `/sybermem-update`.

## Flow

### Step 1: Read current phase index

Read `.sybermem/analysis/phase-index.md` and extract:
- current analysis progress
- existing phase candidates
- existing confirmed phases
- current coverage map

### Step 2: Determine analysis scope

Default to the full `.sybermem/` record set plus relevant git history context.

If the phase index already has a usable boundary, determine which records were added since the last analyzed record boundary.

### Step 3: Build or refresh candidate groups

Use lightweight heuristics across the relevant record set:
- time proximity
- file/path proximity
- title/topic similarity
- sequential implementation relationship

Use this canonical Markdown block shape for every candidate entry:

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

Candidate IDs are stable, sequential identifiers in the `candidate-phase-<NNN>` format. Reuse an existing candidate ID when refreshing the same underlying grouping.

On re-analysis, refresh the `## Phase Candidates` section instead of appending blindly:
- update or replace older candidate blocks when they describe the same record cluster
- remove stale superseded candidate proposals that no longer match the latest analysis
- keep materially distinct candidate proposals only when they represent separate plausible groupings

Do not auto-confirm candidates.

### Step 4: Update confirmed phases and coverage map conservatively

Use this canonical Markdown block shape for every confirmed phase entry:

```md
### Phase: <phase_title>
- phase_id: phase-<NNN>
- source_candidate_id: candidate-phase-<NNN>
- status: confirmed
- covered_records:
  - <category>-NNN
  - <category>-NNN
- confirmed_at: <YYYY-MM-DD>
- notes: <optional short note>
```

Confirmed phase IDs use the stable `phase-<NNN>` format. `source_candidate_id` should point back to the candidate that was confirmed when that lineage is known.

- keep existing confirmed phases unchanged unless the user explicitly revisits them
- avoid silently removing coverage mappings
- add new unassigned records to the coverage map when no phase match is clear

### Step 5: Update analysis progress

Write back:
- last analysis time
- last analyzed record boundary
- optional git boundary
- whether unprocessed new records remain
- enough current-state metadata for future summary to identify the most recently active confirmed phase

## Output Rules

- The phase index must remain human-readable Markdown.
- Candidate phases must be lightweight grouping proposals, not final digests.
- If the system is uncertain, prefer narrower candidate proposals over broad confident ones.
- The phase index should make it possible for `/sybermem-summary` to distinguish confirmed phases from candidates and identify the most recently active confirmed phase.
