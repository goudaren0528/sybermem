---
type: change
date: 2026-07-07
number: 030
title: Align init-project propagation with Team and reminder workflows
status: implemented
author: Claude
related_files:
  - packages/claude-skills/sybermem-init-project/SKILL.md
  - skills/sybermem-init-project/SKILL.md
  - packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json
  - skills/sybermem-init-project/project-files/.claude/settings.json
  - packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py
  - skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py
  - packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md
  - skills/sybermem-init-project/project-files/CLAUDE.md
  - packages/claude-skills/sybermem-init-project/project-files/AGENTS.md
  - skills/sybermem-init-project/project-files/AGENTS.md
implements: [requirement-003]
---

## Change Content
Aligned the `sybermem-init-project` propagation layer with the recently added Team and reminder-first capabilities. This filled the remaining gap between the new core/CLI behavior and the files/templates/health checks that fresh installs and `/sybermem-update` rely on.

## Reason for Change
Recent work added:
- Team publish / Team summary skills
- Team-aware project linking and Team repo workflows
- reminder-first stop/nudge behavior
- natural-language record intent capture via `UserPromptSubmit`

But the init/update propagation layer had drifted. Some mirrored templates still lacked the new `UserPromptSubmit` hook and Team guidance, and some init docs did not tell users that Team workflows now exist. Without this alignment, a project could be technically upgraded at the core level but still receive stale setup behavior or stale onboarding guidance.

## Impact Scope
- Affected modules/features
  - init-project skill guidance
  - project-level settings template propagation
  - project-level health-check propagation
  - project instruction templates (`CLAUDE.md` / `AGENTS.md`)
  - Team workflow discoverability after init/update
- Affected user groups
  - users initializing new SyberMem projects
  - users upgrading existing projects with `/sybermem-update`
  - users adopting Team memory workflows through project-local guidance

## Implementation
- Updated `sybermem-init-project/SKILL.md` so Step 7 and Step 8 explicitly include:
  - `.sybermem/hooks/detect_record_intent.py`
  - `UserPromptSubmit` hook in `.claude/settings.json`
  - the real `auto` / `remind` semantics
  - Team workflow next steps after initialization
- Synced the plugin-facing `skills/sybermem-init-project/` mirror to match the source skill.
- Updated `project-files/.claude/settings.json` (and mirrored copy) so fresh init/update templates include the `UserPromptSubmit` hook for record-intent capture.
- Updated `project-files/.sybermem/hooks/check_project_health.py` (and mirrored copy) so health checks understand:
  - `has_record_intent_hook`
  - `.sybermem/hooks/detect_record_intent.py`
  - Team linkage state
- Updated `project-files/CLAUDE.md` and `project-files/AGENTS.md` (and mirrored copies) so generated project instructions now mention:
  - Team skills (`/sybermem-team-publish`, `/sybermem-team-summary`)
  - reminder-first semantics
  - explicit natural-language record-intent capture

## Test Verification
Verified by source inspection and propagation audit:
- Confirmed `sybermem-init-project` source and `skills/` mirror now both contain:
  - `detect_record_intent.py`
  - updated `.claude/settings.json`
  - Team-aware `check_project_health.py`
  - Team-aware `CLAUDE.md` / `AGENTS.md`
- Confirmed `SKILL.md` next-step guidance now includes Team publish/summary guidance.
- Re-ran project health checks after update and confirmed the current project reports `has_record_intent_hook: true` and Team linkage correctly.

## Notes
This change does not add new Team or reminder capabilities itself; it closes the propagation gap so installs and updates can consistently carry those capabilities into real projects. It is a classic “make the upgrade path honest” change, which is essential for Requirement-003 to be operational rather than only implemented in the main repo.