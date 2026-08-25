---
type: bug
record_id: bug-17a87caf3b014254bdc0d284ad010540
date: 2026-08-25
title: Python updater recreated existing CLI venv on Windows
source: manual
severity: medium
status: resolved
key_conclusion: Fixed the Python updater to reuse an existing CLI venv so Windows OpenCode updates no longer fail on a locked venv python.exe.
topics: [installer, windows, opencode]
related: [change-e3777a9e3b784c43b6af93be99707348]
---

## Bug Description
Running `/sybermem-update` through the new Python local update path refreshed global skill files but failed during runtime refresh with `Permission denied: 'C:\Users\ttx\.claude\sybermem\cli\venv\Scripts\python.exe'`.

## Root Cause
`scripts/_install_common.py` always ran `python -m venv` against the existing SyberMem CLI venv before reinstalling packages. On Windows, the venv executable can be locked or protected while OpenCode is running, so recreating the venv can fail even though the existing venv is usable.

## Solution
Changed runtime refresh to create the venv only when the venv Python launcher is missing. Existing venvs are reused for `pip install --upgrade pip` and `pip install --upgrade --force-reinstall` of Core and CLI packages.

## Prevention Measures
Added a regression test that simulates a Windows-style existing venv and asserts the Python installer does not call `python -m venv` while still running pip refresh commands.

## Related Changes
Related to `change-e3777a9e3b784c43b6af93be99707348`, which introduced the Python-based update path for Windows OpenCode environments that cannot spawn PowerShell.
