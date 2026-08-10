---
type: change
record_id: change-88bfdebb0f2f4e31bb7b0e70857c288d
date: 2026-08-07
title: SessionStart proactively reminds when commits accrue since the last record
key_conclusion: Added a commit-gap record reminder to the SessionStart context so unrecorded work surfaces proactively, because record timeliness is what keeps reasons and impact from evaporating across sessions
topics: [usability, hooks, automation]
status: implemented
related: [change-003]
---

## Change Content

`session_start_context.py` already surfaced a phase-index stale signal (commits ahead of the phase boundary) but never nudged about unrecorded work. Added:

- `latest_record_date(root)`: newest `YYYY-MM-DD` prefix across `changes/decisions/requirements/bugs`.
- `detect_record_gap(root)`: counts git commits since that date; flags a nudge at >= 3.
- A one-line reminder appended to the SessionStart context when the gap threshold is met, phrased as a suggestion (consider `/sybermem-record`), never an action.

Kept the hook dependency-free (shells git directly, like the existing stale-signal code) so it works on every install. Synced to both distribution copies.

## Reason for Change

A3 in the improvement plan: move recording from a pull model (user must remember) to a light push model. Record timeliness is the lifeblood of a memory system — context evaporates across sessions, so a proactive but non-intrusive reminder is high-leverage.

## Impact Scope

- `.sybermem/hooks/session_start_context.py` + 2 distribution copies.
- Fail-open: no reminder when git/dates unavailable; verified no false nudge on this project (today's records → gap 0).
