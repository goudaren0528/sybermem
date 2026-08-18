# Codex Installation Notes

SyberMem Codex support is **user skills plus bounded SessionStart/UserPromptSubmit/Stop/PostCompact hooks**.

The global install and update scripts copy the canonical SyberMem skills from
`packages/claude-skills/` into the Codex user skills directory:

- macOS / Linux: `$HOME/.agents/skills`
- Windows: `%USERPROFILE%\.agents\skills`

This lets Codex users invoke the same SyberMem slash-style skills, including
`/sybermem-init-project`, `/sybermem-record`, `/sybermem-resume`,
`/sybermem-search`, `/using-sybermem`, and `/sybermem-habit`, when their Codex
environment loads user skills from `~/.agents/skills`.

Codex support includes discoverability and release verification around the
skills path, plus conservative managed hooks for startup project context,
prompt-time project recall, User Habit Memory reminders, record-intent capture,
Stop-time record nudges, and compact re-seed markers. It still does not add
hidden auto-resume or broader Codex runtime automation.

## Install and update

Run the normal SyberMem global installer or updater:

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

Clone-based installs use `./scripts/install.sh` or `./scripts/install.ps1`.
Clone-based updates use `./scripts/update.sh` or `./scripts/update.ps1`.

Each install/update path refreshes:

- Claude Code user skills
- OpenCode user skills and plugin
- Codex user skills at `~/.agents/skills`
- the Codex `SessionStart` startup context hook at `~/.codex/hooks/sybermem_session_start.py`
- the Codex `UserPromptSubmit` prompt context hook at `~/.codex/hooks/sybermem_user_prompt.py`
- the Codex `Stop` record nudge hook at `~/.codex/hooks/sybermem_stop.py`
- the Codex `PostCompact` marker hook at `~/.codex/hooks/sybermem_post_compact.py`
- the Codex hook registry merge in `~/.codex/hooks.json`
- the SyberMem CLI / Core runtime
- the fixed SyberMem CLI launcher

The fixed launcher remains in the existing SyberMem location:

- macOS / Linux: `$HOME/.claude/sybermem/cli/sybermem`
- Windows: `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd`

CLI-using skills and the Codex hooks include fallback guidance for that launcher
when a subprocess cannot resolve bare `sybermem`. Install scripts do not modify
persistent PATH automatically.

The Codex hooks are merged under `SessionStart`, `UserPromptSubmit`, `Stop`, and
`PostCompact`. `SessionStart` and `UserPromptSubmit` return bounded context
through `hookSpecificOutput.additionalContext`. The prompt hook combines
high-signal project recall and User Habit Memory reminders when either one
qualifies, and it writes bounded `.sybermem/.record-intent.json` classifier
metadata for explicit record requests without persisting the raw prompt. `Stop`
emits at most one bounded `/sybermem-record` continuation nudge per changed-file
fingerprint and returns nothing when `stop_hook_active` is true. `PostCompact`
writes only `.sybermem/.codex-compact-marker.json`; it does not inject direct
compaction context.

## Project setup

After the global install, open the target project in Codex and run:

```text
/sybermem-init-project
```

Existing projects should run:

```text
/sybermem-update
```

Those project-local skills create or refresh `.sybermem/` and the shared project
instructions that are useful to Codex agents, and remove any legacy SyberMem
protocol block from `AGENTS.md` / `CLAUDE.md`. SyberMem no longer injects a session
protocol into `AGENTS.md`; project-local guidance is provided by the visible
`/using-sybermem` skill instead.
`/sybermem-update` prefers the deterministic `sybermem project refresh --format json`
CLI path for this project-local refresh. It falls back to agent-orchestrated
`/sybermem-init-project` only when the CLI is missing, exits nonzero, or emits
invalid JSON.

## Hook-backed and manual context workflow

Codex receives bounded SyberMem startup context through `SessionStart` and
high-signal project recall through `UserPromptSubmit` when the shared CLI helpers
find relevant context. Manual commands remain useful for explicit review or when
you want more context than the hot-path hooks inject:

```text
/sybermem-resume
/sybermem-search <topic>
sybermem context prompt --query "<what you are about to do>" --format markdown
/sybermem-record
```

`sybermem context prompt` emits a copy/paste-safe manual context brief from the
current project's SyberMem records. `sybermem context session --format markdown`
is useful at the start of a Codex session, and `sybermem context habit --context
planning --format markdown` can surface user habits explicitly. The managed hooks
reuse the stricter `context session`, `context recall`, and `context habit
--delivery prompt-time` contracts, fail open, and do not install or require
`.codex/config.toml`.

## Verify

Check that the user skills directory contains SyberMem skills:

```bash
ls ~/.agents/skills/sybermem-resume
ls ~/.agents/skills/sybermem-record
```

On Windows PowerShell:

```powershell
Test-Path "$env:USERPROFILE\.agents\skills\sybermem-resume"
Test-Path "$env:USERPROFILE\.agents\skills\sybermem-record"
```

Then run `/sybermem-init-project` or `/sybermem-update` in a target project. A
successful project setup creates or refreshes `.sybermem/` and removes any legacy
SyberMem protocol block from `AGENTS.md`; a
healthy `/sybermem-update` reports the `sybermem project refresh --format json`
summary rather than performing a slow file-by-file agent refresh.

Verify the Codex managed hooks too:

```bash
ls ~/.codex/hooks/sybermem_user_prompt.py
ls ~/.codex/hooks/sybermem_session_start.py
ls ~/.codex/hooks/sybermem_stop.py
ls ~/.codex/hooks/sybermem_post_compact.py
cat ~/.codex/hooks.json
```

On Windows PowerShell:

```powershell
Test-Path "$env:USERPROFILE\.codex\hooks\sybermem_user_prompt.py"
Test-Path "$env:USERPROFILE\.codex\hooks\sybermem_session_start.py"
Test-Path "$env:USERPROFILE\.codex\hooks\sybermem_stop.py"
Test-Path "$env:USERPROFILE\.codex\hooks\sybermem_post_compact.py"
Test-Path "$env:USERPROFILE\.codex\hooks.json"
```

The installed `hooks.json` should contain `SessionStart`, `UserPromptSubmit`,
`Stop`, and `PostCompact` entries that point to the SyberMem hooks. Only
`SessionStart` and `UserPromptSubmit` write bounded context through
`hookSpecificOutput.additionalContext`; `Stop` can return a bounded continuation
nudge, and `PostCompact` is side-effect-only.

## Repository verification

For repository release checks, run the Codex-safe smoke set from a checkout:

```bash
python -m pytest packages/core/tests/test_package_integrity_scripts.py packages/core/tests/test_init_project_distribution.py -q
python scripts/check-plugin-package.py
```

These checks are non-mutating: they do not copy files into your real
`~/.agents/skills` directory. They verify that the install/update scripts still
target Codex user skills, that project health checks can discover templates from
`~/.agents/skills/sybermem-init-project/project-files`, and that Codex docs and
metadata remain honest about the supported boundaries.

For an installed user environment, verify both layers:

1. Global skills exist under `~/.agents/skills` or `%USERPROFILE%\.agents\skills`.
2. The target project has fresh `.sybermem/` (and no legacy SyberMem protocol block in `AGENTS.md`) after running
   `/sybermem-init-project` or `/sybermem-update`.

## Troubleshooting

- **Codex does not show SyberMem skills**
  Re-run the global installer or updater, then confirm the skill directories
  exist under `~/.agents/skills`. If Codex uses a non-default user profile or
  home directory, check that Codex and the installer agree on the same home.
- **Codex sees stale project guidance after a global refresh**
  Run `/sybermem-update` inside the project. Global refresh updates user-level
  skills and runtime files; project-local `.sybermem/` refresh (and removal of any
  legacy SyberMem protocol block from `AGENTS.md`) happens only when the project
  update skill runs the CLI-first project refresh.
- **Codex startup context or prompt context never appears after an upgrade**
  Re-run the global installer or updater so `~/.codex/hooks/sybermem_user_prompt.py`,
  `~/.codex/hooks/sybermem_session_start.py`, `~/.codex/hooks/sybermem_stop.py`,
  `~/.codex/hooks/sybermem_post_compact.py`, and `~/.codex/hooks.json` are refreshed.
  Then run `/sybermem-update` in the project if you also need fresh project-managed files.
- **A skill subprocess cannot resolve `sybermem`**
  Re-run the global installer or updater so the fixed launcher is refreshed.
  CLI-using skills include guidance for `$HOME/.claude/sybermem/cli/sybermem`
  and `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd` without modifying
  persistent PATH.
- **Project health still reports stale managed files**
  Confirm `/sybermem-update` was run from the target project after the global
  refresh. Codex support lets the health check read current templates from Codex's
  global skill install, but it still reports project-local freshness.

## Supported hook behavior

The Codex `SessionStart` hook injects bounded startup context from `sybermem
context session --format markdown`. The Codex `UserPromptSubmit` hook injects
high-signal project recall from `sybermem context recall --query ...` and bounded
User Habit Memory reminders from `sybermem context habit --delivery prompt-time`.
It also captures explicit record intent into `.sybermem/.record-intent.json`
using bounded classifier metadata. The Codex `Stop` hook can return one bounded
`/sybermem-record` continuation nudge and uses both Codex `stop_hook_active` and
a local fingerprint to avoid loops. The Codex `PostCompact` hook writes a marker
so the next compact-source `SessionStart` can re-seed ordinary session context;
it does not inject direct compaction prompt context. All hook paths fail open.

Manual commands stay documented and supported:

- `sybermem context session --format markdown`
- `sybermem context prompt --query "..." --format markdown`
- `sybermem context habit --context planning --format markdown`
- `/sybermem-resume`
- `/sybermem-search`

## Explicitly unsupported

Codex support does not add broad Codex runtime automation. It only adds bounded
managed command hooks through `SessionStart`, `UserPromptSubmit`, `Stop`, and
`PostCompact`.

In particular, SyberMem does **not** install or claim:

- `.codex/config.toml`
- hidden auto-resume
- unsupported background automation
- prompt or agent handler runtimes
- direct compaction prompt injection
- plugin-copy lifecycle behavior
- a repository `.agents/skills` mirror

Codex users can still invoke project memory intentionally through the installed
user skills and the `sybermem` CLI when they want more context than the bounded
hot-path hooks provide.
