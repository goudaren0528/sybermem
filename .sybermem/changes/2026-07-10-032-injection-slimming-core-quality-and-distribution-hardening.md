---
type: change
date: 2026-07-10
number: 032
title: Injection slimming, core quality fixes, and distribution chain hardening
status: implemented
---

## Change Content

Comprehensive quality pass across SyberMem's core capabilities, injection footprint, and distribution chain:

### Injection Slimming
- CLAUDE.md / AGENTS.md template reduced from ~76 lines to ~22 lines; removed duplicated Available Skills list, Workflow 11 items, and Directory Resolution (all already defined in skill SKILL.md files)
- `session_start_context.py` output capped: only injects most recent 5 Key Conclusions (sorted by date), removed full Topic Index dump and skill list (triple-duplication with harness registry)
- Default `SYBERMEM_RECORD_MODE` changed from `auto` to `remind` (only remind, no automatic change trail)

### Core Quality Fixes (Two Rounds)
- **Bug lifecycle**: added `status: open|resolved` to bug template; `project_status()` now filters `open_bugs` by status instead of counting all bugs forever
- **Publish→summary contract**: `render_current_status` now emits `## Open Bugs` / `## Open Requirements` sections with actual record IDs, unblocking team summary attention signals
- **FTS5 search**: `parse_record_file` now extracts `#topic` tags; `search_workspace` uses FTS5 `MATCH` when available instead of `LIKE %q%`
- **Search coverage**: `iter_record_files` now includes `digests/` and `theme-digests/` so CLI search covers compressed-phase content
- **Router nudge loop**: replaced `record_count >= 1` with `commit_gap >= 5`; added phase-index existence check; router now recommends `/sybermem-phase-analyze` when phase index is missing
- **Summary schema**: added per-section field requirements and digest cross-reference step to `/sybermem-summary` SKILL.md
- **English intent patterns**: added 4 English regex patterns + fallback to `detect_record_intent.py`
- **Stop hook**: lowered `COMMIT_GAP_THRESHOLD` from 10 to 5; record intent now honored even with no changed files

### Distribution Chain Hardening
- Fixed init-project INDEX.md template pollution (was carrying sybermem's own history)
- Fixed init-project settings.json template hardcoded `C:/Users/69046/` paths
- Fixed remote install scripts (`install-remote.ps1/sh`) missing Team skills
- Added `pip show sybermem-core` skip check to avoid redundant venv rebuild on update
- Added `check_project_health.py` self-update mechanism: old project-local health check replaces itself from global template before running
- Added stale protocol block detection: health check now compares block content, not just markers
- Added old heavy SyberMem template detection: files with `## Available Skills` / `## Workflow` are recognized as sybermem-managed and replaced entirely
- Auto-trail conclusions no longer written to Key Conclusions; existing ones moved to Archived
- Digest workflow now archives source record conclusions on completion

### Uninstall Model
- Added project-level uninstall (`sybermem project uninstall`): preserves `.sybermem/` history, non-destructively removes hooks/protocol/settings
- Added global uninstall scripts (`scripts/uninstall.ps1/sh`): removes global skills/CLI/launcher, never touches project history
- README updated with uninstall documentation

### README Restructure
- Both Chinese and English READMEs rewritten around current capabilities and usage, not historical evolution
- Removed `docs/superpowers/specs/` reference from user-facing README

## Reason

SyberMem's injection footprint was too heavy for what skills already define. Core data pipelines had silent bugs (open_bugs never closing, publish→summary contract mismatch, FTS5 built but unused). Distribution chain had template pollution and propagation gaps. Users needed a way to temporarily stop SyberMem without losing history.

## Impact

- **Context efficiency**: ~60-100 lines of per-session injection eliminated
- **Data correctness**: bug lifecycle, publish→summary pipeline, and search coverage all fixed
- **Distribution reliability**: no more hardcoded paths, template pollution, or missing Team skills in remote install
- **User control**: can now temporarily disable SyberMem per-project or globally uninstall
- **Update propagation**: old heavy templates now correctly detected and replaced by `/sybermem-update`

## Verification

- All changes verified with automated assertions before commit
- Non-destructive uninstall verified: user custom env/hooks/content preserved
- Health check self-update verified: old script → global template replacement → re-exec with new logic
- Stale protocol block detection verified: old 7-rule block correctly identified as stale
- Old heavy template detection verified: files with `## Available Skills` correctly identified as sybermem-managed

## Related Changes

- Builds on change-030 (init-project propagation alignment)
- Builds on change-026 (Team skills exposure)
- Builds on change-023 (Team publication pipeline)
