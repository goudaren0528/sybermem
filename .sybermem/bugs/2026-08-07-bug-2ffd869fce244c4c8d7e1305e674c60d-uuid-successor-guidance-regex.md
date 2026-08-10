---
type: bug
record_id: bug-2ffd869fce244c4c8d7e1305e674c60d
date: 2026-08-07
title: Successor guidance regex only matched numeric ids, breaking UUID records
key_conclusion: Fixed retrieval RECORD_ID_RE to accept UUID-backed ids via a shared RECORD_ID_SUFFIX, so superseded_by/fixes successor guidance resolves for records created after the UUID migration
topics: [quality, search, retrieval]
status: fixed
severity: high
related: [change-6a3ab8a0e44e4c41843b66bde8b7134a]
---

## Bug Description

After the UUID-backed record-id migration (change-6a3ab8a0...), any new record whose `superseded_by` or `fixes` frontmatter pointed at a UUID-backed id was classified `lifecycle=superseded` (because the string was non-empty) but never received `successor_record`, `current_record`, or `current_guidance`. The system could tell an agent a record was historical/superseded without telling it which current record to use instead — the exact moment trust guidance matters most. Both project-scope search (`search_project`) and cross-project workspace search (which reuse `apply_successor_guidance`) were affected.

## Root Cause

`retrieval.py` extracted record ids for relation/successor resolution with:

```
RECORD_ID_RE = re.compile(r"(?:change|decision|requirement|bug|digest)-\d{3}")
```

The `-\d{3}` suffix only matches legacy 3-digit numeric ids. New ids are `<type>-<uuid4-hex>` (32 hex chars). `_record_ids` / `_first_record_id` therefore returned nothing for UUID relation values, so `apply_successor_guidance` could not resolve any successor for UUID records. `project_index.py`'s own `RECORD_ID_PATTERN` already handled both formats (`\d{3}|[0-9a-f]{32}`), so the two id parsers had drifted out of sync.

## Solution

Introduced a single shared suffix constant in `records.py` (the natural home for id logic, alongside `generate_record_id` and `LEGACY_RECORD_ID_PATTERN`):

```
RECORD_ID_SUFFIX = r"(?:\d{3}|[0-9a-f]{32})"
```

- `retrieval.RECORD_ID_RE` now composes it: `(?:change|decision|requirement|bug|digest)-<suffix>` — still embedded, still includes `digest`.
- `project_index.RECORD_ID_PATTERN` now composes it too (anchored, record-type subset) so the two parsers can no longer drift.
- Added two regression tests in `test_recall_retrieval_contract.py` covering UUID-backed `superseded_by` and UUID-backed `fixes` through `search_project` -> `apply_successor_guidance`.

Verified: full `packages/core` suite green (116 passed) including the 2 new tests; runtime check confirms `RECORD_ID_RE` now matches UUID, legacy numeric, and digest ids.

## Prevention Measures

There must be exactly one canonical definition of the record-id shape. Any future id-format change edits `RECORD_ID_SUFFIX` once; all parsers compose it. When adding a relation-bearing feature, add a UUID-id fixture — legacy 3-digit fixtures alone hide this whole class of regression.
