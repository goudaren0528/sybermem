---
type: change
date: 2026-08-05
number: 048
title: Distribution consistency, UX terminology, and workspace stale detection (batches D/E/F)
status: implemented
author: Sisyphus
related_files: .codex-plugin/plugin.json, .cursor-plugin/plugin.json, .kimi-plugin/plugin.json, .github/workflows/ci.yml, README.md, README.en.md, CONTRIBUTING.md, .sybermem/INDEX.md, .sybermem/hooks/check_project_health.py, packages/claude-skills/sybermem-digest/SKILL.md, packages/core/sybermem_core/workspace_search.py, packages/core/sybermem_core/search.py, packages/cli/sybermem_cli/main.py, packages/core/tests/test_workspace_staleness.py
related: [change-045]
---

## Change Content

Completed the second-tier audit follow-ups as three committed batches (D/E/F), each spec-driven and verified.

**Batch D — distribution consistency (§4):**
- Unified Codex/Cursor/Kimi `plugin.json` from 4-field stubs to full metadata matching Claude/Gemini (object author, description, homepage, repository, license, keywords).
- Added two CI gates in the package job: `sync-version.py` + `git diff --exit-code` (version-skew) and `sync-plugin-skills.py` + `git diff --exit-code skills/` (skill-mirror drift).
- Added a platform support-level matrix to README.md/README.en.md (Claude/OpenCode full; Gemini entry; Codex/Cursor/Kimi metadata placeholders).

**Batch E — UX terminology + install docs (§3):**
- Renamed `Stage Digests` → `Phase Digests` across INDEX (runtime + template), `check_project_health.py`, digest/theme-digest/update/init-project skills, and docs/zh, so one concept has one name. Verified safe: health check detects the section via the HTML anchor, not the heading.
- Fixed install ordering: one-line remote install marked recommended for users, `claude --plugin-dir .` marked developer/local validation.
- Added a Key Conclusions governance section to CONTRIBUTING.

**Batch F — workspace stale detection (§2-e):**
- Added `workspace_index_staleness()` (read-only, fail-open) comparing each registered project's `last_seen_commit` to its current HEAD.
- `cmd_search` (workspace scope) now prints a stderr note listing stale projects and adds an `index_staleness` field to json output; results/signatures/exit codes unchanged; no auto-rebuild.

## Reason for Change

After the P0/P1 root-cause fixes, the audit's second-tier gaps remained: platform manifests were inconsistent and over-claimed support; the "Stage Digest vs phase digest" naming split raised cognitive load and the install docs pointed users at the developer command; and workspace search served stale results silently because it never compared indexed vs current HEAD.

## Impact Scope

- Distribution: platform manifests are uniform; CI now hard-fails on version skew or skill-mirror drift; platform claims are honest.
- UX: digest terminology is consistent everywhere; new users are pointed at the intuitive one-line install; contributors have a rule for keeping Key Conclusions high-signal.
- Efficiency/trust: workspace search now surfaces when its index is behind a project's HEAD, so users know to rebuild instead of trusting stale hits.

## Implementation

- `workspace_search.py`: `workspace_index_staleness()` over `load_registry()` + `current_head()`; re-exported through `search.py`; consumed by `cmd_search`.
- Terminology rename applied to source `packages/claude-skills` + INDEX + health hook, then mirrored via `sync-plugin-skills.py`.
- CI `ci.yml` package job gained the two drift gates.

## Test Verification

- Batch D: manifests valid JSON, `sync-version.py` idempotent, `check-plugin-package.py` OK, `ci.yml` valid YAML.
- Batch E: health check digest anchor intact after heading rename; skill mirror in sync; no residual "Stage Digest" in shipped files.
- Batch F: 3 new unit tests (fresh/stale/skip); CLI end-to-end prints the stale note only when stale, exit code unchanged.
- Overall: `pytest packages/core` → 86 passed; `pytest packages/cli` → 11 passed; `check-plugin-package.py` → OK.

## Notes

Deferred: skill machine-contract slimming (init-project 236-line HARD-GATE split — AI-behavior risk, independent work); Codex/Cursor/Kimi runtime hooks (platform-completion work); batch C (clean up the 26 legacy auto-trail records + recompute status/publish from the journal — changes publish source_hash semantics); real CI green (needs GitHub push). Specs under docs/superpowers/specs/2026-08-05-sybermem-{distribution-consistency,ux-terminology-install,workspace-stale-detection}-design.md. Continues change-045/047.
