# Installation Guide

## Upgrading existing projects

Refreshing the global install alone does not automatically refresh project-local hooks, templates, or managed settings patches. After every global install or update, open each target project and run `/sybermem-update`.

That matters for resume and search behavior too. A global refresh makes the latest skills and runtime available to the user, but existing projects still need `/sybermem-update` when you want refreshed managed instructions, hook files, templates, or settings surgery inside the project.

Installers write the installed version to `~/.claude/sybermem/VERSION`, and `sybermem project refresh` stamps `sybermem_version` into each project's `.sybermem/project.yaml`. When a project trails the installed SyberMem, session-start surfaces a throttled, fail-open `⭐ run /sybermem-update` nudge (OpenCode `session.created` toast; Claude/Codex `SessionStart` additionalContext). Run `sybermem doctor` to see installed vs project version on demand. Unknown/empty versions never nag.

If the project is not initialized yet, run `/sybermem-init-project`. If the project already exists, the safe order is:

1. global install or global refresh
2. `/sybermem-update` inside the target project
3. `/sybermem-init-project` only when initialization is still missing

If the same source records have already been compressed into an existing digest, `/sybermem-digest` must point to the existing digest instead of creating a duplicate.

If an older project still contains project-local copies such as `.claude/skills/sybermem-*`, Claude may load both the local and global copies and show duplicates in the `/` list. Once you have switched to the global-install model, those old project-local copies can be deleted.

`/sybermem-link` is retired. Re-run the global installer or updater to remove old copies from Claude Code, OpenCode, and Codex skill homes. Use `/sybermem-record` to add, correct, or confirm relations between existing records; stored relation fields and search behavior require no data migration.

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

Script install remains supported as the compatibility path. These commands refresh the user-level Claude Code skills, OpenCode skills, Codex skills, the OpenCode plugin, the Codex `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` hooks, and the CLI/Core runtime. User Habit Memory ships through the Core/CLI runtime plus `/sybermem-habit`, and stores data in the user-owned `~/.sybermem/user-habits/` tree, so it does not require a project `.sybermem/` migration. Scoped uninstall ships through the same update path: `/sybermem-uninstall` is copied to all supported skill roots, and the refreshed CLI provides `sybermem uninstall --scope project|global`.

Installers also create an agent-safe fixed CLI launcher: `$HOME/.claude/sybermem/cli/sybermem` on macOS / Linux and `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd` on Windows. OpenCode plugin code, the Codex hooks, and CLI-using skills prefer that launcher when a child agent process cannot resolve bare `sybermem`. The scripts do not modify persistent PATH by default; adding the launcher directory to PATH is optional user configuration.

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

##### Windows OpenCode / cmd.exe (PowerShell-free)

```cmd
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.py').read())"
```

Use `python scripts/update.py` for a local checkout update. This path avoids
spawning `powershell.exe` and does not modify persistent `PATH`.

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

On OpenCode, `/sybermem-resume` is manual and read-only; `/sybermem-search` and `sybermem context session|prompt|habit` provide explicit historical/context diagnostics. V1's separate compatibility plugin uses `chat.message` plus `experimental.chat.system.transform`; V2 uses persisted-message `prompt`/`context` injection and a server + companion TUI directory package. Do not expect hidden auto-resume or unsupported background execution. V2 does not yet perform V1's background remote-version refresh.

### Codex

Codex support is partial runtime integration plus user skills. The global install/update scripts copy `packages/claude-skills` to `~/.agents/skills` on macOS / Linux and `%USERPROFILE%\.agents\skills` on Windows with the `Codex` target label, and they install `~/.codex/hooks/sybermem_session_start.py`, `sybermem_user_prompt.py`, `sybermem_stop.py`, and `sybermem_post_compact.py` plus `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` merges in `~/.codex/hooks.json`. Project setup still uses `/sybermem-init-project` or `/sybermem-update`, which refresh `.sybermem/` for Codex agents and remove any legacy SyberMem protocol block from `AGENTS.md`. Project health checks can also discover current templates from the Codex-installed `~/.agents/skills/sybermem-init-project/project-files` tree.

For Codex-specific boundaries and verification, see [`.codex/INSTALL.md`](.codex/INSTALL.md). Codex now supports bounded startup context through `SessionStart`, high-signal project recall/User Habit Memory reminders/record-intent capture through `UserPromptSubmit` + `hookSpecificOutput.additionalContext`, loop-safe record nudges through `Stop`, and compact re-seed markers through `PostCompact`, but do not expect `.codex/config.toml`, hidden auto-resume, background automation, prompt/agent handler runtimes, or direct compaction prompt injection.

## Update

### One-liner update

Re-run the one-liner install command. This is a real global runtime refresh, not just a skill copy. It refreshes:

- Claude Code skills
- OpenCode skills
- Codex skills
- OpenCode plugin selected by host major: V1 separate `sybermem-v1.ts` → `~/.config/opencode/plugins/sybermem.ts`; V2 complete `dist-v2` package → `~/.config/opencode/sybermem-v2/` with one directory plugin entry (never both loaded)
- Codex SessionStart / UserPromptSubmit / Stop / PostCompact hooks
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

```cmd
:: Windows OpenCode / cmd.exe
cd sybermem && git pull && python scripts/update.py
```

After the script finishes, open the target project and run `/sybermem-update`.
That follow-up is where project-local hook files, templates, and settings entries are created or refreshed, the `.gitignore` SyberMem block is added (git projects), the `sybermem_version` stamp is updated, and any legacy `CLAUDE.md` / `AGENTS.md` protocol block is removed (migration).

That same project-local refresh is also how older Claude projects pick up updated guidance and managed prompt hooks, including `/sybermem-resume` routing, read-only recall, and User Habit Memory reminders.

For CLI availability fixes, OpenCode plugin fixes, Codex hook fixes, or skill instruction fixes, use the same propagation path: re-run the global installer/updater to refresh the runtime, fixed launcher, OpenCode plugin, Codex hook, and user-level skills; then run `/sybermem-update` inside each existing project so project-local instructions and managed files are refreshed.

For uninstall routing fixes, the global installer/updater is sufficient to refresh the CLI and `/sybermem-uninstall` skill. Existing project histories remain in `.sybermem/`; project-level deactivation is `sybermem uninstall --scope project`, and machine-level removal is `sybermem uninstall --scope global --yes`.

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

For existing projects, `/sybermem-update` should also remove any legacy marker-bounded `using-sybermem` protocol block from managed instruction files. This is how old projects are migrated to the no-injection model without requiring full document replacement.

For existing projects, `/sybermem-update` should now deliver the visible `/using-sybermem` skill in the global install; no instruction-file protocol block is injected.

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
  Re-run the remote install command or local update script. Check the OpenCode-specific result: unknown host major skips its plugin unless `--opencode-major 1|2` (or `SYBERMEM_OPENCODE_MAJOR`) is supplied. V1 deploys the standalone file; V2 deploys the complete directory package and replaces the known V1 entry rather than dual-loading it. Verify deployed hashes, reload and check the host loader, then test recall and (V2) actual TUI feedback separately; files alone prove neither. Run `/sybermem-update` if project-managed files need refresh.
- **Codex skills are missing after an upgrade**
  Re-run the remote install command or the local update script. That refreshes `~/.agents/skills`; then run `/sybermem-update` in the project if `.sybermem/` needs refresh. From a checkout, use `python -m pytest packages/core/tests/test_package_integrity_scripts.py packages/core/tests/test_init_project_distribution.py -q` and `python scripts/check-plugin-package.py` as the non-mutating Codex package smoke set.
- **Codex runtime hooks are missing after an upgrade**
  Re-run the remote install command or the local update script so `~/.codex/hooks/sybermem_session_start.py`, `~/.codex/hooks/sybermem_user_prompt.py`, `~/.codex/hooks/sybermem_stop.py`, `~/.codex/hooks/sybermem_post_compact.py`, and `~/.codex/hooks.json` are refreshed. Then run `/sybermem-update` in the project if project-managed files also need refresh.
- **`sybermem habit` is missing**
  Re-run the global install/update command. Habit commands are part of the CLI/Core runtime refresh, not project-local templates.

## What gets installed: Skill discovery tiers

Installation delivers all 13 Skills to every supported host. For finding your way
around, they are presented in two tiers — the same classification used by
`docs/feature_map.md`, `README.md`, and `README.en.md`. Start at the Core tier;
reach the advanced/lifecycle tier when you hit the specific moment it serves.
"Advanced / lifecycle" means specialized or less frequent, never deprecated;
every Skill in that tier is fully supported and directly invocable.

### Core entrypoints

- `using-sybermem`: read-only orientation — resolve the project, report compact installation/project state, and present the one canonical next command.
- `sybermem-init-project`: initialize or re-scaffold SyberMem in a project.
- `sybermem-record`: record a completed unit of work as a canonical record, and crystallize binding project rules into norms.
- `sybermem-resume`: bounded read-only continuity brief for restarting work in an existing project.
- `sybermem-search`: find historical records, decisions, and digests inside the project.
- `sybermem-digest`: compress a settled phase into durable phase-level conclusions.
- `sybermem-habit`: manage user-level habits and pending habit candidates across projects.

### Advanced / lifecycle

- `sybermem-install`: first-time installation of the SyberMem system on a machine.
- `sybermem-update`: refresh an existing project's managed SyberMem files after a version upgrade.
- `sybermem-uninstall`: natural-language uninstall entrypoint; it asks project vs global scope when unclear, requires explicit confirmation for global uninstall, and project scope preserves `.sybermem/` history.
- `sybermem-summary`: project status and memory/recall health panel for weekly or monthly review.
- `sybermem-phase-analyze`: build or refresh the structural phase index from full record history.
- `sybermem-theme-digest`: synthesize a cross-phase, topic-level conclusion from related records and phases.

This section documents discovery order only. It does not change what the
installers copy, and the installers' own emitted skill catalog is unchanged.

## Verify Installation

Type `/sybermem-init-project` or `/sybermem-update` in Claude Code, OpenCode, or Codex. If the project gets the `.sybermem/` directory structure or removes a legacy SyberMem protocol block from `AGENTS.md` / `CLAUDE.md`, the installation was successful.

For Claude Code specifically, a successful refresh also means the project can receive `.sybermem/hooks/task_recall.py` plus the managed `UserPromptSubmit` wiring without losing unrelated custom settings. For OpenCode, project refresh alone does not verify plugin loading, prompt-time recall or toasts; perform the three separate install/hash, loader, and functionality checks in [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

For Claude Code, OpenCode, and Codex, `/sybermem-resume` remains a user-invoked skill. Successful installation does not imply hidden auto-resume, background execution, or a second persistent memory store. In Codex specifically, successful installation also does not imply `.codex/config.toml` management, prompt/agent handler runtimes, or direct compaction prompt injection.
