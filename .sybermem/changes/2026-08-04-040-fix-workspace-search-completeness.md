---
type: change
date: 2026-08-04
number: 040
title: Fix workspace search completeness
status: implemented
author: SyberMem
related_files:
  - packages/core/sybermem_core/search.py
  - packages/core/sybermem_core/workspace_search.py
  - packages/core/sybermem_core/workspace_query.py
  - packages/cli/sybermem_cli/main.py
  - packages/core/tests/test_workspace_index.py
  - packages/core/tests/test_workspace_index_consistency.py
  - packages/core/tests/test_search_review_findings.py
  - packages/cli/tests/test_cli_search.py
---

## Change Content

Fixed workspace and project search review findings:

- Added a typed workspace index incompatibility error that tells users to run `sybermem index build` instead of leaking SQLite tracebacks.
- Extracted workspace SQLite execution into `workspace_search.py` while keeping `sybermem_core.search.search_workspace` stable.
- Reused continuity metadata and successor guidance for workspace search rows so superseded workspace hits point at current records like project search.
- Limited digest stale/conflict marking to related authoritative records through digest coverage or explicit digest relations.
- Suppressed low-signal manual substring searches such as `hi` without changing meaningful explicit search, compact recall, CJK/natural multi-term matching, FTS fallback, or workspace filters.

## Reason for Change

Workspace search needed to match the source-aware recall and correction/supersession trust model introduced for project search. The fix keeps SQLite as a rebuildable derived cache, preserves Markdown as the canonical store, and avoids adding a second ranking path or retrieval backend.

## Impact Scope

- Workspace search CLI and JSON/text rendering for stale indexes, filters, FTS fallback, and successor guidance.
- Project search conflict freshness for digests and low-signal manual queries.
- Regression coverage for stale schemas, workspace supersession, unrelated digest matches, and short substring noise.

## Implementation

The implementation added schema preflight before workspace SELECTs, routed incompatible schemas through a structured `WorkspaceIndexIncompatibleError`, queried filtered workspace guidance rows for successor resolution, and changed digest conflict annotation to require related digest evidence. Review-specific regressions live in a small focused test file to avoid growing the existing oversized recall contract module.

## Test Verification

- Focused regression suite: `30 passed`.
- Full suite: `86 passed`.
- Bytecode compile for changed Python files: passed with no output/errors.
- Real workspace CLI smoke in isolated HOME: `index build` indexed 1 project and 2 records; text and JSON workspace search both showed successor/current guidance.
- `basedpyright` and `ruff` could not run because neither executable is installed in the local `uv` environment.

## Notes

During CLI smoke setup, an initial PowerShell `$HOME` variable collision overwrote the user registry file. It was restored immediately from the existing SQLite index evidence (`sybermem` and `teamspark` projects), and subsequent smoke used process-scoped `HOME`/`USERPROFILE` overrides plus disposable temp directories.
