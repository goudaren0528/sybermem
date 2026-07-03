---
type: change
date: 2026-07-03
number: 026
title: Expose Team workflows as first-class SyberMem skills
status: implemented
author: Claude
related_files:
  - packages/claude-skills/sybermem-team-publish/SKILL.md
  - skills/sybermem-team-publish/SKILL.md
  - packages/claude-skills/sybermem-team-summary/SKILL.md
  - skills/sybermem-team-summary/SKILL.md
  - packages/claude-skills/using-sybermem/SKILL.md
  - skills/using-sybermem/SKILL.md
implements: [requirement-003]
---

## Change Content
Added Team-oriented SyberMem skills so the Team workflow is exposed through the same slash-command interaction model as the rest of SyberMem. This introduced `/sybermem-team-publish` and `/sybermem-team-summary`, and extended `/using-sybermem` so it can report Team state and route users toward the right Team actions.

## Reason for Change
The Team publication and Team summary capabilities already existed in the CLI, but they were awkward to trigger compared with the rest of the SyberMem workflow. Users naturally use slash skills such as `/sybermem-record`, `/sybermem-summary`, and `/sybermem-digest`; leaving Team workflows only as CLI commands made the overall UX inconsistent and reduced discoverability.

## Impact Scope
- Affected modules/features
  - Team publication entrypoint
  - Team summary entrypoint
  - using-sybermem routing / diagnostics
  - README Team workflow guidance
- Affected user groups
  - Project owners publishing into Team memory
  - Management users consuming Team summaries
  - Users relying on slash-command workflows rather than manual CLI calls

## Implementation
- Added `/sybermem-team-publish` as a thin skill wrapper around the existing Team publish pipeline.
- Added `/sybermem-team-summary` as a thin skill wrapper around the Team management summary generation flow.
- Mirrored both skills into the plugin-facing `skills/` tree so plugin/runtime distribution stays aligned.
- Extended `/using-sybermem` instructions to surface Team state and explain the Team routing paths.
- Updated README docs so Team skills are visible as first-class workflow entrypoints.

## Test Verification
Verified the skill layer by ensuring the new Team skills exist in both source skill trees (`packages/claude-skills/` and `skills/`) and that the mirrored files match exactly. Confirmed the existing Team CLI flows they wrap are already working against the real Team repo (`D:/team-memory`) from earlier dogfood runs, so the Team skills now provide a consistent interaction layer on top of proven Team publication and summary commands.

## Notes
This change does not create new Team business logic; it makes the existing Team workflow ergonomic and discoverable. The boundary remains clear: CLI is the execution layer, Team skills are the user-facing interaction layer.