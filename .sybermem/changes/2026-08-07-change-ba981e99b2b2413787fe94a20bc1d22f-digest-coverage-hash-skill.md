---
type: change
record_id: change-ba981e99b2b2413787fe94a20bc1d22f
date: 2026-08-07
title: Digest skill and template now emit the computed coverage_hash
key_conclusion: Completed the E3 skill-side work so the digest template carries a real computed coverage_hash and the digest skill instructs computing it exactly as core does, making mechanical stale-digest detection actually fire in production
topics: [digest, distribution, quality]
status: implemented
related: [change-b70ea980b0934358aad0ba47b64bff33]
---

## Change Content

Follow-on to the E3 core mechanism (change-b70ea980...). The core could detect stale digests, but nothing produced the `coverage_hash` the check reads. This change wires the producer side:

- Replaced the never-computed `fingerprint: {{fingerprint}}` placeholder with `coverage_hash: {{coverage_hash}}` in the digest template (all 3 canonical/distribution copies).
- Updated `sybermem-digest/SKILL.md` (both copies) with a new Step 7a describing the exact deterministic algorithm (sorted `rel_path:sha256` lines joined by `\n`, then SHA-256), and telling the skill to prefer calling `sybermem_core.digest_coverage.compute_coverage_hash(root, source_records)` rather than reimplementing it, so the written value always matches what the freshness check recomputes.
- Added a Red Flag against leaving the placeholder unfilled or hashing anything other than the exact `source_records` set.

## Reason

E3 shipped the detection mechanism (`digest_coverage.py` + search annotation) but a mechanism with no producer is inert. Without the skill emitting `coverage_hash`, every new digest would classify as `unknown` forever and stale digests would keep reading as authoritative — the exact trust gap E3 set out to close.

## Impact Scope

- `.sybermem/templates/digest-template.md` + `packages/claude-skills/.../digest-template.md` + `skills/.../digest-template.md`: `coverage_hash` field.
- `packages/claude-skills/sybermem-digest/SKILL.md` + `skills/sybermem-digest/SKILL.md`: Step 7/7a/8 + Red Flag.
- Distribution propagation for the template addition is handled by bug-9e13ab86... (health-check now replaces stale digest templates).
- Verified: core suite 126 passed; live health check reports this project's digest template fresh.
