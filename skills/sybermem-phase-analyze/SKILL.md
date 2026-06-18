---
name: sybermem-phase-analyze
description: Use when building or incrementally refreshing the project phase index from full SyberMem records and related git context.
---

# sybermem-phase-analyze Skill

**Announce at start:** "I'm using the sybermem-phase-analyze skill to build or refresh the project phase index."

Analyze the project's full `.sybermem/` record history, update `.sybermem/analysis/phase-index.md`, and propose candidate phases without auto-confirming them.

## Core Invariants

- **Phase analysis proposes and auto-confirms structure. The user can later adjust via `/sybermem-phase-confirm`.**
- **No re-analysis may append contradictory duplicate candidates blindly.**

<HARD-GATE>
Do NOT declare analysis complete unless ALL of the following are true:
1. `.sybermem/analysis/phase-index.md` has been read and its current state extracted
2. All `.sybermem/` records have been scanned and grouped into candidate phases
3. All candidates have been auto-confirmed into confirmed phases with canonical block shapes
4. The coverage map has been updated to reflect all record-to-phase mappings
5. Analysis progress metadata has been written back (last_analysis_at, boundaries, pending status)

If any of these is false, the analysis is incomplete. Go back and finish it.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Preconditions

Before analysis, verify all of the following:
- `.sybermem/INDEX.md` exists
- at least one raw record exists in `changes/`, `decisions/`, `requirements/`, or `bugs/`

If `.sybermem/analysis/phase-index.md` does not exist, create it from the starter template (create the `analysis/` directory first if needed). The starter template should contain empty `## Analysis Progress`, `## Phase Candidates`, `## Confirmed Phases`, and `## Coverage Map` sections with `status: not_yet_analyzed`. This is the normal first-run path — do not ask the user to run `/sybermem-update` just because the phase index has never been created.

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply Step 0 directory resolution rules above
2. **Verify preconditions** — `.sybermem/INDEX.md` exists, at least one raw record exists. If `.sybermem/analysis/phase-index.md` does not exist, create it from the starter template with `status: not_yet_analyzed`.
3. **Read current phase index** — extract analysis progress, existing phase candidates, existing confirmed phases, current coverage map
4. **Determine analysis scope** — default to full `.sybermem/` record set plus relevant git history context. If phase index has a usable boundary, determine which records were added since the last analyzed record boundary.
5. **Build or refresh candidate groups** — use lightweight heuristics: time proximity, file/path proximity, title/topic similarity, sequential implementation relationship.

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

After proposing candidates, automatically confirm all of them as phases. The user can later adjust, rename, or reject phases via `/sybermem-phase-confirm` if needed. Manual confirmation is no longer required before downstream skills like `/sybermem-digest` can proceed.

6. **Update confirmed phases and coverage map conservatively** — use this canonical Markdown block shape for every confirmed phase entry:

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

7. **Update analysis progress** — write back: last analysis time, last analyzed record boundary, optional git boundary, whether unprocessed new records remain, enough current-state metadata for future summary to identify the most recently active confirmed phase

## Output Rules

- The phase index must remain human-readable Markdown.
- Candidate phases must be lightweight grouping proposals, not final digests.
- If the system is uncertain, prefer narrower candidate proposals over broad confident ones.
- The phase index should make it possible for `/sybermem-summary` to distinguish confirmed phases from candidates and identify the most recently active confirmed phase.

## Verification

After updating phase-index.md, verify:
1. **No orphaned records:** Every record in `.sybermem/` appears in at least one phase's `covered_records` or in the unassigned section of the coverage map.
2. **No duplicate coverage:** No single record appears in two different confirmed phases.
3. **Block shape compliance:** Every confirmed phase uses the canonical `### Phase:` block shape with all required fields.
4. **Stale candidate cleanup:** No candidate blocks remain that describe the same cluster as a confirmed phase.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Appending new candidate blocks without checking if they duplicate existing ones
- Leaving stale candidates that overlap with confirmed phases
- Silently removing existing confirmed phases or coverage mappings
- Declaring analysis complete without writing back analysis progress metadata
- Confirming phases with empty `covered_records` lists when records actually exist

**All of these mean: go back to the relevant step and re-verify.**

## Terminal State

This skill is complete when:
- `.sybermem/analysis/phase-index.md` has been updated with refreshed and auto-confirmed phases
- the user has been told what phases were proposed and confirmed

## Integration

**Related skills:**
- **sybermem-phase-confirm** — Downstream: confirm or adjust candidate phases after analysis
- **sybermem-digest** — Downstream: create durable phase digests from confirmed phases
