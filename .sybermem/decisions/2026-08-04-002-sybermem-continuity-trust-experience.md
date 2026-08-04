---
type: decision
date: 2026-08-04
number: 002
title: Adopt a lightweight continuity and trust experience layer
status: accepted
supersedes: []
---

## Context

SyberMem already provides structured Project records, phase/theme digests, lifecycle-aware retrieval, task recall, Hub indexing, and Team publication. The remaining user-facing gap is continuity friction: after a pause or tool switch, users need a bounded current-state handoff; recalled history needs visible source, authority, freshness, and conflict signals; and recording or publishing needs a clearer low-friction route.

The solution must preserve `.sybermem/` Markdown as the canonical source, keep derived indexes rebuildable, retain Project/Hub/Team boundaries, and avoid turning ordinary work into a complex or silently mutating memory workflow.

## Considered Options

### Option A: Local output enhancements

Add a few fields and messages to existing summary, search, record, and Team publish outputs.

- Pros: smallest change surface and lowest operational risk.
- Cons: resume, recall, recording, and publishing remain fragmented.

### Option B: Lightweight continuity and trust experience layer

Add a unified read-only resume checkpoint and source-aware recall packet while reusing existing search, retrieval, phase, digest, relation, and publish capabilities. Add suggest/plan record routing, visible correction state, and lightweight preview checks for high-impact actions.

- Pros: creates one coherent experience without duplicating canonical memory; supports phased delivery.
- Cons: requires shared output contracts for authority, lifecycle, freshness, conflict, and review state.

### Option C: Independent memory engine

Create a separate current-state store, event log, write protocol, and retrieval engine.

- Pros: maximum freedom for a new memory product.
- Cons: duplicates existing records/digests/relations and creates competing sources of truth, migration work, and cross-scope consistency risk.

## Final Decision

Adopt **Option B: a lightweight continuity and trust experience layer**.

The first implementation phases are:

1. read-only resume checkpoint and source-aware recall packet;
2. abstention and correction/supersession presentation;
3. suggest/plan/confirm/write recording route;
4. Hub/Team freshness, unpublished-change, conflict, and review metadata;
5. lightweight revision/source-hash preview for digest, promote, and Team publish.

Do not introduce a second canonical memory directory, vector database, resident worker, silent full-capture pipeline, or complex receipt/lease state machine for ordinary records.

## Impact and Consequences

### Positive

- Lower cross-session restart cost.
- More explainable and safer task recall.
- Less ambiguity around whether to record, digest, or publish.
- Corrections remain auditable through successor relations.
- Team consumers can distinguish current, stale, conflicted, and unpublished status.

### Risks and mitigations

- Shared metadata could drift if each surface defines it independently. Mitigate with one derived retrieval/output contract and contract tests.
- Extra status fields could increase output noise. Mitigate with bounded packets, abstention, and read-mode tiers.
- Preview checks could slow ordinary work. Limit them to digest, promote, publish, and other high-impact operations.
- OpenCode cannot rely on unsupported prompt-time injection. Preserve manual search and compaction fallback.

## Related Changes

- `docs/superpowers/specs/2026-08-04-sybermem-continuity-trust-experience-design.md`
- `docs/superpowers/plans/2026-08-04-sybermem-continuity-trust-experience.md`

## Notes

The implementation plan is intentionally staged. Phase 1 is read-only and independently valuable; later phases must not begin by creating a parallel memory source.
