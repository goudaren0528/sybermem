---
type: change
date: 2026-08-04
number: 039
title: Implement continuity and trust experience
status: implemented
author: SyberMem
related_files:
  - packages/core/sybermem_core/retrieval.py
  - packages/core/sybermem_core/search.py
  - packages/core/sybermem_core/resume.py
  - packages/core/sybermem_core/next_step_router.py
  - packages/core/sybermem_core/publish.py
  - packages/core/sybermem_core/status.py
  - packages/core/sybermem_core/project.py
  - packages/cli/sybermem_cli/main.py
  - .sybermem/hooks/task_recall.py
  - .sybermem/hooks/detect_record_intent.py
  - .sybermem/hooks/record_change_on_stop.py
  - docs/superpowers/specs/2026-08-04-sybermem-continuity-trust-experience-design.md
  - docs/superpowers/plans/2026-08-04-sybermem-continuity-trust-experience.md
---

## Change Content

Implemented the Project/Hub/Team continuity and trust experience layer:

- Added derived authority, lifecycle, freshness, conflict, source, and successor metadata.
- Added read-only fast/standard/deep resume checkpoints.
- Upgraded automatic recall packets to bounded, source-aware retrieval hints.
- Added abstention for weak, stale, superseded, archived, and evidence-only automatic recall.
- Added correction/supersession guidance without rewriting historical truth.
- Added suggest/plan/confirm/write record routing with safe no-write, defer, blocked, and duplicate paths.
- Added read-only Team publish preview, source revision/hash checks, stale-preview rejection, and trust envelope metadata.
- Added user-facing resume skill, documentation, package mirrors, and OpenCode manual fallback guidance.

## Reason for Change

Reduce cross-session restart friction and make recalled or published memory easier to trust without introducing a second canonical memory system. The implementation preserves Markdown/Git as the source of truth, keeps derived indexes rebuildable, and limits high-impact review checks to promotion and publication workflows.

## Impact Scope

- Project task recall, search ranking, resume, record-intent routing, correction guidance, and lifecycle display.
- Hub/Team status and publish preview metadata.
- Claude skill distribution, documentation, and supported OpenCode manual workflows.
- No new vector database, resident worker, silent full-capture pipeline, or ordinary-write receipt/lease state machine.

## Implementation

The implementation was delivered in eight staged tasks: shared retrieval metadata; read-only resume; source-aware recall packets; abstention and correction presentation; record routing; Team preview/trust envelope; user-facing skill/docs propagation; and release-gate verification. Existing Project/Hub/Team boundaries and auto/remind semantics were retained.

## Test Verification

- Core tests: `73 passed`.
- CLI tests: `4 passed`.
- Focused continuity/trust suite: `69 passed`.
- Plugin/package validation: `OK`.
- Real hook smoke covered meaningful, low-signal, malformed, unavailable-core, unsafe, duplicate, auto, and remind cases.
- Resume fast/standard/deep smoke confirmed bounded read-only behavior.
- Publish preview smoke confirmed deterministic previews, stale-source rejection before mutation, missing-identity blocking, and strict JSON output.
- SQLite/FTS delete-and-rebuild smoke confirmed Markdown hashes and search determinism.

## Notes

Design and execution plan:

- `docs/superpowers/specs/2026-08-04-sybermem-continuity-trust-experience-design.md`
- `docs/superpowers/plans/2026-08-04-sybermem-continuity-trust-experience.md`

The worktree remains intentionally uncommitted and contains prior dirty state plus generated execution artifacts; no unrelated changes were reverted.
