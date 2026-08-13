# Installation Guide

## Upgrading existing ADR/ projects

If a project already uses `ADR/`, do not rename directories manually. The first run of `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, `/sybermem-digest`, `/sybermem-phase-analyze`, or `/sybermem-phase-confirm` automatically migrates `ADR/` to `.sybermem/`.

If both `.sybermem/` and `ADR/` exist, the skills use `.sybermem/` and warn that the legacy `ADR/` directory was ignored.

Refreshing the global install alone does not automatically refresh project-local `AGENTS.md`, `CLAUDE.md`, hooks, templates, or managed settings patches. After every global install or update, open each target project and run `/sybermem-update`.

That matters for resume, search, and Team publish behavior too. A global refresh makes the latest skills and runtime available to the user, but existing projects still need `/sybermem-update` when you want refreshed managed instructions, hook files, templates, or settings surgery inside the project.

If the project is not initialized yet, run `/sybermem-init-project`. If the project already exists, the safe order is:

1. global install or global refresh
2. `/sybermem-update` inside the target project
3. `/sybermem-init-project` only when initialization is still missing

If the same source records have already been compressed into an existing digest, `/sybermem-digest` must point to the existing digest instead of creating a duplicate.

If an older project still contains project-local copies such as `.claude/skills/sybermem-*`, Claude may load both the local and global copies and show duplicates in the `/` list. Once you have switched to the global-install model, those old project-local copies can be deleted.

## Install

### Claude Code 插件安装（推荐）

Plugin install is the preferred future path for Claude Code because it can load both the plugin metadata and the hook lifecycle directly.

#### Local development / testing

```bash
claude --plugin-dir .
```

This loads the current repository as a Claude Code plugin using `.claude-plugin/`, `hooks/`, and the synced top-level `skills/` tree.

#### Future install path

The repository already includes `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` so it can evolve toward marketplace-based installation. Until that path is finalized, use `claude --plugin-dir .` for local validation.

### Claude Code / OpenCode / Codex 脚本安装（兼容模式）

Script install remains supported as the compatibility path. These commands refresh the user-level Claude Code skills, OpenCode skills, Codex skills, OpenCode plugin, and the CLI/Core runtime. User Habit Memory ships through the Core/CLI runtime plus `/sybermem-habit`, and stores data in the user-owned `~/.sybermem/user-habits/` tree, so it does not require a project `.sybermem/` migration.

Installers also create an agent-safe fixed CLI launcher: `$HOME/.claude/sybermem/cli/sybermem` on macOS / Linux and `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd` on Windows. OpenCode plugin code and CLI-using skills prefer that launcher when a child agent process cannot resolve bare `sybermem`. The scripts do not modify persistent PATH by default; adding the launcher directory to PATH is optional user configuration.

#### One-liner install

No clone needed — downloads directly from GitHub.

##### macOS / Linux

```bash
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash
```

##### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

After install, open your target project and run `/sybermem-update` for existing projects, or `/sybermem-init-project` for new projects.
Those project-local steps create or refresh the default project-level `.claude/settings.json` for SyberMem `auto` / `remind` mode, `.sybermem/hooks/record_change_on_stop.py` for automatic `change` records, `.sybermem/hooks/detect_record_intent.py` for reminder-first record-intent capture, and `.sybermem/hooks/task_recall.py` for read-only task recall.
In Claude Code projects, the managed `UserPromptSubmit` hook performs natural-language record-intent capture, read-only task recall, and bounded User Habit Memory reminders. Habit reminders never create active habits automatically; they either point to prompt-approved habits or ask the user to confirm `/sybermem-habit`.

#### Clone and install

Clone the repo, then run the local install script.

```bash
# macOS / Linux
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem && ./scripts/install.sh
```

```powershell
# Windows (PowerShell)
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem; .\scripts\install.ps1
```

### OpenCode

For OpenCode plugin installation and lifecycle details, see [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

Project initialization still uses `/sybermem-init-project` after the global install or plugin setup.

On OpenCode, `/sybermem-resume` is a manual, read-only entrypoint. Use it to rebuild current context, use `/sybermem-search` when you need explicit historical evidence, and rely on the supported compaction flow for automatic memory carry-forward during compaction only. Do not expect unsupported prompt-time injection, hidden auto-resume, or background execution.

### Codex

Codex support is Phase 1.5 user skills with verification. The global install/update scripts copy `packages/claude-skills` to `~/.agents/skills` on macOS / Linux and `%USERPROFILE%\.agents\skills` on Windows with the `Codex` target label. Project setup still uses `/sybermem-init-project` or `/sybermem-update`, which refresh `.sybermem/` and `AGENTS.md` for Codex agents. Project health checks can also discover current templates from the Codex-installed `~/.agents/skills/sybermem-init-project/project-files` tree.

For Codex-specific boundaries and verification, see [`.codex/INSTALL.md`](.codex/INSTALL.md). Do not expect Codex hooks, `.codex/config.toml`, prompt-time injection, hidden auto-resume, or background automation in Phase 1.

## Update

### One-liner update

Re-run the one-liner install command. This is a real global runtime refresh, not just a skill copy. It refreshes:

- Claude Code skills
- OpenCode skills
- Codex skills
- OpenCode plugin
- CLI / Core runtime

This includes `/sybermem-habit` and `sybermem habit add/list/search/pause/delete/remind/inject`. Habit data stays in user-level storage and is not copied into existing project records by `/sybermem-update`.

After the global refresh, open the target project and run `/sybermem-update`.
That project-local step repairs missing or stale managed hook files, templates, and instruction blocks, and patches only recognized SyberMem-managed settings entries when `.claude/settings.json` is otherwise custom.

### Clone-based update

```bash
# macOS / Linux
cd sybermem && git pull && ./scripts/update.sh
```

```powershell
# Windows (PowerShell)
cd sybermem; git pull; .\scripts\update.ps1
```

After the script finishes, open the target project and run `/sybermem-update`.
That follow-up is where project-local hook files, templates, instruction blocks, and settings entries are actually created, refreshed, or migrated.

That same project-local refresh is also how older Claude projects pick up updated guidance and managed prompt hooks, including `/sybermem-resume` routing, read-only recall, and User Habit Memory reminders.

For CLI availability fixes, OpenCode plugin fixes, or skill instruction fixes, use the same propagation path: re-run the global installer/updater to refresh the runtime, fixed launcher, OpenCode plugin, and user-level skills; then run `/sybermem-update` inside each existing project so project-local instructions and managed files are refreshed.

## Subdirectory Hook Fix

For existing users who experienced stop hook errors when working in project subdirectories: running `/sybermem-update` in the project refreshes the hook with automatic project root resolution. The updated hook finds the correct `.sybermem/` directory even when your working directory is a subdirectory of the project root.

When phase analysis is available, `/sybermem-summary` is no longer just a weekly/monthly report. It becomes a dynamic current-state panel for the most recently active confirmed phase, while `/sybermem-digest` remains the durable phase conclusion artifact.

`/sybermem-resume` is the bounded restart view layered on top of that status path. In user terms:

- `fast` gives the short restart brief
- `standard` adds the most useful trust context
- `deep` stays bounded and points to the right records or digests for follow-up instead of auto-reading full history

Resume output should surface current phase, recent progress, risks, next action, confidence, freshness, and reason. It is read-only and must never auto-run the suggested action.

For existing projects, the global refresh is only half of the rollout. If a behavior change depends on project-local managed files, you must run `/sybermem-update` in that project so the managed files can be created or refreshed safely.

For existing projects, `/sybermem-update` now performs a Stop hook command migration to the global launcher path. This is the repair step that fixes file-not-found hook failures when Claude is working from a subdirectory.

For existing projects, `/sybermem-update` should also repair missing or stale `.sybermem/hooks/detect_record_intent.py` and `.sybermem/hooks/task_recall.py` files, and surgically patch recognized SyberMem-managed `UserPromptSubmit` settings entries instead of replacing the whole `.claude/settings.json` file.

For existing projects, `/sybermem-update` should also insert or refresh the marker-bounded `using-sybermem` protocol block in managed instruction files. This is how the new session-entry rules reach old projects without requiring full document replacement.

For existing projects, `/sybermem-update` should now deliver both parts of `using-sybermem`: the marker-bounded protocol block in instruction files and the visible `/using-sybermem` skill in the global install.

## Release / update troubleshooting

- **`/sybermem-resume` exists globally but a project still answers with old guidance**
  Run `/sybermem-update` inside that project. Global refresh does not rewrite project-local instructions by itself.
- **Workspace search says the index is missing**
  Run `sybermem index build`, then retry workspace search.
- **Workspace search says the schema is stale or incompatible**
  Run `sybermem index build` to rebuild the disposable workspace index.
- **Claude record-intent capture says Core is unavailable**
  Use the bounded diagnostic path, then rerun `/sybermem-update` or reinstall the managed Claude hook. This diagnostic should not store prompt content.
- **OpenCode looks stale after an upgrade**
  Re-run the remote install command or the local update script. That refreshes the OpenCode skills and plugin, then run `/sybermem-update` in the project if project-local managed files also need refresh.
- **Codex skills are missing after an upgrade**
  Re-run the remote install command or the local update script. That refreshes `~/.agents/skills`; then run `/sybermem-update` in the project if `AGENTS.md` or `.sybermem/` needs refresh. From a checkout, use `python -m pytest packages/core/tests/test_package_integrity_scripts.py packages/core/tests/test_init_project_distribution.py -q` and `python scripts/check-plugin-package.py` as the non-mutating Codex Phase 1.5 smoke set.
- **`sybermem habit` is missing**
  Re-run the global install/update command. Habit commands are part of the CLI/Core runtime refresh, not project-local templates.

## Verify Installation

Type `/sybermem-init-project` or `/sybermem-update` in Claude Code, OpenCode, or Codex. If the project gets the `.sybermem/` directory structure, reports that an existing `ADR/` directory will be auto-migrated, or offers to refresh stale `AGENTS.md` / `CLAUDE.md`, the installation was successful.

For Claude Code specifically, a successful refresh also means the project can receive `.sybermem/hooks/task_recall.py` plus the managed `UserPromptSubmit` wiring without losing unrelated custom settings. For OpenCode, success still does not imply unsupported prompt-time automatic injection.

For Claude Code, OpenCode, and Codex, `/sybermem-resume` remains a user-invoked skill. Successful installation does not imply hidden auto-resume, background execution, or a second persistent memory store.
