---
type: change
record_id: change-55183042d89842e7a2ab5292fc5ebf4f
date: 2026-09-01
title: Habit recall diagnostic test and explain commands
status: completed
source: user PRD docs/prd/habit-recall-diagnostic-explain-test.md
key_conclusion: Added read-only prompt-time habit diagnostics and CLI test/explain commands so users can see why confirmed habits are selected, skipped, or blocked without changing habit state.
topics: [habit, diagnostic, cli]
author: Sisyphus
related_files: [packages/core/sybermem_core/habit_diagnostics.py, packages/core/sybermem_core/user_habits.py, packages/cli/sybermem_cli/habit_diagnostic_cli.py, packages/cli/sybermem_cli/habits.py, packages/core/tests/test_user_habits.py, packages/cli/tests/test_cli_habits.py, packages/cli/tests/test_cli_context.py, README.md, packages/cli/README.md, packages/core/README.md, skills/sybermem-habit/SKILL.md, packages/claude-skills/sybermem-habit/SKILL.md]
related: [change-7f75f17f01cc4d249ca8468e7bbfec7d, change-57a47bcef74841b6a454fe5e53d23b2f]
---

## Change Content

Implemented the P1 habit recall diagnostic/explain/test scope from the PRD. Core now has a read-only `evaluate_prompt_habits(context, higher_authority_text="")` evaluator that reports prompt-time habit counts, pending candidate count, context summary, and per-habit decisions with status, confidence, policy, review expiry, tag matches, score/floor, and reason codes.

The real prompt-time reminder renderer now consumes the evaluator's selected rows, so CLI dry-runs and production reminder selection share the same scoring path. Pending candidates remain counted separately and are never selected as active habits.

CLI adds `sybermem habit test --context <text>` and `sybermem habit explain --id <habit-id> --context <text>` with Markdown and JSON output. Unknown IDs return a concise `unknown_habit` response. Documentation and the mirrored `sybermem-habit` skill copies now describe the diagnostic workflow and reason-code troubleshooting path.

## Reason for Change

Habit prompt-time reminders were still hard to debug: users could see that no habit appeared, but could not tell whether the cause was inactive/pending state, confidence, policy, review expiry, `not_applies_to`, relevance score, or higher-authority suppression. The PRD required a dry-run diagnostic source of truth without lowering the conservative prompt-time injection gate or reusing the project-memory recall pipeline.

## Impact Scope

The change affects user-habit Core evaluation, the habit CLI parser and rendering path, CLI/core tests, README guidance, and the two in-repo `sybermem-habit` skill copies. It does not change `habits.jsonl` or `.habit-intent.json` schemas, does not add data migration, does not add host metadata logs, and does not implement the PRD's optional P2 OpenCode/Claude/Codex diagnostic logging.

## Implementation

- Added `packages/core/sybermem_core/habit_diagnostics.py` for typed read-only prompt-time habit evaluation.
- Reused the evaluator from `render_habit_reminder_markdown` and kept `sybermem_core.user_habits.evaluate_prompt_habits` as a compatibility entrypoint.
- Added `packages/cli/sybermem_cli/habit_diagnostic_cli.py` and registered `habit test` / `habit explain` from the existing habit parser.
- Added regression coverage for selected, not-selected, excluded, empty-context, higher-authority, pending-candidate, read-only, unknown-id, and prompt-time Markdown compactness behavior.
- Closed code-quality review findings by avoiding private `argparse` annotations, using explicit selection eligibility instead of exact reason-list equality, and documenting the intentional same-package coupling to production scoring helpers.

## Test Verification

- Red-phase evidence: Core tests first failed because `evaluate_prompt_habits` did not exist; CLI tests first failed because `habit test` / `habit explain` were not registered.
- `uv run pytest packages/core/tests/test_user_habits.py packages/cli/tests/test_cli_habits.py packages/cli/tests/test_cli_context.py` -> `87 passed`.
- `uv run pytest packages/core/tests packages/cli/tests` -> `497 passed, 4 skipped`.
- `python -m compileall -q packages/core/sybermem_core packages/cli/sybermem_cli` -> passed with no output.
- Isolated CLI smoke with temp `SYBERMEM_HOME`: `habit add`, `habit test`, and `context habit --delivery prompt-time` produced the expected diagnostic table for dry-run and normal compact reminder Markdown for prompt-time output.
- Review lanes: goal review PASS, security review PASS, runtime QA PASS, context mining PASS; code-quality review findings were fixed and re-reviewed PASS.

## Notes

Python LSP diagnostics could not be used because `basedpyright` is not installed and was previously declined in this environment. `ruff` was also unavailable. These tooling gaps were offset with focused tests, full Core+CLI regression, compileall, isolated CLI smoke, and independent review lanes.
