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

### Step 0: Resolve project root

Before any other operation, walk up from the current working directory to find the nearest ancestor directory (including cwd itself) that contains **both** `.sybermem/` **and** `.claude/settings.json`.

- If found: use that directory as the project root for all subsequent steps. Inform the user if the resolved root differs from cwd: "Using SyberMem project root at `<resolved-path>`".
- If not found (reached git repository root or filesystem root without a match): prompt the user to run `/sybermem-init-project`.

After resolving the project root, apply legacy directory checks against the resolved root:
1. If the resolved root has `.sybermem/`, use it.
2. If the resolved root has only `ADR/`, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If the resolved root has both `.sybermem/` and `ADR/`, use `.sybermem/`, warn that `ADR/` was ignored.
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
- **Use the right layer**: `/sybermem-summary` is for dynamic recent-progress views; use `/sybermem-digest` when you need a durable, indexed phase summary
- **Analysis-aware future**: when `.sybermem/analysis/phase-index.md` exists, future summary behavior should prefer the project’s confirmed phase structure when available over ad hoc record grouping
