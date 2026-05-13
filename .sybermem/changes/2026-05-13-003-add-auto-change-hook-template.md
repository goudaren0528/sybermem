---
type: change
date: 2026-05-13
number: 003
title: Add auto change hook template
status: implemented
author: Developer
related_files: packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json, packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py, packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md, packages/claude-skills/sybermem-init-project/project-files/AGENTS.md, packages/claude-skills/sybermem-init-project/SKILL.md, packages/claude-skills/sybermem-update/SKILL.md, README.md, README.en.md, INSTALL.md, docs/zh/README.md, docs/zh/CLAUDE.zh.md, docs/zh/AGENTS.zh.md, docs/zh/skills/init-project.zh.md
---

## Change Content

Added a default project-level auto/remind hook template for SyberMem. New projects initialized through `/sybermem-init-project` now receive a project `.claude/settings.json` with `SYBERMEM_RECORD_MODE`, plus a `.sybermem/hooks/record_change_on_stop.py` helper that writes a basic `change` record from real workspace file changes at stop time.

Key changes:

- Added `.claude/settings.json` to the init-project template set
- Added `.sybermem/hooks/record_change_on_stop.py` as the default auto-change helper
- Updated generated `CLAUDE.md` / `AGENTS.md` to explain `auto` vs `remind`
- Limited automatic recording to `change` records based on workspace file changes
- Updated English and Chinese docs plus skill docs to describe the new default behavior and discoverability path

## Reason for Change

The previous behavior depended on instruction text asking the assistant to remind the user about `/sybermem-record`, but there was no actual hook automation in project settings. As a result, many completed tasks never triggered a record flow reliably. This change moves the default behavior into project-level hook configuration so new projects get a real automation entry point, while still keeping richer `decision`, `requirement`, and `bug` records manual.

## Impact Scope

- New projects: receive working auto/remind configuration and a runnable stop-hook helper
- Existing projects refreshed through `/sybermem-update`: can pick up the new managed settings/helper path
- Users: can discover and switch modes through generated docs or by editing `.claude/settings.json`
- Record quality: automatic mode stays intentionally narrow and only produces lightweight `change` records

## Implementation

- Created `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py`
- Kept the stop-hook command in `packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json`
- Updated init-project and update skill docs so they explicitly create or refresh the helper alongside project settings
- Updated README / INSTALL and Chinese backups to include `.claude/settings.json` and the hook helper in generated project files
- Replaced old reminder-only template wording in generated `CLAUDE.md` / `AGENTS.md` with documented auto/remind behavior

## Test Verification

- Ran `python -m py_compile packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py`
- Parsed `packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json` with Python JSON loading
- Created a temporary git repo, copied the helper, executed it twice with `SYBERMEM_RECORD_MODE=auto`, and verified:
  - one `change` record was created in `.sybermem/changes/`
  - `.sybermem/INDEX.md` was updated
  - the second run did not duplicate the record for the same fingerprint
- Removed temporary smoke-test artifacts after verification

## Notes

Automatic mode only records `change`. Users should still use `/sybermem-record` for `decision`, `requirement`, and `bug` records, or when they want a richer summary than the hook can infer.
