# SyberMem Index

This file summarizes all project changes, decisions, requirements, and bug records.

---

## Key Conclusions

<!-- One-line core conclusion per record, AI reads this section at session start for project context -->
- [requirement-001] Adopted ADR system: four category directories (changes/decisions/requirements/bugs) + INDEX master index + templates + skill automation (2026-05-08)
- [change-001] Added one-liner remote install scripts (curl/irm) to simplify new user onboarding, no clone needed (2026-05-12)
- [change-002] Moved SyberMem skill source to packages/claude-skills and removed repo-local runnable skill copies, so global installs no longer duplicate project-loaded skills (2026-05-12)
- [change-003] Added a default project-level auto/remind hook template with a runnable stop-hook helper, so new projects can auto-write lightweight change records instead of relying only on reminders (2026-05-13)
- [bug-001] Fixed init-project misclassifying missing hook files as "custom/kept" by requiring mandatory file-system verification before classification; also identified the deeper need for project-root resolution from subdirectories (2026-06-09)
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
