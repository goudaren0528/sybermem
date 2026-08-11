# SyberMem Index

This file summarizes all project changes, decisions, requirements, and bug records.

---

## Key Conclusions

<!-- One-line core conclusion per record. Format: [id] #topic1 #topic2 — description (date) -->
<!-- add new conclusions here -->
- [bug-001] #hooks #init — Fixed init-project misclassifying missing hook files; exposed need for project-root resolution from subdirectories (2026-06-09)
- [bug-004] #distribution #hooks — Fixed a batch-A propagation gap where check_project_health.py still keyed on the legacy dual UserPromptSubmit hooks, so `/sybermem-update` would drag already-merged projects back to dual-hook; health check now treats a single user_prompt.py entry as fresh and offers a non-destructive dual→single migration (2026-08-05)
- [bug-2c0914a052994c239bdc40f2917209d8] #quality #retrieval — Unified terminal record statuses into a single TERMINAL_STATUSES set so status open-detection and lifecycle classification both treat fixed/resolved/completed/done/closed as closed, fixing fixed bugs being reported as open (2026-08-07)
- [bug-2ffd869fce244c4c8d7e1305e674c60d] #quality #search #retrieval — Fixed retrieval RECORD_ID_RE to accept UUID-backed ids via a shared RECORD_ID_SUFFIX, so superseded_by/fixes successor guidance resolves for records created after the UUID migration (2026-08-07)
- [bug-3a161fa287bd425daf3e685e0f13f6b1] #recall #hooks #quality #distribution — Routed the merged user_prompt.py recall through high_signal_recall_hints + log_recall_event so the E1 high-signal gate and E6 inject/abstain logging actually run on the wired production hook instead of only in the standalone task_recall.main (2026-08-10)
- [bug-9e13ab868e444035a97ae77dbbee5122] #distribution #hooks #quality — Made digest-template.md content-checked in the health check \(stale when missing coverage_hash\) so /sybermem-update replaces stale copies, closing a distribution-chain gap that would have stranded the coverage_hash capability on fresh installs only (2026-08-07)
- [change-001] #distribution #install — Added one-liner remote install scripts \(curl/irm\) to simplify new user onboarding, no clone needed (2026-05-12)
- [change-002] #distribution #skills — Moved SyberMem skill source to packages/claude-skills; eliminates duplicate skill loading from global installs (2026-05-12)
- [change-003] #automation #hooks — Added default project-level auto/remind hook template with stop-hook helper for lightweight change records (2026-05-13)
- [change-005] #hooks #init — Refreshed project instruction files to auto/remind mode and added project-level settings + stop-hook helper (2026-05-13)
- [change-006] #framework #skills — Repaired missing .claude/settings.json, fixed INDEX.md omissions, refreshed phase index, upgraded all 8 skills with HARD-GATE + numbered checklist (2026-06-16)
- [change-008] #automation #distribution #hooks — Added Claude Code plugin metadata and lifecycle hook delegators so SyberMem can install as a plugin without breaking existing project-managed hook files (2026-06-18)
- [change-010] #digest #distribution #lifecycle #relations #search — Transformed SyberMem from v1 \(record+group+compress\) to v2 \(lifecycle-aware, retrieval-capable, relation-linked, topic-compressible, multi-platform\) in a single session covering 6 capability rounds (2026-06-22)
- [change-045] #distribution #hooks #quality #search — Executed audit-driven P0/P1: exposed `sybermem resume` CLI \(was implemented but unreachable\), made search no-root failure explicit while keeping the hook path silent, merged the two prompt hooks into one process \(~491ms→~297ms\), and added LICENSE + CI + cli→core dependency + single-source VERSION so the repo reaches an OSS-trust baseline (2026-08-05)
- [change-047] #hooks #quality — Stopped the auto stop-hook from writing per-stop markdown records + INDEX rows; auto-trails now go to a bounded rolling `.auto-trail.jsonl` journal so low-signal noise stays out of the canonical corpus, while the existing 26 records stay untouched to preserve digest/publish/status semantics (2026-08-05)
- [change-048] #distribution #quality #search — Second-tier audit follow-ups: unified Codex/Cursor/Kimi manifests + CI drift gates + honest platform matrix \(§4\), unified `Stage→Phase Digests` terminology + install-order doc fix \(§3\), and query-time workspace stale detection warning when indexed HEAD lags current HEAD \(§2-e\) (2026-08-05)
- [change-049] #quality #skills — Extended the human quick-guide layer to search/using-sybermem/record/update so all five ceremony-heavy skills now open with a plain-language overview marked "not the execution contract", lowering human cognitive load without changing the authoritative machine contracts (2026-08-05)
- [change-087966eda55f40a0aada0f86dd290e29] #usability #quality — Added a deterministic 3-4 line resume brief \(phase/confidence, latest work, open items, suggested next\) so fast resume reads like a briefing instead of a field dump, without changing the authoritative structured fields (2026-08-07)
- [change-358d10ce63284f98a90e8da4bbbf8079] #usability #skills — Added an opt-in sample record step to init-project for brand-new projects so new users immediately see a record and can try resume, without violating the scan-but-do-not-auto-create-records invariant (2026-08-07)
- [change-36b8a2dca14a4d459c3ff964eb5ea5f5] #recall #quality #hooks — Generalized the recall debug log to record both which records were injected \(with match type\) and why recall abstained, giving a bounded local baseline to measure recall quality and tune thresholds (2026-08-07)
- [change-619fadbe5ba0498f9c25a51f83f9c78c] #governance #retrieval #quality — Let records optionally declare source_kind/authority/lifecycle in frontmatter \(recognized values only\) so trust classification no longer depends solely on fragile path/marker/status inference, while keeping inference as the zero-change default for legacy records (2026-08-07)
- [change-6a3ab8a0e44e4c41843b66bde8b7134a] #architecture #collaboration #quality — Added UUID-backed canonical record IDs and derived INDEX build/check commands so parallel record creation merges safely while legacy numeric records remain readable. (2026-08-07)
- [change-71c1f4bdc01a4b6cb07731667f1c08c7] #quality #distribution #index — SyberMem derived INDEX generation now validates untrusted record metadata, escapes Markdown safely, and update/install propagation carries the UUID-backed record contract end to end. (2026-08-07)
- [change-72be196fdec34faf93c9fee00ce26881] #recall #search #quality — Added match-specificity \(record-id>relation>topic>keyword\) to the compact recall sort ahead of freshness/recency so a precisely-matched record is no longer buried under a newer, generically-matched one (2026-08-07)
- [change-77f02b5fc9f34d7abd2987c7a89c0d7a] #usability #cli #distribution — Added `sybermem record id --type <type>` CLI command and re-exported generate_record_id from the package root so record creation has a discoverable entrypoint instead of forcing callers to guess a buried module path (2026-08-11)
- [change-88bfdebb0f2f4e31bb7b0e70857c288d] #usability #hooks #automation — Added a commit-gap record reminder to the SessionStart context so unrecorded work surfaces proactively, because record timeliness is what keeps reasons and impact from evaporating across sessions (2026-08-07)
- [change-895dad61b374427586a8b14df4c7281e] #governance #retrieval — Confirmed and tested that a record's declared lifecycle:archived frontmatter is authoritative without any INDEX-derived flag, so archival truth lives in the canonical record rather than in a derived index section (2026-08-07)
- [change-8fd6b65d1a0940f592c2179f55f8801d] #distribution #quality #init — Refreshed global SyberMem skills, launchers, and Core/CLI runtime, then verified this project's managed files are fresh so upgraded behavior propagates without overwriting custom configuration. (2026-08-07)
- [change-a6dd46baa8994962a257a43e1a73daee] #recall #search #quality — Restricted automatic task-recall injection to high-signal matches \(record-id/relation/score>=12\) and logged abstention reasons, because wrong hot-path hints cost more trust than missed ones (2026-08-07)
- [change-afab61686c2e4311b517e61f902ec34b] #usability #cli #quality — Added `sybermem next-step` wrapping the core router and made using-sybermem present its output as the authoritative recommendation, so the single advisory entrypoint stops re-deriving routing by AI and can no longer drift from resume (2026-08-07)
- [change-b135cb2e65a24808aaef1f3007acee43] #usability #skills — Added a fast path to the record skill that writes a single unambiguous record in one pass from context, skipping per-item confirmation friction while keeping the same HARD-GATE completion guarantees (2026-08-07)
- [change-b70ea980b0934358aad0ba47b64bff33] #digest #quality #search — Added a deterministic coverage_hash check that mechanically flags a digest as stale when its declared source records change, so AI-authored summaries can no longer read as authoritative after drifting (2026-08-07)
- [change-ba981e99b2b2413787fe94a20bc1d22f] #digest #distribution #quality — Completed the E3 skill-side work so the digest template carries a real computed coverage_hash and the digest skill instructs computing it exactly as core does, making mechanical stale-digest detection actually fire in production (2026-08-07)
- [change-be55f3f0c00e4172b45822a398c3316a] #recall #search #quality — Added an opt-in pure-Python char n-gram vector recall supplement so project search can recover synonym/rephrased/typo misses that exact-term lexical scoring drops, without new dependencies, without changing default behavior, and without ever auto-injecting on the hot path (2026-08-07)
- [change-dcdc1324b2f340c1acb470df990a37c0] #governance #quality — Relabeled the publish preview hash as "memory source hash" with an explicit scope note \(stale-preview guard, not a full publish-safety proof\) in user-facing text, without renaming the stable persisted field key (2026-08-07)
- [decision-003] #architecture #quality — Consciously deferred 3 of 4 remaining audit follow-ups \(real CI green, batch-C auto-trail cleanup, non-core platform runtime\) with documented revisit triggers, and did the low-risk skill-slimming variant \(human quick-guide layer over the preserved machine contract, piloted on init-project\) (2026-08-05)
- [requirement-001] #architecture #foundation — Adopted ADR system: four category directories + INDEX master index + templates + skill automation (2026-05-08)
- [requirement-002] #compression #digest — Identified need for persistent phase summary/compression layer to prevent understanding cost from growing linearly with records (2026-06-05)

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

| ID | Date | Title | Status | Link |
|----|------|-------|--------|------|
<!-- add new records here -->
| change-001 | 2026-05-12 | Add remote install scripts for one-liner installation | implemented | [link](changes/2026-05-12-001-add-remote-install-scripts.md) |
| change-002 | 2026-05-12 | Migrate global skill source to packages directory | implemented | [link](changes/2026-05-12-002-migrate-global-skill-source-to-packages.md) |
| change-003 | 2026-05-13 | Add auto change hook template | implemented | [link](changes/2026-05-13-003-add-auto-change-hook-template.md) |
| change-005 | 2026-05-13 | Refresh project instructions and add auto record hook files | implemented | [link](changes/2026-05-13-005-refresh-project-instructions-and-add-auto-record-hook-files.md) |
| change-006 | 2026-06-16 | SyberMem framework hardening and project repair | implemented | [link](changes/2026-06-16-006-sybermem-framework-hardening-and-project-repair.md) |
| change-007 | 2026-06-18 | marketplace plugin hooks and more | implemented | [link](changes/2026-06-18-007-marketplace-plugin-hooks-and-more.md) |
| change-008 | 2026-06-18 | Add Claude Code plugin skeleton | implemented | [link](changes/2026-06-18-008-add-claude-code-plugin-skeleton.md) |
| change-009 | 2026-06-19 | marketplace | implemented | [link](changes/2026-06-19-009-marketplace.md) |
| change-010 | 2026-06-22 | SyberMem v2 — lifecycle layer, search, relations, theme digest, and platform ecosystem | implemented | [link](changes/2026-06-22-010-sybermem-v2-lifecycle-search-relations-theme-digest-platform.md) |
| change-011 | 2026-06-29 | skill skill | implemented | [link](changes/2026-06-29-011-skill-skill.md) |
| change-012 | 2026-06-30 | skill skill superpowers skill design analysis | implemented | [link](changes/2026-06-30-012-skill-skill-superpowers-skill-design-analysis.md) |
| change-013 | 2026-06-30 | skill superpowers skill design analysis | implemented | [link](changes/2026-06-30-013-skill-superpowers-skill-design-analysis.md) |
| change-014 | 2026-06-30 | init cpython 310 main cpython 310 init cpython 310 and more | implemented | [link](changes/2026-06-30-014-init-cpython-310-main-cpython-310-init-cpython-310-and-more.md) |
| change-015 | 2026-06-30 | readme en readme 2026 06 30 sybermem core phase1 and more | implemented | [link](changes/2026-06-30-015-readme-en-readme-2026-06-30-sybermem-core-phase1-and-more.md) |
| change-016 | 2026-06-30 | init main pkg info and more | implemented | [link](changes/2026-06-30-016-init-main-pkg-info-and-more.md) |
| change-017 | 2026-07-01 | init cpython 310 main cpython 310 init cpython 310 and more | implemented | [link](changes/2026-07-01-017-init-cpython-310-main-cpython-310-init-cpython-310-and-more.md) |
| change-018 | 2026-07-01 | publish | implemented | [link](changes/2026-07-01-018-publish.md) |
| change-019 | 2026-07-02 | init main pkg info and more | implemented | [link](changes/2026-07-02-019-init-main-pkg-info-and-more.md) |
| change-020 | 2026-07-02 | main project publish and more | implemented | [link](changes/2026-07-02-020-main-project-publish-and-more.md) |
| change-021 | 2026-07-02 | main project publish and more | implemented | [link](changes/2026-07-02-021-main-project-publish-and-more.md) |
| change-022 | 2026-07-02 | init cpython 310 main cpython 310 init cpython 310 and more | implemented | [link](changes/2026-07-02-022-init-cpython-310-main-cpython-310-init-cpython-310-and-more.md) |
| change-023 | 2026-07-02 | Build Team memory publication and management layer | implemented | [link](changes/2026-07-02-023-build-team-memory-publication-and-management-layer.md) |
| change-024 | 2026-07-02 | init main pkg info and more | implemented | [link](changes/2026-07-02-024-init-main-pkg-info-and-more.md) |
| change-025 | 2026-07-03 | init main pkg info and more | implemented | [link](changes/2026-07-03-025-init-main-pkg-info-and-more.md) |
| change-026 | 2026-07-03 | Expose Team workflows as first-class SyberMem skills | implemented | [link](changes/2026-07-03-026-expose-team-workflows-as-first-class-sybermem-skills.md) |
| change-027 | 2026-07-03 | detect record intent | implemented | [link](changes/2026-07-03-027-detect-record-intent.md) |
| change-028 | 2026-07-07 | init cpython 310 identity cpython 310 next step router cpython 310 and more | implemented | [link](changes/2026-07-07-028-init-cpython-310-identity-cpython-310-next-step-router-cpython-310-and-more.md) |
| change-029 | 2026-07-07 | init cpython 310 main cpython 310 init cpython 310 and more | implemented | [link](changes/2026-07-07-029-init-cpython-310-main-cpython-310-init-cpython-310-and-more.md) |
| change-030 | 2026-07-07 | Align init-project propagation with Team and reminder workflows | implemented | [link](changes/2026-07-07-030-align-init-project-propagation-with-team-and-reminder-workflows.md) |
| change-031 | 2026-07-10 | init cpython 310 uninstall cpython 310 | implemented | [link](changes/2026-07-10-031-init-cpython-310-uninstall-cpython-310.md) |
| change-032 | 2026-07-10 | Injection slimming, core quality fixes, and distribution chain hardening | implemented | [link](changes/2026-07-10-032-injection-slimming-core-quality-and-distribution-hardening.md) |
| change-033 | 2026-08-04 | Improve natural-language search matching | implemented | [link](changes/2026-08-04-033-improve-natural-language-search-matching.md) |
| change-034 | 2026-08-04 | ses 033df0fbcffeqyba0s73awy2uf | implemented | [link](changes/2026-08-04-034-ses-033df0fbcffeqyba0s73awy2uf.md) |
| change-035 | 2026-08-04 | ses 0336c3bd8ffetz577almie35yc ses 0336eef75ffe1ilmviizik84kc ses 0336fc40fffebm7dwdusugh7wk and more | implemented | [link](changes/2026-08-04-035-ses-0336c3bd8ffetz577almie35yc-ses-0336eef75ffe1ilmviizik84kc-ses-0336fc40fffebm7dwdusugh7wk-and-more.md) |
| change-036 | 2026-08-04 | Upgrade source-aware task recall packets | implemented | [link](changes/2026-08-04-036-upgrade-source-aware-task-recall-packets.md) |
| change-037 | 2026-08-04 | Add Team publish preview trust envelope | implemented | [link](changes/2026-08-04-037-add-team-publish-preview-trust-envelope.md) |
| change-038 | 2026-08-04 | install install readme en and more | implemented | [link](changes/2026-08-04-038-install-install-readme-en-and-more.md) |
| change-039 | 2026-08-04 | Implement continuity and trust experience | implemented | [link](changes/2026-08-04-039-implement-continuity-trust-experience.md) |
| change-040 | 2026-08-04 | Fix workspace search completeness | implemented | [link](changes/2026-08-04-040-fix-workspace-search-completeness.md) |
| change-041 | 2026-08-04 | Close continuity and trust review findings | implemented | [link](changes/2026-08-04-041-close-continuity-trust-review-findings.md) |
| change-042 | 2026-08-04 | install install readme en and more | implemented | [link](changes/2026-08-04-042-install-install-readme-en-and-more.md) |
| change-043 | 2026-08-05 | agents md claude md | implemented | [link](changes/2026-08-05-043-agents-md-claude-md.md) |
| change-044 | 2026-08-05 | agents md claude md 2026 08 05 sybermem comprehensive audit | implemented | [link](changes/2026-08-05-044-agents-md-claude-md-2026-08-05-sybermem-comprehensive-audit.md) |
| change-045 | 2026-08-05 | Audit-driven P0/P1 — dual-track alignment, hot-path efficiency, OSS readiness | implemented | [link](changes/2026-08-05-045-audit-driven-p0-p1-dual-track-efficiency-oss-readiness.md) |
| change-046 | 2026-08-05 | gitignore readme en readme and more | implemented | [link](changes/2026-08-05-046-gitignore-readme-en-readme-and-more.md) |
| change-047 | 2026-08-05 | Auto-trail rolling journal — stop writing per-stop markdown records \(batch B\) | implemented | [link](changes/2026-08-05-047-auto-trail-rolling-journal-batch-b.md) |
| change-048 | 2026-08-05 | Distribution consistency, UX terminology, and workspace stale detection \(batches D/E/F\) | implemented | [link](changes/2026-08-05-048-distribution-ux-workspace-stale-batches-def.md) |
| change-049 | 2026-08-05 | Extend human quick-guide layer to the remaining ceremony-heavy skills | implemented | [link](changes/2026-08-05-049-extend-skill-quick-guide-layer.md) |
| change-087966eda55f40a0aada0f86dd290e29 | 2026-08-07 | Resume leads with a human-readable brief | implemented | [link](changes/2026-08-07-change-087966eda55f40a0aada0f86dd290e29-resume-brief.md) |
| change-358d10ce63284f98a90e8da4bbbf8079 | 2026-08-07 | Init-project offers an opt-in first sample record on fresh projects | implemented | [link](changes/2026-08-07-change-358d10ce63284f98a90e8da4bbbf8079-init-sample-record.md) |
| change-36b8a2dca14a4d459c3ff964eb5ea5f5 | 2026-08-07 | Recall observability logs inject and abstain events | implemented | [link](changes/2026-08-07-change-36b8a2dca14a4d459c3ff964eb5ea5f5-recall-observability.md) |
| change-619fadbe5ba0498f9c25a51f83f9c78c | 2026-08-07 | Trust metadata can be declared in frontmatter, with inference as fallback | implemented | [link](changes/2026-08-07-change-619fadbe5ba0498f9c25a51f83f9c78c-declared-trust-metadata.md) |
| change-6a3ab8a0e44e4c41843b66bde8b7134a | 2026-08-07 | UUID-backed record IDs and derived project index | implemented | [link](changes/2026-08-07-change-6a3ab8a0e44e4c41843b66bde8b7134a-uuid-record-ids-derived-index.md) |
| change-71c1f4bdc01a4b6cb07731667f1c08c7 | 2026-08-07 | Close derived INDEX review blockers | implemented | [link](changes/2026-08-07-change-71c1f4bdc01a4b6cb07731667f1c08c7-close-derived-index-review-blockers.md) |
| change-72be196fdec34faf93c9fee00ce26881 | 2026-08-07 | Rank compact recall by match specificity before freshness | implemented | [link](changes/2026-08-07-change-72be196fdec34faf93c9fee00ce26881-recall-specificity-ranking.md) |
| change-77f02b5fc9f34d7abd2987c7a89c0d7a | 2026-08-11 | Make record-id generation discoverable via CLI command and package export | implemented | [link](changes/2026-08-11-change-77f02b5fc9f34d7abd2987c7a89c0d7a-record-id-discoverable-entrypoint.md) |
| change-88bfdebb0f2f4e31bb7b0e70857c288d | 2026-08-07 | SessionStart proactively reminds when commits accrue since the last record | implemented | [link](changes/2026-08-07-change-88bfdebb0f2f4e31bb7b0e70857c288d-session-start-record-reminder.md) |
| change-895dad61b374427586a8b14df4c7281e | 2026-08-07 | Lock archived-lifecycle declaration as canonical truth | implemented | [link](changes/2026-08-07-change-895dad61b374427586a8b14df4c7281e-archived-declaration-truth.md) |
| change-8fd6b65d1a0940f592c2179f55f8801d | 2026-08-07 | Refresh global skills and verify project propagation | implemented | [link](changes/2026-08-07-change-8fd6b65d1a0940f592c2179f55f8801d-global-refresh-project-propagation.md) |
| change-a6dd46baa8994962a257a43e1a73daee | 2026-08-07 | High-signal recall gate for automatic prompt-time injection | implemented | [link](changes/2026-08-07-change-a6dd46baa8994962a257a43e1a73daee-high-signal-recall-gate.md) |
| change-afab61686c2e4311b517e61f902ec34b | 2026-08-07 | Expose deterministic next-step router as a CLI and route using-sybermem through it | implemented | [link](changes/2026-08-07-change-afab61686c2e4311b517e61f902ec34b-next-step-cli-single-entrypoint.md) |
| change-b135cb2e65a24808aaef1f3007acee43 | 2026-08-07 | Record skill offers a one-shot fast path | implemented | [link](changes/2026-08-07-change-b135cb2e65a24808aaef1f3007acee43-record-fast-path.md) |
| change-b70ea980b0934358aad0ba47b64bff33 | 2026-08-07 | Mechanical digest coverage staleness detection | implemented | [link](changes/2026-08-07-change-b70ea980b0934358aad0ba47b64bff33-digest-coverage-staleness.md) |
| change-ba981e99b2b2413787fe94a20bc1d22f | 2026-08-07 | Digest skill and template now emit the computed coverage_hash | implemented | [link](changes/2026-08-07-change-ba981e99b2b2413787fe94a20bc1d22f-digest-coverage-hash-skill.md) |
| change-be55f3f0c00e4172b45822a398c3316a | 2026-08-07 | Opt-in zero-dependency semantic recall supplement | implemented | [link](changes/2026-08-07-change-be55f3f0c00e4172b45822a398c3316a-opt-in-semantic-recall.md) |
| change-dcdc1324b2f340c1acb470df990a37c0 | 2026-08-07 | Honest labeling for the publish preview memory source hash | implemented | [link](changes/2026-08-07-change-dcdc1324b2f340c1acb470df990a37c0-publish-hash-honest-labeling.md) |

## Technical Decisions

| ID | Date | Title | Status | Link |
|----|------|-------|--------|------|
<!-- add new records here -->
| decision-001 | 2026-06-30 | Team MVP should precede full Hub experience for Requirement-003 | decided | [link](decisions/2026-06-30-001-team-mvp-before-full-hub-experience.md) |
| decision-002 | 2026-08-04 | Adopt a lightweight continuity and trust experience layer | accepted | [link](decisions/2026-08-04-002-sybermem-continuity-trust-experience.md) |
| decision-003 | 2026-08-05 | Deferral decisions for the four remaining audit follow-ups + skill quick-guide pilot | decided | [link](decisions/2026-08-05-003-audit-followup-deferral-decisions.md) |

## Requirements / Discussions

| ID | Date | Title | Source | Priority | Link |
|----|------|-------|--------|----------|------|
<!-- add new records here -->
| requirement-001 | 2026-05-08 | 创建ADR项目规范系统 | 内部讨论 | high | [link](requirements/2026-05-08-001-%E5%88%9B%E5%BB%BAADR%E9%A1%B9%E7%9B%AE%E8%A7%84%E8%8C%83%E7%B3%BB%E7%BB%9F.md) |
| requirement-002 | 2026-06-05 | 阶段性总结与记录压缩需求 | 用户使用反馈 | high | [link](requirements/2026-06-05-002-%E9%98%B6%E6%AE%B5%E6%80%A7%E6%80%BB%E7%BB%93%E4%B8%8E%E8%AE%B0%E5%BD%95%E5%8E%8B%E7%BC%A9%E9%9C%80%E6%B1%82.md) |
| requirement-003 | 2026-06-29 | SyberMem 跨项目与团队记忆扩展方案 | 内部方案评审 | high | [link](requirements/2026-06-29-003-sybermem-cross-project-team-memory-extension.md) |

## Bug Fix Records

| ID | Date | Title | Severity | Link |
|----|------|-------|----------|------|
<!-- add new records here -->
| bug-001 | 2026-06-09 | init-project misclassifies missing hook file as custom/kept | medium | [link](bugs/2026-06-09-001-init-project-misclassifies-missing-hook-file.md) |
| bug-002 | 2026-08-04 | Publish preview bootstrap and JSON output leaks | high | [link](bugs/2026-08-04-002-publish-preview-bootstrap-json-output.md) |
| bug-003 | 2026-08-04 | Publish trust summary and skill flow gaps | high | [link](bugs/2026-08-04-003-publish-trust-summary-and-skill-flow-gaps.md) |
| bug-004 | 2026-08-05 |  | high | [link](bugs/2026-08-05-004-merged-hook-not-propagated-by-health-check.md) |
| bug-2c0914a052994c239bdc40f2917209d8 | 2026-08-07 | Bugs with status "fixed" were miscounted as open | medium | [link](bugs/2026-08-07-bug-2c0914a052994c239bdc40f2917209d8-fixed-status-counted-open.md) |
| bug-2ffd869fce244c4c8d7e1305e674c60d | 2026-08-07 | Successor guidance regex only matched numeric ids, breaking UUID records | high | [link](bugs/2026-08-07-bug-2ffd869fce244c4c8d7e1305e674c60d-uuid-successor-guidance-regex.md) |
| bug-3a161fa287bd425daf3e685e0f13f6b1 | 2026-08-10 | Merged prompt hook bypassed the high-signal recall gate and observability | high | [link](bugs/2026-08-10-bug-3a161fa287bd425daf3e685e0f13f6b1-merged-hook-bypassed-recall-gate.md) |
| bug-9e13ab868e444035a97ae77dbbee5122 | 2026-08-07 | Digest template was existence-checked only, so template improvements never propagated to existing projects | high | [link](bugs/2026-08-07-bug-9e13ab868e444035a97ae77dbbee5122-digest-template-not-propagated.md) |

## Usage

- **changes/**: Record all feature changes
- **decisions/**: Record important technical decisions and their rationale
- **requirements/**: Record discussion processes, requirement sources, and design reasoning
- **bugs/**: Record bug analysis and fix approaches
- **analysis/phase-index.md**: Persistent project phase analysis state used to track candidates, confirmed phases, and incremental analysis progress

When adding records, create the canonical record file first, then run `sybermem project index build` and `sybermem project index check`.

---

## Topic Index

<!-- Auto-maintained: maps topic tags to record IDs for fast lookup -->
- architecture: change-6a3ab8a0e44e4c41843b66bde8b7134a, decision-001, decision-002, decision-003, requirement-001, requirement-003
- automation: change-003, change-008, change-88bfdebb0f2f4e31bb7b0e70857c288d
- cli: change-77f02b5fc9f34d7abd2987c7a89c0d7a, change-afab61686c2e4311b517e61f902ec34b
- collaboration: change-023, change-026, change-6a3ab8a0e44e4c41843b66bde8b7134a, decision-001, requirement-003
- compression: requirement-002
- digest: change-010, change-023, change-b70ea980b0934358aad0ba47b64bff33, change-ba981e99b2b2413787fe94a20bc1d22f, requirement-002
- distribution: bug-004, bug-3a161fa287bd425daf3e685e0f13f6b1, bug-9e13ab868e444035a97ae77dbbee5122, change-001, change-002, change-008, change-010, change-045, change-048, change-71c1f4bdc01a4b6cb07731667f1c08c7, change-77f02b5fc9f34d7abd2987c7a89c0d7a, change-8fd6b65d1a0940f592c2179f55f8801d, change-ba981e99b2b2413787fe94a20bc1d22f
- foundation: requirement-001
- framework: change-006
- governance: change-619fadbe5ba0498f9c25a51f83f9c78c, change-895dad61b374427586a8b14df4c7281e, change-dcdc1324b2f340c1acb470df990a37c0
- hooks: bug-001, bug-004, bug-3a161fa287bd425daf3e685e0f13f6b1, bug-9e13ab868e444035a97ae77dbbee5122, change-003, change-005, change-008, change-030, change-036, change-041, change-045, change-047, change-36b8a2dca14a4d459c3ff964eb5ea5f5, change-88bfdebb0f2f4e31bb7b0e70857c288d
- hub: change-040, change-041, requirement-003
- index: change-71c1f4bdc01a4b6cb07731667f1c08c7
- init: bug-001, change-005, change-030, change-8fd6b65d1a0940f592c2179f55f8801d
- install: change-001
- lifecycle: change-010
- quality: bug-002, bug-003, bug-2c0914a052994c239bdc40f2917209d8, bug-2ffd869fce244c4c8d7e1305e674c60d, bug-3a161fa287bd425daf3e685e0f13f6b1, bug-9e13ab868e444035a97ae77dbbee5122, change-033, change-036, change-037, change-039, change-040, change-041, change-045, change-047, change-048, change-049, change-087966eda55f40a0aada0f86dd290e29, change-36b8a2dca14a4d459c3ff964eb5ea5f5, change-619fadbe5ba0498f9c25a51f83f9c78c, change-6a3ab8a0e44e4c41843b66bde8b7134a, change-71c1f4bdc01a4b6cb07731667f1c08c7, change-72be196fdec34faf93c9fee00ce26881, change-8fd6b65d1a0940f592c2179f55f8801d, change-a6dd46baa8994962a257a43e1a73daee, change-afab61686c2e4311b517e61f902ec34b, change-b70ea980b0934358aad0ba47b64bff33, change-ba981e99b2b2413787fe94a20bc1d22f, change-be55f3f0c00e4172b45822a398c3316a, change-dcdc1324b2f340c1acb470df990a37c0, decision-002, decision-003
- recall: bug-3a161fa287bd425daf3e685e0f13f6b1, change-36b8a2dca14a4d459c3ff964eb5ea5f5, change-72be196fdec34faf93c9fee00ce26881, change-a6dd46baa8994962a257a43e1a73daee, change-be55f3f0c00e4172b45822a398c3316a
- relations: change-010
- retrieval: bug-2c0914a052994c239bdc40f2917209d8, bug-2ffd869fce244c4c8d7e1305e674c60d, change-619fadbe5ba0498f9c25a51f83f9c78c, change-895dad61b374427586a8b14df4c7281e
- search: bug-2ffd869fce244c4c8d7e1305e674c60d, change-010, change-033, change-036, change-039, change-040, change-041, change-045, change-048, change-72be196fdec34faf93c9fee00ce26881, change-a6dd46baa8994962a257a43e1a73daee, change-b70ea980b0934358aad0ba47b64bff33, change-be55f3f0c00e4172b45822a398c3316a, decision-002
- skills: bug-003, change-002, change-006, change-026, change-041, change-049, change-358d10ce63284f98a90e8da4bbbf8079, change-b135cb2e65a24808aaef1f3007acee43
- team: bug-002, bug-003, change-023, change-026, change-030, change-037, change-039, change-041, decision-001, decision-002, requirement-003
- topic: change-032
- usability: change-087966eda55f40a0aada0f86dd290e29, change-358d10ce63284f98a90e8da4bbbf8079, change-77f02b5fc9f34d7abd2987c7a89c0d7a, change-88bfdebb0f2f4e31bb7b0e70857c288d, change-afab61686c2e4311b517e61f902ec34b, change-b135cb2e65a24808aaef1f3007acee43
