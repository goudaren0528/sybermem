---
type: bug
date: 2026-08-05
number: 004
status: fixed
severity: high
related: [change-045]
---

## Bug Description

Batch A (change-045) merged the two UserPromptSubmit hooks (`detect_record_intent.py` + `task_recall.py`) into a single `user_prompt.py` process and updated the runtime settings, the settings templates, the plugin delegator, and `check-plugin-package.py`. But it did not update `check_project_health.py`, which is the detector that the `/sybermem-init-project` incremental-update path relies on.

Confirmed effect: a project already migrated to the single `user_prompt.py` hook is judged `needs_update` and told to "add UserPromptSubmit hook entry" + "add task_recall UserPromptSubmit entry" — which would drag every project running `/sybermem-update` BACK to the dual-hook layout, actively undoing batch A. New installs were also affected (they get the single-hook template, then the same health check flags it stale).

## Root Cause

`check_settings_json` decided UserPromptSubmit freshness by looking for `detect_record_intent.py` AND `task_recall.py` in `.claude/settings.json` (`all_present = ... has_record_intent_hook and has_task_recall_hook ...`). The new settings template only contains `user_prompt.py`, so the check always failed and emitted the two legacy "add" actions. `check_project_health.py` also had no create/replace entry for `user_prompt.py`.

Compounding confusion during the fix: `check_project_health.py` self-updates by copying the GLOBAL installed template (`~/.claude/skills/.../check_project_health.py`) over itself and re-execing. So local edits to the project copy appeared to "revert" on every run until the global skill was refreshed.

## Solution

In `check_project_health.py`:
- Added `has_user_prompt_hook = "user_prompt.py" in content`; UserPromptSubmit freshness now keys on it. The legacy pair is still detected only to offer migration.
- Replaced the two regressive "add" actions with a single action: migrate the legacy dual hooks to one `user_prompt.py` entry (or wire it when missing), preserving unrelated custom hooks.
- Added `check_user_prompt_hook` + a create/replace managed-hook check for `user_prompt.py`.
- Kept `detect_record_intent.py` / `task_recall.py` as recognized backward-compatible modules.

Also updated the `sybermem-update` and `sybermem-init-project` SKILLs to describe `user_prompt.py` and the dual→single migration. Synced all 3 copies (source + mirror + refreshed global).

## Prevention Measures

When a managed-file layout changes, update `check_project_health.py` in the same change — it is the propagation gate for existing projects, and the `sybermem-update` SKILL's own invariant already requires that every new managed behavior state whether `/sybermem-update` changes project-local files. Batch A satisfied the template/runtime/plugin paths but skipped the health-check detector; treat the health check as a required surface of any hook/settings change.

## Related Changes

- change-045: batch A that introduced the merged hook and the propagation gap.
- Fix committed in batch G (this record); spec: docs/superpowers/specs/2026-08-05-sybermem-merged-hook-propagation-fix-design.md.
