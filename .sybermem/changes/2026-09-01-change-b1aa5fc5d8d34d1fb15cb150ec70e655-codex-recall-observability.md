---
type: change
record_id: change-b1aa5fc5d8d34d1fb15cb150ec70e655
date: 2026-09-01
title: Codex recall observability and perceptibility
status: completed
source: manual
key_conclusion: Codex now writes bounded recall/memory observability and visible injection markers so memory-stats and Desktop users can verify prompt-time recall.
topics: [codex, observability, recall]
author: Sisyphus
related_files: [.codex/hooks/user_prompt.py, .codex/hooks/session_start.py, .codex/hooks/session_end.py, .codex/hooks/_codex_observability.py, packages/core/sybermem_core/memory_usage_stats.py, scripts/_install_common.py, scripts/managed-install.json, scripts/check-plugin-package.py]
---

## Change Content

Implemented Codex recall observability and perceptibility across the runtime hooks, installers, Core stats parser, tests, and documentation. Codex `UserPromptSubmit` now writes metadata-only recall-debug and memory-usage rows, emits count/id markers in `additionalContext`, and supports a default-on env-gated `systemMessage`. Codex `SessionStart` journals startup lane usage, and the new `SessionEnd` hook records best-effort edit-alignment outcomes.

## Reason for Change

Codex previously received prompt-time recall and startup context but did not leave the same observability evidence as OpenCode, so `sybermem project memory-stats` could report `no_log` for Codex sessions and Desktop users could not easily perceive whether SyberMem memory was active.

## Impact Scope

- Codex hooks: prompt-time recall/habit/norm injection, startup context, and SessionEnd outcome recording.
- Core stats: `.memory-usage.jsonl` rows from both `opencode` and `codex` are now parsed and aggregated.
- Distribution: all install/update paths copy `session_end.py` plus `_codex_observability.py`, register `SessionEnd`, and use Codex `statusMessage` rather than the older `message` key.
- Managed removal: the manifest now includes the new Codex hook/helper so uninstall does not leave managed files behind.
- Project hygiene: `.sybermem/.memory-usage.jsonl` is ignored by root and project-refresh gitignore blocks.

## Implementation

- Added `.codex/hooks/_codex_observability.py` for bounded JSONL appends and shared Codex observability payloads.
- Extended `.codex/hooks/user_prompt.py` to call `context recall --format json`, preserve injected IDs/classes, write inject/abstain metadata, write memory lane totals, emit UTF-8-safe output, and include visible count/id markers plus an optional `systemMessage`.
- Extended `.codex/hooks/session_start.py` to journal startup context and use UTF-8-safe output.
- Added `.codex/hooks/session_end.py` to aggregate injected IDs for the session, approximate edited files from git diff/cached/untracked state, resolve `related_files`, and write precision/evidence outcome rows fail-open.
- Updated installers, package guard checks, managed removal manifest, tests, README files, `.codex/INSTALL.md`, and `docs/feature_map.md` for the new Codex contract.

## Test Verification

- `python -m pytest -q` in `packages/core`: `405 passed, 4 skipped`.
- `python scripts/check-plugin-package.py` with bytecode disabled after cache cleanup: `OK (13 skills; static checks only; claude CLI not found, skipped plugins validate)`.
- `python -m py_compile .codex/hooks/_codex_observability.py .codex/hooks/user_prompt.py .codex/hooks/session_start.py .codex/hooks/session_end.py scripts/_install_common.py scripts/check-plugin-package.py`: exit 0.
- `git diff --check`: no whitespace errors; only expected CRLF normalization warnings on Windows.
- Independent review lanes found no remaining security or behavior blockers after fixing stale tests, README text, unsupported hook wording, and the managed uninstall manifest.

## Notes

Codex Desktop still does not expose OpenCode-style TUI toasts. SyberMem relies on `statusMessage`, model-visible context markers, and best-effort dynamic `systemMessage` where Codex surfaces hook warnings/events. Hidden auto-resume and background workers remain unsupported.
