---
type: change
date: 2026-08-04
number: 033
title: Improve natural-language search matching
status: implemented
---

## Change Content

Improved SyberMem core search recall for natural prompts without changing public search APIs or canonical Markdown formats:

- Added dependency-free query tokenization that preserves meaningful ASCII terms and extracts CJK runs through bounded 2-4 character n-grams instead of single common characters.
- Added bounded overlap scoring across title, topics, relations, and body while preserving record-id, authority, lifecycle, freshness, and relation ranking behavior.
- Stripped Markdown frontmatter from body scoring so title/topic metadata is not counted twice.
- Added safe workspace FTS query construction from escaped terms and LIKE fallback behavior for malformed or unusable FTS paths.
- Extracted token/scoring helpers into `search_query.py` and workspace SQL helpers into `workspace_query.py`, reducing `search.py` from the prior oversized state to 198 pure LOC.
- Added tests for distributed English terms, natural Chinese/CJK prompts, low-signal prompt silence, and FTS metacharacter/fallback behavior.

## Reason

Natural task prompts were brittle: ASCII-only term extraction missed Chinese/CJK prompts, exact phrase matching missed meaningful English terms spread across record fields, and weak generic prompts could over-recall. `search.py` also needed to stay below the project's 250 pure-LOC ceiling after previous retrieval fixes.

## Impact

- Project compact recall can retrieve relevant records from meaningful multi-term English and CJK prompts without exact phrase matches.
- Low-signal prompts stay quiet in automatic recall.
- Workspace search uses safe term FTS queries and falls back without raising when FTS is unavailable or unusable.
- Explicit evidence visibility and compact evidence filtering remain unchanged.
- Recall packets remain capped and metadata-only through existing task recall rendering tests.

## Verification

- `python -m pytest packages/core/tests/test_recall_retrieval_contract.py packages/core/tests/test_workspace_index_consistency.py` — 11 passed
- `python -m pytest packages/core/tests` — 26 passed
- `python -m compileall packages/core/sybermem_core` — passed
- `python -m py_compile packages/core/sybermem_core/search.py packages/core/sybermem_core/search_query.py packages/core/sybermem_core/workspace_query.py packages/core/tests/test_recall_retrieval_contract.py packages/core/tests/test_workspace_index_consistency.py` — passed
- Pure LOC audit: `search.py` 198, `search_query.py` 90, `workspace_query.py` 62

## Related Changes

- Builds on change-010 (SyberMem v2 lifecycle, search, relations, and retrieval)
- Builds on change-032 (core quality fixes and FTS5 search coverage)
