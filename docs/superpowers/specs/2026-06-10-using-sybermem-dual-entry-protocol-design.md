# Using-SyberMem Dual-Entry Protocol Design

Date: 2026-06-10
Status: Proposed

## Overview

SyberMem now has a growing collection of skills and layers:
- raw records
- summary
- digest
- phase analysis
- phase confirmation
- root resolution
- stop-hook nudges
- launcher migration
- managed-file upgrade rules

Earlier work introduced a marker-bounded `using-sybermem` protocol block at the top of `CLAUDE.md` / `AGENTS.md`. That solved one half of the problem:

- the project now has a session-entry contract written into instruction files

But recent feedback exposed the remaining gap:

> **The protocol block alone still behaves more like static text than like a first-class entrypoint.**

Users do not experience it the same way they experience `using-superpowers`, because there is still no visible `using-sybermem` skill that they can invoke directly and that the protocol can conceptually point to.

This spec upgrades `using-sybermem` into a **dual-entry system**:

1. a **top-of-file session protocol block** for automatic session-entry guidance
2. a **visible `/using-sybermem` skill** for manual diagnostic entry and routing guidance

## Goals

- Preserve the top-of-file `using-sybermem` protocol block
- Add a visible `using-sybermem` skill
- Make both forms share the same conceptual contract
- Keep the first version advisory / diagnostic rather than heavy-handed
- Improve the user’s sense that SyberMem has a real entry layer, not just scattered rules
- Preserve non-destructive rollout for existing projects

## Non-Goals

- Do not replace the concrete SyberMem business skills (`record`, `summary`, `digest`, etc.)
- Do not make `using-sybermem` auto-run long command chains in v1.1
- Do not make the visible skill a hard blocker for all workflows
- Do not remove the protocol block from instruction files
- Do not make `using-sybermem` a second implementation of all other skills

## Core Product Problem

Without a visible entrypoint, `using-sybermem` can still feel like:
- a hidden instruction fragment
- a passive reminder
- a block that exists in files but is not strongly felt in use

That weakens compliance. The user may still experience:
- forgetting the correct route between summary / digest / phase analyze
- uncertainty about whether the current project is fully upgraded
- ambiguity about whether a phase-aware path is available
- reduced trust that the entry protocol is actually governing the session

The protocol needs to be both:
- automatically present at session start
- manually visible and callable when the user wants to inspect or re-establish the current SyberMem context

## Dual-Entry Model

### Entry 1: Session protocol block

The existing marker-bounded block in `CLAUDE.md` / `AGENTS.md` remains.

Its role is:
- automatic session-entry guidance
- high-priority routing hints
- non-destructive upgrade target via `/sybermem-update`

### Entry 2: Visible `/using-sybermem` skill

A new explicit skill is added.

Its role is:
- manual entrypoint
- current-session diagnostic summary
- routing recommendation layer
- visible embodiment of the protocol

It does not replace the protocol block. It gives users a concrete handle on that same logic.

## Relationship Between the Two Entries

The protocol block and the visible skill should not diverge.

### The block should establish
- root resolution first
- context loading first
- analysis/digest/summary prerequisite awareness
- no candidate treated as canonical
- prefer `/sybermem-record` when lightweight trail is insufficient

### The visible skill should report
- what project root was resolved
- what core SyberMem artifacts were found
- what capability layers are available
- what summary/digest behavior would currently happen
- what the recommended next command is for the current situation

The block is automatic and brief.
The skill is explicit and diagnostic.

## First-Version Behavior of the Visible Skill

The first version should be **advisory**, not heavy-handed.

### Manual invocation contract

When the user runs `/using-sybermem`, the skill should:

1. resolve the project root
2. report the resolved root
3. check for the presence of:
   - `.sybermem/INDEX.md`
   - `.sybermem/digests/`
   - `.sybermem/analysis/phase-index.md`
   - `CLAUDE.md` / `AGENTS.md` managed protocol block presence
   - stop-hook launcher state if relevant
4. summarize which SyberMem layers are currently available
5. explain what will happen if the user runs:
   - `/sybermem-summary`
   - `/sybermem-digest`
   - `/sybermem-phase-analyze`
   - `/sybermem-record`
6. recommend the most relevant next command

### Example output shape

Conceptually, the output should look like:

```md
## SyberMem Status

- Project root: ...
- Index: present / missing
- Phase index: present / missing
- Digests: present / missing
- Managed session protocol block: present / missing

## Current routing

- `/sybermem-summary`: phase-aware / weekly fallback
- `/sybermem-digest`: phase-backed / source-set mode / needs analyze first
- `/sybermem-record`: recommended / optional

## Recommended next step

- ...
```

This is illustrative, not a locked markdown schema.

## Advisory Strength

The first visible `using-sybermem` skill should be **advisory**.

### It should do
- diagnosis
- capability reporting
- prerequisite explanation
- recommended next-step guidance

### It should not do by default
- forcibly block other commands
- auto-run phase analysis
- auto-run digest
- auto-run record creation
- rewrite files on its own

This makes it safer and more acceptable as a first version.

## Why Advisory First

A hard-blocking version would be much stronger, but it risks making the system feel too rigid before the protocol itself has been fully proven in real usage.

The first version should earn trust by being:
- visible
- useful
- accurate
- lightweight

Later versions can become stricter if needed.

## What the Visible Skill Makes Better

### 1. User understanding
The user can explicitly ask:
- is this project fully upgraded?
- do I have a phase index?
- what would summary do right now?
- should I record, analyze, summarize, or digest next?

### 2. Session recovery
If work has drifted and the user wants to re-anchor the session, `/using-sybermem` gives a stable re-entry point.

### 3. Psychological weight
The protocol becomes tangible. It is no longer just a hidden top-of-file rule block.

## Integration with Existing Skills

### `/sybermem-summary`
The visible skill should explain whether summary is currently:
- phase-aware (confirmed phase exists)
- or still in fallback mode (needs analyze or no confirmed phase)

### `/sybermem-digest`
The visible skill should explain whether digest is currently:
- ready to use a confirmed phase
- likely to need phase analysis first
- or likely to need explicit source records / confirmation

### `/sybermem-record`
The visible skill should remind users when the current task pattern looks like a high-value record candidate.

### `/sybermem-update`
If a project is partially upgraded or missing the protocol block or phase index, `/using-sybermem` should say so and point to `/sybermem-update`.

## Managed Instruction File Rollout

The existing protocol-block rollout remains valid.

### Managed files
If `CLAUDE.md` / `AGENTS.md` are still SyberMem-managed:
- ensure the protocol block exists
- refresh only the bounded block on upgrade
- do not rewrite the rest of the file unnecessarily

### Custom files
If the file is custom:
- do not overwrite it wholesale
- if the block already exists, allow block-only refresh
- if the block does not exist, treat insertion as an explicit upgrade choice rather than a silent rewrite

### Additional rollout requirement

Since `using-sybermem` now also becomes a visible skill, install/update distribution must ensure that:
- the skill is globally installed
- the instruction-block rollout remains in place
- old projects can receive both parts through the existing update path

## Existing-User Upgrade Requirement

This spec inherits the same non-destructive existing-user contract:

> **The `using-sybermem` upgrade is incomplete unless existing managed projects can receive both the bounded protocol block and the visible skill through the normal SyberMem upgrade path.**

That means:
- global install/update must ship the visible skill
- `/sybermem-update` must ensure instruction files receive or refresh the block
- custom local files must still be treated conservatively

## Risks

### Risk: duplicated logic between the block and the skill

Mitigation:
- keep the block short and high-level
- keep the visible skill diagnostic and explanatory
- derive both from the same conceptual contract

### Risk: users assume the visible skill auto-fixes everything

Mitigation:
- make the first version advisory
- clearly say which command should be run next
- do not silently mutate project files from the visible skill

### Risk: drift between the protocol block and the visible skill

Mitigation:
- define the same routing principles in one canonical source of truth during implementation
- add smoke tests that verify both the block and the visible skill mention the same prerequisite rules

## Acceptance Criteria

1. A visible `using-sybermem` skill exists and is globally installable.
2. The existing top-of-file protocol block remains in place.
3. The visible skill reports the resolved project root and the availability of key SyberMem layers.
4. The visible skill explains current routing for summary/digest/analyze/record rather than directly executing them.
5. The visible skill remains advisory in the first version.
6. Existing managed projects can receive the protocol block via `/sybermem-update`.
7. Custom instruction files are not overwritten wholesale.
8. The visible skill and the protocol block remain conceptually aligned.

## Recommendation

The existing marker-bounded protocol block is necessary but not sufficient.

To get closer to the usability and felt consistency of `using-superpowers`, SyberMem should pair that automatic block with a visible diagnostic entry skill.

In one sentence:

**SyberMem should evolve `using-sybermem` into a dual-entry protocol: an automatically injected top-of-file session-entry block plus a visible advisory skill that reports current SyberMem state and routes users toward the right next command.**
