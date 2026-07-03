---
name: sybermem-team-summary
description: Generate the Team management summary from the current project's remembered Team repo or a one-time Team path.
---

# sybermem-team-summary Skill

**Announce at start:** "I'm using the sybermem-team-summary skill to generate a Team management summary."

Use the existing Team summary CLI surface to generate management-consumption outputs.

## Flow

1. Resolve the current project root.
2. Check `.sybermem/project.yaml` for `team.team_path`.
3. If present, run:

```bash
sybermem team summary --team-path <team-path> --format json
```

4. If not present, ask the user for a Team repo path.
5. Report:
- team ID
- summary markdown path
- summary JSON path
- summary-state path
- recommend reading `latest-management-summary.md`

## Output Style

```md
## Team Summary Generated
- Team: ...
- Markdown: ...
- JSON: ...
- Baseline state: ...
- Recommended reading: ...
```
