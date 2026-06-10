---
name: sybermem-summary
description: Use when generating weekly or monthly SyberMem project summaries, including projects that still have legacy ADR storage.
---

# sybermem-summary Skill

Generate SyberMem project current-state summaries. When `.sybermem/analysis/phase-index.md` exists and contains confirmed phases, default to the most recently active confirmed phase. Fall back to weekly/monthly time-window reporting only when confirmed phase structure is unavailable.

## Core Invariants

- **Summary is a dynamic current-state panel, not a durable conclusion artifact.**
- **When confirmed phase structure exists, summary must prefer it over ad hoc grouping.**

## Usage

- `/sybermem-summary` — Show the current-state panel for the most recently active confirmed phase
- `/sybermem-summary weekly` — Force the weekly fallback report
- `/sybermem-summary monthly` — Force the monthly fallback report

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

### Step 1: Determine summary mode

- If `.sybermem/analysis/phase-index.md` does not exist → automatically trigger `/sybermem-phase-analyze` first to generate it, then continue
- If `.sybermem/analysis/phase-index.md` exists and contains at least one confirmed phase → use the most recently active confirmed phase as the default summary target
- If the user explicitly passes `weekly` → force the weekly fallback mode
- If the user explicitly passes `monthly` → force the monthly fallback mode
- If no confirmed phase structure exists after analysis → fall back to weekly mode

### Step 2: Collect data

If using phase-aware mode:
- read `.sybermem/analysis/phase-index.md`
- identify the most recently active confirmed phase
- collect the raw records covered by that phase
- inspect only recent raw records as supporting detail when needed

If using fallback time-window mode:
- scan `.sybermem/` records in the requested time range
- also reference git log for commit history

### Step 3: Generate summary

In phase-aware mode, output this dynamic current-state panel:

```markdown
# Phase Summary: <phase title>

## Current Phase
- ...

## Status
- ...

## Open Issues
- ...

## Next Steps
- ...

## Recent Changes
- ...
```

In fallback weekly/monthly mode, keep the current time-window report shape.

## Design Principles

- **`.sybermem/` is canonical**: summarize records from the canonical project data directory
- **Legacy compatibility**: old `ADR/` is auto-migrated on first use
- **No persistent storage**: summaries are generated dynamically
- **Prefer confirmed phase structure**: when `.sybermem/analysis/phase-index.md` contains confirmed phases, use that structure before ad hoc record grouping
- **Current-state only**: `/sybermem-summary` answers “what is the current state of the most relevant confirmed phase?”
- **Not a digest**: `/sybermem-summary` is a dynamic status panel; use `/sybermem-digest` for a durable phase conclusion artifact

## Terminal State

This skill is complete when:
- the dynamic current-state panel (or fallback time-window report) has been output to the user
- no file has been written (summary is non-persistent)
- **Concise output**: keep it readable within one screen
- **Data-driven**: base the output on actual records and git history when needed for supporting detail only.
