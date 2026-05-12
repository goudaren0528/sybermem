---
name: summary
description: Use when generating weekly or monthly SyberMem project summaries, including projects that still have legacy ADR/ storage.
---

# summary Skill

Generate SyberMem project progress reports. Defaults to a weekly report; pass the `monthly` argument for a monthly report.

## Usage

- `/summary` — Generate this week's report
- `/summary monthly` — Generate this month's report

## Directory Resolution Rules

Resolve the project data directory before collecting report data:

1. If `.sybermem/` exists, use it.
2. If only `ADR/` exists, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If both `.sybermem/` and `ADR/` exist, use `.sybermem/`, warn that `ADR/` was ignored, and do not auto-merge them.
4. If neither exists, prompt the user to run `/init-project` first.

## Flow

### Step 1: Determine report scope

- No argument or `weekly` → This week (last 7 days)
- `monthly` → This month (last 30 days)

### Step 2: Collect data

Scan record files in `.sybermem/` within the corresponding time range:

```
.sybermem/changes/      → Feature changes
.sybermem/decisions/    → Technical decisions
.sybermem/requirements/ → Requirement records
.sybermem/bugs/         → Bug fixes
```

Also reference Git log for commit history.

### Step 3: Generate report

Dynamic output (not persisted), format:

```markdown
# Project Progress Report (YYYY-MM-DD ~ YYYY-MM-DD)

## Key Achievements
- ...

## Key Decisions
- .sybermem/decisions/...

## Issues & Fixes
- .sybermem/bugs/...

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

- **`.sybermem/` is canonical**: Reports summarize records from the canonical project data directory
- **Legacy compatibility**: Upgrading skills is enough; old `ADR/` is auto-migrated on first use
- **No persistent storage**: Reports are generated dynamically to avoid file bloat
- **Data-driven**: Based on actual record files, no speculation
- **Concise output**: Keep it readable within one screen
