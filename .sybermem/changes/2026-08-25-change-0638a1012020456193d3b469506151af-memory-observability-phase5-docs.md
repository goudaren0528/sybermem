---
type: change
record_id: change-0638a1012020456193d3b469506151af
date: 2026-08-25
title: Minimal OpenCode memory injection observability
status: done
source: manual
key_conclusion: Added an OpenCode-first actual-injection journal, session outcomes, one prompt-time usage summary, and 7d/30d stats so users can inspect memory context cost and Edit Alignment evidence before budget controls are introduced.
topics: [memory, observability, opencode]
author: Sisyphus
related_files: [packages/opencode-plugin/src/memory_usage.ts, packages/opencode-plugin/src/session_activity.ts, packages/opencode-plugin/src/recall_outcome.ts, packages/opencode-plugin/src/injection_toast.ts, packages/core/sybermem_core/memory_usage_stats.py, packages/core/sybermem_core/memory_stats.py, packages/cli/sybermem_cli/memory_stats_render.py]
implements: [requirement-ffb8b8130ecd4d33b8a08cfbb9479b59]
---

## Change Content
Delivered the complete minimal memory injection observability loop for OpenCode. The system records metadata-only per-turn actual injection usage after model-visible insertion, accumulates session usage through the existing `SessionActivity` lifecycle, writes session outcomes at idle, distinguishes measurable, unmeasurable, and unavailable recall evidence, emits one prompt-time usage summary, and extends existing project memory stats with 7d/30d usage and lane metrics.

## Reason for Change
SyberMem previously had conservative recall and an edit-alignment proxy but did not expose actual context usage or the portion of recall evidence that was measurable. Observability was implemented first to establish a factual baseline before configurable budgets, allocation, or cross-host expansion.

## Impact Scope
OpenCode now writes bounded `.memory-usage.jsonl` per-turn and `session_outcome` entries without raw prompts or full injected memory text. Existing recall selection and injection policies remain unchanged. Core and CLI aggregate and display memory turns, items, characters, average and p95 characters per turn, lane distributions, and explicit Edit Alignment evidence coverage.

## Implementation
Added typed OpenCode usage measurement and bounded journaling, session accumulation and idle outcomes, combined prompt-time injection summary, Core mixed-journal parsing and aggregation, and CLI rendering through the existing `project memory-stats` command. Updated bilingual product and CLI documentation plus the feature map for the shipped behavior and privacy boundaries.

## Test Verification
Verified focused and full OpenCode plugin tests, Core tests, CLI tests, generated bundle freshness, package integrity, TypeScript diagnostics, SyberMem INDEX build/check, and the fixed-launcher `project memory-stats` surface. Final repository-wide verification and Review Work remain the required release gates.

## Notes
This change does not introduce configurable budgets, token counts, task utility scoring, Claude/Codex telemetry parity, user controls, or semantic accuracy claims.
