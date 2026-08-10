---
type: change
record_id: change-b70ea980b0934358aad0ba47b64bff33
date: 2026-08-07
title: Mechanical digest coverage staleness detection
key_conclusion: Added a deterministic coverage_hash check that mechanically flags a digest as stale when its declared source records change, so AI-authored summaries can no longer read as authoritative after drifting
topics: [digest, quality, search]
status: implemented
related: [requirement-002]
---

## Change Content

Added `digest_coverage.py` with:

- `parse_digest_coverage(text)` — reads `source_records` + stored `coverage_hash` from a digest's frontmatter.
- `compute_coverage_hash(root, source_records)` — deterministic, order-independent SHA-256 over the current content of the declared source files (a missing source participates as an explicit `<missing>` marker).
- `digest_coverage_verdict(root, text)` — returns `current` / `stale` / `unknown`.

Wired `_annotate_digest_coverage` into `search_project`: any digest row whose verdict is `stale` is demoted to `freshness=stale` with a conflict note ("digest source records changed after this digest was written; regenerate before relying on it").

## Reason

Digests are AI-authored compression of a fixed set of source records. When a source changes after the digest is written, the digest silently drifts while still reading as authoritative (the hooks theme-digest already contained a conclusion later overturned by change-047). Turning "is this digest still accurate?" from an AI judgement into a mechanical hash comparison closes that trust gap deterministically, in core.

## Impact Scope

- `packages/core/sybermem_core/digest_coverage.py`: new module.
- `packages/core/sybermem_core/search.py`: `_annotate_digest_coverage` + import, called before conflict annotation.
- Tests: new `test_digest_coverage.py` (5 cases: parse, unknown-not-stale, current->stale, search demotion).
- Back-compat: digests without `coverage_hash` return `unknown` and are never falsely flagged.
- Follow-up: the digest-generation skill must emit `coverage_hash` when writing new digests (skill-side change; core mechanism is ready).
- Verified: core suite 123 passed.
