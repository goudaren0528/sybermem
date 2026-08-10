---
type: change
record_id: change-619fadbe5ba0498f9c25a51f83f9c78c
date: 2026-08-07
title: Trust metadata can be declared in frontmatter, with inference as fallback
key_conclusion: Let records optionally declare source_kind/authority/lifecycle in frontmatter (recognized values only) so trust classification no longer depends solely on fragile path/marker/status inference, while keeping inference as the zero-change default for legacy records
topics: [governance, retrieval, quality]
status: implemented
related: [decision-002]
---

## Change Content

Trust metadata was derived entirely from fragile signals: `source_kind` from path substrings, `authority` from marker text, `lifecycle` from status/relations/INDEX archived lines. E4 adds an explicit-declaration path:

- `classify_source_kind` / `classify_authority` / `classify_lifecycle` gained a `declared` parameter. A declaration wins over inference, but only when it is a recognized value (`VALID_SOURCE_KINDS` / `VALID_AUTHORITIES` / `VALID_LIFECYCLES`); unknown/typo values are ignored so a malformed record cannot corrupt classification.
- `records.parse_record_file` now parses optional `authority:` and `lifecycle:` frontmatter.
- `derive_continuity_metadata` (search path) and both authoritative-filter sites in `resume.py` pass the declared values; removed the now-orphaned `_source_kind` helper in resume.
- `sybermem-record` SKILL documents the optional override fields and that inference remains the default.

## Reason for Change

E4 in the improvement plan: reduce reliance on string-derived trust that can drift from canonical truth, without introducing a second store or forcing changes on existing records. Declaration-first-with-safe-fallback keeps Markdown authoritative and back-compatible.

## Impact Scope

- `packages/core/sybermem_core/retrieval.py`: declared params + valid-value guards.
- `packages/core/sybermem_core/records.py`: parse optional authority/lifecycle.
- `packages/core/sybermem_core/resume.py`: declaration-aware authority filtering; dead helper removed.
- `sybermem-record/SKILL.md` + mirror: documents optional fields.
- Verified: 3 new tests (override, invalid-fallback, evidence demotion); core suite 129 passed.
