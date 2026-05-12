---
name: summary
description: Generate project progress report (weekly or monthly), summarize work outcomes
---

# summary Skill

Generate project progress reports. Defaults to weekly report, pass `monthly` argument for monthly report.

## Usage

- `/summary` — Generate this week's report
- `/summary monthly` — Generate this month's report

## Flow

### Step 1: Determine report scope

- No argument or `weekly` → This week (last 7 days)
- `monthly` → This month (last 30 days)

### Step 2: Collect data

Scan record files in ADR/ directory within the corresponding time range:

```
ADR/changes/      → Feature changes
ADR/decisions/    → Technical decisions
ADR/requirements/ → Requirement records
ADR/bugs/         → Bug fixes
```

Also reference Git log for commit history.

### Step 3: Generate report

Dynamic output (not persisted), format:

```markdown
# Project Progress Report (YYYY-MM-DD ~ YYYY-MM-DD)

## Key Achievements
- ...

## Key Decisions
- ADR/decisions/...

## Issues & Fixes
- ADR/bugs/...

## Open Issues
- ...

## Next Steps
- ...
```

### Step 4: Monthly report additional content

Monthly reports add on top of weekly format:
- Progress summary grouped by week
- Monthly statistics (record counts, type distribution)
- Trend observations

## Design Principles

- **No persistent storage**: Reports are generated dynamically to avoid file bloat
- **Data-driven**: Based on actual record files, no speculation
- **Concise output**: Keep it readable within one screen
