# SyberMem Two-Layer Uninstall Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe uninstall model that separates project-level SyberMem deactivation from global SyberMem removal, preserving history while making the runtime behavior stop cleanly.

**Architecture:** Introduce two separate commands/entrypoints: one for project-level deactivation that leaves `.sybermem/` intact but removes runtime integration, and one for global uninstall that removes globally installed skills/CLI/launchers without touching project history. Keep them independent to avoid dangerous flag combinations.

**Tech Stack:** Python 3.10+, Claude/OpenCode skill layer, filesystem operations, project-local `.claude/settings.json` / instruction files

---

### Task 1: Implement project-level uninstall (deactivate runtime, preserve history)

**Files:**
- Create: `packages/core/sybermem_core/uninstall.py`
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Create `packages/core/sybermem_core/uninstall.py`**

```python
from __future__ import annotations

from pathlib import Path
import json


def remove_sybermem_protocol_block(text: str) -> str:
    start = "<!-- SYBERMEM_SESSION_PROTOCOL:START -->"
    end = "<!-- SYBERMEM_SESSION_PROTOCOL:END -->"
    if start not in text or end not in text:
        return text
    before = text.split(start, 1)[0].rstrip()
    after = text.split(end, 1)[1].lstrip()
    pieces = []
    if before:
        pieces.append(before)
    if after:
        pieces.append(after)
    return "\n\n".join(pieces).rstrip() + "\n"


def deactivate_project_sybermem(root: Path) -> dict[str, object]:
    changed = []

    # 1) Preserve .sybermem/ untouched
    sybermem_dir = root / ".sybermem"
    if not sybermem_dir.is_dir():
        raise ValueError(f"No .sybermem directory found at {root}")

    # 2) Remove SyberMem hook/env entries from .claude/settings.json
    settings_path = root / ".claude" / "settings.json"
    if settings_path.is_file():
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        env = dict(data.get("env", {}))
        env.pop("SYBERMEM_RECORD_MODE", None)
        if env:
            data["env"] = env
        elif "env" in data:
            data.pop("env")

        hooks = dict(data.get("hooks", {}))
        for key in ["SessionStart", "Stop", "UserPromptSubmit"]:
            hooks.pop(key, None)
        if hooks:
            data["hooks"] = hooks
        elif "hooks" in data:
            data.pop("hooks")

        settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed.append(str(settings_path).replace('\\', '/'))

    # 3) Remove protocol block from CLAUDE.md / AGENTS.md
    for name in ["CLAUDE.md", "AGENTS.md"]:
        p = root / name
        if p.is_file():
            original = p.read_text(encoding="utf-8")
            updated = remove_sybermem_protocol_block(original)
            if updated != original:
                p.write_text(updated, encoding="utf-8")
                changed.append(str(p).replace('\\', '/'))

    return {
        "status": "project_deactivated",
        "root": str(root).replace('\\', '/'),
        "history_preserved": True,
        "changed_files": changed,
    }
```

- [ ] **Step 2: Add a CLI surface**

In `packages/cli/sybermem_cli/main.py`, add an import:

```python
from sybermem_core.uninstall import deactivate_project_sybermem
```

Add a handler:

```python
def cmd_project_uninstall(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    try:
        payload = deactivate_project_sybermem(root)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.format == "json":
        print(dump_json(payload))
    else:
        print("Deactivated SyberMem runtime in this project:")
        print(f"- project root: {payload['root']}")
        print("- history preserved: yes")
        if payload['changed_files']:
            print("- changed files:")
            for f in payload['changed_files']:
                print(f"  - {f}")
    return 0
```

And add parser wiring:

```python
    uninstall_cmd = project_sub.add_parser("uninstall")
    uninstall_cmd.add_argument("--format", choices=["text", "json"], default="text")
    uninstall_cmd.set_defaults(func=cmd_project_uninstall)
```

- [ ] **Step 3: Verify on a temp project clone/copy**

Use a temporary copy of a SyberMem-initialized project (not the live repo) and run:

```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main project uninstall --format json
```

Expected:
- `.sybermem/` still exists
- `.claude/settings.json` no longer contains SyberMem hooks or `SYBERMEM_RECORD_MODE`
- `CLAUDE.md` / `AGENTS.md` no longer contain the SyberMem protocol block

- [ ] **Step 4: Commit**

```bash
git add packages/core/sybermem_core/uninstall.py packages/cli/sybermem_cli/main.py
git commit -m "feat: add project-level SyberMem uninstall"
```

---

### Task 2: Implement global uninstall (remove global runtime, preserve project history)

**Files:**
- Create: `scripts/uninstall.ps1`
- Create: `scripts/uninstall.sh`
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Create `scripts/uninstall.ps1`**

```powershell
$ErrorActionPreference = "Stop"

$claudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
$opencodeSkills = Join-Path $env:USERPROFILE ".config\opencode\skills"
$claudeSybermem = Join-Path $env:USERPROFILE ".claude\sybermem"
$opencodePlugin = Join-Path $env:USERPROFILE ".config\opencode\plugins\sybermem.ts"

foreach ($name in @(
  "sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest",
  "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem",
  "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest",
  "sybermem-team-publish", "sybermem-team-summary"
)) {
  Remove-Item -Recurse -Force (Join-Path $claudeSkills $name) -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force (Join-Path $opencodeSkills $name) -ErrorAction SilentlyContinue
}

Remove-Item -Recurse -Force $claudeSybermem -ErrorAction SilentlyContinue
Remove-Item -Force $opencodePlugin -ErrorAction SilentlyContinue

Write-Host "SyberMem global uninstall complete."
Write-Host "Project histories under .sybermem/ were not removed."
```

- [ ] **Step 2: Create `scripts/uninstall.sh`**

```bash
#!/bin/bash
set -e

CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"
CLAUDE_SYBERMEM="$HOME/.claude/sybermem"
OPENCODE_PLUGIN="$HOME/.config/opencode/plugins/sybermem.ts"

for name in \
  sybermem-init-project sybermem-record sybermem-summary sybermem-digest \
  sybermem-phase-analyze sybermem-phase-confirm using-sybermem \
  sybermem-update sybermem-search sybermem-link sybermem-theme-digest \
  sybermem-team-publish sybermem-team-summary; do
  rm -rf "$CLAUDE_SKILLS/$name" || true
  rm -rf "$OPENCODE_SKILLS/$name" || true
done

rm -rf "$CLAUDE_SYBERMEM" || true
rm -f "$OPENCODE_PLUGIN" || true

echo "SyberMem global uninstall complete."
echo "Project histories under .sybermem/ were not removed."
```

- [ ] **Step 3: Add a README note for uninstall behavior**

Add a small section to both READMEs documenting:
- project-level uninstall preserves `.sybermem/`
- global uninstall removes global skills/CLI/launchers only

- [ ] **Step 4: Verify on the current machine**

Do a dry-run inspection of the target paths before removal (list what would be deleted). If you do not want to actually uninstall your own environment during development, explicitly document that this task was verified by path inspection and script review rather than executing the destructive removal.

- [ ] **Step 5: Commit**

```bash
git add scripts/uninstall.ps1 scripts/uninstall.sh README.md README.en.md
git commit -m "feat: add global SyberMem uninstall scripts"
```

---

### Task 3: Final acceptance verification and route consistency check

**Files:**
- No repo-file changes required by default

- [ ] **Step 1: Verify project-level uninstall preserves history**

Use a temp SyberMem project copy and confirm:
- `.sybermem/` still exists after uninstall
- runtime integration files are disabled/cleaned
- no history files were deleted

- [ ] **Step 2: Verify global uninstall scope is limited**

By inspection or a safe dry-run, confirm the uninstall scripts only target:
- global skill directories
- global CLI/launcher directory
- OpenCode plugin file

and do **not** touch:
- arbitrary projects
- Team repo content
- `.sybermem/` histories inside repositories

- [ ] **Step 3: Record the acceptance result**

Summarize clearly:
- what project uninstall removes
- what project uninstall preserves
- what global uninstall removes
- what global uninstall preserves

- [ ] **Step 4: No commit needed** (verification only)
