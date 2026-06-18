---
type: change
date: 2026-06-18
number: 008
title: Add Claude Code plugin skeleton
status: implemented
author: Developer
related_files: [.claude-plugin/plugin.json, .claude-plugin/marketplace.json, hooks/hooks.json, hooks/run-hook.cmd, hooks/session-start, hooks/stop]
---

## Change Content
Added first-class Claude Code plugin packaging for SyberMem while preserving the existing project install and hook helper layout.

The change introduced:
- `.claude-plugin/plugin.json` with SyberMem package metadata.
- `.claude-plugin/marketplace.json` as a minimal development marketplace pointing at the plugin root.
- `hooks/hooks.json` declaring SessionStart and Stop lifecycle hooks.
- `hooks/run-hook.cmd` as a cross-platform wrapper that invokes extensionless hook scripts through bash.
- `hooks/session-start` to resolve initialized SyberMem projects and delegate to the project-managed startup context helper.
- `hooks/stop` to resolve initialized SyberMem projects and delegate to the project-managed stop-record helper when present.

## Reason for Change
Phase 1 of the SyberMem Platform Ecosystem Integration Plan requires a Claude Code plugin package shape so Claude Code can install and run SyberMem lifecycle hooks as a plugin, without breaking existing installs that already rely on `.sybermem/` project files and project-level hook helpers.

## Impact Scope
- Claude Code plugin distribution: adds the metadata and declarative hook entrypoints needed for plugin packaging.
- Hook lifecycle integration: SessionStart can inject existing SyberMem context, and Stop can reuse existing change-recording behavior.
- Existing installs: no existing `.sybermem/`, package, or installer files were moved or replaced.

## Implementation
The plugin-level hook scripts are thin delegators. They resolve a project root from `CLAUDE_PROJECT_DIR` or the current working directory, walk upward until they find `.sybermem/` plus `.claude/settings.json` or `.sybermem/INDEX.md`, and then call the existing project-managed Python helpers when available.

The Windows/Unix wrapper adapts the Superpowers polyglot `run-hook.cmd` pattern: Windows searches for Git Bash in standard install paths or `bash` on `PATH`, while Unix executes the requested extensionless hook script through bash.

## Test Verification
Verified with:
- `python -c "import json, pathlib; [json.load(open(p, encoding='utf-8')) for p in ['D:/adr-project/.claude-plugin/plugin.json','D:/adr-project/.claude-plugin/marketplace.json','D:/adr-project/hooks/hooks.json']]; print('JSON valid')"`
- `bash "D:/adr-project/hooks/session-start"`
- `bash "D:/adr-project/hooks/stop"`

Results:
- JSON validation printed `JSON valid`.
- `session-start` exited 0 and emitted valid JSON with SyberMem startup context.
- `stop` exited 0; in this initialized repository it emitted the expected non-blocking SyberMem note from the existing stop helper.

## Notes
The wrapper intentionally follows the cached Superpowers pattern to match Claude Code plugin behavior across Windows and Unix. The Windows batch branch forwards `%2` through `%9`, which is sufficient for the current lifecycle hooks.
