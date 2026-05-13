# SyberMem Project Record System

## Core Rule

After completing meaningful work, run `/sybermem-record` to create a record. AI auto-detects the type.

## Directories

- `.sybermem/changes/` — Feature changes
- `.sybermem/decisions/` — Technical decisions
- `.sybermem/requirements/` — Requirements / discussions
- `.sybermem/bugs/` — Bug fixes
- `.sybermem/INDEX.md` — Master index

## Directory Resolution

- `.sybermem/` is the canonical project data directory.
- If `.sybermem/` exists, use it.
- If only `ADR/` exists, first use of `/sybermem-init-project`, `/sybermem-record`, or `/sybermem-summary` renames it to `.sybermem/` automatically.
- If both `.sybermem/` and `ADR/` exist, use `.sybermem/` and warn that `ADR/` was ignored.
- Users should not manually rename legacy `ADR/` directories.

## Workflow

1. **Session start (mandatory)**: Before responding to the user's first message, you MUST read the Key Conclusions section in `.sybermem/INDEX.md` to get project context. Do not skip this step.
2. **During work (proactive association)**: Before modifying code, check if any key conclusions relate to the current work. If so, proactively inform the user of relevant historical decisions or context before proceeding. When encountering architecture, technology choice, or historical questions, search `.sybermem/` for detailed records before answering.
3. **After work (auto/remind mode)**: This project may automatically create a basic SyberMem `change` record from current file changes, or remind the user when meaningful work is completed. The mode is controlled by `.claude/settings.json` via `SYBERMEM_RECORD_MODE`.
4. **Record type scope**: Automatic mode only writes `change` records from workspace file changes. Use `/sybermem-record` for `decision`, `requirement`, and `bug` records.
5. **Mode switching**: Supported modes are `auto` and `remind`. Change them through `/hooks` or by editing `.claude/settings.json`. The default hook helper lives at `.sybermem/hooks/record_change_on_stop.py`.
6. File naming: `YYYY-MM-DD-NNN-title.md`

## Available Skills

- `/sybermem-record` — Create a record (auto-detects type)
- `/sybermem-init-project` — Initialize or refresh the SyberMem system in this project
- `/sybermem-summary` — Generate weekly/monthly reports
- `/sybermem-update` — Refresh installed SyberMem skills, then re-check this project

## No Record Needed

Formatting adjustments, comment edits, config tweaks with no functional impact.
