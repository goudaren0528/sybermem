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
<!-- add new conclusions here -->

---

## Stage Digests

| Number | Date | Title | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
| 001 | 2026-06-05 | sybermem v1 digest design phase | completed | 3 records | [link](digests/2026-06-05-001-sybermem-v1-digest-design-phase.md) |
<!-- add new digest records here -->

---

## Feature Changes

| Number | Date | Title | Status | Link |
|--------|------|-------|--------|------|
| 001 | 2026-05-12 | Add remote install scripts for one-liner installation | implemented | [link](changes/2026-05-12-001-add-remote-install-scripts.md) |
| 002 | 2026-05-12 | Migrate global skill source to packages directory | implemented | [link](changes/2026-05-12-002-migrate-global-skill-source-to-packages.md) |
| 003 | 2026-05-13 | Add auto change hook template | implemented | [link](changes/2026-05-13-003-add-auto-change-hook-template.md) |
| 005 | 2026-05-13 | Refresh project instructions and add auto record hook files | implemented | [link](changes/2026-05-13-005-refresh-project-instructions-and-add-auto-record-hook-files.md) |
| 006 | 2026-06-16 | SyberMem framework hardening and project repair | implemented | [link](changes/2026-06-16-006-sybermem-framework-hardening-and-project-repair.md) |
<!-- add new records here -->

---

## Technical Decisions

| Number | Date | Title | Status | Link |
|--------|------|-------|--------|------|
<!-- add new records here -->

---

## Requirements / Discussions

| Number | Date | Title | Source | Priority | Link |
|--------|------|-------|--------|----------|------|
| 001 | 2026-05-08 | Create ADR Project Record System | Internal discussion | high | [link](requirements/2026-05-08-001-创建ADR项目规范系统.md) |
| 002 | 2026-06-05 | Phase summary and record compression requirements | User feedback | high | [link](requirements/2026-06-05-002-阶段性总结与记录压缩需求.md) |
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
- architecture: requirement-001
- automation: change-003
- compression: requirement-002
- digest: requirement-002
- distribution: change-001, change-002
- framework: change-006
- hooks: change-003, change-005, bug-001
- init: change-005, bug-001
- install: change-001
- foundation: requirement-001
- skills: change-002, change-006
