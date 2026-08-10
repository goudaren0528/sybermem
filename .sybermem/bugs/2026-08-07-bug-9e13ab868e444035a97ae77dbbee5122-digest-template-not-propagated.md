---
type: bug
record_id: bug-9e13ab868e444035a97ae77dbbee5122
date: 2026-08-07
title: Digest template was existence-checked only, so template improvements never propagated to existing projects
key_conclusion: Made digest-template.md content-checked in the health check (stale when missing coverage_hash) so /sybermem-update replaces stale copies, closing a distribution-chain gap that would have stranded the coverage_hash capability on fresh installs only
topics: [distribution, hooks, quality]
status: fixed
severity: high
related: [change-b70ea980b0934358aad0ba47b64bff33, bug-004]
---

## Bug Description

SyberMem ships managed files as multiple copies: project-local `.sybermem/`, the canonical distribution source `packages/claude-skills/sybermem-init-project/project-files/`, and the mirror `skills/sybermem-init-project/project-files/`. `/sybermem-update` uses `check_project_health.py` to decide which managed files to create or replace in an existing project.

`digest-template.md` was classified with `check_file_exists` — present means "fresh", full stop. Its content was never compared. So when E3 added the `coverage_hash` field to the digest template, existing projects running `/sybermem-update` would keep their old template forever: the coverage_hash capability (mechanical stale-digest detection) would reach fresh installs only. This is the same class of silent distribution break as bug-001 and bug-004.

## Root Cause

The health check has two tiers of managed-file classification — `check_record_template` (content-aware: stale → replace) and `check_file_exists` (existence-only: create-if-missing). The phase-digest template was wired to the existence-only tier, and the file map in `main()` and the action generator in `generate_actions` each list managed files separately, so a template could be checked one way and actioned another with no single source of truth catching the mismatch.

## Solution

- Added `check_digest_template(path)`: returns `stale` when the template lacks `coverage_hash:` (covers both legacy `fingerprint`-only templates and any other pre-capability copy), else `fresh`.
- Wired `digest-template.md` to it in `main()`, and moved it out of the existence-only loop in `generate_actions` into a create/replace block.
- Synced the change to both distribution copies of `check_project_health.py`.
- Added regression tests in `test_init_project_distribution.py`:
  - shipped digest template carries `coverage_hash` and no longer carries `fingerprint`;
  - a legacy `fingerprint`-only template is classified `stale` and produces a `replace` action;
  - canonical vs mirror copies of digest template / health check / task_recall stay byte-identical.

Verified live: `check_project_health.py` against this project reports the digest template `fresh` (it now has coverage_hash) with no action; core suite 126 passed.

## Prevention Measures

Two general guardrails are tracked as D1 follow-ups in `docs/improvement-plan-2026-08-07.md`: (1) collapse the managed-file inventory + its check kind into a single source of truth so `main()` and `generate_actions` cannot drift; (2) extend the byte-identical distribution-consistency test to every managed-file class. Rule of thumb: any new capability field must ship with a health-check stale predicate, or the distribution is not complete.
