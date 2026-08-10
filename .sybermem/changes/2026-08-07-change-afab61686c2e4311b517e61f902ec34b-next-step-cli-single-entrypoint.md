---
type: change
record_id: change-afab61686c2e4311b517e61f902ec34b
date: 2026-08-07
title: Expose deterministic next-step router as a CLI and route using-sybermem through it
key_conclusion: Added `sybermem next-step` wrapping the core router and made using-sybermem present its output as the authoritative recommendation, so the single advisory entrypoint stops re-deriving routing by AI and can no longer drift from resume
topics: [usability, cli, quality]
status: implemented
related: [decision-002]
---

## Change Content

The `recommend_next_step` router in `next_step_router.py` was only reachable internally through `/sybermem-resume`. `using-sybermem` re-derived the recommendation from an AI-interpreted DOT decision graph, a second source that could disagree with resume.

- Added `sybermem next-step [--format text|json]` (`cmd_next_step`) as a thin wrapper over `recommend_next_step`, with a graceful no-project fallback to `/sybermem-init-project`.
- Rewrote `using-sybermem` Step 3 to run `sybermem next-step --format json` and treat its `action`+`reason` as canonical; the DOT graph is now explicitly a CLI-unavailable manual fallback, not a competing source.
- Synced the skill to its mirror copy.

## Reason for Change

A1 in the improvement plan: collapse "which of 6 commands do I run?" to one advisory entrypoint, and make that entrypoint deterministic. Reusing the existing core router (instead of AI re-derivation) removes drift between using-sybermem and resume and matches the product principle that determinism belongs in core.

## Impact Scope

- `packages/cli/sybermem_cli/main.py`: `cmd_next_step` + `next-step` subparser + import.
- `packages/claude-skills/using-sybermem/SKILL.md` + mirror: Step 3 routes through the CLI.
- Verified: `sybermem next-step` returns deterministic text+json for this project.
