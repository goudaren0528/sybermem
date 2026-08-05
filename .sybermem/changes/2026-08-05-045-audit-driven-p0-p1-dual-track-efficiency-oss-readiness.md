---
type: change
date: 2026-08-05
number: 045
title: Audit-driven P0/P1 — dual-track alignment, hot-path efficiency, OSS readiness
status: implemented
author: Sisyphus
related_files: packages/cli/sybermem_cli/main.py, packages/core/sybermem_core/search.py, .sybermem/hooks/user_prompt.py, .sybermem/hooks/record_change_on_stop.py, packages/cli/pyproject.toml, packages/core/pyproject.toml, VERSION, scripts/sync-version.py, scripts/check-plugin-package.py, .github/workflows/ci.yml, LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, README.md, README.en.md, docs/audit/2026-08-05-sybermem-comprehensive-audit.md
---

## Change Content

Executed the top-priority improvements from the 2026-08-05 comprehensive audit (docs/audit/2026-08-05-sybermem-comprehensive-audit.md) after re-verifying every audit conclusion against source. Each part followed spec → plan → implement → verify.

**P0-§1 Dual-track alignment:**
- Added a real `sybermem resume` CLI command (`--mode fast|standard|deep`, `--format text|json`) wiring the already-implemented but previously unreachable `build_resume_checkpoint`.
- `search_project` now raises `ProjectRootNotFoundError` instead of silently returning `[]`; the CLI surfaces an explicit error, while `compact_project_search` (per-prompt hook path) still degrades silently.
- Documented the CLI-vs-Skill execution split in README.md and README.en.md.

**P0-§2 Hot-path efficiency (batch A):**
- Added a process-local project-search cache keyed by record-dir mtime, eliminating the fallback double full-scan; results are byte-identical.
- Merged `detect_record_intent` + `task_recall` into a single `user_prompt.py` hook (one process: one stdin read, one root resolve, one core import), synced across all 3 authoritative hook copies + 2 settings templates + current settings + the plugin delegator `hooks/user-prompt-submit`, with `check-plugin-package.py` updated accordingly.
- Deduplicated the stop-hook commit-gap computation.

**P1-§5 OSS readiness:**
- Added root `LICENSE` (MIT) + per-package license copies; wired `license`/`license-files` into both pyprojects.
- `sybermem-cli` now declares `dependencies = ["sybermem-core"]` plus rich metadata (readme, authors, keywords, classifiers, project.urls).
- Introduced `VERSION` single-source + `scripts/sync-version.py` (covers all 8 manifests) + a version-consistency gate in `check-plugin-package.py`.
- Added `.github/workflows/ci.yml` (test matrix / build / package / install-smoke) and CONTRIBUTING/SECURITY/CODE_OF_CONDUCT + issue/PR templates.

## Reason for Change

The audit found three systemic problems: an undocumented CLI/skill dual-track (with `resume` implemented but unreachable), linear hot-path degradation (measured ~517ms per prompt from two separate hook processes + unindexed project search), and near-zero OSS operational maturity (no LICENSE file, no CI, cli importing core without declaring the dependency, version hardcoded in 8 places). These are the highest-leverage reliability, performance, and trust gaps.

## Impact Scope

- Users gain a programmatic, scriptable `sybermem resume`; no-project-root errors are now explicit instead of silent.
- Per-prompt hook cost dropped from ~491ms (two-process) to ~297ms merged (~39% faster) at 51 records; project search no longer double-scans on the fallback path.
- The repo now has a valid LICENSE, buildable+publishable packages with a declared dependency graph, single-sourced versioning with an enforced consistency gate, CI scaffolding, and community health files.
- Distribution integrity preserved: `check-plugin-package.py` passes including `claude plugins validate`.

## Implementation

- CLI: `cmd_resume` + subparser in `packages/cli/sybermem_cli/main.py`; `ProjectRootNotFoundError` in `packages/core/sybermem_core/search.py` with the hook-path fallback preserved.
- Search cache: `_load_all_rows` + `_records_fingerprint` + `_ROW_CACHE`, returning per-call shallow copies so caller mutation cannot poison the cache.
- Merged hook: `.sybermem/hooks/user_prompt.py` reusing the two legacy modules' pure helpers as a single source of truth; legacy files retained for backward compatibility.
- Version single-source: root `VERSION` + `scripts/sync-version.py` (regex line edits preserving format) + `check_version_consistency` handling marketplace.json's nested `plugins[*].version`.

## Test Verification

- `pytest packages/core` → 83 passed (80 pre-existing + 3 new cache tests); `pytest packages/cli` → 11 passed (7 pre-existing + 4 new resume tests).
- `sybermem resume` exercised for fast/standard/deep in text and json in a real terminal; no-root path returns exit 1 with a stderr message; `task_recall`/`user_prompt` hook confirmed to fail open with no project root.
- Merged hook timed at ~297ms vs ~491ms two-process sum; intent capture writes `.record-intent.json`, recall prints valid `additionalContext` JSON, no stdout cross-contamination.
- `python -m build` succeeds for both packages; METADATA shows `License-Expression: MIT`, `License-File: LICENSE`, `Requires-Dist: sybermem-core`, project URLs.
- `scripts/sync-version.py` idempotent across 8 sites; `check-plugin-package.py` fails on injected version skew and prints `OK` at parity; `ci.yml` parses as valid YAML.

## Notes

Deferred by explicit decision: P0-§2 batch B (auto-trail rolling journal — storage migration + INDEX/Team/digest downstream risk), stop-hook next-id persistence (id-conflict risk, kept glob), real CI green (needs GitHub push to run the matrix), and §3/§4 second-tier items. Also fixed incidental stop-hook template drift where the two template copies lagged the runtime version (`GIT_CWD=Path.cwd()` old buggy form, missing `theme_key or "misc"`). Specs are under docs/superpowers/specs/2026-08-05-*; plans are under docs/superpowers/plans/ (that dir is gitignored per repo convention).
