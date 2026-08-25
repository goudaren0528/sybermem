# OpenCode Installation Notes

SyberMem currently installs into OpenCode in two parts:

- Skills are copied to `~/.config/opencode/skills/`
- The plugin file is copied to `~/.config/opencode/plugins/sybermem.ts`

The current OpenCode plugin implements these hooks:

- `session.created`
- `session.idle`
- `chat.message` — captures each user prompt, computes gated recall hints, and writes bounded record-intent / recall-debug metadata without storing raw prompt text
- `experimental.chat.system.transform` — injects those hints plus bounded User Habit Memory reminder markdown into the same turn's system prompt
- `experimental.session.compacting`

## Capability parity with Claude Code

Across the OpenCode seams above, the plugin mirrors the Claude Code
lifecycle-hook and prompt-time recall behavior:

- `session.created` surfaces the loaded key-conclusion count, a stale-signal note,
  and a commit-gap record reminder (threshold >= 3 commits since the last record),
  matching the Claude `SessionStart` context.
- `chat.message` + `experimental.chat.system.transform` deliver per-prompt high-signal
  task recall with the same `⭐` (important) / `💡` (ordinary) markers the Claude
  `UserPromptSubmit` hook uses, and they also append User Habit Memory reminder
  markdown in the same transform. Recall is gated by the same high-signal
  threshold (record-id / relation, or score >= 12), so weak keyword matches stay
   silent and every injected recall hint carries a visible marker. Habit reminders
   stay conservative and fail open: only active, high-confidence, directly relevant,
   prompt-ok-when-supported habits are included, with bounded output. Habits added
   via `/sybermem-habit` are prompt-ok-when-supported by DEFAULT, so a confirmed
   habit is perceptible at prompt time without extra flags; relevance uses CJK-aware
   tokenization plus a weighted floor (an `applies_to` tag match is a strong boost,
   otherwise a habit needs two distinct statement/type overlaps) so Chinese contexts
   match while unrelated habits stay silent.
- To make in-session injection perceptible (not just the `session.created` toast),
  `experimental.chat.system.transform` shows SEPARATE throttled toasts at the moment
  context actually reaches the model: a `⭐` recall toast for injected recall hints and
  a distinct `🧠` toast for applied user habits, so an applied habit is as perceptible
  as recall instead of being merged into one notice. `chat.message` shows a scope-aware
  `💡` toast when a prompt looks like a reusable preference — routing to `/sybermem-habit`
  for a cross-project habit, to `/sybermem-record` for a project-specific convention, or
  deferring the user-vs-project question to the confirm step when ambiguous — turning an
  otherwise silently-dropped signal into a discoverable action.
  Both toasts are cooldown-throttled (~30s per type) and fail open, so they never
  block or spam the prompt flow.
- `session.idle` classifies changed files into a record nudge, a digest nudge, or
  no nudge using the same thresholds and high-signal / high-level-area heuristics
  as the Claude `Stop` hook, tracks a per-theme window for digest clustering, and
  persists a bounded `.sybermem/.auto-trail.jsonl` journal with >80% overlap dedup.
- `chat.message` writes `.sybermem/.record-intent.json` only when an explicit
  record request classifies as `change`, `decision`, `requirement`, or `bug`.
  The file stores bounded classifier metadata (`source`, `classification`,
  `action`, `reason`, `matched_pattern`, timestamp, and an empty `phrase`) and
  never stores raw prompt text.
- `chat.message` also appends `.sybermem/.recall-debug.jsonl` for recall
  `inject` / `abstain` outcomes. The log is capped to the newest 200 entries and
  stores only source, timestamp, event, record IDs, match classes, and reason
  codes — not the prompt.
- `experimental.session.compacting` first tries to include the shared manual
  session brief from `sybermem context session --format markdown`, then adds
  project identity (`slug` / `project_id`), phase-index status and confirmed
  count, active phase, stale signal, the topic index, a next-step recommendation
  from `sybermem next-step`, and bounded User Habit Memory from `sybermem habit
  inject` with a compaction/planning/review/coding context (fails open when the
  CLI is unavailable or no habits match).

The OpenCode implementation is still bounded to documented plugin hooks. This
limitation means it does not add hidden auto-resume, hidden background workers, or undocumented
post-response hooks.

Per-prompt task recall and prompt-time User Habit Memory reminders are now
automatic on OpenCode through `chat.message` +
`experimental.chat.system.transform`. Carry-forward also relies on the supported
compaction hook.

OpenCode does not expose a Claude-style `UserPromptSubmit` hook name, but it does
support per-prompt context injection through the plugin's `chat.message` +
`experimental.chat.system.transform` hooks, which SyberMem now uses to deliver
gated, marker-tagged recall. Task recall can additionally be done manually via
`/sybermem-search` or `sybermem context prompt --query "..." --format markdown`.

This means:

- `/sybermem-resume` is manual
- `/sybermem-search` is manual
- `sybermem context prompt --query "..." --format markdown` is a manual helper
  for copying relevant project memory into an important prompt
- `sybermem context session --format markdown` and `sybermem context habit --context planning --format markdown` remain manual helpers
- per-prompt high-signal recall is automatic through `chat.message` +
  `experimental.chat.system.transform`, surfacing `⭐`/`💡` markers on qualifying prompts
- prompt-time User Habit Memory reminders are automatic through the same transform path, but stay bounded and conservative
- prompt-time record-intent metadata and recall debug metadata are automatic through `chat.message`, bounded, and prompt-free
- User Habit Memory is still manual through `/sybermem-habit`, `sybermem habit remind`, and `sybermem context habit`, plus compaction carry-forward through `sybermem habit inject`
- there is no hidden auto-resume
- the plugin does not create a second memory store

`/sybermem-resume` is also manual on OpenCode. Use it when you want a bounded,
read-only restart brief for the current project. It can show the current phase,
recent progress, risks, next action, confidence, freshness, and reason, but it
never auto-runs the suggested action.

Mode guidance on OpenCode is the same as elsewhere:

- `fast` for the short restart brief
- `standard` for the default handoff with a bit more trust context
- `deep` for a bounded follow-up that points you to the right records or digests

Deep mode still does not auto-read or inject full history. When you need
historical evidence, run `/sybermem-search`. When OpenCode compacts a session,
rely on the supported compaction hook rather than unsupported prompt-time
injection.

## Install and update boundaries

The OpenCode side is refreshed by the same global install/update scripts used for
the rest of SyberMem.

On Windows OpenCode, prefer the Python path because it does not spawn
`powershell.exe`:

```cmd
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.py').read())"
```

From a SyberMem checkout, use `python scripts/update.py`. The PowerShell and
shell installers remain supported alternatives.

- global install or global update refreshes `~/.config/opencode/skills/`
- global install or global update refreshes `~/.config/opencode/plugins/sybermem.ts`
- global install or global update refreshes the fixed SyberMem CLI launcher at `$HOME/.claude/sybermem/cli/sybermem` on macOS / Linux or `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd` on Windows
- re-running the remote install command is a real refresh path for the OpenCode plugin and skills

The OpenCode plugin and CLI-using skills prefer that fixed launcher when an OpenCode or agent subprocess cannot resolve bare `sybermem` from PATH. SyberMem does not modify persistent PATH automatically; adding the launcher directory to PATH remains an optional user choice.

That global refresh does not replace project-local SyberMem files. Existing
projects still need `/sybermem-update` when you want refreshed managed hooks,
templates, or instruction files inside the project. Older users should re-run
the global install or update first to get the new bundled OpenCode plugin
(`~/.config/opencode/plugins/sybermem.ts`) with prompt-time record-intent and
recall debug support, then run `/sybermem-update` so project-managed files stay fresh.
`/sybermem-update` now uses the deterministic `sybermem project refresh --format json`
CLI path first for project-local files. It falls back to agent-orchestrated
`/sybermem-init-project` only when the CLI is missing, exits nonzero, or emits
invalid JSON.

Project initialization still uses `/sybermem-init-project`.

The project-local distribution path is still important on OpenCode: `/sybermem-init-project`
or `/sybermem-update` can create or refresh `.sybermem/`,
`.claude/settings.json`, `.sybermem/hooks/detect_record_intent.py`, and
`.sybermem/hooks/task_recall.py` for Claude-compatible project sharing, and removes
any legacy SyberMem protocol block from `AGENTS.md` / `CLAUDE.md`. That does
not change the OpenCode recall path above: OpenCode uses its own `chat.message` +
`experimental.chat.system.transform` hooks for per-prompt recall, which the plugin
refresh delivers regardless of project-local Claude hooks.

Use this workflow:

1. run the global install or global update first
2. run `/sybermem-update` inside an existing project; it should report the CLI refresh JSON summary when the CLI is healthy
3. run `/sybermem-init-project` when initialization is still missing

The OpenCode plugin does not replace project `.sybermem/` files. It complements the project-managed `.sybermem/` and `.claude/settings.json` setup.

### Optional: reply marker (default OFF)

By default, SyberMem signals recall/habit injection with throttled TUI toasts
(`⭐`/`🧠`/`💡`). If you want a guaranteed, model-independent signal in the reply
itself, set `SYBERMEM_REPLY_MARKER=1` in the OpenCode environment. When enabled,
the plugin prepends ONE line to the first assistant text part of any turn that
actually received injected recall/habit context (e.g. `> SyberMem: 本轮参考了 ⭐2 条记忆`).
It is OFF by default because it uses the experimental `experimental.text.complete`
seam and the marker persists in message history.
