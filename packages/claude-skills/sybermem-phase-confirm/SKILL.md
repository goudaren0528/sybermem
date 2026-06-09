---
name: sybermem-phase-confirm
description: Use when explicitly confirming, renaming, adjusting, or rejecting candidate phases in the project phase index.
---

# sybermem-phase-confirm Skill

Promote a candidate phase into a confirmed phase, or explicitly adjust/reject candidate phases in `.sybermem/analysis/phase-index.md`.

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

Do not auto-create digests.
