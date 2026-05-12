---
type: change
date: 2026-05-12
number: 002
title: Migrate global skill source to packages directory
status: implemented
author: Developer
related_files: packages/claude-skills, scripts/install.sh, scripts/install.ps1, scripts/update.sh, scripts/update.ps1, scripts/install-remote.sh, scripts/install-remote.ps1, README.md, README.en.md, INSTALL.md, docs/zh/README.md, docs/zh/skills/init-project.zh.md, docs/zh/skills/record.zh.md
---

## Change Content

Migrated the SyberMem skill source out of the auto-loaded project directory into `packages/claude-skills/`, updated all install and update scripts to copy from that package source into global skill locations, refreshed user-facing documentation, and removed the repository's project-local `.claude/skills/sybermem-*` copies.

Key changes:

- Added canonical skill source under `packages/claude-skills/`
- Updated local and remote install/update scripts to install from `packages/claude-skills/`
- Clarified in docs that new projects only receive `.sybermem/`, `CLAUDE.md`, and `AGENTS.md`
- Removed repo-local runnable skill copies to prevent duplicate skill loading
- Migrated the project record directory from `ADR/` to `.sybermem/`

## Reason for Change

The repository previously contained project-local runnable skill copies under `.claude/skills/` while users could also have the same skills installed globally. Claude then loaded both sources and showed duplicate SyberMem skills in the `/` list. The distribution repo should provide canonical source files for global installation, while target projects should only contain project-scoped records and instruction files.

## Impact Scope

- Repo maintainers: maintain one canonical skill source in `packages/claude-skills/`
- End users: install globally without creating duplicate project-local skills
- New projects: only create or refresh `.sybermem/`, `CLAUDE.md`, and `AGENTS.md`
- Existing projects with stale local skill copies: now receive explicit cleanup guidance in docs and install/update messaging

## Implementation

- Copied SyberMem skill definitions and templates into `packages/claude-skills/`
- Updated Bash and PowerShell install/update scripts to read from the package source
- Updated remote install scripts to extract `packages/claude-skills/` from the archive
- Updated English and Chinese docs plus Chinese skill docs to reflect the new distribution model
- Deleted `.claude/skills/sybermem-init-project`, `sybermem-record`, `sybermem-summary`, and `sybermem-update`
- Updated package-source internal references from `.claude/skills/...` to `packages/claude-skills/...`

## Test Verification

- Verified no `.claude/skills/sybermem-*` directories remain in the repo worktree
- Verified package-source skill files now reference `packages/claude-skills/...`
- Verified repo-wide searches only find `.claude/skills/sybermem-*` in expected warning/documentation text
- Reviewed `git status` to confirm the migration footprint matches the intended move from project-local source to package source

## Notes

This change preserves global skill installation while keeping project-level state limited to `.sybermem/`, `CLAUDE.md`, and `AGENTS.md`.
