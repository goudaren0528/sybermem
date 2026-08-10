---
type: change
record_id: change-36b8a2dca14a4d459c3ff964eb5ea5f5
date: 2026-08-07
title: Recall observability logs inject and abstain events
key_conclusion: Generalized the recall debug log to record both which records were injected (with match type) and why recall abstained, giving a bounded local baseline to measure recall quality and tune thresholds
topics: [recall, quality, hooks]
status: implemented
related: [change-a6dd46baa8994962a257a43e1a73daee]
---

## Change Content

Refactored the task-recall hook's `log_abstention` into a general `log_recall_event(root, event, **fields)` and now log two event kinds to `.sybermem/.recall-debug.jsonl`:

- `inject` — the record_ids surfaced this turn plus their match type.
- `abstain` — the bounded reason nothing crossed the high-signal bar.

Kept bounded (200-line roll), never stores the prompt payload, never writes to stdout (so the hook contract stays intact). Synced to both distribution copies.

## Reason for Change

E6: E1 made recall conservative but gave no way to see whether it was helping. Logging inject/abstain events builds an empirical baseline so the high-signal threshold can be tuned with data instead of guesswork.

## Impact Scope

- `.sybermem/hooks/task_recall.py` + 2 distribution copies.
- Verified: a record-id prompt writes an `inject` event (`change-047 / record-id`).
