---
type: change
date: 2026-08-05
number: 049
title: Extend human quick-guide layer to the remaining ceremony-heavy skills
status: implemented
author: Sisyphus
related_files: packages/claude-skills/sybermem-search/SKILL.md, packages/claude-skills/using-sybermem/SKILL.md, packages/claude-skills/sybermem-record/SKILL.md, packages/claude-skills/sybermem-update/SKILL.md, skills/sybermem-search/SKILL.md, skills/using-sybermem/SKILL.md, skills/sybermem-record/SKILL.md, skills/sybermem-update/SKILL.md
related: [decision-003]
---

## Change Content

Extended the init-project quick-guide pilot to the four remaining ceremony-heavy skills identified by the audit: `sybermem-search`, `using-sybermem`, `sybermem-record`, `sybermem-update`. Each now leads with a `## Quick guide (for humans)` section (what it does, when to run, what you get), placed after the one-line overview and before the machine contract. Applied to the source under `packages/claude-skills` and synced to the `skills/` mirror.

## Reason for Change

decision-003 recorded that if the init-project quick-guide pilot proved out, it should extend to search / using-sybermem / record / update. The owner confirmed the extension. The audit (§3) flagged these skills as reading like compliance manuals, raising cognitive load for humans.

## Impact Scope

- People reading these skills get a short plain-language orientation before the HARD-GATE / Flow ceremony.
- Agent behavior is unchanged: each quick guide is explicitly marked "NOT the execution contract — the HARD-GATE / Flow / query/verification sections below are authoritative and win on any conflict." No machine-contract content was removed or reworded.
- Source and mirror stay byte-identical (sync-plugin-skills).

## Implementation

- Inserted a blockquote-marked quick-guide section into each of the 4 source SKILL.md files, then ran `scripts/sync-plugin-skills.py` to propagate to `skills/`.
- Placement respects each skill's early control flow (e.g. after `<SUBAGENT-STOP>` in using-sybermem).

## Test Verification

- All 4 mirrors verified identical to their source (MD5).
- `pytest packages/core` → 86 passed; `pytest packages/cli` → 11 passed.
- `check-plugin-package.py` → OK (skill parity + claude plugins validate).

## Notes

Completes the skill-slimming direction from the audit §3 improvement framework using the low-risk "add human layer, keep machine contract" variant. init-project was the pilot (committed earlier); this covers the rest. Continues decision-003.
