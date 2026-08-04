---
type: change
date: 2026-08-04
number: 037
title: Add Team publish preview trust envelope
status: implemented
---

## Change Content

Implemented Task 6 from the continuity/trust plan for Team publish and status flows:

- Added deterministic Project source snapshots derived from project identity plus canonical records and digests.
- Added a read-only Team publish preview payload with source revision/hash, selected records/digests, freshness, conflicts, review requirement, Team id, project id, slug, and Team path.
- Added publish-time `preview_source_hash` validation that returns `stale_preview` before Team writes, Project association writes, git staging, commit, push, or Project canonical record mutation when the source changed after preview.
- Added Team trust metadata fields for `local_changes_after_publish`, `published_at`, `source_scope`, `stale`, `conflict`, and `review_required` in status/meta/overview-compatible additive outputs.
- Added CLI publish preview flags while preserving the existing ordinary publish path.
- Split publish rendering/source helpers out of oversized modules so the touched files stay below the 250 pure-LOC ceiling.

## Reason

High-impact Team publication needs a reviewable, revision-aware preflight so agents can inspect exactly which Project truth will be published and reject stale reviewed state without introducing a second canonical store or complicating ordinary record writes.

## Impact Scope

- Team publish callers can request a read-only preview and optionally enforce the reviewed source hash during publish.
- Team `meta.json`, Team overview parsing, and project status expose additive trust envelope fields without changing Markdown record schemas.
- Stale preview rejection preserves Project canonical records, Project Team association, Team files, Team git index, commits, pushes, and remote state.
- Existing `latest_phase_digest` / `latest_theme_digest` imports remain available through `publish.py` while helper logic lives in smaller modules.

## Verification

- Red phase: `python -m pytest packages/core/tests/test_publish.py packages/core/tests/test_status.py -q` failed on missing `publish_status_preview` before implementation.
- Focused publish/status tests: `python -m pytest packages/core/tests/test_publish.py packages/core/tests/test_status.py -q` passed (`8 passed`).
- CLI tests: `python -m pytest packages/cli/tests -q` passed (`2 passed`).
- Full core tests: `python -m pytest packages/core/tests -q` passed (`73 passed`).
- Compile check: `python -m py_compile packages/core/sybermem_core/project.py packages/core/sybermem_core/status.py packages/core/sybermem_core/publish.py packages/core/sybermem_core/publish_bootstrap.py packages/core/sybermem_core/publish_render.py packages/core/sybermem_core/publish_sources.py packages/cli/sybermem_cli/main.py packages/cli/sybermem_cli/publish_render.py packages/core/tests/test_publish.py packages/core/tests/test_status.py` passed.
- LOC audit: all touched files are at or below 230 pure LOC after the refactor split.
- Isolated Team Git smoke: temp fixture `C:\Users\69046\AppData\Local\Temp\opencode\sybermem-task6-smoke-8mowj6u4` proved preview has no side effects and stale publish returns `stale_preview` with Team and Project unchanged except for the deliberately added local record.

## Related Changes

- Implements the Team publish preview portion of decision-002's lightweight continuity and trust experience direction.
- Builds on requirement-003 and change-023 Team memory publication architecture without adding a second canonical memory store.
