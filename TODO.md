# To Do

## Minimal Memory Injection Observability

Implements `requirement-ffb8b8130ecd4d33b8a08cfbb9479b59`.

Goal: add an OpenCode-first observability loop for actual memory injection usage and session outcomes without changing recall selection, injection policy, or context budgets.

### Engineering Rules

- Write or update the focused test before each behavior change.
- Keep logging bounded, local, prompt-free, content-free, and fail-open.
- Commit each verified phase promptly as an atomic commit. Do not wait until the entire feature is complete.
- Every implementation commit that fulfills this requirement should be linked in its SyberMem change record with `implements: [requirement-ffb8b8130ecd4d33b8a08cfbb9479b59]`.
- After all engineering tasks and local verification are complete, run Review Work and resolve every blocking finding before handoff.

### 1. Actual Injection Usage Journal

- [x] Add focused tests for extracting actual injected lane counts, record ids, startup presence, and rendered character counts from the OpenCode transform path.
- [x] Add a bounded `.sybermem/.memory-usage.jsonl` writer that records only `schema_version`, timestamp, host, session id, total items/chars, lane totals, injected ids, and startup presence.
- [x] Write the journal only after context is actually inserted into the model-visible system prompt.
- [x] Verify no raw prompt or complete injected memory content is persisted and all write failures remain fail-open.
- [x] Run focused OpenCode plugin tests and TypeScript diagnostics.
- [x] Commit: `feat(opencode): log actual memory injection usage`.

### 2. Session Outcome Reuse

- [x] Add focused tests for accumulating memory turns, total injected characters, item counts, and lane totals in the existing `SessionActivity` lifecycle.
- [x] Extend recall outcome evidence with `measurable` and `unmeasurable` injected counts while preserving the current edit-alignment calculation.
- [x] Reuse `session.idle` to flush a bounded session usage/outcome entry with edit, todo, tool, and memory evidence.
- [x] Verify session reset behavior and repeated idle events cannot double-count one completed activity window.
- [x] Run focused session activity and recall outcome tests.
- [x] Commit: `feat(opencode): record memory session outcomes`.

### 3. User-Visible Injection Summary

- [x] Add focused tests for one bounded post-injection summary containing total items, total characters, and recall/habit/norm/startup counts.
- [x] Replace multiple successful-injection notices with one summary notice while preserving the existing habit-candidate notice.
- [x] Keep silent when no model-visible memory was injected.
- [x] Verify the summary is emitted at injection time, not candidate collection time.
- [x] Run focused toast and system-transform tests.
- [x] Commit: `feat(opencode): summarize injected memory usage`.

### 4. Existing Memory Stats Extension

- [x] Add Core tests for parsing the bounded usage/outcome journal and aggregating 7-day and 30-day totals.
- [x] Add totals for memory turns, items, characters, average characters per memory turn, p95 characters per memory turn, and lane distribution.
- [x] Rename the displayed recall proxy to `Edit Alignment` and show hit/measurable plus unmeasurable counts.
- [x] Extend `sybermem project memory-stats --format json` without removing existing fields in the same release.
- [x] Extend the existing terminal renderer instead of creating a separate stats command.
- [x] Run focused Core/CLI tests, then the relevant package test suites.
- [x] Commit: `feat(stats): report memory injection usage`.

### 5. Documentation and SyberMem Record

- [x] Document `.memory-usage.jsonl`, privacy boundaries, fail-open behavior, and the meaning of Edit Alignment in README/CLI docs.
- [x] Create a SyberMem change record linked with `implements: [requirement-ffb8b8130ecd4d33b8a08cfbb9479b59]`.
- [x] Build and check the derived SyberMem INDEX.
- [x] Commit: `docs(memory): document injection observability`.

### 6. Review Work Blocker Fixes

- [x] Move usage journal retention compaction out of the OpenCode system-transform hot path; append metadata rows only during the transform and compact at idle.
- [x] Reject symlinked `.sybermem` journal destinations and oversized JSONL entries fail-open.
- [x] Bound `session_id`, packet scan volume, and injected ID cardinality; extract IDs only from structured memory item lines.
- [x] Write memory `session_outcome` rows only for sessions that had actual model-visible memory turns.
- [x] Treat unreadable, non-UTF-8, or oversized Core usage journals as `unavailable` rather than crashing `project memory-stats`.
- [x] Update public docs that still described separate recall/habit/norm success toasts.
- [x] Record the Review Work blocker resolution as project engineering memory.

### 7. Final Verification and Review Work

- [x] Run all relevant OpenCode plugin, Core, and CLI tests.
- [x] Run diagnostics on every changed source file and verify build/type-check success where applicable.
- [x] Manually exercise one injected turn and one abstained turn; inspect the usage log, session outcome, user summary, and `project memory-stats` output.
- [ ] Run Review Work after engineering is complete.
- [x] Resolve every blocking Review Work finding and rerun affected verification.
- [ ] Confirm the final worktree contains no unintended changes and all engineering phases were committed atomically.

### Deferred

- Configurable memory budgets or minimal/balanced/rich modes.
- Active budget rejection or a unified allocator.
- Exact model-specific tokenization.
- Semantic cross-lane deduplication.
- Claude/Codex telemetry parity.
- A new memory Skill or Memory Center UI.
- Injected-vs-withheld experimentation.
