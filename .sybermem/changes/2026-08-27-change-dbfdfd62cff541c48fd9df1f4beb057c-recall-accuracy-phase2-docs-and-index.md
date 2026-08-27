---
type: change
record_id: change-dbfdfd62cff541c48fd9df1f4beb057c
date: 2026-08-27
title: Recall accuracy Phase 2 docs and derived index update
status: implemented
source: manual
key_conclusion: Recall accuracy Phase 2 now documents one-hop typed relation expansion and strict prompt-time caps so public guidance matches the shipped conservative recall gate.
topics: [recall, docs, search]
author: Sisyphus
related_files:
  - README.md
  - README.en.md
  - docs/feature_map.md
related: [change-5d2b321fcbd440b393bb2030376043de]
---

## Change Content

Updated the public documentation for recall accuracy Phase 2 without changing product code or tests:

- `README.md` now states that explicit project search can perform one-hop typed relation expansion and expose `relation-expanded`, `expanded_from`, and `expansion_relation` provenance on machine-readable surfaces.
- `README.en.md` mirrors the same search and prompt-time recall behavior in English.
- `docs/feature_map.md` now treats one-hop typed relation expansion and prompt-time expansion caps as the current source-of-truth behavior for Search and High-signal Recall.
- The new change record links back to the Phase 1 recall-accuracy change so the derived history shows the documentation follow-up in sequence.

## Reason for Change

Phase 2 needed the public docs and derived project memory to match the implemented recall contract exactly, because the shipped behavior is intentionally conservative: explicit search may show relation-expanded rows with provenance, but prompt-time recall must stay capped and must not promote weak keyword, topic, or semantic-only matches into injected memory.

## Impact Scope

Affected repository-level product documentation, the Feature Map source of truth, one manual SyberMem change record, and the derived `.sybermem/INDEX.md` rebuilt by CLI. No product code, tests, plugin bundles, or search behavior changed in this todo.

## Implementation

The documentation now distinguishes between explicit search surfaces and the prompt-time `context recall` gate:

- explicit project search may add one-hop typed relation expansions when a direct `record_id` match or typed relation match produces a qualified seed;
- machine-readable outputs may include `match: relation-expanded`, `expanded_from`, and `expansion_relation` provenance;
- prompt-time recall may append at most one non-evidence one-hop expansion per qualifying high-signal seed, and at most two total expansions in one packet;
- weak keyword-only, topic-only, and semantic-only matches remain non-expanding and non-injecting.

The record was written manually with a generated canonical `record_id`, then `sybermem project index build` and `sybermem project index check` were run so `.sybermem/INDEX.md` stayed CLI-derived.

## Test Verification

- Behavior consistency verified against current implementation in `packages/core/sybermem_core/search.py`, `packages/core/sybermem_core/relation_expansion.py`, and `packages/opencode-plugin/src/prompt_context.ts`: explicit search can emit `relation-expanded` rows with provenance, while prompt-time recall only appends bounded expansions from high-signal seeds.
- Historical successful verification cited for the underlying shipped feature set: targeted Core/CLI suite `60 passed`; full Core+CLI suite from QA `477 passed, 4 skipped`; focused CLI tests `16 passed`; core contract `37 passed`.
- `sybermem project index build` ran successfully and regenerated the derived `.sybermem/INDEX.md`.
- `sybermem project index check` ran successfully after the build and confirmed the derived index is current.

## Notes

This Phase 2 todo is documentation and project-memory only. It intentionally avoids product code, tests, plugin rebundling, commits, pushes, and any manual edit to `.sybermem/INDEX.md`.
