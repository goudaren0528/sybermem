---
type: bug
date: 2026-06-09
number: 001
title: init-project misclassifies missing hook file as custom/kept
severity: medium
---

## Bug Description
`/sybermem-init-project` and `/sybermem-update` reported `.sybermem/hooks/record_change_on_stop.py` as "custom (kept, has local improvements)" even though the file did not exist on disk. This caused the stop hook to fail with `[Errno 2] No such file or directory` every time a session stopped.

## Root Cause
The `sybermem-init-project` skill's Step 1.1 file classification logic did not require a file-system verification (Read/Glob/Test-Path) before classifying project files. The AI inferred file existence from indirect evidence (e.g., `.claude/settings.json` referencing the hook path) and classified it as "custom" without confirming the file actually existed on disk.

A secondary contributing factor: the user's actual working directory was a subdirectory (`D:\erp-lite\web`) of the true project root (`D:\erp-lite`), so even when the file existed at the project root, the relative-path stop hook command could not find it from the subdirectory.

## Solution
1. Added a mandatory file-system verification requirement to `sybermem-init-project/SKILL.md` Step 1.1: before classifying any file, the AI must use a file-system tool to confirm existence. Indirect inference is explicitly forbidden.
2. Identified a deeper architectural issue: SyberMem currently lacks a "project root resolution" layer that can trace from a subdirectory back to the nearest parent SyberMem project root. This is being addressed in a separate spec.

## Related Records
- `packages/claude-skills/sybermem-init-project/SKILL.md` — the fixed skill definition
- Commit `159fe57` — the fix commit
