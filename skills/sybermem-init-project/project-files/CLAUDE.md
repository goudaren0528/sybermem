# SyberMem Project Record System

<!-- This file defers to AGENTS.md as the single source of truth for SyberMem instructions. -->
<!-- Claude Code reads CLAUDE.md; OpenCode reads AGENTS.md. Both get the same rules. -->

<!-- SYBERMEM_SESSION_PROTOCOL:START -->
## SyberMem Session Protocol

Before any SyberMem workflow proceeds in this session:

1. Resolve the project root first.
2. Read `.sybermem/INDEX.md` `## Key Conclusions`. Then tell the user: "Loaded N key conclusions from SyberMem." If any conclusions are relevant to the current work context, list them.
3. If `.sybermem/analysis/phase-index.md` exists, treat it as the current structural source of truth for phase-aware workflows.
4. If `/sybermem-summary` is requested and no phase index exists, run `/sybermem-phase-analyze` first.
5. If `/sybermem-digest` is requested without explicit source records and no phase index exists, run `/sybermem-phase-analyze` first.
6. Phase analysis auto-confirms candidates. Use `/sybermem-phase-confirm` to adjust if needed.
7. If important work is happening and a lightweight trail is not enough, prefer `/sybermem-record`.

This protocol block establishes entry rules only. It does not replace the concrete SyberMem commands.
<!-- SYBERMEM_SESSION_PROTOCOL:END -->

The `using-sybermem` protocol block above loads automatically at session start. You can also run `/using-sybermem` manually when you want to inspect the current SyberMem state and get a recommended next command.

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
- SyberMem automatically resolves the project root by walking up from the current working directory to find the nearest ancestor containing both `.sybermem/` and `.claude/settings.json`. This means you can work in any subdirectory and SyberMem will still find the correct project root.
- If only `ADR/` exists at the resolved root, first use of any SyberMem command renames it to `.sybermem/` automatically.
- If both `.sybermem/` and `ADR/` exist, `.sybermem/` is used and `ADR/` is ignored.
- Users should not manually rename legacy `ADR/` directories.

## Workflow

1. **Session start (mandatory)**: Before responding to the user's first message, you MUST read the Key Conclusions section in `.sybermem/INDEX.md` to get project context. Do not skip this step.
2. **During work (proactive association)**: Before modifying code, check if any key conclusions relate to the current work. If so, proactively inform the user of relevant historical decisions or context before proceeding. When encountering architecture, technology choice, or historical questions, search `.sybermem/` for detailed records before answering.
3. **After work (auto/remind mode)**: This project may automatically create a basic SyberMem `change` record from current file changes, or remind the user when meaningful work is completed. `auto` mode = lightweight `change` trail + reminders; `remind` mode = reminders only, no automatic `change` trail. The mode is controlled by `.claude/settings.json` via `SYBERMEM_RECORD_MODE`.
4. **Record type scope**: Automatic mode only writes `change` records from workspace file changes. Use `/sybermem-record` for `decision`, `requirement`, and `bug` records.
5. **Upgrade nudges**: In `auto` or `remind` mode, the stop hook may emit a non-blocking suggestion that a change looks important enough for `/sybermem-record`, or that a recent cluster of work may be ready for `/sybermem-digest`. If you explicitly say something like "这轮结束提醒我记录", the project-level `UserPromptSubmit` hook can capture that intent and the stop hook will prioritize reminding you later. These nudges are hints only and do not block exit.
6. **Summary workflow**: Use `/sybermem-summary` to see the current-state panel for the most recently active confirmed phase when phase analysis exists, or a weekly/monthly fallback report when it does not.
7. **Digest workflow**: Use `/sybermem-digest` when a meaningful phase has stabilized and you want a durable phase conclusion artifact.
8. **Phase analysis workflow**: Use `/sybermem-phase-analyze` to refresh `.sybermem/analysis/phase-index.md` from the full project history. Use `/sybermem-phase-confirm` to explicitly confirm or adjust candidate phases before treating them as canonical.
9. **Mode switching**: Supported modes are `auto` and `remind`. Change them through `/hooks` or by editing `.claude/settings.json`. The default hook helper lives at `.sybermem/hooks/record_change_on_stop.py`.
10. **Managed-file updates**: `/sybermem-update` can refresh missing or stale SyberMem-managed files in this project, but it must not silently overwrite custom local files.
11. File naming: `YYYY-MM-DD-NNN-title.md`

SyberMem commands rely on real project files and durable markdown structure. If a command behavior changes in a new release, the project usually needs `/sybermem-update` to receive the refreshed managed files locally.

## Available Skills

- `/sybermem-record` — Create a record (auto-detects type)
- `/sybermem-summary` — Generate weekly/monthly reports
- `/sybermem-digest` — Create a durable phase digest from existing records
- `/sybermem-theme-digest` — Create a durable topic-level digest that compresses one theme across multiple related phases or records
- `/sybermem-phase-analyze` — Build or refresh the persistent phase index from full project records
- `/sybermem-phase-confirm` — Explicitly confirm, rename, adjust, or reject candidate phases
- `/sybermem-init-project` — Initialize or refresh the SyberMem system in this project
- `/sybermem-update` — Refresh installed SyberMem skills, then re-check this project
- `/using-sybermem` — Show current SyberMem status and the recommended next command
- `/sybermem-search` — Search/query records by keyword, topic, phase range, date range, or record ID
- `/sybermem-link` — Add a forward relation between two existing records

## No Record Needed

Formatting adjustments, comment edits, config tweaks with no functional impact.
