# Codex Installation Notes

SyberMem Codex support is **Phase 1.5: user skills with verification**.

The global install and update scripts copy the canonical SyberMem skills from
`packages/claude-skills/` into the Codex user skills directory:

- macOS / Linux: `$HOME/.agents/skills`
- Windows: `%USERPROFILE%\.agents\skills`

This lets Codex users invoke the same SyberMem slash-style skills, including
`/sybermem-init-project`, `/sybermem-record`, `/sybermem-resume`,
`/sybermem-search`, `/using-sybermem`, and `/sybermem-habit`, when their Codex
environment loads user skills from `~/.agents/skills`.

Phase 1.5 adds discoverability and release verification around that skills-only
path. It does not add Codex runtime automation.

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
- the SyberMem CLI / Core runtime
- the fixed SyberMem CLI launcher

The fixed launcher remains in the existing SyberMem location:

- macOS / Linux: `$HOME/.claude/sybermem/cli/sybermem`
- Windows: `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd`

CLI-using skills include fallback guidance for that launcher when an agent
subprocess cannot resolve bare `sybermem`. Install scripts do not modify
persistent PATH automatically.

## Project setup

After the global install, open the target project in Codex and run:

```text
/sybermem-init-project
```

Existing projects should run:

```text
/sybermem-update
```

Those project-local skills create or refresh `.sybermem/`, `AGENTS.md`, and the
shared project instructions that are useful to Codex agents. `AGENTS.md` is the
main cross-agent utility file for Codex because it exposes the SyberMem session
protocol and project-local guidance without requiring a Codex-specific runtime.

## Manual context workflow

Codex does not receive SyberMem context automatically at prompt time. For an
important prompt, use the installed skills and CLI intentionally:

```text
/sybermem-resume
/sybermem-search <topic>
sybermem context prompt --query "<what you are about to do>" --format markdown
/sybermem-record
```

`sybermem context prompt` emits a copy/paste-safe manual context brief from the
current project's SyberMem records. `sybermem context session --format markdown`
is useful at the start of a Codex session, and `sybermem context habit --context
planning --format markdown` can surface user habits explicitly. These commands
do not install Codex hooks, do not modify `.codex/config.toml`, and do not create
automatic prompt-time injection.

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
successful project setup creates or refreshes `.sybermem/` and `AGENTS.md`.

## Phase 1.5 verification

For repository release checks, run the Codex-safe smoke set from a checkout:

```bash
python -m pytest packages/core/tests/test_package_integrity_scripts.py packages/core/tests/test_init_project_distribution.py -q
python scripts/check-plugin-package.py
```

These checks are non-mutating: they do not copy files into your real
`~/.agents/skills` directory. They verify that the install/update scripts still
target Codex user skills, that project health checks can discover templates from
`~/.agents/skills/sybermem-init-project/project-files`, and that Codex docs and
metadata remain honest about the skills-only boundary.

For an installed user environment, verify both layers:

1. Global skills exist under `~/.agents/skills` or `%USERPROFILE%\.agents\skills`.
2. The target project has fresh `.sybermem/` and `AGENTS.md` after running
   `/sybermem-init-project` or `/sybermem-update`.

## Troubleshooting

- **Codex does not show SyberMem skills**
  Re-run the global installer or updater, then confirm the skill directories
  exist under `~/.agents/skills`. If Codex uses a non-default user profile or
  home directory, check that Codex and the installer agree on the same home.
- **Codex sees stale project guidance after a global refresh**
  Run `/sybermem-update` inside the project. Global refresh updates user-level
  skills and runtime files; project-local `.sybermem/` and `AGENTS.md` refresh
  only when the project update skill runs.
- **A skill subprocess cannot resolve `sybermem`**
  Re-run the global installer or updater so the fixed launcher is refreshed.
  CLI-using skills include guidance for `$HOME/.claude/sybermem/cli/sybermem`
  and `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd` without modifying
  persistent PATH.
- **Project health still reports stale managed files**
  Confirm `/sybermem-update` was run from the target project after the global
  refresh. Phase 1.5 lets the health check read current templates from Codex's
  global skill install, but it still reports project-local freshness.

## Explicitly unsupported in Phase 1.5

Codex Phase 1.5 does not add any Codex runtime automation. In particular,
SyberMem does **not** install or claim:

- Codex hooks
- `.codex/config.toml`
- prompt-time injection
- hidden auto-resume
- background automation
- plugin-copy lifecycle behavior
- a repository `.agents/skills` mirror

Codex users invoke SyberMem intentionally through the installed user skills and
the `sybermem` CLI. Automatic prompt/lifecycle carry-forward remains limited to
platforms where SyberMem has an explicit supported runtime seam.
