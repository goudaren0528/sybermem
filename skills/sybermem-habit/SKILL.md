---
name: sybermem-habit
description: Use when the user wants SyberMem to remember, review, search, pause, delete, or be reminded about personal preferences, habits, working style, tool choices, review style, communication style, or cross-project user-level memory.
---

# sybermem-habit Skill

**Announce at start:** "I'm using the sybermem-habit skill to manage user-level habit memory."

Manage explicit User Habit Memory. Habits are personal preferences stored under `~/.sybermem/user-habits/` or `SYBERMEM_HOME/user-habits/`, not project `.sybermem/` records.

## Hard Rules

- Confirmation first: do not create an active habit unless the user explicitly asks to remember it or confirms your normalized statement.
- Never use `/sybermem-record` for personal habits.
- Never write raw prompt text into project records.
- Do not infer habits silently from behavior.
- Prefer normalized, durable statements over verbatim user phrasing.
- A pending candidate carries a bounded `summary` of the user's own words (a short, filtered fragment — not the full prompt) plus a suggested type/scope. Use it as a proposal to normalize from, never as an already-active habit.
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
| Test prompt-time recall | `$SyberMemCli habit test --context "<bounded context>"` / `"$SYBERMEM_CLI" habit test --context "<bounded context>"` |
| Explain one habit | `$SyberMemCli habit explain --id <habit-id> --context "<bounded context>" --format json` / `"$SYBERMEM_CLI" habit explain --id <habit-id> --context "<bounded context>" --format json` |
| Pending candidates (list) | `$SyberMemCli habit intent-status --format json` / `"$SYBERMEM_CLI" habit intent-status --format json` |
| Discard ONE candidate | `$SyberMemCli habit intent-discard <candidate-id>` / `"$SYBERMEM_CLI" habit intent-discard <candidate-id>` |
| Clear ALL candidates | `$SyberMemCli habit intent-clear` / `"$SYBERMEM_CLI" habit intent-clear` |
| Awareness snapshot | `$SyberMemCli habit awareness --format json` / `"$SYBERMEM_CLI" habit awareness --format json` |

`habit intent-status --format json` returns `{ "count": N, "candidates": [ { "candidate_id", "habit_type", "suggested_scope", "summary", "created_at" }, ... ] }`, newest first (bounded to the last few, expired entries pruned). Use `candidate_id` to confirm or discard a specific one.

Types: `workflow`, `style`, `tooling`, `communication`, `review`, `avoidance`.

Injection policy controls WHERE a user-confirmed habit may surface, not whether it may be remembered (confirmation-first still gates creation). The default is now `prompt_ok_when_supported`, so a confirmed habit is perceptible at prompt time (🧠) on supported hosts such as Claude Code, OpenCode, or Codex — bounded by the conservative selection gate (active, high-confidence, directly relevant, `not_applies_to`-excluded, at most 3). Pass `--injection-policy compaction_ok` when the user wants a habit carried forward only at compaction, or `--injection-policy manual_only` to keep it out of automatic injection entirely.

Use `habit test` when the user asks what would recall for a given context, or why no habit appeared. Use `habit explain` when a specific habit did not appear. Both commands are dry-run diagnostics over the same prompt-time gate: they explain confidence, policy, review expiry, tag matches, score/floor, and reasons without writing habit events, candidates, injection logs, or model context. Pending candidates remain separate and never count as active habits until confirmed.

## Workflow

**Always start by reading BOTH active habits and pending candidates**, then branch on intent:

1. Read state:
   - `$SyberMemCli habit list --format json` → active habits.
   - `$SyberMemCli habit intent-status --format json` → pending candidates (list, newest first).
2. **Default status view (no explicit add/confirm/discard/pause/delete request).** When the user just invoked `/sybermem-habit` (or said something vague like "看看我的习惯"), present a compact status view and ask what they want — do NOT jump straight to adding:
   ```
   Active habits (N):
   - [habit-…] <statement>  (<type>, applies_to=…)
   Pending candidates (M):
   1. [cand-…] <age> ago (<type>/<scope>): "<summary>"
   2. …
   下一步：确认某条候选激活 / 舍弃某条候选 / 新增一个习惯 / 什么都不做？
   ```
   Render `created_at` as a relative age (e.g. "2h ago", "昨天"). If there are 0 active and 0 pending, say so and offer to add one.
3. Classify the request: **confirm-candidate**, **discard-candidate**, add, list, search, pause, delete, remind, inject, test, or explain.
4. For add / confirm requests, normalize the habit into ONE short statement and choose type/tags. If the user did not explicitly authorize saving, ask one confirmation question and stop (confirmation-first).
5. Run the matching CLI command.
6. Summarize the result with the habit id / candidate id and current status.

## Confirming a pending candidate

The passive capture is candidate-only and never creates a habit on its own. To turn a specific pending candidate into a real habit in one confirmed step:

1. Read the list: `$SyberMemCli habit intent-status --format json`. Each candidate carries `candidate_id`, a suggested `habit_type`, a suggested `suggested_scope` (`user` / `project` / `ambiguous`), a bounded `summary` of the user's own words, and `created_at`. If more than one is pending, ask which one (by number / summary) unless the user already pointed at one.
2. Propose ONE normalized statement. **Prefer the current conversation** (freshest, most complete wording); fall back to the candidate's `summary` when the triggering context has scrolled away. Never present the summary as an already-active habit — it is a proposal to confirm.
3. Route by `suggested_scope` (a suggestion; the user always decides):
   - `user` → a cross-project personal habit. Propose statement + type, confirm, then add it (below).
   - `project` → a project-specific convention. Do NOT add a user habit; suggest recording it via `/sybermem-record` as a `decision` or `requirement`, then discard the candidate.
   - `ambiguous` → ask ONE question: "记成跨项目的个人习惯，还是本项目的约定（走 /sybermem-record）？" Route by the answer.
4. On confirmation of a user habit, add it: `$SyberMemCli habit add --type <type> --applies-to <tag> "<normalized statement>"`.
5. Discard THAT candidate so it does not linger: `$SyberMemCli habit intent-discard <candidate-id>` (discard the single confirmed one, not the whole list).

## Discarding a candidate

If the user wants to drop a candidate without activating it, discard just that one:

```
$SyberMemCli habit intent-discard <candidate-id>
```

Use `$SyberMemCli habit intent-clear` only when the user wants to drop ALL pending candidates at once. If the user declines a specific candidate, discard that one and do not add anything.

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

User: "这个偏好只在压缩时带上就行，别每轮都提醒。"

Run (opt into the more conservative compaction-only policy; prompt-time is the default):

```bash
$SyberMemCli habit add --type workflow --applies-to planning --applies-to implementation --injection-policy compaction_ok "Prefer plans before code changes"
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
| Treating a pending candidate as already active | Explain that candidates require confirmation; use `habit test` to show pending count and selected=0. |
| Guessing why a habit did not appear | Run `$SyberMemCli habit explain --id <habit-id> --context "<bounded context>" --format json` and report the concrete reason codes. |
| Claiming unsupported platform reminders | State the actual boundary: Claude Code, OpenCode, and Codex support prompt-time habit reminders on their supported prompt seams; Codex also supports bounded startup context, prompt recall, record-intent capture, Stop record nudges, and compact re-seed markers, but not hidden auto-resume or direct compaction prompt injection. Gemini/Cursor/Kimi do not have runtime reminder wiring. |
| Forcing a habit to compaction-only without reason | Prompt-time (`prompt_ok_when_supported`) is the default so confirmed habits stay perceptible; only downgrade to `compaction_ok`/`manual_only` when the user asks for quieter delivery. |

## Completion

After a successful add/list/search/pause/delete/remind/test/explain operation, report only the relevant habit ids, status, diagnostic reason codes, and next available action. Do not create project records for habit-only work.
