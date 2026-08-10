---
type: change
record_id: change-a6dd46baa8994962a257a43e1a73daee
date: 2026-08-07
title: High-signal recall gate for automatic prompt-time injection
key_conclusion: Restricted automatic task-recall injection to high-signal matches (record-id/relation/score>=12) and logged abstention reasons, because wrong hot-path hints cost more trust than missed ones
topics: [recall, search, quality]
status: implemented
related: [change-036]
---

## Change Content

Added `high_signal_recall_hints(query, limit)` in `search.py` as the dedicated contract for automatic prompt-time recall. It wraps the existing `compact_project_search`, then keeps only high-signal rows:

- exact `record-id` match, or
- an explicit `relation` match, or
- lexical `score >= HIGH_SIGNAL_SCORE_FLOOR` (12.0).

Bare keyword overlap — however current/authoritative — is dropped from the hook path (explicit `/sybermem-search` still surfaces it). The function returns `(rows, abstention_reason)`; when it abstains, the reason is a bounded phrase for local debug logging, never injected into the prompt.

`.sybermem/hooks/task_recall.py` now imports only `high_signal_recall_hints` and, on abstention, appends a bounded non-sensitive entry to `.sybermem/.recall-debug.jsonl` (rolling 200-line cap, no prompt payload, fail-open). Both distributed hook templates (`packages/claude-skills/...` and `skills/...`) were synced byte-identical, and `.recall-debug.jsonl` was gitignored.

## Reason

The previous hook injected on every eligible prompt whenever `score>=5 && matched_fields>=2`. That both missed semantically relevant prompts and occasionally injected plausible-but-wrong keyword hints. On the hot path a wrong hint pollutes the agent's context while a missing hint costs nothing, so the gate is deliberately conservative — prefer silence over noise.

## Impact Scope

- `packages/core/sybermem_core/search.py`: new `high_signal_recall_hints`, `_is_high_signal`, `HIGH_SIGNAL_SCORE_FLOOR`.
- `.sybermem/hooks/task_recall.py` + 2 distributed templates: high-signal call + abstention logging.
- Tests: 3 new cases in `test_recall_retrieval_contract.py`; `write_fake_core` stub extended to expose the new contract.
- Verified: core suite 123 passed; live run against this project — record-id prompt injects, generic keyword prompt stays silent and logs abstention.
