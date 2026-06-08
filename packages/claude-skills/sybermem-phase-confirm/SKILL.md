---
name: sybermem-phase-confirm
description: Use when explicitly confirming, renaming, adjusting, or rejecting candidate phases in the project phase index.
---

# sybermem-phase-confirm Skill

Promote a candidate phase into a confirmed phase, or explicitly adjust/reject candidate phases in `.sybermem/analysis/phase-index.md`.

## Directory Resolution Rules

1. If `.sybermem/` exists, use it.
2. If only `ADR/` exists, rename it to `.sybermem/` and tell the user migration was performed.
3. If both `.sybermem/` and `ADR/` exist, use `.sybermem/` and warn that `ADR/` was ignored.
4. If neither exists, prompt the user to run `/sybermem-init-project` first.

## Preconditions

Before confirmation, verify:
- `.sybermem/analysis/phase-index.md` exists
- the file contains at least one candidate phase or confirmed phase

If the phase index is missing, ask the user to run `/sybermem-update`.

## Flow

### Step 1: Read the phase index

Read current:
- analysis progress
- candidate phases
- confirmed phases
- coverage map

### Step 2: Ask the user which candidate to act on when needed

<<<<<<< HEAD
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
- covered_records:
  - <category>-NNN
  - <category>-NNN
- confirmed_at: <YYYY-MM-DD>
- notes: <optional short note>
```

=======
>>>>>>> 596a58d (feat: add phase analysis layer skills)
Support these explicit actions:
- confirm candidate as phase
- rename candidate or phase
- adjust covered records
- reject candidate

### Step 3: Update the file conservatively

<<<<<<< HEAD
- move confirmed candidates into `## Confirmed Phases` using the canonical confirmed phase block
- keep confirmation date visible
- remove or rewrite candidate entries as needed
- preserve `candidate-phase-<NNN>` and `phase-<NNN>` ID formats for stable references
- set `source_candidate_id` when a candidate is confirmed
=======
- move confirmed candidates into `## Confirmed Phases`
- keep confirmation date visible
- remove or rewrite candidate entries as needed
>>>>>>> 596a58d (feat: add phase analysis layer skills)
- update coverage mappings to match the confirmed phase

Do not auto-create digests.
