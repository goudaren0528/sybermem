---
name: sybermem-summary
description: Use when generating weekly or monthly SyberMem project summaries, including projects that still have legacy ADR storage.
---

# sybermem-summary Skill

Generate SyberMem project progress reports. Defaults to a weekly report; pass the `monthly` argument for a monthly report.

## Usage

- `/sybermem-summary` — Generate this week's report
- `/sybermem-summary monthly` — Generate this month's report

## Directory Resolution Rules

Resolve the project data directory before collecting report data:

1. If `.sybermem/` exists, use it.
2. If only `ADR/` exists, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If both `.sybermem/` and `ADR/` exist, use `.sybermem/`, warn that `ADR/` was ignored, and do not auto-merge them.
4. If neither exists, prompt the user to run `/sybermem-init-project` first.

## Flow

### Step 1: Determine report scope

- No argument or `weekly` → This week (last 7 days)
- `monthly` → This month (last 30 days)

### Step 2: Collect data

Scan `.sybermem/` records in the corresponding time range:

```
.sybermem/changes/      → Feature changes
.sybermem/decisions/    → Technical decisions
.sybermem/requirements/ → Requirement records
.sybermem/bugs/         → Bug fixes
```

Also reference Git log for commit history.

### Step 3: Generate report

Output a concise dynamic report:

```markdown
# Project Progress Report (YYYY-MM-DD ~ YYYY-MM-DD)

## Key Achievements
- ...

## Key Decisions
- ...

## Issues & Fixes
- ...

## Open Issues
- ...

## Next Steps
- ...
```

### Step 4: Monthly report additions

Monthly reports also include:
- Progress summary grouped by week
- Record counts and type distribution
- Trend observations

## Design Principles

- **`.sybermem/` is canonical**: summarize records from the canonical project data directory
- **Legacy compatibility**: old `ADR/` is auto-migrated on first use
- **No persistent storage**: reports are generated dynamically
- **Data-driven**: base the report on actual records and git history
- **Concise output**: keep it readable within one screen
