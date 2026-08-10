---
type: change
record_id: change-087966eda55f40a0aada0f86dd290e29
date: 2026-08-07
title: Resume leads with a human-readable brief
key_conclusion: Added a deterministic 3-4 line resume brief (phase/confidence, latest work, open items, suggested next) so fast resume reads like a briefing instead of a field dump, without changing the authoritative structured fields
topics: [usability, quality]
status: implemented
related: [decision-002]
---

## Change Content

`build_resume_checkpoint` now includes a `brief` field composed by `_brief()` from existing checkpoint data: active phase + confidence/freshness, most recent authoritative record, up to three open bugs/requirements to watch, and the suggested next action. The CLI prints the brief first in text mode, above the structured lines.

## Reason for Change

A4: the resume output was a field dump; a plain-language lead lowers the reading cost of "where am I / what next" while the structured fields remain the source of truth. Composition is deterministic and read-only.

## Impact Scope

- `packages/core/sybermem_core/resume.py`: `_brief` + `brief` key in checkpoint.
- `packages/cli/sybermem_cli/main.py`: `cmd_resume` prints the brief.
- Building the brief surfaced bug-2c0914a0 (fixed-status bugs miscounted as open), fixed in the same batch.
- Verified: `sybermem resume` prints a 4-line brief for this project.
