---
type: decision
date: 2026-08-05
number: 003
title: Deferral decisions for the four remaining audit follow-ups + skill quick-guide pilot
status: decided
supersedes:
related: [change-045, change-048]
---

## Context

After landing the audit-driven P0/P1 fixes and batches B/D/E/F (change-045/047/048), four follow-ups from docs/audit/2026-08-05-sybermem-comprehensive-audit.md remained, each needing an owner decision because they carry real risk or depend on external factors:

1. Real CI green (needs a GitHub push to run the matrix + install-smoke).
2. Batch C: clean up the 26 legacy auto-trail records and recompute status/publish from the journal.
3. Skill machine-contract slimming (init-project etc.).
4. Codex/Cursor/Kimi runtime completion.

## Considered Options

For each item the options were: do it now (larger scope), do a minimal/pilot slice, or defer.

- CI: push-and-iterate vs local-only-prep vs defer.
- Batch C: full cleanup + recompute vs archive-only vs defer.
- Skill slimming: rewrite machine contract vs add a human quick-guide layer only vs defer.
- Non-core platforms: complete all three vs pilot one vs defer.

## Final Decision

- **Real CI green: DEFER.** ci.yml stays in the repo; push/iterate happens whenever the owner is ready to release. Not touched this round.
- **Batch C (legacy auto-trail cleanup): DO NOT DO.** The existing 26 records already stopped growing (batch B). Cleanup benefit is below the risk of changing publish `source_hash` semantics and breaking the 8 digest `source_records` references.
- **Codex/Cursor/Kimi runtime: DO NOT DO, keep placeholders.** Honestly labelled as metadata placeholders (batch D); no runtime investment until there is real user demand.
- **Skill slimming: DO the low-risk variant — add a human quick-guide layer, keep the machine contract.** Piloted on the most ceremony-heavy skill (init-project) only.

## Impact and Consequences

- Three items are consciously parked with documented rationale, so a future session knows why they were not done rather than assuming they were missed.
- The init-project skill now leads with a plain-language quick guide marked "not the execution contract"; the HARD-GATE / Flow / Red Flags remain authoritative, so agent behavior is unchanged while human cognitive load drops.
- No change to publish semantics, platform claims, or CI state this round.

## Related Changes

- change-045: audit-driven P0/P1 round.
- change-048: batches D/E/F (distribution, terminology, workspace stale detection).
- init-project SKILL quick-guide layer (committed 69412f3).

## Notes

Revisit triggers: (1) CI — when preparing a release; (2) Batch C — only if the auto-trail corpus becomes a measured problem AND a migration that preserves digest provenance + publish hashing is designed; (3) non-core platforms — when a platform gains real users; (4) skill slimming — if the init-project quick-guide pilot proves out, extend to search / using-sybermem / record / update next.
