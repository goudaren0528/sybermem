---
type: bug
record_id: bug-3a161fa287bd425daf3e685e0f13f6b1
date: 2026-08-10
title: Merged prompt hook bypassed the high-signal recall gate and observability
key_conclusion: Routed the merged user_prompt.py recall through high_signal_recall_hints + log_recall_event so the E1 high-signal gate and E6 inject/abstain logging actually run on the wired production hook instead of only in the standalone task_recall.main
topics: [recall, hooks, quality, distribution]
status: fixed
severity: high
related: [change-a6dd46baa8994962a257a43e1a73daee, change-36b8a2dca14a4d459c3ff964eb5ea5f5]
---

## Bug Description

E1 (high-signal recall gate) and E6 (inject/abstain observability) were implemented in `task_recall.py`'s `main()` / `high_signal_recall_hints`. But the hook actually wired into `.claude/settings.json` is the **merged** `user_prompt.py`, which reuses only `task_recall`'s pure helpers (`should_skip`, `render_packet`, `configure_import_path`) and ran recall via a direct `compact_project_search(prompt, limit=3)` call.

Effect: in the real installed path, E1 and E6 were dead. The merged hook injected any compact hit — including keyword-only and semantic-supplement rows — with no high-signal gating and no recall-debug logging. `task_recall.main` (where the gate lived) is not the wired entrypoint, so the earlier standalone-hook verification passed while production behavior was unchanged. Found during the final chain-integrity review.

## Root Cause

Two hook files with overlapping responsibility: the standalone `task_recall.py` and the merged `user_prompt.py`. Improvements were applied to the standalone `main()`, but `user_prompt.py._run_recall` had its own copy of the recall orchestration that called `compact_project_search` directly, so it never picked up the gate/logging.

## Solution

Rewrote `user_prompt.py._run_recall` to call `high_signal_recall_hints` and `recall_hook.log_recall_event` exactly as `task_recall.main` does — reusing `task_recall`'s helpers as the single source of truth. Synced to both distribution copies.

Added regression tests: (1) the shipped `user_prompt.py` references `high_signal_recall_hints` + `log_recall_event` and does NOT call `compact_project_search` directly; (2) `user_prompt.py` added to the byte-identical distribution-consistency check.

Verified live: the merged hook now injects on a record-id prompt, stays silent on a keyword-only prompt, and writes both `inject` and `abstain` events to `.recall-debug.jsonl`.

## Prevention Measures

When two hook files share a responsibility, the orchestration must live in one and be reused, not copied. The new test asserts the wired hook routes through the gated contract, so re-introducing a raw `compact_project_search` call in `user_prompt.py` fails CI. General rule (D1): verify improvements on the *actually-wired* entrypoint, not a sibling module with the same helpers.
