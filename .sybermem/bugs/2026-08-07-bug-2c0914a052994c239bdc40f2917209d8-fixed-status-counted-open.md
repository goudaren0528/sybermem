---
type: bug
record_id: bug-2c0914a052994c239bdc40f2917209d8
date: 2026-08-07
title: Bugs with status "fixed" were miscounted as open
key_conclusion: Unified terminal record statuses into a single TERMINAL_STATUSES set so status open-detection and lifecycle classification both treat fixed/resolved/completed/done/closed as closed, fixing fixed bugs being reported as open
topics: [quality, retrieval]
status: fixed
severity: medium
related: [change-087966eda55f40a0aada0f86dd290e29]
---

## Bug Description

`project_status` computed `open_bugs`/`open_requirements` as "status != 'resolved'", but bug records widely use `status: fixed`. So every `fixed` bug was reported as open. The A4 resume brief surfaced this immediately by listing already-fixed bugs (2ffd869f, 9e13ab86, bug-004) under "open items to watch".

## Root Cause

Two separate, drifting notions of "terminal status": `status.py` recognized only `resolved`, while `retrieval.classify_lifecycle` recognized `{resolved, completed, done}` — and neither included `fixed`, the status bugs actually use.

## Solution

Added a single source of truth in `retrieval.py`:

- `TERMINAL_STATUSES = {resolved, fixed, completed, done, closed}`
- `is_open_status(status)` helper.

`status.py` open-detection now uses `is_open_status`; `classify_lifecycle` uses `TERMINAL_STATUSES`. A record with no status field is conservatively treated as open.

Verified: resume no longer lists fixed bugs as open (remaining open items bug-001/bug-003 genuinely have no status field); new tests cover fixed/resolved closed vs status-less open; core suite green.

## Prevention Measures

Any notion of "done/closed/terminal" for records must reference `TERMINAL_STATUSES`, not an inline literal. Inline status comparisons are the drift vector that caused this.
