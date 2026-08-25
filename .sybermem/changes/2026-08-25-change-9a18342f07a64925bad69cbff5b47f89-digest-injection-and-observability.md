---
type: change
record_id: change-9a18342f07a64925bad69cbff5b47f89
date: 2026-08-25
title: Digest injection and observability rollout
status: done
source: manual
key_conclusion: Delivered current digest conclusion injection and digest usage observability across Codex, Claude templates, OpenCode, Core, and docs so stable phase conclusions become model-visible and measurable without adding new memory infrastructure.
topics: [digest, recall, observability]
author: Sisyphus
related_files: [.codex/hooks/session_start.py, packages/core/sybermem_core/search.py, packages/core/sybermem_core/memory_stats.py, packages/core/sybermem_core/memory_usage_stats.py, packages/opencode-plugin/src/prompt_context.ts, packages/opencode-plugin/src/recall_debug.ts, packages/opencode-plugin/src/memory_usage.ts, packages/opencode-plugin/sybermem.ts, packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py, skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py]
---

## Change Content
Shipped the digest-deepening rollout as nine atomic commits on `main`. Codex SessionStart and Claude project hook templates now inject the latest current phase digest Core Conclusions with freshness gates and bounded item counts. Core compact recall now demotes stale or archived digest rows while keeping high-signal recall gates intact. OpenCode prompt context, recall debug, injection toasts, and memory usage journals now tag and count digest-backed injected items. Core and CLI memory stats expose digest usage defaults and aggregates. Digest authoring docs and templates now emphasize source-aware, compact Core Conclusions, and the init/update freshness checker recognizes hooks missing the latest digest injection marker as stale.

## Reason for Change
Earlier digest work made phase digests searchable, but stable conclusions still needed stronger runtime feedback: host startup contexts should surface only current conclusions, stale digests should not crowd out fresh recall rows, and users should be able to see digest contribution in actual injection observability. The rollout keeps the architecture local and bounded while making digest conclusions practically visible to future agents.

## Impact Scope
The change affects SyberMem runtime behavior for Codex startup hooks, Claude project hook templates distributed through init/update, OpenCode memory injection metadata, Core recall ranking, and CLI memory statistics. It does not introduce vector databases, cloud services, a new memory store, broad semantic recall expansion, automatic record rewrites, or hidden prompt payload persistence. Existing legacy records and normal recall selection semantics remain supported.

## Implementation
Implemented freshness-gated latest digest block generation for Codex and Claude template startup contexts, including a five-conclusion cap and fail-open behavior when freshness is stale, unknown, or unavailable. Added Core digest staleness ranking for compact recall. Extended OpenCode classification and usage metadata with `has_digest` and `digest_items`, then regenerated the bundled plugin. Updated Core/CLI usage parsing and reporting for legacy-safe digest defaults. Updated mirrored skills/templates and project freshness checks so old managed hooks are refreshed through `/sybermem-update`.

## Test Verification
Verified with focused Core, CLI, and OpenCode plugin tests: `python -m pytest packages/core/tests/test_init_project_distribution.py packages/core/tests/test_recall_retrieval_contract.py packages/core/tests/test_codex_lifecycle_hooks.py packages/core/tests/test_memory_usage_stats.py packages/core/tests/test_package_integrity_scripts.py packages/cli/tests/test_cli_project_memory_stats.py` passed with 100 tests, `bun test tests/prompt_context.test.ts tests/memory_usage.test.ts tests/recall_debug.test.ts tests/injection_toast.test.ts` passed with 23 tests, `python scripts/check-plugin-package.py` succeeded, and `git diff --check` found no whitespace errors beyond Windows line-ending warnings. Additional review agents checked distribution-chain freshness and targeted test coverage; a missing digest ranking plus high-signal gate regression was added and rerun successfully.

## Notes
The work was committed and pushed to `origin/main` through commits `697b6d1` through `dc63a9b`. The project-local `.sybermem/INDEX.md` was not hand-edited during the rollout; this record will be incorporated through the derived index build/check flow.
