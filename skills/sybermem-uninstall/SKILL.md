---
name: sybermem-uninstall
description: Use when uninstalling, removing, disabling, deactivating, or cleaning SyberMem. Routes ambiguous natural-language requests by asking whether the user wants project-level deactivation or global removal.
---

# sybermem-uninstall Skill

**Announce at start:** "I'm using the sybermem-uninstall skill to safely choose project-level or global SyberMem uninstall."

Safe uninstall router for SyberMem. It protects project history by default and separates two very different operations:

- **Project-level deactivation**: stop SyberMem runtime takeover in the current project while preserving `.sybermem/` records.
- **Global uninstall**: remove user-level SyberMem skills, CLI/runtime, Claude launchers, OpenCode plugin, and Codex hooks; never delete project `.sybermem/` records.

## Hard Gate

Do NOT run a global uninstall unless the user explicitly confirmed global scope in the current turn. If scope is ambiguous, ask exactly one question and stop.

## Scope Detection

Treat the request as **project** when the user says or implies:

- current project / this repo / this project only
- disable hooks here / deactivate runtime here
- keep SyberMem installed but stop this project from using it
- 项目级 / 当前项目 / 这个仓库 / 停用当前项目

Treat the request as **global** only when the user says or implies:

- uninstall SyberMem from this machine
- remove all SyberMem skills/hooks/tools/CLI
- clean Claude/OpenCode/Codex SyberMem installation
- 全局卸载 / 从机器上删除 / 删除所有 hooks/tools/skills

If both are mentioned, or neither is clear, ask:

> 你要做哪一种卸载？
> 1. 项目级：只停用当前项目的 SyberMem runtime 接管，保留 `.sybermem/` 记录。
> 2. 全局：删除用户级 skills/hooks/plugin/CLI，但仍不删除任何项目 `.sybermem/` 记录。

## CLI Resolution

Before running SyberMem CLI commands, resolve a command variable first. On Windows PowerShell, prefer `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd` and store the chosen command in `$SyberMemCli`; on Unix, prefer `$HOME/.claude/sybermem/cli/sybermem` and store the chosen command in `"$SYBERMEM_CLI"`. If the fixed launcher is unavailable, fall back to bare `sybermem`. Do not modify persistent PATH automatically.

## Commands

### Project-level

Run from the target project:

```powershell
& $SyberMemCli uninstall --scope project --format json
```

```bash
"$SYBERMEM_CLI" uninstall --scope project --format json
```

Expected result: `status == "project_deactivated"`, `history_preserved == true`, and changed files list only project-managed deactivation targets. Summarize the JSON.

### Global

Only after explicit current-turn confirmation:

```powershell
& $SyberMemCli uninstall --scope global --yes --format json
```

```bash
"$SYBERMEM_CLI" uninstall --scope global --yes --format json
```

Expected result: `status == "global_uninstalled"` and `history_preserved == true`. Explain that user-level skills/hooks/plugin/CLI were removed and project `.sybermem/` histories were not removed.

## Fallbacks

If `sybermem uninstall --scope global --yes` is unavailable because the CLI is stale, tell the user to run the latest global update first, then retry. If the user is in a repository checkout and explicitly wants the script fallback, use:

- Windows: `./scripts/uninstall.ps1`
- macOS / Linux: `./scripts/uninstall.sh`

Do not use repository scripts as the first path for ordinary users; the installed CLI is the stable path after update.

## Verification

- Project scope: confirm the command exited 0 and reported `history_preserved: true`.
- Global scope: confirm the command exited 0 and reported `history_preserved: true`.
- Never claim `.sybermem/` records were deleted; deletion of history is not part of this skill.
