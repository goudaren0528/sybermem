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

- [ ] Add focused tests for extracting actual injected lane counts, record ids, startup presence, and rendered character counts from the OpenCode transform path.
- [ ] Add a bounded `.sybermem/.memory-usage.jsonl` writer that records only `schema_version`, timestamp, host, session id, total items/chars, lane totals, injected ids, and startup presence.
- [ ] Write the journal only after context is actually inserted into the model-visible system prompt.
- [ ] Verify no raw prompt or complete injected memory content is persisted and all write failures remain fail-open.
- [ ] Run focused OpenCode plugin tests and TypeScript diagnostics.
- [ ] Commit: `feat(opencode): log actual memory injection usage`.

### 2. Session Outcome Reuse

- [ ] Add focused tests for accumulating memory turns, total injected characters, item counts, and lane totals in the existing `SessionActivity` lifecycle.
- [ ] Extend recall outcome evidence with `measurable` and `unmeasurable` injected counts while preserving the current edit-alignment calculation.
- [ ] Reuse `session.idle` to flush a bounded session usage/outcome entry with edit, todo, tool, and memory evidence.
- [ ] Verify session reset behavior and repeated idle events cannot double-count one completed activity window.
- [ ] Run focused session activity and recall outcome tests.
- [ ] Commit: `feat(opencode): record memory session outcomes`.

### 3. User-Visible Injection Summary

- [ ] Add focused tests for one bounded post-injection summary containing total items, total characters, and recall/habit/norm/startup counts.
- [ ] Replace multiple successful-injection notices with one summary notice while preserving the existing habit-candidate notice.
- [ ] Keep silent when no model-visible memory was injected.
- [ ] Verify the summary is emitted at injection time, not candidate collection time.
- [ ] Run focused toast and system-transform tests.
- [ ] Commit: `feat(opencode): summarize injected memory usage`.

### 4. Existing Memory Stats Extension

- [ ] Add Core tests for parsing the bounded usage/outcome journal and aggregating 7-day and 30-day totals.
- [ ] Add totals for memory turns, items, characters, average characters per memory turn, p95 characters per memory turn, and lane distribution.
- [ ] Rename the displayed recall proxy to `Edit Alignment` and show hit/measurable plus unmeasurable counts.
- [ ] Extend `sybermem project memory-stats --format json` without removing existing fields in the same release.
- [ ] Extend the existing terminal renderer instead of creating a separate stats command.
- [ ] Run focused Core/CLI tests, then the relevant package test suites.
- [ ] Commit: `feat(stats): report memory injection usage`.

### 5. Documentation and SyberMem Record

- [ ] Document `.memory-usage.jsonl`, privacy boundaries, fail-open behavior, and the meaning of Edit Alignment in README/CLI docs.
- [ ] Create a SyberMem change record linked with `implements: [requirement-ffb8b8130ecd4d33b8a08cfbb9479b59]`.
- [ ] Build and check the derived SyberMem INDEX.
- [ ] Commit: `docs(memory): document injection observability`.

### 6. Final Verification and Review Work

- [ ] Run all relevant OpenCode plugin, Core, and CLI tests.
- [ ] Run diagnostics on every changed source file and verify build/type-check success where applicable.
- [ ] Manually exercise one injected turn and one abstained turn; inspect the usage log, session outcome, user summary, and `project memory-stats` output.
- [ ] Run Review Work after engineering is complete.
- [ ] Resolve every blocking Review Work finding and rerun affected verification.
- [ ] Confirm the final worktree contains no unintended changes and all engineering phases were committed atomically.

### Deferred

- Configurable memory budgets or minimal/balanced/rich modes.
- Active budget rejection or a unified allocator.
- Exact model-specific tokenization.
- Semantic cross-lane deduplication.
- Claude/Codex telemetry parity.
- A new memory Skill or Memory Center UI.
- Injected-vs-withheld experimentation.
