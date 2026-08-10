---
type: change
record_id: change-dcdc1324b2f340c1acb470df990a37c0
date: 2026-08-07
title: Honest labeling for the publish preview memory source hash
key_conclusion: Relabeled the publish preview hash as "memory source hash" with an explicit scope note (stale-preview guard, not a full publish-safety proof) in user-facing text, without renaming the stable persisted field key
topics: [governance, quality]
status: implemented
related: [bug-002]
---

## Change Content

`render_publish_status_text` now prints "memory source hash" (not bare "source hash"), and for a preview adds a one-line scope note: `(scope: project_records_digests_identity — a stale-preview guard over project memory, not a full publish-safety proof)`. The stale_preview rejection text now explains "project memory changed since the reviewed preview" and labels both hashes as memory source hashes.

## Reason for Change

G4: "source hash" read like a broad publish-safety guarantee, but it only covers project records + digests + identity and only guards against publishing a stale reviewed preview. Renaming the persisted `source_hash` key was rejected — it is a stable contract across payloads, meta.json, the `--preview-source-hash` CLI flag, and Team summary consumers, so a rename would break already-published data and the flag contract. Clarifying the user-facing wording achieves honesty with zero contract breakage.

## Impact Scope

- `packages/cli/sybermem_cli/publish_render.py`: preview + stale_preview text only.
- No change to persisted keys, CLI flags, or JSON payload shape.
- Verified: render output shows the new label + scope note.
