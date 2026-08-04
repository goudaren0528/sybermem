---
type: bug
date: 2026-08-04
number: 003
title: Publish trust summary and skill flow gaps
severity: high
---

## Bug Description

Two reviews found high-impact Team publish usability and completeness gaps. Team management summaries did not expose the full publish trust envelope that was already written to Team `meta.json`, the primary `/sybermem-team-publish` skill documented direct publish as the default path, publish preview freshness could report `current` when the phase index was missing, and blocked no-project previews could report an ancestor path instead of the actual invocation path.

## Root Cause

The Team publish trust work landed in the publish metadata path first, but management-summary loading still projected only older fields. The skill docs were not upgraded with the preview hash binding even though the CLI supported `--preview` and `--preview-source-hash`. Preview freshness used the status phase lifecycle alone, so missing structural phase truth inherited the default active/current status. Blocked preview diagnostics used the resolved project root for missing identity cases, which is misleading when a broad ancestor such as the home directory is accidentally detected.

## Solution

The fix threads `source_revision`, `source_hash`, `published_at`, `source_scope`, `local_changes_after_publish`, `stale`, `conflict`, `review_required`, and a recommended next action into Team management summary JSON and Markdown. The mirrored Team publish skills now require preview -> review -> publish with the exact preview source hash and instruct agents to stop on `stale_preview`. Publish preview freshness now treats missing or not-yet-analyzed phase indexes as stale. Blocked preview payloads report the invoked path for no-project or missing-identity diagnostics.

## Prevention Measures

Focused tests now cover Team summary trust fields, missing-phase preview freshness, blocked preview path reporting, and mirrored skill instructions. The verification included full pytest plus an isolated temp Team Git smoke proving preview hash publish, summary trust fields, no configured remote, and `pushed=false`.

## Related Changes

Related to `change-037`, `bug-002`, `change-039`, and `decision-002`.
