---
type: change
record_id: change-878c029967b944cca3fc634c7148cf27
date: 2026-08-25
title: Codex context markers and 0.1.1 version rollout
status: active
source: implementation
key_conclusion: Codex additionalContext now carries explicit SyberMem markers and the distribution version is bumped to 0.1.1 so users can refresh project-local files after global updates.
topics: [codex, distribution, versioning]
author: Sisyphus
related_files: [.codex/hooks/user_prompt.py, .codex/hooks/session_start.py, .codex/INSTALL.md, docs/feature_map.md, VERSION, packages/core/pyproject.toml, packages/cli/pyproject.toml]
---

## Change Content

Added explicit ASCII SyberMem marker headings to Codex `additionalContext` payloads:

- `## SyberMem Codex Context` for prompt-time `UserPromptSubmit` injections.
- `## SyberMem Codex Startup` for `SessionStart` startup context injections.

The prompt marker summarizes which context classes were injected using stable ASCII labels: `[recall]`, `[habit]`, and `[norms]`. Empty prompt-time injections remain silent. Codex documentation and the feature map now state that this is the supported Codex visibility path and that SyberMem does not install OpenCode-style TUI toasts or default Windows desktop notifications for Codex.

The repository version was bumped from `0.1.0` to `0.1.1` and synchronized across Python packages and plugin manifests.

## Reason for Change

Recent installer, updater, OpenCode, and Codex integration fixes needed a real version increment to close the existing installed-version versus project-version update-notification loop. Without the bump, already stamped `0.1.0` projects would not see themselves as trailing a refreshed global install.

Codex lacks a confirmed OpenCode-equivalent `client.tui.showToast` API, and Windows desktop notifications are not a reliable default hot-path mechanism. Keeping visibility inside `hookSpecificOutput.additionalContext` preserves model-visible, cross-platform, fail-open behavior without reintroducing PowerShell or desktop-notification dependencies.

## Impact Scope

- Old users who rerun a global installer/update receive version `0.1.1`; projects still stamped `0.1.0` can then surface the existing `/sybermem-update` nudge.
- Codex users who receive startup or prompt-time SyberMem context get an explicit marker inside the same model-visible context packet.
- OpenCode toast behavior is unchanged.
- No default Windows toast, third-party notifier, `.codex/config.toml`, or extra stdout/stderr channel was added.

## Implementation

- Updated `.codex/hooks/user_prompt.py` to prefix non-empty prompt-time context with a summary marker derived from actual injected sections.
- Updated `.codex/hooks/session_start.py` to prefix startup context with a startup marker.
- Updated Codex hook tests for the new marker contract, including scoped project norms.
- Updated `.codex/INSTALL.md` and `docs/feature_map.md` to document Codex marker visibility and unsupported toast claims.
- Bumped `VERSION` to `0.1.1` and ran `scripts/sync-version.py` to update all managed manifests and `FALLBACK_VERSION`.

## Test Verification

- `python -m py_compile .codex/hooks/user_prompt.py .codex/hooks/session_start.py packages/core/tests/test_codex_habit_hook.py packages/core/tests/test_codex_lifecycle_hooks.py`
- `python -m pytest packages/core/tests/test_codex_habit_hook.py packages/core/tests/test_codex_lifecycle_hooks.py packages/core/tests/test_package_integrity_scripts.py -q` -> 61 passed
- `python scripts/check-plugin-package.py` -> OK after removing generated Python cache artifacts
- `python -m pytest packages/core/tests/test_package_integrity_scripts.py -q` -> 41 passed
- `python -m pytest packages/core/tests/test_init_project_distribution.py packages/core/tests/test_install_shell_safety.py packages/core/tests/test_install_powershell_safety.py packages/core/tests/test_uninstall_shell_safety.py packages/core/tests/test_uninstall_powershell_safety.py packages/core/tests/test_cli_uninstall_scope.py -q` -> 17 passed, 1 skipped

## Notes

Distribution chain check confirmed install/update scripts copy canonical `.codex/hooks/user_prompt.py` and `.codex/hooks/session_start.py` into user-level `~/.codex/hooks/sybermem_user_prompt.py` and `~/.codex/hooks/sybermem_session_start.py`, so old users receive the marker functionality after rerunning the global installer or updater.
