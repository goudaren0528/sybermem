# SyberMem Index

This file summarizes all project changes, decisions, requirements, and bug records.

---

## Key Conclusions

<!-- One-line core conclusion per record. Format: [id] #topic1 #topic2 — description (date) -->
<!-- add new conclusions here -->
- [bug-146ffbf8c1d9415d9708e8f18b003971] #schema #retrieval #quality — Decision records authored with `supersedes` were silently parsed without the relation, breaking successor/current-truth guidance and relation recall; parser, derived inverse graph, and search scoring now support both directions compatibly (2026-08-25)
- [bug-17a87caf3b014254bdc0d284ad010540] #installer #windows #opencode — Fixed the Python updater to reuse an existing CLI venv so Windows OpenCode updates no longer fail on a locked venv python.exe. (2026-08-25)
- [change-0638a1012020456193d3b469506151af] #memory #observability #opencode — Added an OpenCode-first actual-injection journal, session outcomes, one prompt-time usage summary, and 7d/30d stats so users can inspect memory context cost and Edit Alignment evidence before budget controls are introduced. (2026-08-25)
- [change-0c35875b8fde4feb93837ce354533b9b] #team #distribution #refactor — Moved latest_phase_digest/latest_theme_digest out of the Team publish subsystem into a neutral digest_sources.py and repointed resume/next-step/publish, so non-Team digest-aware features no longer depend on Team code — zero behavior change, unblocking safe Team removal later (2026-08-25)
- [change-13b0a327e1544f3e8e5ac5d3992c5c97] #team #distribution #qa — Independent Oracle post-implementation review confirmed the Team removal is correct \(no residual refs, seam decoupled, contract removed, distribution + data-safe\) but flagged 2 P1s in the portfolio replacement + test coverage; both fixed and re-reviewed to GO (2026-08-25)
- [change-2011a3f2b21e40dbb926187ebae50cf8] #norm #opencode #architecture — Delivered the P0 closed loop for binding project norms — a first-class `norm` record type + constitution/scoped selector + `norms list` CLI + /sybermem-record crystallization + OpenCode startup constitution injection — so norms can be recorded distinctly and reliably govern later OpenCode work (2026-08-24)
- [change-2b4df42e0ff942718e9afef5897ecc4c] #distribution #security #qa — A second, stricter 5-lane review-work found 4 distribution/safety blockers \(stale-on-upgrade PowerShell manifest/remover copy, ancestor-symlink traversal + tampered-plugin-path in the managed remover, inaccurate README "team" tagline, stale OpenCode bundle\); all fixed and re-reviewed to all-PASS, making the Team removal releasable (2026-08-25)
- [change-2b9c79a39ea64b178c9902894cbd49fd] #team #distribution #refactor — Verified the non-Team status/routing/project paths are already robust without Team, made that explicit via deprecation docstrings, and added a regression test locking project_status\(\) publication.team=={} \(shape preserved\) for the deprecation window (2026-08-25)
- [change-374880d44753411096e8bd198bae6985] #habit #opencode #distribution — Habit injection stayed silent because the candidate-confirmation reminder was swallowed by a one-shot throttled toast \(never surfaced on Claude/Codex\) and the user-habit store was split across ~/.sybermem vs the launcher-forced ~/.claude/sybermem/cli; fixed by a single-source pending_habit_reminder surfaced on every host's SessionStart/startup context plus a per-session model-visible OpenCode nudge, and by unifying the home on ~/.sybermem with a one-time non-destructive legacy import. (2026-08-26)
- [change-3d8c9c844d5747c3b15e84838a2d4fe8] #norm #architecture #ux — Delivered norm P2 — Claude Code and Codex now inject the constitution at SessionStart and scoped norms at UserPromptSubmit \(reusing the norms-list CLI as single source of truth\), plus a same-scope conflict detector + `norms doctor` governance CLI, completing cross-host norm reach and drift protection (2026-08-24)
- [change-57a47bcef74841b6a454fe5e53d23b2f] #habit #opencode #ux — /sybermem-habit could not confirm candidates because the capture stored no statement \(only type/scope\) and only one overwritable candidate; fixed by storing a bounded, blocklist-filtered prompt summary on each candidate, moving to a bounded candidate LIST \(last 5, 10-day expiry, dedup by summary, stable candidate_id\), adding list_habit_candidates/discard_habit_candidate + CLI intent-discard, a default status view + one-step confirm/discard skill workflow, and a host dedup keyed on the candidate-set fingerprint — so daily-captured preferences are reviewable, confirmable, and discardable end to end. (2026-08-26)
- [change-5d2b321fcbd440b393bb2030376043de] #recall #search #observability — Recall Phase 1 now ranks key conclusions and path anchors while preserving the conservative auto-injection gate. (2026-08-27)
- [change-657dd8880ab24e889e1f3b2b1521ee3a] #team #distribution #refactor — Removed the entire Team memory subsystem \(core/cli/skills/schema/tests/docs/distribution\) as a breaking change and replaced its only useful capability with a read-only registry-based portfolio, leaving zero residual Team executable refs and never touching users' .sybermem/ history or external Team repos (2026-08-25)
- [change-6a3ab8a0e44e4c41843b66bde8b7134a] #architecture #collaboration #quality — Added UUID-backed canonical record IDs and derived INDEX build/check commands so parallel record creation merges safely while legacy numeric records remain readable. (2026-08-07)
- [change-71c1f4bdc01a4b6cb07731667f1c08c7] #quality #distribution #index — SyberMem derived INDEX generation now validates untrusted record metadata, escapes Markdown safely, and update/install propagation carries the UUID-backed record contract end to end. (2026-08-07)
- [change-76481099f07c4f1f9de150a0281fb58f] #digest #opencode #ux — SyberMem could detect a STALE digest \(coverage_hash\) but never "should make a NEW digest"; added digest_backlog \(uncovered records + age\), fixed the next-step dead condition that only fired before the first digest, and an OpenCode session.idle backlog toast — all fed by one core signal via digest status JSON (2026-08-24)
- [change-7f75f17f01cc4d249ca8468e7bbfec7d] #habit #opencode #ux — Habits were invisible because add_habit defaulted to compaction_ok while the prompt-time selector required prompt_ok_when_supported, and _terms\(\) never tokenized CJK so applies_to killed every Chinese context; fixed by defaulting to prompt-ok, CJK-aware weighted relevance, and a suggested_scope routing hint (2026-08-24)
- [change-7fd560c9a8414c8b9cde8ac842fbad0e] #memory #observability #opencode #quality #security — Review Work required the memory-usage journal to be secure, bounded, append-only on the prompt hot path, and semantically limited to real memory turns before the observability rollout could be considered handoff-ready. (2026-08-25)
- [change-878c029967b944cca3fc634c7148cf27] #codex #distribution #versioning — Codex additionalContext now carries explicit SyberMem markers and the distribution version is bumped to 0.1.1 so users can refresh project-local files after global updates. (2026-08-25)
- [change-9a18342f07a64925bad69cbff5b47f89] #digest #recall #observability — Delivered current digest conclusion injection and digest usage observability across Codex, Claude templates, OpenCode, Core, and docs so stable phase conclusions become model-visible and measurable without adding new memory infrastructure. (2026-08-25)
- [change-a40b6aaa5a864b049fd05dd861e283d4] #observability #opencode #distribution — Serialized OpenCode injection toasts through a FIFO queue with a minimum on-screen gap so same-tick multi-toasts no longer clobber each other, and added remote-version awareness that warns when GitHub main publishes a newer SyberMem than the machine has installed — because same-tick toasts were silently lost and users had no signal to re-install when a new version shipped. (2026-08-26)
- [change-b1aa5fc5d8d34d1fb15cb150ec70e655] #codex #observability #recall — Codex now writes bounded recall/memory observability and visible injection markers so memory-stats and Desktop users can verify prompt-time recall. (2026-09-01)
- [change-bcac35f53e004164adb47471d7cf094d] #norm #opencode #ux — Delivered norm P1 — per-prompt scoped-norm recall + compaction constitution reuse \(OpenCode\), memory-stats norm coverage, and digest-time emergent nomination of recurring constraints \(confirmation-first\) — so norms reach relevant work and recurring rules get proactively surfaced for crystallization (2026-08-24)
- [change-c2be7cced7eb4250b288606869f1e726] #uninstall #distribution #safety — Added explicit project/global uninstall routing because users need safe natural-language scope selection while preserving project memory histories. (2026-08-25)
- [change-dbfdfd62cff541c48fd9df1f4beb057c] #recall #docs #search — Recall accuracy Phase 2 now documents one-hop typed relation expansion and strict prompt-time caps so public guidance matches the shipped conservative recall gate. (2026-08-27)
- [change-e3777a9e3b784c43b6af93be99707348] #opencode #installer #windows — Added a Python-based SyberMem install/update path so Windows OpenCode users can refresh globally without spawning powershell.exe. (2026-08-25)
- [change-f8bd388c7bac4ee584c68edc97951e18] #documentation #norm #digest — Brought docs/feature_map.md and both READMEs \(zh + en\) up to date with the three recent subsystems \(prompt-time habit perceptibility + CJK relevance, digest backlog + digest-conclusion feedback, and the full project-norm subsystem\) so public capability claims match the shipped code (2026-08-24)
- [decision-c24f122fbe5d46ee8095022e6b8c53c8] #architecture #memory #retrieval — The 7 record types are the right main split, but the schema is NOT sufficient for high-quality future summarize/recall/review/QA; the accepted upgrade is typed relations + provenance/verification + selective temporal/confidence fields + an open-item type + entity/question fields + schema-assisted retrieval — all Markdown-first, optional, fail-open, with reverse edges and salience DERIVED not agent-authored (2026-08-25)
- [decision-f780ec7166e14fc2ab1ac595c0edda03] #architecture #team #distribution — For a single team sharing one repo's .sybermem/ via Git, Team mode's only genuinely unique value \(cross-repo management projection\) targets a persona that does not exist here, so it is chicken-rib; the accepted path is DEPRECATE-THEN-REMOVE \(not direct delete, not demote-to-optional\), preceded by a mandatory shared-seam migration, with a read-only registry-based portfolio as the cheaper replacement (2026-08-25)
- [norm-e86ae226dbbf4e28af3de8c1db92f552] #architecture #process — New cross-host features are implemented OpenCode-complete first, then Claude Code and Codex in their existing hook frameworks (2026-08-24)
- [requirement-75f7b0e98b7043eeac310fa2a36ba36d] #norm #opencode #architecture — Add a first-class `norm` record type + dual feedback \(always-on bounded global constitution at startup + scope-matched high-signal recall\) + dual identification \(explicit crystallization + digest-time emergent nomination, both confirmation-first\), reusing existing trust/relation/distribution machinery without lowering the recall gate; deliver OpenCode-complete first, then Claude Code and Codex in their existing hook frameworks (2026-08-24)
- [requirement-ffb8b8130ecd4d33b8a08cfbb9479b59] #memory #observability #opencode — Add an OpenCode-first injection usage and session outcome observability loop so users can see memory cost and quality evidence before SyberMem introduces budget controls. (2026-08-25)

## Archived Conclusions

<!-- Not injected at session start; findable via /sybermem-search -->
<!-- Suffix each line with: [superseded by <id>] or [compressed in <id>] or [archived] -->
<!-- add new archived conclusions here -->

---

## Phase Digests

| Number | Date | Title | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
| 006 | 2026-08-25 | Cross-project Team memory MVP planning | completed | 2 records | [link](digests/2026-08-25-006-cross-project-team-memory-mvp-planning.md) |
| 007 | 2026-08-25 | Skill UX and CLI packaging expansion | completed | 14 records | [link](digests/2026-08-25-007-skill-ux-and-cli-packaging-expansion.md) |
| 008 | 2026-08-25 | Team publication layer implementation | completed | 2 records | [link](digests/2026-08-25-008-team-publication-layer-implementation.md) |
| 009 | 2026-08-25 | Record intent and session continuity hooks | completed | 6 records | [link](digests/2026-08-25-009-record-intent-and-session-continuity-hooks.md) |
| 010 | 2026-08-25 | Continuity trust and recall quality layer | completed | 9 records | [link](digests/2026-08-25-010-continuity-trust-and-recall-quality-layer.md) |
| 011 | 2026-08-25 | Audit-driven OSS readiness and distribution UX hardening | completed | 6 records | [link](digests/2026-08-25-011-audit-driven-oss-readiness-and-distribution-ux-hardening.md) |
| 012 | 2026-08-25 | UUID records and derived index reliability | completed | 2 records | [link](digests/2026-08-25-012-uuid-records-and-derived-index-reliability.md) |
| 013 | 2026-08-25 | Prompt-time habit perceptibility and documentation refresh | completed | 2 records | [link](digests/2026-08-25-013-prompt-time-habit-perceptibility-and-documentation-refresh.md) |
| 014 | 2026-08-25 | Codex OpenCode installer and uninstall rollout | completed | 4 records | [link](digests/2026-08-25-014-codex-opencode-installer-and-uninstall-rollout.md) |
<!-- add new digest records here -->

---

## Theme Digests

| Number | Date | Theme | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
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
| change-036 | 2026-08-04 | Upgrade source-aware task recall packets | implemented | [link](changes/2026-08-04-036-upgrade-source-aware-task-recall-packets.md) |
| change-037 | 2026-08-04 | Add Team publish preview trust envelope | implemented | [link](changes/2026-08-04-037-add-team-publish-preview-trust-envelope.md) |
| change-039 | 2026-08-04 | Implement continuity and trust experience | implemented | [link](changes/2026-08-04-039-implement-continuity-trust-experience.md) |
| change-040 | 2026-08-04 | Fix workspace search completeness | implemented | [link](changes/2026-08-04-040-fix-workspace-search-completeness.md) |
| change-041 | 2026-08-04 | Close continuity and trust review findings | implemented | [link](changes/2026-08-04-041-close-continuity-trust-review-findings.md) |
| change-045 | 2026-08-05 | Audit-driven P0/P1 — dual-track alignment, hot-path efficiency, OSS readiness | implemented | [link](changes/2026-08-05-045-audit-driven-p0-p1-dual-track-efficiency-oss-readiness.md) |
| change-047 | 2026-08-05 | Auto-trail rolling journal — stop writing per-stop markdown records \(batch B\) | implemented | [link](changes/2026-08-05-047-auto-trail-rolling-journal-batch-b.md) |
| change-048 | 2026-08-05 | Distribution consistency, UX terminology, and workspace stale detection \(batches D/E/F\) | implemented | [link](changes/2026-08-05-048-distribution-ux-workspace-stale-batches-def.md) |
| change-049 | 2026-08-05 | Extend human quick-guide layer to the remaining ceremony-heavy skills | implemented | [link](changes/2026-08-05-049-extend-skill-quick-guide-layer.md) |
| change-0638a1012020456193d3b469506151af | 2026-08-25 | Minimal OpenCode memory injection observability | done | [link](changes/2026-08-25-change-0638a1012020456193d3b469506151af-memory-observability-phase5-docs.md) |
| change-0c35875b8fde4feb93837ce354533b9b | 2026-08-25 | Team removal stage 0 — extract digest-path seam into neutral digest_sources.py | done | [link](changes/2026-08-25-change-0c35875b8fde4feb93837ce354533b9b-team-removal-stage0-digest-seam.md) |
| change-13b0a327e1544f3e8e5ac5d3992c5c97 | 2026-08-25 | Team removal review-work — Oracle GO after fixing 2 P1 portfolio/compat blockers | done | [link](changes/2026-08-25-change-13b0a327e1544f3e8e5ac5d3992c5c97-team-removal-reviewwork.md) |
| change-2011a3f2b21e40dbb926187ebae50cf8 | 2026-08-24 | Norm subsystem P0 — first-class norm type, selector, norms list CLI, crystallization skill, OpenCode startup constitution | done | [link](changes/2026-08-24-change-2011a3f2b21e40dbb926187ebae50cf8-norm-p0-opencode-closed-loop.md) |
| change-2b4df42e0ff942718e9afef5897ecc4c | 2026-08-25 | Team removal — distribution-safety hardening; 5-lane review-work all PASS | done | [link](changes/2026-08-25-change-2b4df42e0ff942718e9afef5897ecc4c-team-removal-distribution-safety-hardening.md) |
| change-2b9c79a39ea64b178c9902894cbd49fd | 2026-08-25 | Team removal stage 1 — deprecation annotations + lock no-Team status contract | done | [link](changes/2026-08-25-change-2b9c79a39ea64b178c9902894cbd49fd-team-removal-stage1-decouple.md) |
| change-33b663865936415c9ae9a34e28f6ea6c | 2026-08-24 | Digest effect \(startup/compaction injection + memory-stats coverage\), decoupled threshold, cross-host backlog heads-up | done | [link](changes/2026-08-24-change-33b663865936415c9ae9a34e28f6ea6c-digest-consumption-and-cross-host-backlog.md) |
| change-374880d44753411096e8bd198bae6985 | 2026-08-26 | Cross-host pending-habit reminder and user-habit home unification | done | [link](changes/2026-08-26-change-374880d44753411096e8bd198bae6985-cross-host-pending-habit-and-home-unification.md) |
| change-3d8c9c844d5747c3b15e84838a2d4fe8 | 2026-08-24 | Norm subsystem P2 — Claude Code + Codex host adapters and same-scope conflict governance | done | [link](changes/2026-08-24-change-3d8c9c844d5747c3b15e84838a2d4fe8-norm-p2-cross-host-and-governance.md) |
| change-57a47bcef74841b6a454fe5e53d23b2f | 2026-08-26 | Habit candidate lifecycle — bounded list, prompt summary, status view, single discard | done | [link](changes/2026-08-26-change-57a47bcef74841b6a454fe5e53d23b2f-habit-candidate-lifecycle-list-summary-discard.md) |
| change-5d2b321fcbd440b393bb2030376043de | 2026-08-27 | Recall accuracy Phase 1 scoring and health signals | implemented | [link](changes/2026-08-27-change-5d2b321fcbd440b393bb2030376043de-recall-accuracy-phase1.md) |
| change-657dd8880ab24e889e1f3b2b1521ee3a | 2026-08-25 | Team removal stage 3 — full breaking removal of the Team memory subsystem + portfolio replacement | done | [link](changes/2026-08-25-change-657dd8880ab24e889e1f3b2b1521ee3a-team-removal-stage3-full-removal.md) |
| change-6a3ab8a0e44e4c41843b66bde8b7134a | 2026-08-07 | UUID-backed record IDs and derived project index | implemented | [link](changes/2026-08-07-change-6a3ab8a0e44e4c41843b66bde8b7134a-uuid-record-ids-derived-index.md) |
| change-71c1f4bdc01a4b6cb07731667f1c08c7 | 2026-08-07 | Close derived INDEX review blockers | implemented | [link](changes/2026-08-07-change-71c1f4bdc01a4b6cb07731667f1c08c7-close-derived-index-review-blockers.md) |
| change-76481099f07c4f1f9de150a0281fb58f | 2026-08-24 | Add digest backlog signal so "long time / accumulated work with no digest" is detected \(OpenCode P0\) | done | [link](changes/2026-08-24-change-76481099f07c4f1f9de150a0281fb58f-digest-backlog-signal.md) |
| change-7f75f17f01cc4d249ca8468e7bbfec7d | 2026-08-24 | Make user habits perceptible at prompt time \(default prompt-ok, CJK match, scope routing\) | done | [link](changes/2026-08-24-change-7f75f17f01cc4d249ca8468e7bbfec7d-habit-prompt-time-perceptibility.md) |
| change-7fd560c9a8414c8b9cde8ac842fbad0e | 2026-08-25 | Review fixes for OpenCode memory observability | done | [link](changes/2026-08-25-change-7fd560c9a8414c8b9cde8ac842fbad0e-memory-observability-review-fixes.md) |
| change-878c029967b944cca3fc634c7148cf27 | 2026-08-25 | Codex context markers and 0.1.1 version rollout | active | [link](changes/2026-08-25-change-878c029967b944cca3fc634c7148cf27-codex-context-marker-version-bump.md) |
| change-9a18342f07a64925bad69cbff5b47f89 | 2026-08-25 | Digest injection and observability rollout | done | [link](changes/2026-08-25-change-9a18342f07a64925bad69cbff5b47f89-digest-injection-and-observability.md) |
| change-a40b6aaa5a864b049fd05dd861e283d4 | 2026-08-26 | OpenCode toast queue and remote-version awareness | done | [link](changes/2026-08-26-change-a40b6aaa5a864b049fd05dd861e283d4-toast-queue-and-remote-version-awareness.md) |
| change-b1aa5fc5d8d34d1fb15cb150ec70e655 | 2026-09-01 | Codex recall observability and perceptibility | completed | [link](changes/2026-09-01-change-b1aa5fc5d8d34d1fb15cb150ec70e655-codex-recall-observability.md) |
| change-bcac35f53e004164adb47471d7cf094d | 2026-08-24 | Norm subsystem P1 — scoped recall, compaction constitution, memory-stats visibility, emergent nomination | done | [link](changes/2026-08-24-change-bcac35f53e004164adb47471d7cf094d-norm-p1-scoped-recall-nomination.md) |
| change-c2be7cced7eb4250b288606869f1e726 | 2026-08-25 | Scoped uninstall CLI and natural-language uninstall skill | active | [link](changes/2026-08-25-change-c2be7cced7eb4250b288606869f1e726-scoped-uninstall.md) |
| change-dbfdfd62cff541c48fd9df1f4beb057c | 2026-08-27 | Recall accuracy Phase 2 docs and derived index update | implemented | [link](changes/2026-08-27-change-dbfdfd62cff541c48fd9df1f4beb057c-recall-accuracy-phase2-docs-and-index.md) |
| change-e3777a9e3b784c43b6af93be99707348 | 2026-08-25 | OpenCode Python update path for Windows PowerShell spawn failures | active | [link](changes/2026-08-25-change-e3777a9e3b784c43b6af93be99707348-opencode-python-update-path.md) |
| change-f8bd388c7bac4ee584c68edc97951e18 | 2026-08-24 | Refresh Feature Map and READMEs for habit perceptibility, digest backlog/feedback, and the norm subsystem | done | [link](changes/2026-08-24-change-f8bd388c7bac4ee584c68edc97951e18-docs-refresh-habit-digest-norm.md) |

## Technical Decisions

| ID | Date | Title | Status | Link |
|----|------|-------|--------|------|
<!-- add new records here -->
| decision-001 | 2026-06-30 | Team MVP should precede full Hub experience for Requirement-003 | decided | [link](decisions/2026-06-30-001-team-mvp-before-full-hub-experience.md) |
| decision-002 | 2026-08-04 | Adopt a lightweight continuity and trust experience layer | accepted | [link](decisions/2026-08-04-002-sybermem-continuity-trust-experience.md) |
| decision-003 | 2026-08-05 | Deferral decisions for the four remaining audit follow-ups + skill quick-guide pilot | decided | [link](decisions/2026-08-05-003-audit-followup-deferral-decisions.md) |
| decision-c24f122fbe5d46ee8095022e6b8c53c8 | 2026-08-25 | Memory record schema is sufficient in direction but needs field/relation upgrades \(GO-WITH-REFINEMENTS\) | accepted | [link](decisions/2026-08-25-decision-c24f122fbe5d46ee8095022e6b8c53c8-memory-schema-sufficiency.md) |
| decision-f780ec7166e14fc2ab1ac595c0edda03 | 2026-08-25 | Team memory mode is chicken-rib for a single-repo Git-shared workflow — deprecate then remove | accepted | [link](decisions/2026-08-25-decision-f780ec7166e14fc2ab1ac595c0edda03-team-mode-deprecate-then-remove.md) |

## Requirements / Discussions

| ID | Date | Title | Source | Priority | Link |
|----|------|-------|--------|----------|------|
<!-- add new records here -->
| requirement-001 | 2026-05-08 | 创建ADR项目规范系统 | 内部讨论 | high | [link](requirements/2026-05-08-001-%E5%88%9B%E5%BB%BAADR%E9%A1%B9%E7%9B%AE%E8%A7%84%E8%8C%83%E7%B3%BB%E7%BB%9F.md) |
| requirement-002 | 2026-06-05 | 阶段性总结与记录压缩需求 | 用户使用反馈 | high | [link](requirements/2026-06-05-002-%E9%98%B6%E6%AE%B5%E6%80%A7%E6%80%BB%E7%BB%93%E4%B8%8E%E8%AE%B0%E5%BD%95%E5%8E%8B%E7%BC%A9%E9%9C%80%E6%B1%82.md) |
| requirement-003 | 2026-06-29 | SyberMem 跨项目与团队记忆扩展方案 | 内部方案评审 | high | [link](requirements/2026-06-29-003-sybermem-cross-project-team-memory-extension.md) |
| requirement-75f7b0e98b7043eeac310fa2a36ba36d | 2026-08-24 | Project binding-norm subsystem — identify, record distinctly, and reliably feed norms back into future work | user request — crystallize recurring/binding project decisions into governing norms that reliably reach later work | high | [link](requirements/2026-08-24-requirement-75f7b0e98b7043eeac310fa2a36ba36d-project-norm-subsystem.md) |
| requirement-ffb8b8130ecd4d33b8a08cfbb9479b59 | 2026-08-25 | Minimal memory injection observability for OpenCode | product discussion | high | [link](requirements/2026-08-25-requirement-ffb8b8130ecd4d33b8a08cfbb9479b59-minimal-memory-observability.md) |

## Bug Fix Records

| ID | Date | Title | Severity | Link |
|----|------|-------|----------|------|
<!-- add new records here -->
| bug-001 | 2026-06-09 | init-project misclassifies missing hook file as custom/kept | medium | [link](bugs/2026-06-09-001-init-project-misclassifies-missing-hook-file.md) |
| bug-002 | 2026-08-04 | Publish preview bootstrap and JSON output leaks | high | [link](bugs/2026-08-04-002-publish-preview-bootstrap-json-output.md) |
| bug-003 | 2026-08-04 | Publish trust summary and skill flow gaps | high | [link](bugs/2026-08-04-003-publish-trust-summary-and-skill-flow-gaps.md) |
| bug-004 | 2026-08-05 |  | high | [link](bugs/2026-08-05-004-merged-hook-not-propagated-by-health-check.md) |
| bug-146ffbf8c1d9415d9708e8f18b003971 | 2026-08-25 | Decision supersedes relation was silently dropped from parsing and recall | high | [link](bugs/2026-08-25-bug-146ffbf8c1d9415d9708e8f18b003971-supersedes-relation-drop.md) |
| bug-17a87caf3b014254bdc0d284ad010540 | 2026-08-25 | Python updater recreated existing CLI venv on Windows | medium | [link](bugs/2026-08-25-bug-17a87caf3b014254bdc0d284ad010540-python-update-recreates-existing-venv.md) |

## Usage

- **changes/**: Record all feature changes
- **decisions/**: Record important technical decisions and their rationale
- **requirements/**: Record discussion processes, requirement sources, and design reasoning
- **bugs/**: Record bug analysis and fix approaches
- **analysis/phase-index.md**: Persistent project phase analysis state used to track candidates, confirmed phases, and incremental analysis progress

`.sybermem/INDEX.md` is derived from canonical record files. Use `sybermem project index build` to regenerate it and `sybermem project index check` to verify it is current.

---

## Topic Index

<!-- Auto-maintained: maps topic tags to record IDs for fast lookup -->
- architecture: change-2011a3f2b21e40dbb926187ebae50cf8, change-3d8c9c844d5747c3b15e84838a2d4fe8, change-6a3ab8a0e44e4c41843b66bde8b7134a, decision-c24f122fbe5d46ee8095022e6b8c53c8, decision-f780ec7166e14fc2ab1ac595c0edda03, norm-e86ae226dbbf4e28af3de8c1db92f552, requirement-75f7b0e98b7043eeac310fa2a36ba36d
- codex: change-878c029967b944cca3fc634c7148cf27, change-b1aa5fc5d8d34d1fb15cb150ec70e655
- collaboration: change-6a3ab8a0e44e4c41843b66bde8b7134a
- digest: change-33b663865936415c9ae9a34e28f6ea6c, change-76481099f07c4f1f9de150a0281fb58f, change-9a18342f07a64925bad69cbff5b47f89, change-f8bd388c7bac4ee584c68edc97951e18
- distribution: change-0c35875b8fde4feb93837ce354533b9b, change-13b0a327e1544f3e8e5ac5d3992c5c97, change-2b4df42e0ff942718e9afef5897ecc4c, change-2b9c79a39ea64b178c9902894cbd49fd, change-374880d44753411096e8bd198bae6985, change-657dd8880ab24e889e1f3b2b1521ee3a, change-71c1f4bdc01a4b6cb07731667f1c08c7, change-878c029967b944cca3fc634c7148cf27, change-a40b6aaa5a864b049fd05dd861e283d4, change-c2be7cced7eb4250b288606869f1e726, decision-f780ec7166e14fc2ab1ac595c0edda03
- docs: change-dbfdfd62cff541c48fd9df1f4beb057c
- documentation: change-f8bd388c7bac4ee584c68edc97951e18
- habit: change-374880d44753411096e8bd198bae6985, change-57a47bcef74841b6a454fe5e53d23b2f, change-7f75f17f01cc4d249ca8468e7bbfec7d
- index: change-71c1f4bdc01a4b6cb07731667f1c08c7
- installer: bug-17a87caf3b014254bdc0d284ad010540, change-e3777a9e3b784c43b6af93be99707348
- memory: change-0638a1012020456193d3b469506151af, change-7fd560c9a8414c8b9cde8ac842fbad0e, decision-c24f122fbe5d46ee8095022e6b8c53c8, requirement-ffb8b8130ecd4d33b8a08cfbb9479b59
- norm: change-2011a3f2b21e40dbb926187ebae50cf8, change-3d8c9c844d5747c3b15e84838a2d4fe8, change-bcac35f53e004164adb47471d7cf094d, change-f8bd388c7bac4ee584c68edc97951e18, requirement-75f7b0e98b7043eeac310fa2a36ba36d
- observability: change-0638a1012020456193d3b469506151af, change-5d2b321fcbd440b393bb2030376043de, change-7fd560c9a8414c8b9cde8ac842fbad0e, change-9a18342f07a64925bad69cbff5b47f89, change-a40b6aaa5a864b049fd05dd861e283d4, change-b1aa5fc5d8d34d1fb15cb150ec70e655, requirement-ffb8b8130ecd4d33b8a08cfbb9479b59
- opencode: bug-17a87caf3b014254bdc0d284ad010540, change-0638a1012020456193d3b469506151af, change-2011a3f2b21e40dbb926187ebae50cf8, change-33b663865936415c9ae9a34e28f6ea6c, change-374880d44753411096e8bd198bae6985, change-57a47bcef74841b6a454fe5e53d23b2f, change-76481099f07c4f1f9de150a0281fb58f, change-7f75f17f01cc4d249ca8468e7bbfec7d, change-7fd560c9a8414c8b9cde8ac842fbad0e, change-a40b6aaa5a864b049fd05dd861e283d4, change-bcac35f53e004164adb47471d7cf094d, change-e3777a9e3b784c43b6af93be99707348, requirement-75f7b0e98b7043eeac310fa2a36ba36d, requirement-ffb8b8130ecd4d33b8a08cfbb9479b59
- process: norm-e86ae226dbbf4e28af3de8c1db92f552
- qa: change-13b0a327e1544f3e8e5ac5d3992c5c97, change-2b4df42e0ff942718e9afef5897ecc4c
- quality: bug-146ffbf8c1d9415d9708e8f18b003971, change-6a3ab8a0e44e4c41843b66bde8b7134a, change-71c1f4bdc01a4b6cb07731667f1c08c7, change-7fd560c9a8414c8b9cde8ac842fbad0e
- recall: change-5d2b321fcbd440b393bb2030376043de, change-9a18342f07a64925bad69cbff5b47f89, change-b1aa5fc5d8d34d1fb15cb150ec70e655, change-dbfdfd62cff541c48fd9df1f4beb057c
- refactor: change-0c35875b8fde4feb93837ce354533b9b, change-2b9c79a39ea64b178c9902894cbd49fd, change-657dd8880ab24e889e1f3b2b1521ee3a
- retrieval: bug-146ffbf8c1d9415d9708e8f18b003971, decision-c24f122fbe5d46ee8095022e6b8c53c8
- safety: change-c2be7cced7eb4250b288606869f1e726
- schema: bug-146ffbf8c1d9415d9708e8f18b003971
- search: change-5d2b321fcbd440b393bb2030376043de, change-dbfdfd62cff541c48fd9df1f4beb057c
- security: change-2b4df42e0ff942718e9afef5897ecc4c, change-7fd560c9a8414c8b9cde8ac842fbad0e
- team: change-0c35875b8fde4feb93837ce354533b9b, change-13b0a327e1544f3e8e5ac5d3992c5c97, change-2b9c79a39ea64b178c9902894cbd49fd, change-657dd8880ab24e889e1f3b2b1521ee3a, decision-f780ec7166e14fc2ab1ac595c0edda03
- topic: change-032
- uninstall: change-c2be7cced7eb4250b288606869f1e726
- ux: change-33b663865936415c9ae9a34e28f6ea6c, change-3d8c9c844d5747c3b15e84838a2d4fe8, change-57a47bcef74841b6a454fe5e53d23b2f, change-76481099f07c4f1f9de150a0281fb58f, change-7f75f17f01cc4d249ca8468e7bbfec7d, change-bcac35f53e004164adb47471d7cf094d
- versioning: change-878c029967b944cca3fc634c7148cf27
- windows: bug-17a87caf3b014254bdc0d284ad010540, change-e3777a9e3b784c43b6af93be99707348

## Project Norms

| ID | Date | Title | Status | Link |
|----|------|-------|--------|------|
<!-- add new records here -->
| norm-e86ae226dbbf4e28af3de8c1db92f552 | 2026-08-24 | OpenCode-first then Claude/Codex for cross-host features | active | [link](norms/2026-08-24-norm-e86ae226dbbf4e28af3de8c1db92f552-opencode-first.md) |
