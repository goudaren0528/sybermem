---
type: change
record_id: change-5d2b321fcbd440b393bb2030376043de
date: 2026-08-27
title: Recall accuracy Phase 1 scoring and health signals
status: implemented
source: manual
key_conclusion: Recall Phase 1 now ranks key conclusions and path anchors while preserving the conservative auto-injection gate.
topics: [recall, search, observability]
author: Sisyphus
related_files:
  - packages/core/sybermem_core/search_query.py
  - packages/core/sybermem_core/search.py
  - packages/core/sybermem_core/memory_stats.py
  - packages/cli/sybermem_cli/context.py
  - packages/opencode-plugin/src/recall_health_signal.ts
  - packages/opencode-plugin/sybermem.ts
  - docs/recall_accuracy_product_design.md
  - docs/recall_accuracy_phase1_plan.md
  - docs/feature_map.md
related: [decision-c24f122fbe5d46ee8095022e6b8c53c8, change-0638a1012020456193d3b469506151af]
---

## Change Content

Implemented recall accuracy Phase 1 across Core, CLI, and the OpenCode plugin:

- `key_conclusion` is now a first-class lexical scoring facet for project recall.
- `related_files` now provides a capped path/module boost that can break ties without penalizing records that do not declare anchors.
- Search rows carry bounded `matched_fields_detail` and `score_breakdown` metadata for debug/JSON surfaces.
- `recall_health` can now report `low_measurability` when recall is firing but too many injected records cannot be checked against edited files because `related_files` anchors are sparse.
- `sybermem context recall --format json` exposes explanation metadata, while the prompt-time Markdown recall packet remains compact.
- OpenCode recall-health toasts now handle `low_measurability` in addition to `low_signal` and `low_relevance`.
- Public README and feature-map docs now describe Phase 1 ranking, explainability, and measurability semantics.

## Reason for Change

The product review found that SyberMem should not simply recall more records. The safer Phase 1 improvement is to rank existing high-value record fields better, make decisions explainable to tools and humans, and distinguish poor relevance from missing measurement anchors without lowering automatic prompt-injection trust gates.

## Impact Scope

Affected project recall scoring, recall-health advisory status, CLI JSON output, OpenCode health toasts, generated OpenCode plugin bundle, and public documentation. The high-signal automatic recall threshold remains unchanged at `12.0`, and weak keyword-only matches still abstain from automatic injection.

## Implementation

Core scoring now adds weighted overlap for `key_conclusion`, capped overlap for `related_files`, and bounded score explanation metadata on lexical overlap results. Core health now computes a separate low-measurability verdict from `.memory-usage.jsonl` session outcomes when edit evidence exists and unmeasurable anchors dominate the sample. CLI JSON serializes explanation metadata only for recall JSON consumers, leaving Markdown prompt output unchanged. The OpenCode plugin source and generated bundle now surface a low-measurability toast.

## Test Verification

- `uv run pytest packages/core/tests/test_recall_retrieval_contract.py packages/core/tests/test_search_review_findings.py packages/core/tests/test_status.py packages/core/tests/test_memory_usage_stats.py packages/core/tests/test_semantic_recall.py packages/cli/tests/test_cli_context.py packages/cli/tests/test_cli_project_memory_stats.py packages/cli/tests/test_cli_search.py` → 81 passed.
- `bun test packages/opencode-plugin/tests/recall_debug.test.ts packages/opencode-plugin/tests/recall_health_signal.test.ts packages/opencode-plugin/tests/recall_outcome.test.ts` → 16 passed.
- `bun scripts/build-opencode-plugin.mjs --check` → passed.
- Independent QA pass reported PASS after running the full package suites: core 386 passed / 4 skipped, CLI 78 passed, OpenCode plugin 113 passed.

## Notes

Generated local `.codegraph/` index was used for navigation only and is intentionally not part of this change.
