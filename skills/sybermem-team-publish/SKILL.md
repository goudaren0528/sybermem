---
name: sybermem-team-publish
description: Publish the current project into Team memory using the remembered Team association or a one-time Team path.
---

# sybermem-team-publish Skill

**Announce at start:** "I'm using the sybermem-team-publish skill to publish this project into Team memory."

Use the existing Team publication pipeline through the `sybermem` CLI.

## Flow

1. Resolve the current project root.
2. Check `.sybermem/project.yaml` for a `team:` block.
3. If the project is already linked to Team memory, run:

```bash
sybermem publish status --format json
```

4. If the project is not yet linked to Team memory, ask the user for a Team repo path, then run:

```bash
sybermem publish status --team-path <path> --format json
```

5. Report:
- team ID
- project slug
- files updated
- whether Team push succeeded

## Output Style

```md
## Team Publish
- Team: ...
- Project: ...
- Files updated:
  - ...
- Push: success / failed
```
