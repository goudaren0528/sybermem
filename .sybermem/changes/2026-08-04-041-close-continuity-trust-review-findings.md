---
type: change
date: 2026-08-04
number: 041
title: Close continuity and trust review findings
status: implemented
author: Sisyphus
related_files: [packages/core/sybermem_core/team_summary.py, packages/core/sybermem_core/publish_bootstrap.py, packages/core/sybermem_core/search.py, packages/core/sybermem_core/workspace_search.py, packages/core/sybermem_core/workspace_query.py, .sybermem/hooks/detect_record_intent.py]
---

## Change Content
Closed the completeness and usability findings from the continuity/trust implementation review. Team publish now exposes the complete trust envelope and requires preview/hash review flow; workspace search handles stale indexes, successor guidance, relation-scoped digest freshness, and low-signal queries; record-intent has a bounded explicit diagnostic path for Core-unavailable environments.

## Reason for Change
The independent review found gaps that could make high-impact publication hard to audit, workspace recall unstable or misleading, and Core-unavailable behavior confusing while preserving fail-open safety.

## Impact Scope
- Team publish preview, management summaries, and distributed Team publish/record-intent skills.
- Project and workspace search, index compatibility errors, successor guidance, and digest freshness annotations.
- Automated record-intent hooks remain quiet and fail-open; only explicit diagnosis emits bounded feedback.

## Implementation
- Added the missing trust envelope fields to Team management Markdown and JSON output.
- Made the Team publish skill flow preview -> review -> publish with `--preview-source-hash`.
- Unified publish preview freshness/path diagnostics with project trust state.
- Added actionable stale-index errors and workspace metadata parity with project search.
- Scoped digest staleness to related authoritative records and suppressed manual low-signal substring noise.
- Added explicit `--diagnose` feedback without persisting or echoing prompt content.

## Test Verification
- Full test suite: `86 passed`.
- Focused Team publish/summary tests and CLI tests passed.
- Workspace stale-schema, successor, digest-scope, low-signal, FTS/LIKE fallback, and CLI smoke tests passed.
- Core-unavailable default and `--diagnose` smoke tests passed without persistence or secret/path leakage.
- Independent final review confirmed the Team, workspace, and record-intent fixes.

## Notes
No commit or remote push was performed. Existing unrelated worktree changes were preserved.
