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
| Pending candidate status | `$SyberMemCli habit intent-status --format json` / `"$SYBERMEM_CLI" habit intent-status --format json` |
| Clear a candidate | `$SyberMemCli habit intent-clear` / `"$SYBERMEM_CLI" habit intent-clear` |
| Awareness snapshot | `$SyberMemCli habit awareness --format json` / `"$SYBERMEM_CLI" habit awareness --format json` |

Types: `workflow`, `style`, `tooling`, `communication`, `review`, `avoidance`.

Use `--injection-policy prompt_ok_when_supported` only when the user explicitly wants prompt-time reminders on supported hosts such as Claude Code, OpenCode, or Codex. Default `compaction_ok` is safer and works for manual/compaction carry-forward.

## Workflow

1. **Check for a pending candidate first.** Run `habit intent-status --format json`. A pending candidate means a supported host (e.g. OpenCode `chat.message`) passively detected a reusable-preference phrase and wrote a candidate-only intent (it is NOT an active habit). If one is pending, surface it and offer to confirm it in one step (see "Confirming a pending candidate" below) before treating the request as a fresh add.
2. Classify the request: confirm-candidate, add, list, search, pause, delete, remind, or inject.
3. For add requests, normalize the habit into one short statement and choose type/tags.
4. If the user did not explicitly authorize saving, ask one confirmation question and stop.
5. Run the matching CLI command.
6. Summarize the result with habit id and current status.

## Confirming a pending candidate

The passive capture is candidate-only and never creates a habit on its own. To turn a pending candidate into a real habit in one confirmed step:

1. Read it: `$SyberMemCli habit intent-status --format json`. The candidate JSON carries a suggested `habit_type` but no statement.
2. Propose ONE normalized statement to the user based on the recent conversation, plus the suggested type. Ask them to confirm (confirmation-first still applies — the passive candidate is a hint, not authorization).
3. On confirmation, add it: `$SyberMemCli habit add --type <type> --applies-to <tag> "<normalized statement>"`.
4. Clear the candidate so it does not linger: `$SyberMemCli habit intent-clear`.

If the user declines, just clear the candidate with `habit intent-clear` and do not add anything.

## Semantic nomination (you judge intent, not keywords)

A pending candidate is only ONE trigger. The keyword prefilter that writes it
(`always/habit/prefer/以后/习惯/...`) is a cheap hot-path guard, NOT the decision:
many reusable preferences and norms are phrased without any trigger word. YOU
decide, from the conversation's meaning, whether something is worth fixing down.

Nominate a candidate (confirmation-first) when EITHER holds:

- The user states a reusable preference or a reasonable standing requirement, even
  without a trigger word (e.g. "回复用中文", "先出计划再写代码", "PR 要小而聚焦").
- The same constraint is expressed **two or more times** in this session/section —
  repetition is a strong signal it should become a norm.

Route by where it belongs (no new storage — use the existing homes):

- Personal / cross-project preference → a **user habit** (`habit add ...`).
- Project-specific convention/norm → suggest a **`decision` or `requirement` record**
  via `/sybermem-record` instead (that is the norm's real home). Do not force it into
  a user habit.

Friction rules (keep it friendly, never nagging):

- Only nominate when you are reasonably confident; when unsure, stay silent.
- Never interrupt mid-task. Raise a nomination at a natural stopping point.
- Batch multiple candidates into ONE offer; each is one-step to confirm.
- If the user declines, drop it and do not re-raise the same nomination this session.
- Confirmation-first always (L1): a nomination is a hint, never authorization to write.

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
