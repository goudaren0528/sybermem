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
- If only `ADR/` exists, first use of `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, `/sybermem-digest`, `/sybermem-phase-analyze`, or `/sybermem-phase-confirm` renames it to `.sybermem/` automatically.
- If both `.sybermem/` and `ADR/` exist, use `.sybermem/` and warn that `ADR/` was ignored.
- Users should not manually rename legacy `ADR/` directories.

## Workflow

1. **Session start (mandatory)**: Before responding to the user's first message, you MUST read the Key Conclusions section in `.sybermem/INDEX.md` to get project context. Do not skip this step.
2. **During work (proactive association)**: Before modifying code, check if any key conclusions relate to the current work. If so, proactively inform the user of relevant historical decisions or context before proceeding. When encountering architecture, technology choice, or historical questions, search `.sybermem/` for detailed records before answering.
3. **After work (auto/remind mode)**: This project may automatically create a basic SyberMem `change` record from current file changes, or remind the user when meaningful work is completed. The mode is controlled by `.claude/settings.json` via `SYBERMEM_RECORD_MODE`.
4. **Record type scope**: Automatic mode only writes `change` records from workspace file changes. Use `/sybermem-record` for `decision`, `requirement`, and `bug` records.
5. **Upgrade nudges**: In `auto` mode, the stop hook may also emit a non-blocking suggestion that a change looks important enough for `/sybermem-record`, or that a recent cluster of work may be ready for `/sybermem-digest`. These nudges are hints only and do not block exit.
6. **Digest workflow**: Use `/sybermem-summary` for dynamic weekly/monthly reporting. Use `/sybermem-digest` when a meaningful phase ends and you want a durable, indexed summary in `.sybermem/digests/`.
7. **Phase analysis workflow**: Use `/sybermem-phase-analyze` to refresh `.sybermem/analysis/phase-index.md` from the full project history. Use `/sybermem-phase-confirm` to explicitly confirm or adjust candidate phases before treating them as canonical.
8. **Mode switching**: Supported modes are `auto` and `remind`. Change them through `/hooks` or by editing `.claude/settings.json`. The default hook helper lives at `.sybermem/hooks/record_change_on_stop.py`.
9. File naming: `YYYY-MM-DD-NNN-title.md`

## Available Skills

- `/sybermem-record` — Create a record (auto-detects type)
- `/sybermem-summary` — Generate weekly/monthly reports
- `/sybermem-digest` — Create a durable phase digest from existing records
- `/sybermem-phase-analyze` — Build or refresh the persistent phase index from full project records
- `/sybermem-phase-confirm` — Explicitly confirm, rename, adjust, or reject candidate phases
- `/sybermem-init-project` — Initialize or refresh the SyberMem system in this project
- `/sybermem-update` — Refresh installed SyberMem skills, then re-check this project

## No Record Needed

Formatting adjustments, comment edits, config tweaks with no functional impact.
