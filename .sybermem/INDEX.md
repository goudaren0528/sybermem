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
- [change-045] #quality #distribution #search #hooks — Executed audit-driven P0/P1: exposed `sybermem resume` CLI (was implemented but unreachable), made search no-root failure explicit while keeping the hook path silent, merged the two prompt hooks into one process (~491ms→~297ms), and added LICENSE + CI + cli→core dependency + single-source VERSION so the repo reaches an OSS-trust baseline (2026-08-05)
- [change-047] #hooks #quality — Stopped the auto stop-hook from writing per-stop markdown records + INDEX rows; auto-trails now go to a bounded rolling `.auto-trail.jsonl` journal so low-signal noise stays out of the canonical corpus, while the existing 26 records stay untouched to preserve digest/publish/status semantics (2026-08-05)
<!-- add new conclusions here -->

---

## Archived Conclusions

<!-- Not injected at session start; findable via /sybermem-search -->
<!-- Suffix each line with: [superseded by <id>] or [compressed in <id>] or [archived] -->
- [change-007] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-18) [archived]
- [change-009] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-19) [archived]
- [change-011] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-29) [archived] [compressed in digest-004]
- [change-012] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30) [archived] [compressed in digest-004]
- [change-013] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30) [archived] [compressed in digest-004]
- [change-014] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30) [archived]
- [change-015] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30) [archived] [compressed in digest-005]
- [change-016] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-06-30) [archived]
- [change-017] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-01) [archived]
- [change-018] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-01) [archived] [compressed in digest-005]
- [change-019] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-02) [archived]
- [change-020] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-02) [archived]
- [change-021] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-02) [archived]
- [change-022] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-02) [archived]
- [change-024] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-02) [archived]
- [change-025] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-03) [archived]
- [change-027] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-03) [archived] [compressed in digest-004]
- [change-028] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-07) [archived]
- [change-029] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-07) [archived]
- [change-031] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording (2026-07-10) [archived]
- [requirement-003] #architecture #collaboration #hub #team — Defined SyberMem cross-project and team memory extension: three-scope model (Project/Hub/Team), Skill-vs-Core separation, phased implementation from Hub MVP to Team Git (2026-06-29) [compressed in digest-005]
- [decision-001] #architecture #collaboration #team — Chose to prioritize a minimal Team Git repository MVP before fully polishing the personal Hub experience, because unified team-managed storage is the real near-term value of Requirement-003 (2026-06-30) [compressed in digest-005]
- [change-023] #team #collaboration #digest — Built the end-to-end Team memory publication, summary, and digest-history pipeline so multiple projects can publish into a shared Team repo and management agents can consume it directly (2026-07-02) [compressed in digest-005]
- [change-026] #team #skills #collaboration — Exposed Team publish and Team summary as first-class SyberMem skills so Team workflows now match the project-level slash-command experience instead of requiring raw CLI usage (2026-07-03) [compressed in digest-005]
- [change-030] #team #hooks #init — Aligned init-project propagation, templates, and health checks with the new Team workflows and reminder-first record-intent behavior so installs and updates now carry those capabilities consistently (2026-07-07) [compressed in digest-005]
- [change-032] #injection #quality #distribution #uninstall — Slimmed CLAUDE.md/AGENTS.md injection from ~76 to ~22 lines, fixed 8 core quality issues (bug lifecycle, publish-summary contract, FTS5 search, router nudge loop, summary schema, English intent, stop hook threshold, search coverage), hardened distribution chain (template pollution, hardcoded paths, self-updating health check, old-template detection), and added two-layer uninstall model (2026-07-10) [compressed in digest-004]
- [change-033] #search #quality — Improved natural English multi-term and Chinese/CJK search matching with safe FTS fallback and extracted helpers so automatic recall is more relevant while `search.py` stays below the 250 pure-LOC ceiling (2026-08-04) [compressed in digest-006]
- [decision-002] #architecture #quality #search #team — Adopted a lightweight continuity and trust experience layer over existing records, retrieval, digests, relations, and Team publish to reduce restart friction without creating a second canonical memory system (2026-08-04) [compressed in digest-006]
- [change-036] #hooks #search #quality — Upgraded automatic task recall packets to source-aware bounded retrieval hints so recalled context is explainable without becoming instructions (2026-08-04) [compressed in digest-006]
- [change-037] #team #quality — Added a read-only Team publish preview trust envelope and stale-preview rejection so high-impact publication is reviewable without creating a second canonical store (2026-08-04) [compressed in digest-006]
- [bug-002] #team #quality — Fixed publish preview bootstrap side effects and JSON stdout leakage so read-only preview and machine-readable publish remain trustworthy (2026-08-04) [compressed in digest-006]
- [change-039] #quality #search #team — Implemented bounded project continuity, source-aware recall, safe record routing, correction guidance, and revision-aware Team publish so memory is easier to resume and trust without a second canonical store (2026-08-04) [compressed in digest-006]
- [bug-003] #team #quality #skills — Fixed Team publish trust summary, preview freshness, path diagnostics, and skill hash-flow gaps so high-impact publish is reviewable end to end (2026-08-04) [compressed in digest-006]
- [change-040] #search #quality #hub — Fixed workspace search completeness gaps so stale indexes become actionable, workspace guidance matches project search, digest freshness stays relation-scoped, and low-signal substring noise is suppressed (2026-08-04) [compressed in digest-006]
- [change-041] #quality #search #team — Closed continuity/trust review findings so Team publish, workspace recall, and Core-unavailable diagnostics are auditable and safe (2026-08-04) [compressed in digest-006]
<!-- add new archived conclusions here -->

---

## Phase Digests

| Number | Date | Title | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
| 001 | 2026-06-05 | sybermem v1 digest design phase | completed | 3 records | [link](digests/2026-06-05-001-sybermem-v1-digest-design-phase.md) |
| 002 | 2026-06-29 | foundation and distribution phase | completed | 3 records | [link](digests/2026-06-29-002-foundation-and-distribution-phase.md) |
| 003 | 2026-06-29 | platform ecosystem and plugin packaging phase | completed | 3 records | [link](digests/2026-06-29-003-platform-ecosystem-and-plugin-packaging-phase.md) |
| 004 | 2026-08-05 | skill and lifecycle quality hardening | completed | 5 records | [link](digests/2026-08-05-004-skill-and-lifecycle-quality-hardening.md) |
| 005 | 2026-08-05 | cli hub and team memory foundation | completed | 7 records | [link](digests/2026-08-05-005-cli-hub-and-team-memory-foundation.md) |
| 006 | 2026-08-05 | continuity and source-aware trust experience | completed | 9 records | [link](digests/2026-08-05-006-continuity-and-source-aware-trust-experience.md) |
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
| 017 | 2026-07-01 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-01-017-init-cpython-310-main-cpython-310-init-cpython-310-and-more.md) |
| 018 | 2026-07-01 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-01-018-publish.md) |
| 019 | 2026-07-02 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-02-019-init-main-pkg-info-and-more.md) |
| 020 | 2026-07-02 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-02-020-main-project-publish-and-more.md) |
| 021 | 2026-07-02 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-02-021-main-project-publish-and-more.md) |
| 022 | 2026-07-02 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-02-022-init-cpython-310-main-cpython-310-init-cpython-310-and-more.md) |
| 023 | 2026-07-02 | Build Team memory publication and management layer | implemented | [link](changes/2026-07-02-023-build-team-memory-publication-and-management-layer.md) |
| 024 | 2026-07-02 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-02-024-init-main-pkg-info-and-more.md) |
| 025 | 2026-07-03 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-03-025-init-main-pkg-info-and-more.md) |
| 026 | 2026-07-03 | Expose Team workflows as first-class SyberMem skills | implemented | [link](changes/2026-07-03-026-expose-team-workflows-as-first-class-sybermem-skills.md) |
| 027 | 2026-07-03 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-03-027-detect-record-intent.md) |
| 028 | 2026-07-07 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-07-028-init-cpython-310-identity-cpython-310-next-step-router-cpython-310-and-more.md) |
| 029 | 2026-07-07 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-07-029-init-cpython-310-main-cpython-310-init-cpython-310-and-more.md) |
| 030 | 2026-07-07 | Align init-project propagation with Team and reminder workflows | implemented | [link](changes/2026-07-07-030-align-init-project-propagation-with-team-and-reminder-workflows.md) |
| 031 | 2026-07-10 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-07-10-031-init-cpython-310-uninstall-cpython-310.md) |
| 032 | 2026-07-10 | Injection slimming, core quality fixes, and distribution chain hardening | implemented | [link](changes/2026-07-10-032-injection-slimming-core-quality-and-distribution-hardening.md) |
| 033 | 2026-08-04 | Improve natural-language search matching | implemented | [link](changes/2026-08-04-033-improve-natural-language-search-matching.md) |
| 034 | 2026-08-04 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-08-04-034-ses-033df0fbcffeqyba0s73awy2uf.md) |
| 035 | 2026-08-04 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-08-04-035-ses-0336c3bd8ffetz577almie35yc-ses-0336eef75ffe1ilmviizik84kc-ses-0336fc40fffebm7dwdusugh7wk-and-more.md) |
| 036 | 2026-08-04 | Upgrade source-aware task recall packets | implemented | [link](changes/2026-08-04-036-upgrade-source-aware-task-recall-packets.md) |
| 037 | 2026-08-04 | Add Team publish preview trust envelope | implemented | [link](changes/2026-08-04-037-add-team-publish-preview-trust-envelope.md) |
| 038 | 2026-08-04 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-08-04-038-install-install-readme-en-and-more.md) |
| 039 | 2026-08-04 | Implement continuity and trust experience | implemented | [link](changes/2026-08-04-039-implement-continuity-trust-experience.md) |
| 040 | 2026-08-04 | Fix workspace search completeness | implemented | [link](changes/2026-08-04-040-fix-workspace-search-completeness.md) |
| 041 | 2026-08-04 | Close continuity and trust review findings | implemented | [link](changes/2026-08-04-041-close-continuity-trust-review-findings.md) |
| 042 | 2026-08-04 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-08-04-042-install-install-readme-en-and-more.md) |
| 043 | 2026-08-04 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-08-04-043-gitignore-install-install-and-more.md) |
| 043 | 2026-08-05 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-08-05-043-agents-md-claude-md.md) |
| 044 | 2026-08-05 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-08-05-044-agents-md-claude-md-2026-08-05-sybermem-comprehensive-audit.md) |
| 045 | 2026-08-05 | Audit-driven P0/P1 — dual-track alignment, hot-path efficiency, OSS readiness | implemented | [link](changes/2026-08-05-045-audit-driven-p0-p1-dual-track-efficiency-oss-readiness.md) |
| 046 | 2026-08-05 | Auto-record workspace file changes on stop | implemented | [link](changes/2026-08-05-046-gitignore-readme-en-readme-and-more.md) |
| 047 | 2026-08-05 | Auto-trail rolling journal — stop writing per-stop markdown records (batch B) | implemented | [link](changes/2026-08-05-047-auto-trail-rolling-journal-batch-b.md) |
<!-- add new records here -->

---

## Technical Decisions

| Number | Date | Title | Status | Link |
|--------|------|-------|--------|------|
| 001 | 2026-06-30 | Team MVP should precede full Hub experience for Requirement-003 | decided | [link](decisions/2026-06-30-001-team-mvp-before-full-hub-experience.md) |
| 002 | 2026-08-04 | Adopt a lightweight continuity and trust experience layer | accepted | [link](decisions/2026-08-04-002-sybermem-continuity-trust-experience.md) |
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
| 002 | 2026-08-04 | Publish preview bootstrap and JSON output leaks | high | [link](bugs/2026-08-04-002-publish-preview-bootstrap-json-output.md) |
| 003 | 2026-08-04 | Publish trust summary and skill flow gaps | high | [link](bugs/2026-08-04-003-publish-trust-summary-and-skill-flow-gaps.md) |
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
- architecture: requirement-001, requirement-003, decision-001, decision-002
- automation: change-003, change-008
- collaboration: requirement-003, decision-001, change-023, change-026
- compression: requirement-002
- digest: requirement-002, change-010, change-023
- distribution: change-001, change-002, change-008, change-010, change-032, change-045
- framework: change-006
- hooks: change-003, change-005, bug-001, change-008, change-030, change-036, change-041, change-045, change-047
- hub: requirement-003, change-040, change-041
- init: change-005, bug-001, change-030
- injection: change-032
- install: change-001
- foundation: requirement-001
- lifecycle: change-010
- quality: change-032, change-033, decision-002, change-036, change-037, bug-002, change-039, bug-003, change-040, change-041, change-045, change-047
- relations: change-010
- search: change-010, change-033, decision-002, change-036, change-039, change-040, change-041, change-045
- skills: change-002, change-006, change-026, bug-003, change-041
- team: requirement-003, decision-001, decision-002, change-023, change-026, change-030, change-037, bug-002, change-039, bug-003, change-041
- uninstall: change-032
