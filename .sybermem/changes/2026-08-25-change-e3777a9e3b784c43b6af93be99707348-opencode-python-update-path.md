---
type: change
record_id: change-e3777a9e3b784c43b6af93be99707348
date: 2026-08-25
title: OpenCode Python update path for Windows PowerShell spawn failures
status: active
source: manual
key_conclusion: Added a Python-based SyberMem install/update path so Windows OpenCode users can refresh globally without spawning powershell.exe.
topics: [opencode, installer, windows]
author: Sisyphus
related_files: [scripts/_install_common.py, scripts/install-remote.py, scripts/update.py, packages/claude-skills/sybermem-update/SKILL.md, skills/sybermem-update/SKILL.md, README.md, README.en.md, INSTALL.md, .opencode/INSTALL.md, scripts/check-plugin-package.py, packages/core/tests/test_package_integrity_scripts.py]
---

## Change Content
Added a PowerShell-free Python installation/update route for SyberMem. The new remote installer downloads and extracts the GitHub archive with Python stdlib, then reuses shared installer logic. The local checkout updater runs the same shared logic directly from the repository.

## Reason for Change
Windows OpenCode users reported frequent `EPERM: operation not permitted, uv_spawn 'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.EXE'` failures when `/sybermem-update` tried to run the PowerShell remote installer. The root issue is OpenCode being unable to spawn PowerShell in some restricted environments, so the reliable fix is to avoid PowerShell for that path.

## Impact Scope
Windows OpenCode and `cmd.exe` users can now refresh global SyberMem skills, CLI runtime, OpenCode plugin, and Codex hooks via Python. Existing PowerShell and POSIX shell installers remain supported. Project-local refresh still runs through `sybermem project refresh --format json` after global update.

## Implementation
Created `scripts/_install_common.py` with shared installation behavior, `scripts/install-remote.py` for remote Python install/update, and `scripts/update.py` for local checkout updates. Updated `/sybermem-update` skill instructions in both distributed skill trees with Windows OpenCode/cmd commands and fixed-launcher project refresh syntax. Updated public docs and package integrity checks so Python installers are covered by the same distribution guards.

## Test Verification
Verified Python syntax with `python -m py_compile scripts/_install_common.py scripts/update.py scripts/install-remote.py`. Ran `python scripts/check-plugin-package.py`, `python -m pytest packages/core/tests/test_package_integrity_scripts.py packages/core/tests/test_install_powershell_safety.py -q`, and `git diff --check` successfully before recording.

## Notes
The Python route intentionally does not modify persistent `PATH` and does not require PowerShell execution policy changes.
