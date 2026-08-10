---
type: change
record_id: change-895dad61b374427586a8b14df4c7281e
date: 2026-08-07
title: Lock archived-lifecycle declaration as canonical truth
key_conclusion: Confirmed and tested that a record's declared lifecycle:archived frontmatter is authoritative without any INDEX-derived flag, so archival truth lives in the canonical record rather than in a derived index section
topics: [governance, retrieval]
status: implemented
related: [change-619fadbe5ba0498f9c25a51f83f9c78c]
---

## Change Content

G5 builds directly on the E4 declaration-first trust mechanism (change-619fadbe). `classify_lifecycle` already returns a recognized declared `lifecycle` before consulting inferred signals, so a record carrying `lifecycle: archived` is classified archived without needing an entry in the INDEX `## Archived Conclusions` section. This change adds a regression test locking that behavior: a record declaring `lifecycle: archived`, with `archived=False` passed and no `[archived]` body marker, still classifies as archived/historical.

The record skill already documents the optional `lifecycle` field (added in E4).

## Reason for Change

G5: archival status was derived from a derived artifact (the INDEX archived-conclusions section) plus a `[archived]` string in content — a fragile source that can drift from canonical records. Declaration-first means the canonical record, not the index, is the source of archival truth. INDEX-derived detection remains a fallback for legacy records.

## Impact Scope

- `packages/core/sybermem_core/retrieval.py`: mechanism already in place (E4); no code change this round.
- `packages/core/tests/test_retrieval.py`: new test locking declared-archived precedence.
- Verified: core suite 133 passed.
