---
type: requirement
record_id: requirement-ffb8b8130ecd4d33b8a08cfbb9479b59
date: 2026-08-25
title: Minimal memory injection observability for OpenCode
source: product discussion
priority: high
key_conclusion: Add an OpenCode-first injection usage and session outcome observability loop so users can see memory cost and quality evidence before SyberMem introduces budget controls.
topics: [memory, observability, opencode]
---

## Requirement Source

Product discussion after reviewing SyberMem recall quality, user perceptibility, and context-injection economics.

## Requirement Content

Implement the smallest useful observability loop without changing recall selection or injection behavior:

1. Record each actual OpenCode memory injection in a bounded local `.sybermem/.memory-usage.jsonl` journal.
2. Record the session id, host, injected item count, injected character count, lane breakdown, injected record ids, and startup-context presence without storing raw prompts or full memory content.
3. Reuse the existing `SessionActivity` and `session.idle` lifecycle to aggregate memory turns, injected characters, lane totals, edit/tool/todo signals, and recall outcome evidence.
4. Extend edit-alignment reporting to expose measurable and unmeasurable injected items so anchorless records are not hidden behind a misleading percentage.
5. Show one bounded user-facing injection summary after context actually reaches the model, including total items, lane counts, and total characters.
6. Extend the existing `sybermem project memory-stats` output and JSON payload with 7-day and 30-day memory usage totals, average and p95 characters per memory turn, lane distribution, and measurable/unmeasurable edit-alignment coverage.

## Discussion

SyberMem already has conservative recall gates, bounded packet counts, OpenCode injection toasts, per-session activity accumulation, recall debug logging, edit-alignment outcomes, and a `memory-stats` surface. The first improvement should reuse those paths and establish a factual baseline before introducing configurable budgets or adaptive allocation.

The usage journal must reflect context that was actually injected, not merely candidate records. Character counts are sufficient for this phase and avoid tokenizer/model dependencies. The first implementation targets OpenCode because it already exposes the complete capture, transform, activity, and idle lifecycle needed for trustworthy measurement.

## Final Conclusion

Build observability first. Users should be able to tell whether memory was applied, which lanes contributed, how much context it consumed, and how much of the existing edit-alignment result was actually measurable. Use the resulting data to decide whether later budget controls, deduplication, or cross-host work are justified.

## Design Principles / Constraints

- Preserve current recall, habit, norm, startup, and compaction behavior in this phase.
- Keep all new logging fail-open and bounded.
- Do not persist raw prompts or complete injected memory text.
- Reuse `SessionActivity`, `session.idle`, existing bounded JSONL helpers, and `project memory-stats`.
- Rename or clearly present the existing proxy as edit alignment rather than semantic recall accuracy.
- Implement with tests first for each bounded change.
- Commit each verified engineering phase promptly as an atomic commit; do not wait until the entire feature is complete.
- After all engineering work and local verification are complete, run Review Work and resolve every blocking finding before handoff.
- Out of scope for this requirement: configurable budgets, minimal/balanced/rich modes, active budget rejection, unified allocator, semantic cross-lane deduplication, exact tokenization, Claude/Codex parity, a new memory Skill, a Memory Center UI, and injected-vs-withheld experimentation.

## Related Decisions / Changes

None yet. Implementation changes should link back to this requirement with `implements`.
