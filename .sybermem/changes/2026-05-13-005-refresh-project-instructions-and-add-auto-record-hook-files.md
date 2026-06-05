---
type: change
date: 2026-05-13
number: 005
title: Refresh project instructions and add auto record hook files
status: implemented
author: Claude
related_files: ["AGENTS.md", "CLAUDE.md", ".claude/settings.json", ".sybermem/hooks/record_change_on_stop.py", ".claude/backups/AGENTS.md.backup-2026-05-13", ".claude/backups/CLAUDE.md.backup-2026-05-13"]
---

## Change Content
Refreshed the project's SyberMem-managed instruction files to the new auto/remind mode wording, and added the missing project-level settings plus stop-hook helper required for automatic lightweight change recording.

## Reason for Change
After updating the globally installed SyberMem skills, this repository still had stale project instructions and lacked the project-level files needed for the new auto/remind workflow. The refresh was needed so the repo would match the latest SyberMem behavior without overwriting the user's existing local-only settings.

## Impact Scope
- Affected modules/features
  - Project-root `AGENTS.md`
  - Project-root `CLAUDE.md`
  - Project-level `.claude/settings.json`
  - `.sybermem/hooks/record_change_on_stop.py`
  - Backup copies for the replaced instruction files
- Affected user groups
  - Maintainers updating this SyberMem repository
  - Projects using the default SyberMem auto/remind workflow

## Implementation
Ran `/sybermem-update` from the SyberMem repo to refresh globally installed skills, classified the existing `AGENTS.md` and `CLAUDE.md` as stale SyberMem-managed files, backed them up, replaced them with the latest templates, then created `.claude/settings.json` and `.sybermem/hooks/record_change_on_stop.py` from the packaged project templates. The existing `.claude/settings.local.json` was left untouched as custom local configuration.

## Test Verification
- Verified the refreshed files were written to disk
- Compiled `.sybermem/hooks/record_change_on_stop.py` successfully with `python -m py_compile`
- Validated `.claude/settings.json` contains `SYBERMEM_RECORD_MODE=auto` and the Stop hook command `python .sybermem/hooks/record_change_on_stop.py`
- Confirmed `.claude/settings.local.json` was not overwritten during the refresh

## Notes
- The refreshed project instructions now document the `auto` / `remind` modes and the default stop-hook helper path.
- The repo now has both shared project settings in `.claude/settings.json` and personal overrides in `.claude/settings.local.json`.
