---
type: bug
date: 2026-08-04
number: 002
title: Publish preview bootstrap and JSON output leaks
severity: high
status: resolved
---

## Description

Independent verification found two blocking defects in the Task 6 Team publish trust envelope implementation:

- `sybermem publish status --preview` still called the normal bootstrap path, so a project shell with `.sybermem/` and `.claude/settings.json` but no `.sybermem/project.yaml` had identity created as a side effect.
- `sybermem publish status --format json` could emit git commit summary text before the JSON payload because internal `git add` / `git commit` / `git diff` subprocess calls inherited stdout/stderr.

## Root Cause

Preview mode was routed after `ensure_project_yaml()` in `bootstrap_publish_status()`, so the read-only preflight was not actually read-only for missing Project identity. The publish git helper also only captured remote/push subprocess output; local staging and commit commands wrote directly to the caller's stdout/stderr.

## Solution

- Added an early preview-only blocked response in `bootstrap_publish_status()` for no project, no SyberMem project, and missing project identity before `ensure_project_yaml()` or registry writes can run.
- Returned structured `{"status": "blocked", "reason": "missing_project_identity", ...}` payloads from JSON preview and made blocked preview exit non-zero without creating `.sybermem/project.yaml`.
- Captured stdout/stderr for internal `git add`, `git diff --cached --quiet`, and `git commit` calls so JSON mode emits valid JSON only.
- Added CLI regression tests using `capfd` for subprocess stdout leakage and a missing-identity preview fixture.

## Verification

- Red phase: `python -m pytest packages/cli/tests/test_cli_publish.py -q` failed with both findings reproduced (`2 failed`).
- Focused CLI publish regressions: `python -m pytest packages/cli/tests/test_cli_publish.py -q` passed (`2 passed`).
- Focused core publish/status tests: `python -m pytest packages/core/tests/test_publish.py packages/core/tests/test_status.py -q` passed (`8 passed`).
- Compile check: `python -m py_compile packages/core/sybermem_core/publish.py packages/core/sybermem_core/publish_bootstrap.py packages/cli/sybermem_cli/main.py packages/cli/sybermem_cli/publish_render.py packages/cli/tests/test_cli_publish.py` passed.
- Full core tests: `python -m pytest packages/core/tests -q` passed (`73 passed`).
- Full CLI tests: `python -m pytest packages/cli/tests -q` passed (`4 passed`).
- Isolated temp smoke: `C:\Users\69046\AppData\Local\Temp\opencode\sybermem-task6-review-smoke-agrys4gk` proved missing identity preview is blocked/read-only and successful JSON publish parses as JSON-only.

## Related Changes

- Hardens change-037 Team publish preview trust envelope without changing Project canonical schemas or adding a second store.
