---
name: sybermem-install
description: Use when a new user wants to install the complete SyberMem system from inside an agent conversation for the first time, on a machine that has no SyberMem CLI, plugin, hooks, or other SyberMem skills yet. Orchestrates the official remote install script, verifies all three hosts (Claude Code / OpenCode / Codex) are ready, then initializes the current project. Triggers on "install sybermem", "安装 sybermem", "一键安装 sybermem", "setup sybermem from scratch".
---

# sybermem-install Skill

**Announce at start:** "I'm using the sybermem-install skill to install the complete SyberMem system and verify all hosts."

First-time installer entrypoint for a **fresh machine**. This skill assumes the only
SyberMem asset present is this skill itself — no CLI, no plugin, no hooks, no other
SyberMem skills. It is a **thin orchestration layer**: it runs the official remote
install script (which lands the full system, including every other SyberMem skill),
then verifies each host is ready and initializes the current project.

## Quick guide (for humans)

> Plain-language overview for people. **Not** the execution contract — the
> `<HARD-GATE>`, `## Flow`, and `## Red Flags` sections below are authoritative and
> win on any conflict.

**What it does:** installs the complete SyberMem system from inside the conversation.
It downloads and runs the official installer (the same one behind the one-line
`curl | bash` / `irm | iex` commands), so it lands skills for all three hosts, the
Codex hooks, the Claude launchers, the `sybermem` CLI (a Python venv), the OpenCode
plugin, and the version marker. Then it checks each host is wired up and — if you are
inside a project — initializes that project's `.sybermem/`.

**When to run:** on a brand-new machine, or one that has this skill but nothing else
of SyberMem yet. To *refresh* an already-installed machine, use `/sybermem-update`
instead; to set up only the current project after install, use `/sybermem-init-project`.

**What you get:** an honest per-host readiness report (ready / host not present, skipped
/ error), the installed version, and — inside a project — a project initialized through
the CLI. If anything fails, it tells you exactly what failed and gives the one-line
fallback command; it never claims a partial install succeeded.

## Core Invariant

- **This skill installs the complete SyberMem system by running the official remote install script, then it does not report success until it has verified each host's readiness and (inside a project) completed project initialization through the CLI-first path. It never fabricates success: a download, environment, CLI, or init failure is reported as a partial/failed install with the exact failing stage and a fallback command.**

<HARD-GATE>
Do NOT claim installation succeeded without running the readiness verification for all three hosts and the shared CLI.
Do NOT rely on `/sybermem-init-project` (a skill) for in-session project init: skills just landed on disk are typically NOT hot-loaded in the current session. Use the CLI-first path (`sybermem project refresh --format json`); only offer `/sybermem-init-project` as a NEXT-session fallback.
Do NOT report success when the download, venv/pip, or CLI readiness step failed. Report which stage failed and stop honestly.
Do NOT run any destructive action. This skill only installs; it never deletes user data or project `.sybermem/` records.
</HARD-GATE>

## When to Use

- A brand-new machine where SyberMem has never been installed
- A machine that has this `sybermem-install` skill but no `sybermem` CLI / plugin / hooks / other SyberMem skills
- The user asks to install/setup SyberMem from inside the conversation instead of pasting a terminal command

Use `/sybermem-update` instead when SyberMem is already installed and only needs a
refresh. Use `/sybermem-init-project` instead when the global install already exists
and only the current project needs setup.

## CLI Resolution

Before running SyberMem CLI commands, resolve a command variable first. On Windows
`cmd.exe` or OpenCode, prefer `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd`; in
Windows PowerShell prefer `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd` and
store the chosen command in `$SyberMemCli`; on Unix, prefer
`$HOME/.claude/sybermem/cli/sybermem` and store the chosen command in
`"$SYBERMEM_CLI"`. If the fixed launcher is unavailable, fall back to bare `sybermem`.
Do not modify persistent PATH automatically. Command examples below use
`$SyberMemCli` / `"$SYBERMEM_CLI"`.

## Flow

### Step 1: Detect environment

Determine the host, OS, and shell, and probe prerequisites:

- OS / shell: Windows PowerShell, Windows `cmd.exe` / OpenCode, or Unix (macOS / Linux).
- `python` availability (`python --version`): the PowerShell-free Windows path and the
  installer's internal steps depend on it.
- Whether SyberMem already appears installed (e.g. `~/.claude/sybermem/VERSION` exists).
  If it does, tell the user this will be a refresh-style reinstall (idempotent; it does
  not destroy project `.sybermem/` records) and continue.

### Step 2: Choose the install command

Pick the official remote install script form by OS/shell, in this order (matching
`/sybermem-update`'s command-selection policy):

1. **Windows OpenCode or `cmd.exe`** — prefer the Python path (does not spawn PowerShell):
   ```cmd
   python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.py').read())"
   ```
2. **Windows PowerShell**:
   ```powershell
   irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
   ```
3. **macOS / Linux**:
   ```bash
   curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash
   ```

The remote script downloads the repository archive, extracts it, and installs the full
system (skills for all three hosts, Codex hooks + `hooks.json` handlers, Claude
launchers, the `sybermem` CLI venv, the OpenCode plugin, and the `VERSION` marker). Do
not reimplement those steps here — the script is the single source of truth.

### Step 3: Explain, then run the install command

Tell the user which command you are about to run and that it downloads and installs
SyberMem, then run it. Do not silently execute.

### Step 4: Parse installer output and confirm landing

Read the script's stdout. It prints per-target lines — `installed:` on the shell / PS
paths, `updated:` on the Python path (`_install_common.install_from_checkout`) — and all
three paths end with an `=== Installation Complete ===` banner. The **authoritative
completion signal is exit code 0 plus the `=== Installation Complete ===` banner**, not
the per-line wording. If the command exited nonzero or the completion banner is absent,
treat it as a **download/install failure** (see Exception Flows) — do not proceed to
claim success.

The installer banner then prints generic next-step guidance mentioning
`/sybermem-update` / `/sybermem-init-project`. **Ignore that banner guidance for the rest
of this skill** — it targets terminal users; continue with the CLI-first Step 6 instead
(those slash skills are not hot-loaded in the current session anyway).

### Step 5: Verify all three hosts + the shared CLI are ready

Verify each host explicitly and report an honest per-host verdict: **ready** / **error**.
Note: the installer itself *creates* the user-level integration directories for all
three hosts (skills dirs, and — when the corresponding app root exists — the plugin /
hooks / launchers). So after install, base-dir existence is expected and is **not**
evidence the host app was previously present. Do not report "host not present" merely
because a dir was just created. Judge each host by whether its expected managed files
actually landed: all present → **ready**; some app-conditional components missing (e.g.
the Claude launchers or OpenCode plugin were skipped because that app's root did not
exist) → report that host's integration as **partial** and name what is missing; a
required file that should have landed but did not → **error** with a remedy (re-run the
install command).

| Host | Ready when (verify each path on disk) |
|---|---|
| Claude Code | `~/.claude/skills/sybermem-*` present; `~/.claude/sybermem/launch_record_change_on_stop.py`, `launch_session_start_context.py`, `managed-install.json`, `safe-managed-remove.py`, `VERSION` present |
| OpenCode | `~/.config/opencode/skills/sybermem-*` present; `~/.config/opencode/plugins/sybermem.ts` present |
| Codex | `~/.agents/skills/sybermem-*` present; all five hook files present — `sybermem_user_prompt.py`, `sybermem_session_start.py`, `sybermem_session_end.py`, `sybermem_stop.py`, `sybermem_post_compact.py` — plus `_codex_observability.py`; `~/.codex/hooks.json` contains the managed handlers |

**Shared CLI (required — gates project init and every CLI-backed skill):** resolve the
fixed launcher (see CLI Resolution) and confirm it runs:

```powershell
& $SyberMemCli project refresh --help
```

```bash
"$SYBERMEM_CLI" project refresh --help
```

```cmd
"%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd" project refresh --help
```

Exit code 0 → CLI ready. Nonzero or launcher missing → CLI **error**: the project-init
step (Step 6) must fall back, and the user should re-run the install command.

### Step 6: Initialize the current project (CLI-first)

If the current working directory is a project (has code, or the user asked to set it
up), initialize it — mirroring `/sybermem-update`'s CLI-first model:

1. **CLI-first (in-session, works immediately):** run
   ```powershell
   & $SyberMemCli project refresh --format json
   ```
   ```bash
   "$SYBERMEM_CLI" project refresh --format json
   ```
   ```cmd
   "%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd" project refresh --format json
   ```
   The CLI is a child process and is usable the moment the installer finishes, so this
   is the in-session path. If it exits 0 with valid JSON, summarize the report
   (`overall`, and any created/refreshed/preserved actions). Project init is complete.

2. **Fallback — split by cause (do NOT blanket-report success):**
   - **CLI itself not ready** (fixed launcher missing, or `project refresh --help` was
     nonzero in Step 5): this is a **partial/failed install**, NOT a full success — the
     CLI runtime is part of "complete install" (PRD G2 / A3). Report CLI-not-ready,
     advise re-running the install command, and defer project init. Do not call the
     global install complete.
   - **CLI ready but this project's refresh failed** (`project refresh --format json`
     exited nonzero or emitted non-JSON, while `--help` succeeded): the global install
     **is** a success; only the in-session project init is deferred. Tell the user to run
     `/sybermem-init-project` **in a new session**.

   In both cases, do NOT try to trigger `/sybermem-init-project` in the current session —
   skills just written to disk by the installer are typically not hot-loaded until the
   next session.

If cwd is **not** a project, skip project init and tell the user to open a project and
run `/sybermem-init-project` (or re-invoke and let Step 6 run) there.

### Step 7: Output the install summary

Report, concisely:

- Installed version (from `~/.claude/sybermem/VERSION`).
- Per-host readiness: Claude Code / OpenCode / Codex each as ready / skipped / error.
- CLI readiness.
- Project init result (CLI-refreshed / deferred to next session / skipped — not in a project).
- Next steps: `/sybermem-record` after meaningful work, `/sybermem-resume` to restore
  context, `/sybermem-update` later to refresh.

## Exception Flows

Report the failing stage honestly; never wrap a real failure as generic "install failed",
and never claim success on partial completion.

| Failure | User-visible report | Recovery |
|---|---|---|
| Remote download fails (network / 404 / GitHub unreachable) | "Failed to download the SyberMem installer" + the raw error | Suggest checking the network and retrying; offer the one-line install command as a manual fallback. Do NOT report success. |
| `python` not found (PowerShell-free Windows path relies on it) | "python not found" | PowerShell users can switch to the `install-remote.ps1` path; provide it. Do not silently fail. |
| venv creation / `pip install` fails | "CLI install failed" + the pip error | Other global components may already be on disk — report **partial completion**, state that the CLI is NOT ready, and advise re-running the install command. |
| CLI readiness check fails (launcher present but `--help` nonzero) | "CLI is not ready" | Project init (Step 6) falls back to the next-session `/sybermem-init-project`; advise re-running install. |
| Step 6 CLI exits nonzero / non-JSON | Not fatal | Fall back to next-session `/sybermem-init-project`; the global install still counts as success. |
| A host base dir missing (user doesn't use that host) | "Host X not present, skipped" | Not a failure; informational only. |

## Idempotency

Re-running `sybermem-install` on an already-installed machine is safe: the underlying
installer is idempotent (it force-reinstalls the CLI and surgically overwrites skills
and `hooks.json` handlers without touching unrelated custom entries). This skill adds no
destructive action of its own and must never damage already-landed components or a
project's `.sybermem/` records.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:

- Reporting installation success without verifying all three hosts and the shared CLI
- Trying to trigger `/sybermem-init-project` in the current session for project init instead of using the CLI-first path
- Reporting success when the download, venv/pip, or CLI readiness step failed
- Wrapping a specific failure (download / python / pip / CLI) as a generic "install failed" without naming the stage
- Reimplementing the installer's landing steps inside this skill instead of running the official remote script
- Taking any destructive action (this skill only installs)

## Terminal State

This skill is complete when:

- the official remote install script ran and reached its completion banner
- all three hosts were verified and reported as ready / skipped / error
- the shared CLI was verified ready (or its failure was honestly reported)
- inside a project: `sybermem project refresh --format json` succeeded, or the CLI-unavailable case was deferred to a next-session `/sybermem-init-project`
- the user received an install summary with version, per-host readiness, and next steps

## Safety Rules

- Do not claim success on a partial or failed install; name the failing stage.
- Do not modify persistent PATH automatically.
- Do not run any destructive action; this skill only installs.
- Do not reimplement the installer; run the official remote script as the single source of truth.
- Do not depend on any other SyberMem skill being already installed; the only guaranteed asset is this skill.
- Boundary note: `sybermem-install` itself is externally distributed and is intentionally **not** part of the installer's `SKILLS` manifest. Re-running install/update lands and refreshes every *other* SyberMem skill but does **not** install or refresh `sybermem-install`; equally, managed removal (`safe-managed-remove.py`) only deletes exact manifest-listed names, so it never deletes this unlisted skill. Distributing/refreshing this skill is out of scope here.

## Integration

**Follow-up skills (available after this skill lands them):**
- **sybermem-init-project** — Next-session fallback for project init when the CLI path was unavailable
- **sybermem-update** — Refresh an already-installed machine later
- **sybermem-record** — Create the first project record after meaningful work
- **sybermem-resume** — Read-only restart view for the project
