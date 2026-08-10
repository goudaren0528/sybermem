---
type: change
record_id: change-358d10ce63284f98a90e8da4bbbf8079
date: 2026-08-07
title: Init-project offers an opt-in first sample record on fresh projects
key_conclusion: Added an opt-in sample record step to init-project for brand-new projects so new users immediately see a record and can try resume, without violating the scan-but-do-not-auto-create-records invariant
topics: [usability, skills]
status: implemented
related: [change-b135cb2e65a24808aaef1f3007acee43]
---

## Change Content

Added Step 7.5 to `sybermem-init-project/SKILL.md`: on a brand-new project only, after the structure is created, the skill offers (asks y/n) to create one illustrative `change` record. Only on explicit opt-in does it write via the record fast path plus `sybermem project index build`/`check`. The summary's Next steps gains a line pointing fresh users at `/sybermem-resume`.

Never triggers on existing-codebase init or on a refresh, and never without opt-in.

## Reason for Change

A5: a freshly initialized `.sybermem/` is empty, so new users have nothing concrete to look at and no quick way to see what recall/resume produce. An opt-in sample gives immediate feedback while preserving the long-standing "scan but don't auto-create records for existing code" principle.

## Impact Scope

- `packages/claude-skills/sybermem-init-project/SKILL.md` + mirror (byte-identical, enforced by the skill-tree consistency test).
