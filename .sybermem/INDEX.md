# SyberMem Index

This file summarizes all project changes, decisions, requirements, and bug records.

---

## Key Conclusions

<!-- One-line core conclusion per record. Format: [id] #topic1 #topic2 — description (date) -->
- [requirement-001] #architecture #foundation — Adopted ADR system: four category directories + INDEX master index + templates + skill automation (2026-05-08)
- [change-001] #distribution #install — Added one-liner remote install scripts (curl/irm) to simplify new user onboarding, no clone needed (2026-05-12)
- [change-002] #distribution #skills — Moved SyberMem skill source to packages/claude-skills; eliminates duplicate skill loading from global installs (2026-05-12)
- [change-003] #hooks #automation — Added default project-level auto/remind hook template with stop-hook helper for lightweight change records (2026-05-13)
- [bug-001] #hooks #init — Fixed init-project misclassifying missing hook files; exposed need for project-root resolution from subdirectories (2026-06-09)
- [change-005] #init #hooks — Refreshed project instruction files to auto/remind mode and added project-level settings + stop-hook helper (2026-05-13)
- [requirement-002] #digest #compression — Identified need for persistent phase summary/compression layer to prevent understanding cost from growing linearly with records (2026-06-05)
- [change-006] #skills #framework — Repaired missing .claude/settings.json, fixed INDEX.md omissions, refreshed phase index, upgraded all 8 skills with HARD-GATE + numbered checklist (2026-06-16)
- [change-008] #distribution #hooks #automation — Added Claude Code plugin metadata and lifecycle hook delegators so SyberMem can install as a plugin without breaking existing project-managed hook files (2026-06-18)
- [change-010] #lifecycle #search #relations #digest #distribution — Transformed SyberMem from v1 (record+group+compress) to v2 (lifecycle-aware, retrieval-capable, relation-linked, topic-compressible, multi-platform) in a single session covering 6 capability rounds (2026-06-22)
- [change-011] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-29)
- [requirement-003] #architecture #collaboration #hub #team — Defined SyberMem cross-project and team memory extension: three-scope model (Project/Hub/Team), Skill-vs-Core separation, phased implementation from Hub MVP to Team Git (2026-06-29)
- [change-012] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30)
- [change-013] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30)
- [change-014] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30)
- [change-015] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30)
- [change-016] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30)
- [decision-001] #architecture #collaboration #team — Chose to prioritize a minimal Team Git repository MVP before fully polishing the personal Hub experience, because unified team-managed storage is the real near-term value of Requirement-003 (2026-06-30)
<!-- add new conclusions here -->

---

## Archived Conclusions

<!-- Not injected at session start; findable via /sybermem-search -->
<!-- Suffix each line with: [superseded by <id>] or [compressed in <id>] or [archived] -->
- [change-007] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-18) [archived]
- [change-009] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-19) [archived]
<!-- add new archived conclusions here -->

---

## Stage Digests

| Number | Date | Title | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
| 001 | 2026-06-05 | sybermem v1 digest design phase | completed | 3 records | [link](digests/2026-06-05-001-sybermem-v1-digest-design-phase.md) |
| 002 | 2026-06-29 | foundation and distribution phase | completed | 3 records | [link](digests/2026-06-29-002-foundation-and-distribution-phase.md) |
| 003 | 2026-06-29 | platform ecosystem and plugin packaging phase | completed | 3 records | [link](digests/2026-06-29-003-platform-ecosystem-and-plugin-packaging-phase.md) |
<!-- add new digest records here -->

---

## Theme Digests

| Number | Date | Theme | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
| 001 | 2026-06-22 | hooks | completed | 4 phases, 0 digests, 4 records | [link](theme-digests/2026-06-22-001-hooks.md) |
<!-- add new theme digest records here -->

---

## Feature Changes

| Number | Date | Title | Status | Link |
|--------|------|-------|--------|------|
| 001 | 2026-05-12 | Add remote install scripts for one-liner installation | implemented | [link](changes/2026-05-12-001-add-remote-install-scripts.md) |
| 002 | 2026-05-12 | Migrate global skill source to packages directory | implemented | [link](changes/2026-05-12-002-migrate-global-skill-source-to-packages.md) |
| 003 | 2026-05-13 | Add auto change hook template | implemented | [link](changes/2026-05-13-003-add-auto-change-hook-template.md) |
| 005 | 2026-05-13 | Refresh project instructions and add auto record hook files | implemented | [link](changes/2026-05-13-005-refresh-project-instructions-and-add-auto-record-hook-files.md) |
| 006 | 2026-06-16 | SyberMem framework hardening and project repair | implemented | [link](changes/2026-06-16-006-sybermem-framework-hardening-and-project-repair.md) |
| 007 | 2026-06-18 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-06-18-007-marketplace-plugin-hooks-and-more.md) |
| 008 | 2026-06-18 | Add Claude Code plugin skeleton | implemented | [link](changes/2026-06-18-008-add-claude-code-plugin-skeleton.md) |
| 009 | 2026-06-19 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-06-19-009-marketplace.md) |
| 010 | 2026-06-22 | SyberMem v2 — lifecycle, search, relations, theme digest, platform | implemented | [link](changes/2026-06-22-010-sybermem-v2-lifecycle-search-relations-theme-digest-platform.md) |
| 011 | 2026-06-29 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-06-29-011-skill-skill.md) |
| 012 | 2026-06-30 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-06-30-012-skill-skill-superpowers-skill-design-analysis.md) |
| 013 | 2026-06-30 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-06-30-013-skill-superpowers-skill-design-analysis.md) |
| 014 | 2026-06-30 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-06-30-014-init-cpython-310-main-cpython-310-init-cpython-310-and-more.md) |
| 015 | 2026-06-30 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-06-30-015-readme-en-readme-2026-06-30-sybermem-core-phase1-and-more.md) |
| 016 | 2026-06-30 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-06-30-016-init-main-pkg-info-and-more.md) |
<!-- add new records here -->

---

## Technical Decisions

| Number | Date | Title | Status | Link |
|--------|------|-------|--------|------|
| 001 | 2026-06-30 | Team MVP should precede full Hub experience for Requirement-003 | decided | [link](decisions/2026-06-30-001-team-mvp-before-full-hub-experience.md) |
<!-- add new records here -->

---

## Requirements / Discussions

| Number | Date | Title | Source | Priority | Link |
|--------|------|-------|--------|----------|------|
| 001 | 2026-05-08 | Create ADR Project Record System | Internal discussion | high | [link](requirements/2026-05-08-001-创建ADR项目规范系统.md) |
| 002 | 2026-06-05 | Phase summary and record compression requirements | User feedback | high | [link](requirements/2026-06-05-002-阶段性总结与记录压缩需求.md) |
| 003 | 2026-06-29 | SyberMem 跨项目与团队记忆扩展方案 | Internal review | high | [link](requirements/2026-06-29-003-sybermem-cross-project-team-memory-extension.md) |
<!-- add new records here -->

---

## Bug Fix Records

| Number | Date | Title | Severity | Link |
|--------|------|-------|----------|------|
| 001 | 2026-06-09 | init-project misclassifies missing hook file as custom/kept | medium | [link](bugs/2026-06-09-001-init-project-misclassifies-missing-hook-file.md) |
<!-- add new records here -->

---

## Usage

- **changes/**: Record all feature changes
- **decisions/**: Record important technical decisions and their rationale
- **requirements/**: Record discussion processes, requirement sources, and design reasoning
- **bugs/**: Record bug analysis and fix approaches
- **analysis/phase-index.md**: Persistent project phase analysis state used to track candidates, confirmed phases, and incremental analysis progress

When adding records, update this index file accordingly.

---

## Topic Index

<!-- Auto-maintained: maps topic tags to record IDs for fast lookup -->
<!-- Optional suffix: [active] [low] [deprecated → <new-topic>] -->
- architecture: requirement-001, requirement-003, decision-001
- automation: change-003, change-008
- collaboration: requirement-003, decision-001
- compression: requirement-002
- digest: requirement-002, change-010
- distribution: change-001, change-002, change-008, change-010
- framework: change-006
- hooks: change-003, change-005, bug-001, change-008
- hub: requirement-003
- init: change-005, bug-001
- install: change-001
- foundation: requirement-001
- lifecycle: change-010
- relations: change-010
- search: change-010
- skills: change-002, change-006
- team: requirement-003, decision-001
