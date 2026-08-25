# SyberMem Index

This file summarizes all project changes, decisions, requirements, and bug records.

---

## Key Conclusions

<!-- One-line core conclusion per record. Format: [id] #topic1 #topic2 — description (date) -->
<!-- add new conclusions here -->
- [bug-146ffbf8c1d9415d9708e8f18b003971] #schema #retrieval #quality — Decision records authored with `supersedes` were silently parsed without the relation, breaking successor/current-truth guidance and relation recall; parser, derived inverse graph, and search scoring now support both directions compatibly (2026-08-25)
- [bug-17a87caf3b014254bdc0d284ad010540] #installer #windows #opencode — Fixed the Python updater to reuse an existing CLI venv so Windows OpenCode updates no longer fail on a locked venv python.exe. (2026-08-25)
- [change-0c35875b8fde4feb93837ce354533b9b] #team #distribution #refactor — Moved latest_phase_digest/latest_theme_digest out of the Team publish subsystem into a neutral digest_sources.py and repointed resume/next-step/publish, so non-Team digest-aware features no longer depend on Team code — zero behavior change, unblocking safe Team removal later (2026-08-25)
- [change-13b0a327e1544f3e8e5ac5d3992c5c97] #team #distribution #qa — Independent Oracle post-implementation review confirmed the Team removal is correct \(no residual refs, seam decoupled, contract removed, distribution + data-safe\) but flagged 2 P1s in the portfolio replacement + test coverage; both fixed and re-reviewed to GO (2026-08-25)
- [change-2011a3f2b21e40dbb926187ebae50cf8] #norm #opencode #architecture — Delivered the P0 closed loop for binding project norms — a first-class `norm` record type + constitution/scoped selector + `norms list` CLI + /sybermem-record crystallization + OpenCode startup constitution injection — so norms can be recorded distinctly and reliably govern later OpenCode work (2026-08-24)
- [change-2b4df42e0ff942718e9afef5897ecc4c] #distribution #security #qa — A second, stricter 5-lane review-work found 4 distribution/safety blockers \(stale-on-upgrade PowerShell manifest/remover copy, ancestor-symlink traversal + tampered-plugin-path in the managed remover, inaccurate README "team" tagline, stale OpenCode bundle\); all fixed and re-reviewed to all-PASS, making the Team removal releasable (2026-08-25)
- [change-2b9c79a39ea64b178c9902894cbd49fd] #team #distribution #refactor — Verified the non-Team status/routing/project paths are already robust without Team, made that explicit via deprecation docstrings, and added a regression test locking project_status\(\) publication.team=={} \(shape preserved\) for the deprecation window (2026-08-25)
- [change-3d8c9c844d5747c3b15e84838a2d4fe8] #norm #architecture #ux — Delivered norm P2 — Claude Code and Codex now inject the constitution at SessionStart and scoped norms at UserPromptSubmit \(reusing the norms-list CLI as single source of truth\), plus a same-scope conflict detector + `norms doctor` governance CLI, completing cross-host norm reach and drift protection (2026-08-24)
- [change-657dd8880ab24e889e1f3b2b1521ee3a] #team #distribution #refactor — Removed the entire Team memory subsystem \(core/cli/skills/schema/tests/docs/distribution\) as a breaking change and replaced its only useful capability with a read-only registry-based portfolio, leaving zero residual Team executable refs and never touching users' .sybermem/ history or external Team repos (2026-08-25)
- [change-76481099f07c4f1f9de150a0281fb58f] #digest #opencode #ux — SyberMem could detect a STALE digest \(coverage_hash\) but never "should make a NEW digest"; added digest_backlog \(uncovered records + age\), fixed the next-step dead condition that only fired before the first digest, and an OpenCode session.idle backlog toast — all fed by one core signal via digest status JSON (2026-08-24)
- [change-7f75f17f01cc4d249ca8468e7bbfec7d] #habit #opencode #ux — Habits were invisible because add_habit defaulted to compaction_ok while the prompt-time selector required prompt_ok_when_supported, and _terms\(\) never tokenized CJK so applies_to killed every Chinese context; fixed by defaulting to prompt-ok, CJK-aware weighted relevance, and a suggested_scope routing hint (2026-08-24)
- [change-878c029967b944cca3fc634c7148cf27] #codex #distribution #versioning — Codex additionalContext now carries explicit SyberMem markers and the distribution version is bumped to 0.1.1 so users can refresh project-local files after global updates. (2026-08-25)
- [change-bcac35f53e004164adb47471d7cf094d] #norm #opencode #ux — Delivered norm P1 — per-prompt scoped-norm recall + compaction constitution reuse \(OpenCode\), memory-stats norm coverage, and digest-time emergent nomination of recurring constraints \(confirmation-first\) — so norms reach relevant work and recurring rules get proactively surfaced for crystallization (2026-08-24)
- [change-c2be7cced7eb4250b288606869f1e726] #uninstall #distribution #safety — Added explicit project/global uninstall routing because users need safe natural-language scope selection while preserving project memory histories. (2026-08-25)
- [change-e3777a9e3b784c43b6af93be99707348] #opencode #installer #windows — Added a Python-based SyberMem install/update path so Windows OpenCode users can refresh globally without spawning powershell.exe. (2026-08-25)
- [change-f8bd388c7bac4ee584c68edc97951e18] #documentation #norm #digest — Brought docs/feature_map.md and both READMEs \(zh + en\) up to date with the three recent subsystems \(prompt-time habit perceptibility + CJK relevance, digest backlog + digest-conclusion feedback, and the full project-norm subsystem\) so public capability claims match the shipped code (2026-08-24)
- [decision-c24f122fbe5d46ee8095022e6b8c53c8] #architecture #memory #retrieval — The 7 record types are the right main split, but the schema is NOT sufficient for high-quality future summarize/recall/review/QA; the accepted upgrade is typed relations + provenance/verification + selective temporal/confidence fields + an open-item type + entity/question fields + schema-assisted retrieval — all Markdown-first, optional, fail-open, with reverse edges and salience DERIVED not agent-authored (2026-08-25)
- [decision-f780ec7166e14fc2ab1ac595c0edda03] #architecture #team #distribution — For a single team sharing one repo's .sybermem/ via Git, Team mode's only genuinely unique value \(cross-repo management projection\) targets a persona that does not exist here, so it is chicken-rib; the accepted path is DEPRECATE-THEN-REMOVE \(not direct delete, not demote-to-optional\), preceded by a mandatory shared-seam migration, with a read-only registry-based portfolio as the cheaper replacement (2026-08-25)
- [norm-e86ae226dbbf4e28af3de8c1db92f552] #architecture #process — New cross-host features are implemented OpenCode-complete first, then Claude Code and Codex in their existing hook frameworks (2026-08-24)
- [requirement-75f7b0e98b7043eeac310fa2a36ba36d] #norm #opencode #architecture — Add a first-class `norm` record type + dual feedback \(always-on bounded global constitution at startup + scope-matched high-signal recall\) + dual identification \(explicit crystallization + digest-time emergent nomination, both confirmation-first\), reusing existing trust/relation/distribution machinery without lowering the recall gate; deliver OpenCode-complete first, then Claude Code and Codex in their existing hook frameworks (2026-08-24)

## Archived Conclusions

<!-- Not injected at session start; findable via /sybermem-search -->
<!-- Suffix each line with: [superseded by <id>] or [compressed in <id>] or [archived] -->
<!-- add new archived conclusions here -->

---

## Phase Digests

| Number | Date | Title | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
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
| change-0c35875b8fde4feb93837ce354533b9b | 2026-08-25 | Team removal stage 0 — extract digest-path seam into neutral digest_sources.py | done | [link](changes/2026-08-25-change-0c35875b8fde4feb93837ce354533b9b-team-removal-stage0-digest-seam.md) |
| change-13b0a327e1544f3e8e5ac5d3992c5c97 | 2026-08-25 | Team removal review-work — Oracle GO after fixing 2 P1 portfolio/compat blockers | done | [link](changes/2026-08-25-change-13b0a327e1544f3e8e5ac5d3992c5c97-team-removal-reviewwork.md) |
| change-2011a3f2b21e40dbb926187ebae50cf8 | 2026-08-24 | Norm subsystem P0 — first-class norm type, selector, norms list CLI, crystallization skill, OpenCode startup constitution | done | [link](changes/2026-08-24-change-2011a3f2b21e40dbb926187ebae50cf8-norm-p0-opencode-closed-loop.md) |
| change-2b4df42e0ff942718e9afef5897ecc4c | 2026-08-25 | Team removal — distribution-safety hardening; 5-lane review-work all PASS | done | [link](changes/2026-08-25-change-2b4df42e0ff942718e9afef5897ecc4c-team-removal-distribution-safety-hardening.md) |
| change-2b9c79a39ea64b178c9902894cbd49fd | 2026-08-25 | Team removal stage 1 — deprecation annotations + lock no-Team status contract | done | [link](changes/2026-08-25-change-2b9c79a39ea64b178c9902894cbd49fd-team-removal-stage1-decouple.md) |
| change-33b663865936415c9ae9a34e28f6ea6c | 2026-08-24 | Digest effect \(startup/compaction injection + memory-stats coverage\), decoupled threshold, cross-host backlog heads-up | done | [link](changes/2026-08-24-change-33b663865936415c9ae9a34e28f6ea6c-digest-consumption-and-cross-host-backlog.md) |
| change-3d8c9c844d5747c3b15e84838a2d4fe8 | 2026-08-24 | Norm subsystem P2 — Claude Code + Codex host adapters and same-scope conflict governance | done | [link](changes/2026-08-24-change-3d8c9c844d5747c3b15e84838a2d4fe8-norm-p2-cross-host-and-governance.md) |
| change-657dd8880ab24e889e1f3b2b1521ee3a | 2026-08-25 | Team removal stage 3 — full breaking removal of the Team memory subsystem + portfolio replacement | done | [link](changes/2026-08-25-change-657dd8880ab24e889e1f3b2b1521ee3a-team-removal-stage3-full-removal.md) |
| change-76481099f07c4f1f9de150a0281fb58f | 2026-08-24 | Add digest backlog signal so "long time / accumulated work with no digest" is detected \(OpenCode P0\) | done | [link](changes/2026-08-24-change-76481099f07c4f1f9de150a0281fb58f-digest-backlog-signal.md) |
| change-7f75f17f01cc4d249ca8468e7bbfec7d | 2026-08-24 | Make user habits perceptible at prompt time \(default prompt-ok, CJK match, scope routing\) | done | [link](changes/2026-08-24-change-7f75f17f01cc4d249ca8468e7bbfec7d-habit-prompt-time-perceptibility.md) |
| change-878c029967b944cca3fc634c7148cf27 | 2026-08-25 | Codex context markers and 0.1.1 version rollout | active | [link](changes/2026-08-25-change-878c029967b944cca3fc634c7148cf27-codex-context-marker-version-bump.md) |
| change-bcac35f53e004164adb47471d7cf094d | 2026-08-24 | Norm subsystem P1 — scoped recall, compaction constitution, memory-stats visibility, emergent nomination | done | [link](changes/2026-08-24-change-bcac35f53e004164adb47471d7cf094d-norm-p1-scoped-recall-nomination.md) |
| change-c2be7cced7eb4250b288606869f1e726 | 2026-08-25 | Scoped uninstall CLI and natural-language uninstall skill | active | [link](changes/2026-08-25-change-c2be7cced7eb4250b288606869f1e726-scoped-uninstall.md) |
| change-e3777a9e3b784c43b6af93be99707348 | 2026-08-25 | OpenCode Python update path for Windows PowerShell spawn failures | active | [link](changes/2026-08-25-change-e3777a9e3b784c43b6af93be99707348-opencode-python-update-path.md) |
| change-f8bd388c7bac4ee584c68edc97951e18 | 2026-08-24 | Refresh Feature Map and READMEs for habit perceptibility, digest backlog/feedback, and the norm subsystem | done | [link](changes/2026-08-24-change-f8bd388c7bac4ee584c68edc97951e18-docs-refresh-habit-digest-norm.md) |

## Technical Decisions

| ID | Date | Title | Status | Link |
|----|------|-------|--------|------|
<!-- add new records here -->
| decision-c24f122fbe5d46ee8095022e6b8c53c8 | 2026-08-25 | Memory record schema is sufficient in direction but needs field/relation upgrades \(GO-WITH-REFINEMENTS\) | accepted | [link](decisions/2026-08-25-decision-c24f122fbe5d46ee8095022e6b8c53c8-memory-schema-sufficiency.md) |
| decision-f780ec7166e14fc2ab1ac595c0edda03 | 2026-08-25 | Team memory mode is chicken-rib for a single-repo Git-shared workflow — deprecate then remove | accepted | [link](decisions/2026-08-25-decision-f780ec7166e14fc2ab1ac595c0edda03-team-mode-deprecate-then-remove.md) |

## Requirements / Discussions

| ID | Date | Title | Source | Priority | Link |
|----|------|-------|--------|----------|------|
<!-- add new records here -->
| requirement-75f7b0e98b7043eeac310fa2a36ba36d | 2026-08-24 | Project binding-norm subsystem — identify, record distinctly, and reliably feed norms back into future work | user request — crystallize recurring/binding project decisions into governing norms that reliably reach later work | high | [link](requirements/2026-08-24-requirement-75f7b0e98b7043eeac310fa2a36ba36d-project-norm-subsystem.md) |

## Bug Fix Records

| ID | Date | Title | Severity | Link |
|----|------|-------|----------|------|
<!-- add new records here -->
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
- architecture: change-2011a3f2b21e40dbb926187ebae50cf8, change-3d8c9c844d5747c3b15e84838a2d4fe8, decision-c24f122fbe5d46ee8095022e6b8c53c8, decision-f780ec7166e14fc2ab1ac595c0edda03, norm-e86ae226dbbf4e28af3de8c1db92f552, requirement-75f7b0e98b7043eeac310fa2a36ba36d
- codex: change-878c029967b944cca3fc634c7148cf27
- digest: change-33b663865936415c9ae9a34e28f6ea6c, change-76481099f07c4f1f9de150a0281fb58f, change-f8bd388c7bac4ee584c68edc97951e18
- distribution: change-0c35875b8fde4feb93837ce354533b9b, change-13b0a327e1544f3e8e5ac5d3992c5c97, change-2b4df42e0ff942718e9afef5897ecc4c, change-2b9c79a39ea64b178c9902894cbd49fd, change-657dd8880ab24e889e1f3b2b1521ee3a, change-878c029967b944cca3fc634c7148cf27, change-c2be7cced7eb4250b288606869f1e726, decision-f780ec7166e14fc2ab1ac595c0edda03
- documentation: change-f8bd388c7bac4ee584c68edc97951e18
- habit: change-7f75f17f01cc4d249ca8468e7bbfec7d
- installer: bug-17a87caf3b014254bdc0d284ad010540, change-e3777a9e3b784c43b6af93be99707348
- memory: decision-c24f122fbe5d46ee8095022e6b8c53c8
- norm: change-2011a3f2b21e40dbb926187ebae50cf8, change-3d8c9c844d5747c3b15e84838a2d4fe8, change-bcac35f53e004164adb47471d7cf094d, change-f8bd388c7bac4ee584c68edc97951e18, requirement-75f7b0e98b7043eeac310fa2a36ba36d
- opencode: bug-17a87caf3b014254bdc0d284ad010540, change-2011a3f2b21e40dbb926187ebae50cf8, change-33b663865936415c9ae9a34e28f6ea6c, change-76481099f07c4f1f9de150a0281fb58f, change-7f75f17f01cc4d249ca8468e7bbfec7d, change-bcac35f53e004164adb47471d7cf094d, change-e3777a9e3b784c43b6af93be99707348, requirement-75f7b0e98b7043eeac310fa2a36ba36d
- process: norm-e86ae226dbbf4e28af3de8c1db92f552
- qa: change-13b0a327e1544f3e8e5ac5d3992c5c97, change-2b4df42e0ff942718e9afef5897ecc4c
- quality: bug-146ffbf8c1d9415d9708e8f18b003971
- refactor: change-0c35875b8fde4feb93837ce354533b9b, change-2b9c79a39ea64b178c9902894cbd49fd, change-657dd8880ab24e889e1f3b2b1521ee3a
- retrieval: bug-146ffbf8c1d9415d9708e8f18b003971, decision-c24f122fbe5d46ee8095022e6b8c53c8
- safety: change-c2be7cced7eb4250b288606869f1e726
- schema: bug-146ffbf8c1d9415d9708e8f18b003971
- security: change-2b4df42e0ff942718e9afef5897ecc4c
- team: change-0c35875b8fde4feb93837ce354533b9b, change-13b0a327e1544f3e8e5ac5d3992c5c97, change-2b9c79a39ea64b178c9902894cbd49fd, change-657dd8880ab24e889e1f3b2b1521ee3a, decision-f780ec7166e14fc2ab1ac595c0edda03
- uninstall: change-c2be7cced7eb4250b288606869f1e726
- ux: change-33b663865936415c9ae9a34e28f6ea6c, change-3d8c9c844d5747c3b15e84838a2d4fe8, change-76481099f07c4f1f9de150a0281fb58f, change-7f75f17f01cc4d249ca8468e7bbfec7d, change-bcac35f53e004164adb47471d7cf094d
- versioning: change-878c029967b944cca3fc634c7148cf27
- windows: bug-17a87caf3b014254bdc0d284ad010540, change-e3777a9e3b784c43b6af93be99707348

## Project Norms

| ID | Date | Title | Status | Link |
|----|------|-------|--------|------|
<!-- add new records here -->
| norm-e86ae226dbbf4e28af3de8c1db92f552 | 2026-08-24 | OpenCode-first then Claude/Codex for cross-host features | active | [link](norms/2026-08-24-norm-e86ae226dbbf4e28af3de8c1db92f552-opencode-first.md) |
