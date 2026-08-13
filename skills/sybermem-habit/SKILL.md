---
name: sybermem-habit
description: Use when the user wants SyberMem to remember, review, search, pause, delete, or be reminded about personal preferences, habits, working style, tool choices, review style, communication style, or cross-project user-level memory.
---

# sybermem-habit Skill

**Announce at start:** "I'm using the sybermem-habit skill to manage user-level habit memory."

Manage explicit User Habit Memory. Habits are personal preferences stored under `~/.sybermem/user-habits/` or `SYBERMEM_HOME/user-habits/`, not project `.sybermem/` records and not Team memory.

## Hard Rules

- Confirmation first: do not create an active habit unless the user explicitly asks to remember it or confirms your normalized statement.
- Never use `/sybermem-record` for personal habits.
- Never write raw prompt text into project records or Team memory.
- Do not infer habits silently from behavior.
- Prefer normalized, durable statements over verbatim user phrasing.
- OpenCode supports bounded prompt-time habit reminders through `chat.message` + `experimental.chat.system.transform`; this skill and the CLI remain the explicit management path.

## CLI Resolution

Before running SyberMem CLI commands, resolve a command variable first. On Windows PowerShell, prefer `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd` and store the chosen command in `$SyberMemCli`; on Unix, prefer `$HOME/.claude/sybermem/cli/sybermem` and store the chosen command in `"$SYBERMEM_CLI"`. If the fixed launcher is unavailable, fall back to bare `sybermem`. Do not modify persistent PATH automatically. Command examples below use `$SyberMemCli` / `"$SYBERMEM_CLI"`.

## Commands

| Intent | Command |
|---|---|
| Add habit | `$SyberMemCli habit add --type <type> --applies-to <tag> "<normalized statement>"` / `"$SYBERMEM_CLI" habit add --type <type> --applies-to <tag> "<normalized statement>"` |
| List active | `$SyberMemCli habit list` / `"$SYBERMEM_CLI" habit list` |
| List all | `$SyberMemCli habit list --all --format json` / `"$SYBERMEM_CLI" habit list --all --format json` |
| Search | `$SyberMemCli habit search "<query>" --format json` / `"$SYBERMEM_CLI" habit search "<query>" --format json` |
| Pause | `$SyberMemCli habit pause <habit-id>` / `"$SYBERMEM_CLI" habit pause <habit-id>` |
| Delete | `$SyberMemCli habit delete <habit-id>` / `"$SYBERMEM_CLI" habit delete <habit-id>` |
| Visible reminder | `$SyberMemCli habit remind --context "<bounded context>" --format markdown` / `"$SYBERMEM_CLI" habit remind --context "<bounded context>" --format markdown` |
| Manual injection | `$SyberMemCli habit inject --context "<bounded context>" --format markdown` / `"$SYBERMEM_CLI" habit inject --context "<bounded context>" --format markdown` |

Types: `workflow`, `style`, `tooling`, `communication`, `review`, `avoidance`.

Use `--injection-policy prompt_ok_when_supported` only when the user explicitly wants prompt-time reminders on supported hosts such as Claude Code, OpenCode, or Codex. Default `compaction_ok` is safer and works for manual/compaction carry-forward.

## Workflow

1. Classify the request: add, list, search, pause, delete, remind, or inject.
2. For add requests, normalize the habit into one short statement and choose type/tags.
3. If the user did not explicitly authorize saving, ask one confirmation question and stop.
4. Run the matching CLI command.
5. Summarize the result with habit id and current status.

## Examples

User: "以后改代码前先给方案，帮我记住。"

Run:

```bash
$SyberMemCli habit add --type workflow --applies-to planning --applies-to implementation "Prefer plans before code changes"
```

User: "之后每次都提醒我这个偏好。"

Run:

```bash
$SyberMemCli habit add --type workflow --applies-to planning --applies-to implementation --injection-policy prompt_ok_when_supported "Prefer plans before code changes"
```

User: "这像不像一个要记住的习惯？"

Run:

```bash
$SyberMemCli habit remind --context "planning implementation preference" --format markdown
```

## Common Mistakes

| Mistake | Correct behavior |
|---|---|
| Writing a habit through `/sybermem-record` | Use `$SyberMemCli habit add` or `"$SYBERMEM_CLI" habit add`; habits are user-level. |
| Saving a habit after observing repeated behavior | Ask for confirmation first. |
| Storing the user's raw prompt as the habit | Store a normalized statement. |
| Claiming unsupported platform reminders | State the actual boundary: Claude Code, OpenCode, and Codex support prompt-time habit reminders on their supported prompt seams; Codex also supports bounded startup context, prompt recall, record-intent capture, Stop record nudges, and compact re-seed markers, but not hidden auto-resume or direct compaction prompt injection. Gemini/Cursor/Kimi do not have runtime reminder wiring. |
| Adding prompt-time policy by default | Use `prompt_ok_when_supported` only on explicit request. |

## Completion

After a successful add/list/search/pause/delete/remind operation, report only the relevant habit ids, status, and next available action. Do not create project records for habit-only work.
