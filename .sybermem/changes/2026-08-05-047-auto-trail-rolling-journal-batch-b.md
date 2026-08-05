---
type: change
date: 2026-08-05
number: 047
title: Auto-trail rolling journal — stop writing per-stop markdown records (batch B)
status: implemented
author: Sisyphus
related_files: .sybermem/hooks/record_change_on_stop.py, packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py, skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py, packages/core/tests/test_record_intent.py, docs/superpowers/specs/2026-08-05-sybermem-auto-trail-journal-design.md
related: [change-045]
---

## Change Content

Implemented batch B of the audit-driven efficiency work: the stop hook's auto mode no longer writes one Markdown record per session-stop into `.sybermem/changes/` and no longer adds a row to `.sybermem/INDEX.md`. Instead it appends a bounded rolling journal at `.sybermem/.auto-trail.jsonl` (capped at 200 entries).

- Added journal helpers `read_recent_auto_trail(limit)` and `append_auto_trail_journal(date, files, areas, followup_hint)` (bounded + fail-open) in `record_change_on_stop.py`.
- Rewrote `overlaps_recent_auto_trails` to read the last 3 journal entries instead of scanning `changes/*.md` frontmatter; threshold/window unchanged.
- Rewired the `mode == "auto"` write branch to append one journal entry; removed the `render_record`/`update_index`/`next_change_id` calls from that path (functions kept defined).
- Synced all 3 authoritative hook copies.
- Updated `test_stop_hook_nested_cwd_...` to assert the new journal contract (root-relative paths in the journal, `.sybermem` files skipped, no markdown written) instead of the old "writes 1 markdown record" contract.

## Reason for Change

The audit found 26 of 51 records were low-signal auto-trail noise, and each stop wrote a markdown file + rewrote INDEX.md, inflating every parse/index/search/dedup scan. Downstream investigation showed auto-trails are deeply embedded in canonical enumeration (status/publish/hash/search) and 8 are cited by digest `source_records`, so full migration would change publish-hash and status semantics. The user chose the lowest-risk path: stop future writes and treat the trail as a bounded journal, leaving all existing records untouched.

## Impact Scope

- Future auto-mode stops no longer pollute `.sybermem/changes/` or INDEX.md; the change trail lives in a bounded JSONL journal that is not part of the canonical record corpus.
- The existing 26 auto-trail markdown records and their INDEX rows are untouched, so digest provenance, Team publish source_hash, project_status counts, and search behavior for existing records are all unchanged.
- The journal does not feed status/publish/search counts (auto-trails are low-signal evidence already filtered from compact recall).
- Storage/scan churn from new stops drops to a single bounded append instead of a new markdown file + INDEX rewrite.

## Implementation

- `.sybermem/hooks/record_change_on_stop.py`: journal constants (`AUTO_TRAIL_JOURNAL_PATH`, `AUTO_TRAIL_JOURNAL_MAX=200`), helpers, journal-based dedup, and the rewired auto branch (`append_auto_trail_journal(record_date, files, detect_high_level_areas(files), followup_hint)`), with `last_record` no longer derived from a markdown filename.
- Template copies synced byte-identical to the two `project-files/.sybermem/hooks/` locations.

## Test Verification

- Temp git fixture, auto mode: confirmed 0 markdown records written, journal entry appended with root-relative file paths, and no INDEX row added.
- Dedup: identical file set re-run adds no duplicate journal line; a distinct change set adds a new entry.
- Bounded: appending 205 entries caps the file at 200 lines.
- `pytest packages/core` → 83 passed (updated stop-hook test now asserts the journal contract); `pytest packages/cli` → 11 passed.
- `git diff` confirms only the 3 hook copies + test changed; no existing `changes/*.md` or INDEX rows modified. `check-plugin-package.py` → OK.

## Notes

Deferred to a future batch C (larger, independent decision): actually clean up the 26 existing auto-trail records and recompute status/publish signals from the journal — that would change publish source_hash semantics. Spec: docs/superpowers/specs/2026-08-05-sybermem-auto-trail-journal-design.md; plan under docs/superpowers/plans/ (gitignored per repo convention). Relates to change-045 (the P0/P1 round this continues).
