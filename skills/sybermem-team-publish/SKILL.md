---
name: sybermem-team-publish
description: Publish the current project into Team memory using the remembered Team association or a one-time Team path.
---

# sybermem-team-publish Skill

**Announce at start:** "I'm using the sybermem-team-publish skill to publish this project into Team memory."

Use the existing Team publication pipeline through the `sybermem` CLI. Team publish is a high-impact action: always use preview -> review -> publish with the preview source hash.

## Flow

1. Resolve the current project root.
2. Check `.sybermem/project.yaml` for a `team:` block.
3. Generate a read-only preview. If the project is already linked to Team memory, run:

```bash
sybermem publish status --preview --format json
```

4. If the project is not yet linked to Team memory, ask the user for a Team repo path, then preview with:

```bash
sybermem publish status --team-path <path> --preview --format json
```

5. Review the preview before publishing. Check and report the trust envelope:
- source revision
- source hash
- freshness
- conflicts
- review required

6. Only if the preview is acceptable, publish with the exact preview hash:

```bash
sybermem publish status --preview-source-hash <source_hash_from_preview> --format json
```

If using a one-time Team path, keep the same path:

```bash
sybermem publish status --team-path <path> --preview-source-hash <source_hash_from_preview> --format json
```

If publish returns `stale_preview`, stop and generate a new preview. Do not retry with the old hash.

7. Report:
- team ID
- project slug
- files updated
- whether Team push succeeded
- source revision / source hash
- stale / conflict / review-required state

## Output Style

```md
## Team Publish
- Team: ...
- Project: ...
- Files updated:
  - ...
- Source revision: ...
- Source hash: ...
- Trust: stale=no, conflict=no, review-required=yes
- Push: success / failed
```
