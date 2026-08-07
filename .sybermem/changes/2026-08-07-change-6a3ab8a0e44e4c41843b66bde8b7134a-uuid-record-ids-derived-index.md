---
type: change
record_id: change-6a3ab8a0e44e4c41843b66bde8b7134a
date: 2026-08-07
title: UUID-backed record IDs and derived project index
status: implemented
key_conclusion: Added UUID-backed canonical record IDs and derived INDEX build/check commands so parallel record creation merges safely while legacy numeric records remain readable.
topics:
  - architecture
  - collaboration
  - quality
author: Sisyphus
related_files: [packages/core/sybermem_core/records.py, packages/core/sybermem_core/project_index.py, packages/core/sybermem_core/project_index_render.py, packages/cli/sybermem_cli/main.py, packages/claude-skills/sybermem-record/SKILL.md]
---

## Change Content

Implemented Scheme A for team-safe SyberMem records. New records receive a program-generated UUID-backed `record_id`, while `.sybermem/INDEX.md` is rebuilt as a deterministic derived view from canonical record files.

## Reason for Change

Parallel branches previously allocated the same per-type numeric ID and edited the same INDEX insertion points, causing frequent PR conflicts. The new flow removes distributed number allocation and keeps record files as the canonical merge unit.

## Impact Scope

- New records no longer depend on the local maximum numeric filename.
- Existing numeric records continue to parse and participate in search, resume, status, publish, and derived index generation.
- `sybermem index build` remains the workspace SQLite index command.
- `sybermem project index build/check` now manage the derived project INDEX.

## Implementation

- Added `generate_record_id()` and explicit frontmatter parsing for `record_id`, `key_conclusion`, and `topics`.
- Added deterministic project INDEX build/write/check support with duplicate-ID detection and legacy metadata overlays.
- Added CLI commands for project INDEX maintenance without changing the existing workspace index command.
- Updated the record skill, templates, generated skill mirror, README files, and contributing workflow.

## Test Verification

- `uv run pytest packages/core packages/cli` -> 114 passed.
- `uv run pytest packages/cli -q` -> 17 passed.
- `python scripts/check-plugin-package.py` -> OK.
- `python scripts/sync-plugin-skills.py` -> source and mirror synchronized.
- `python -m py_compile` passed for all changed Python files.
- Real project: `sybermem project index build` -> unchanged; `sybermem project index check` -> current.

## Notes

The migration is backward-compatible and does not mass-rename historical records. A duplicate non-empty `record_id` is reported as an error instead of being silently renumbered.
