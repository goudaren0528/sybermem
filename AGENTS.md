# ADR Record System

## Core Rule

After completing meaningful work, run `/record` to create a record. AI auto-detects the type.

## Directories

- `ADR/changes/` — Feature changes
- `ADR/decisions/` — Technical decisions
- `ADR/requirements/` — Requirements / discussions
- `ADR/bugs/` — Bug fixes
- `ADR/INDEX.md` — Master index

## Workflow

1. **Session start (mandatory)**: Before responding to the user's first message, you MUST read the Key Conclusions section in `ADR/INDEX.md` to get project context. Do not skip this step.
2. **During work (proactive association)**: Before modifying code, check if any key conclusions relate to the current work. If so, proactively inform the user of relevant historical decisions or context before proceeding. When encountering architecture, technology choice, or historical questions, search `ADR/` for detailed records before answering.
3. **After work (proactive reminder)**: After completing feature development, bug fixes, technical decisions, or requirement discussions, proactively ask the user: "Would you like to create a record? I can run /record." Don't wait for the user to remember.
4. File naming: `YYYY-MM-DD-NNN-title.md`

## Available Skills

- `/record` — Create a record (auto-detects type)
- `/init-project` — Initialize ADR system
- `/summary` — Generate weekly/monthly report

## No Record Needed

Formatting adjustments, comment edits, config tweaks with no functional impact.
