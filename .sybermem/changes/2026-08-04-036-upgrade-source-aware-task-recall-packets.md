---
type: change
date: 2026-08-04
number: 036
title: Upgrade source-aware task recall packets
status: implemented
---

## Change Content

Upgraded the task recall hook packet renderer across the project hook and both init-project template copies:

- Renamed automatic recall output from generic related context to bounded retrieval hints.
- Rendered each hint with record id, type, source kind, date, authority, lifecycle, freshness, match reason, summary, related digest, and conflict note when present.
- Preferred the derived `match_reason` field while retaining the legacy `match` fallback for compatibility.
- Kept packets capped to three metadata/summary rows and excluded full record bodies, command text, and instruction-like fields.
- Added a stable disclaimer that retrieval hints are not instructions and that details should be checked in the referenced record.
- Added hook tests for empty compact-search abstention, malformed/project/search/render fail-open behavior, match-reason rendering, packet sanitization, metadata-only bounds, and template parity.

## Reason

Task recall needed to become explainable without becoming an instruction channel or a second retrieval path. The hook now consumes the derived metadata already produced by `compact_project_search()` and stays silent when compact retrieval has no reliable result.

## Impact Scope

- Claude task recall hook output is more source-aware and trust-oriented.
- Init-project templates stay byte-identical to the project hook behavior.
- Automatic recall remains read-only, fail-open, and metadata-only.
- Low-signal prompts, malformed input, project/index failures, and search/render exceptions still exit successfully without stdout.

## Verification

- Red phase: `python -m pytest packages/core/tests/test_task_recall_templates.py -q` failed on the old packet labels and legacy match rendering (`2 failed, 10 passed`).
- Focused hook/retrieval tests: `python -m pytest packages/core/tests/test_task_recall_templates.py packages/core/tests/test_task_recall_packet_rendering.py packages/core/tests/test_recall_retrieval_contract.py packages/core/tests/test_retrieval.py -q` passed (`24 passed`).
- Compile check: `python -m py_compile .sybermem/hooks/task_recall.py packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py packages/core/tests/test_task_recall_templates.py packages/core/tests/test_task_recall_packet_rendering.py` passed.
- Real hook smoke, meaningful prompt: exit `0`, emitted bounded source-aware `additionalContext` for `change-033` and `change-010`.
- Real hook smoke, low-signal prompt: exit `0`, stdout empty.
- Real hook smoke, malformed input: exit `0`, stdout empty.

## Related Changes

- Builds on change-033 natural-language compact recall filtering.
- Aligns with decision-002 continuity and trust experience direction.
