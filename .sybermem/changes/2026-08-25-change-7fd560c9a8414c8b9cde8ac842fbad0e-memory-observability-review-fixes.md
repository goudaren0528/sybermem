---
type: change
record_id: change-7fd560c9a8414c8b9cde8ac842fbad0e
date: 2026-08-25
title: Review fixes for OpenCode memory observability
status: done
source: manual
key_conclusion: Review Work required the memory-usage journal to be secure, bounded, append-only on the prompt hot path, and semantically limited to real memory turns before the observability rollout could be considered handoff-ready.
topics: [memory, observability, opencode, quality, security]
author: Sisyphus
related_files: [packages/opencode-plugin/src/state.ts, packages/opencode-plugin/src/memory_usage.ts, packages/opencode-plugin/src/recall_outcome.ts, packages/opencode-plugin/src/plugin.ts, packages/core/sybermem_core/memory_usage_stats.py, README.md, README.en.md, CHANGELOG.md, TODO.md]
implements: [requirement-ffb8b8130ecd4d33b8a08cfbb9479b59]
related: [change-0638a1012020456193d3b469506151af]
---

## Change Content
Resolved the Review Work blockers found after the initial minimal memory injection observability rollout. The OpenCode JSONL writer now appends on the transform path and compacts at idle, rejects symlinked memory directories and oversized metadata rows fail-open, and bounds metadata extracted from model-visible packets. Session outcome rows are only written when a session had actual memory turns. Core now treats unreadable, non-UTF-8, or oversized `.memory-usage.jsonl` files as `unavailable` instead of failing `project memory-stats`.

## Reason for Change
The first rollout delivered the requested observability loop but Review Work found that the logging layer could follow symlinks, process attacker-sized metadata, block the OpenCode prompt transform with full-journal rewrites, and emit memory outcomes for sessions with no memory. These were release blockers because observability is advisory and must not create privacy, robustness, or semantic-integrity risks.

## Impact Scope
The fix keeps OpenCode-first observability and the existing recall/injection policy unchanged. It narrows what metadata can be persisted, moves bounded retention work to idle, preserves fail-open behavior, and makes downstream stats distinguish unavailable journals from missing logs. Public docs and TODO state now match the single summary toast behavior and the Review blocker resolution state.

## Test Verification
Added and ran focused tests for append-only plus idle compaction, symlinked memory directory refusal, oversized JSONL entry refusal, structured-only injected ID extraction, session/id cardinality limits, non-memory session outcome suppression, and Core unavailable status for read failures, invalid UTF-8, and oversized journals. Final full gates and rerun Review Work remain the handoff gates after bundle rebuild.
