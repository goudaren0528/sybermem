---
type: change
record_id: change-c2be7cced7eb4250b288606869f1e726
date: 2026-08-25
title: Scoped uninstall CLI and natural-language uninstall skill
status: active
source: user-request
key_conclusion: Added explicit project/global uninstall routing because users need safe natural-language scope selection while preserving project memory histories.
topics: [uninstall, distribution, safety]
author: Sisyphus
related_files: [packages/cli/sybermem_cli/main.py, scripts/safe-managed-remove.py, scripts/managed-install.json, packages/claude-skills/sybermem-uninstall/SKILL.md, skills/sybermem-uninstall/SKILL.md, scripts/install.sh, scripts/install.ps1, scripts/update.sh, scripts/update.ps1, scripts/install-remote.sh, scripts/install-remote.ps1]
---

## Change Content

Added a top-level scoped uninstall CLI surface: `sybermem uninstall --scope project` delegates to the existing project deactivation path, while `sybermem uninstall --scope global --yes` removes managed user-level skills/hooks/plugin/CLI through the installed managed remover. Added `/sybermem-uninstall` as a natural-language router that asks when the user has not specified project-level versus global uninstall and requires explicit confirmation before global removal.

## Reason for Change

Project-level and global uninstall were previously separate surfaces. Users had to know the difference between `sybermem project uninstall` and repository-local `scripts/uninstall.*`, which made natural-language uninstall requests ambiguous and risked choosing the wrong scope. The manifest also mixed active and retired skill names, obscuring whether retired Team skills were still current assets or cleanup targets.

## Impact Scope

Impacts the CLI, global uninstall safety path, skill distribution inventory, user-facing install/update output, public docs, and package integrity checks. Project `.sybermem/` histories remain preserved by both project and global uninstall paths. Existing `sybermem project uninstall` remains compatible.

## Implementation

- Added `cmd_uninstall` and `sybermem uninstall --scope project|global` to the CLI; global scope refuses to proceed without `--yes`.
- Reused the installed `~/.claude/sybermem/safe-managed-remove.py` and `managed-install.json` for global CLI uninstall so updated users do not need a repository checkout.
- Added `retired_skills` to `managed-install.json` and taught the remover to clean active and retired skills, preserving old-user cleanup while making the manifest semantics explicit.
- Added `/sybermem-uninstall` to `packages/claude-skills` and mirrored it to `skills`, then wired all local/remote install and update scripts so Claude Code, OpenCode, and Codex receive it after update.
- Added PowerShell best-effort cleanup for a SyberMem-owned `~/.local/bin/sybermem` link for parity with `uninstall.sh`.

## Test Verification

- `python -m pytest packages/core/tests/test_cli_uninstall_scope.py packages/core/tests/test_safe_managed_remove.py packages/core/tests/test_uninstall_shell_safety.py packages/core/tests/test_uninstall_powershell_safety.py packages/core/tests/test_package_integrity_scripts.py -q` passed: 47 passed, 3 skipped.
- `python -m pytest packages/core/tests -q` passed: 346 passed, 4 skipped.
- `python scripts/check-plugin-package.py` passed after clearing generated Python cache artifacts: OK (13 skills; static checks only; claude CLI not found, skipped plugins validate).
- Manual source CLI smoke verified project scope from a nested directory preserves `.sybermem/changes/change.md` while removing managed `.claude/settings.json` entries.
- Manual source CLI smoke verified global scope removes runtime, OpenCode plugin, Codex hook files/hooks.json entries, and preserves separate project `.sybermem/` history.

## Notes

The earlier observation that retired skill names should be removed from the manifest was refined: they must remain uninstallable for old users, but now live under `retired_skills` instead of the active `skills` inventory.
