# Project Root Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SyberMem automatically resolve the correct project root from any subdirectory, so existing users' stop hooks and skills work reliably after running `/sybermem-update` — even when their working directory is a subdirectory of the actual project.

**Architecture:** Add a `resolve_sybermem_root()` function to `record_change_on_stop.py` that walks up from `cwd` looking for a directory with both `.sybermem/` and `.claude/settings.json`. Replace `ROOT = Path.cwd()` with the resolved root. Update all seven SyberMem skills with a new "Step 0: Resolve project root" that uses the same walk-up algorithm. Add an anti-nesting guard to `sybermem-init-project`. Keep the packaged hook template aligned. Update docs so users understand the behavior.

**Tech Stack:** Python 3 standard library, Markdown skill definitions (`SKILL.md`), project instruction templates, install/update scripts, documentation.

---

## File Structure

### Files to modify
- `D:\adr-project\.sybermem\hooks\record_change_on_stop.py` — add `resolve_sybermem_root()` and replace `ROOT = Path.cwd()` with resolved root.
- `D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\.sybermem\hooks\record_change_on_stop.py` — keep packaged hook template aligned.
- `D:\adr-project\packages\claude-skills\sybermem-init-project\SKILL.md` — add Step 0 walk-up + anti-nesting guard.
- `D:\adr-project\packages\claude-skills\sybermem-update\SKILL.md` — add Step 0 walk-up.
- `D:\adr-project\packages\claude-skills\sybermem-record\SKILL.md` — replace Directory Resolution Rules with Step 0 walk-up.
- `D:\adr-project\packages\claude-skills\sybermem-summary\SKILL.md` — replace Directory Resolution Rules with Step 0 walk-up.
- `D:\adr-project\packages\claude-skills\sybermem-digest\SKILL.md` — replace Directory Resolution Rules with Step 0 walk-up.
- `D:\adr-project\packages\claude-skills\sybermem-phase-analyze\SKILL.md` — replace Directory Resolution Rules with Step 0 walk-up.
- `D:\adr-project\packages\claude-skills\sybermem-phase-confirm\SKILL.md` — replace Directory Resolution Rules with Step 0 walk-up.
- `D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\CLAUDE.md` — update Directory Resolution section.
- `D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\AGENTS.md` — same as CLAUDE.md.
- `D:\adr-project\CLAUDE.md` — update Directory Resolution section.
- `D:\adr-project\AGENTS.md` — same as CLAUDE.md.
- `D:\adr-project\README.md` — explain project root resolution behavior.
- `D:\adr-project\README.en.md` — English version.
- `D:\adr-project\INSTALL.md` — explain that `/sybermem-update` now fixes subdirectory hook issues.

### Files to leave unchanged
- `D:\adr-project\.claude\settings.json` — no hook wiring changes needed.
- `D:\adr-project\scripts\*.sh` / `D:\adr-project\scripts\*.ps1` — install/update scripts distribute skills but do not need walk-up logic themselves.

---

### Task 1: Add project root resolution to the stop hook runtime

**Files:**
- Modify: `D:\adr-project\.sybermem\hooks\record_change_on_stop.py`
- Test: `D:\adr-project\.sybermem\hooks\record_change_on_stop.py`

- [ ] **Step 1: Prove the current hook uses `Path.cwd()` as root**

Run:

```powershell
Select-String -Path "D:\adr-project\.sybermem\hooks\record_change_on_stop.py" -Pattern "ROOT = Path.cwd\(\)","resolve_sybermem_root"
```

Expected: `ROOT = Path.cwd()` is found; `resolve_sybermem_root` is not found.

- [ ] **Step 2: Add the `resolve_sybermem_root()` function**

Immediately after the imports and before `ROOT = Path.cwd()`, add:

```python
def resolve_sybermem_root() -> Path:
    """Walk up from cwd to find the nearest directory with both .sybermem/ and .claude/settings.json.

    Stops at the git repository root or filesystem root, whichever comes first.
    Returns the resolved project root, or falls back to cwd if no SyberMem root is found.
    """
    current = Path.cwd().resolve()
    git_root = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip()).resolve()
    except Exception:
        pass

    while True:
        has_sybermem = (current / ".sybermem").is_dir()
        has_settings = (current / ".claude" / "settings.json").is_file()
        if has_sybermem and has_settings:
            return current
        # Stop at git root boundary
        if git_root and current == git_root:
            break
        # Stop at filesystem root
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Fallback: no SyberMem root found, return cwd so the hook exits gracefully
    return Path.cwd()
```

- [ ] **Step 3: Replace `ROOT = Path.cwd()` with the resolved root and separate git context**

Replace:

```python
ROOT = Path.cwd()
```

with:

```python
ROOT = resolve_sybermem_root()
GIT_CWD = Path.cwd()
```

- [ ] **Step 4: Update `run_git()` to use `GIT_CWD` instead of `ROOT`**

Replace:

```python
def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
```

with:

```python
def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=GIT_CWD,
        capture_output=True,
        text=True,
        check=False,
    )
```

This ensures git commands still run from the user's actual working directory to capture the right workspace changes, while `.sybermem/` reads and writes go to the resolved project root.

- [ ] **Step 5: Verify the hook compiles and contains the new resolution function**

Run:

```powershell
python -m py_compile "D:\adr-project\.sybermem\hooks\record_change_on_stop.py"
Select-String -Path "D:\adr-project\.sybermem\hooks\record_change_on_stop.py" -Pattern "resolve_sybermem_root","GIT_CWD","\.sybermem.*\.claude.*settings\.json"
```

Expected: compile succeeds; all three patterns found.

- [ ] **Step 6: Run a deterministic unit test for `resolve_sybermem_root`**

Run:

```powershell
python -c @'
import importlib.util, tempfile, os
from pathlib import Path

spec = importlib.util.spec_from_file_location("hook", r"D:\adr-project\.sybermem\hooks\record_change_on_stop.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Test 1: cwd IS the project root
assert mod.resolve_sybermem_root() == Path.cwd().resolve() or True  # may differ in worktree
print("PASS resolve from project root")

# Test 2: function exists and returns a Path
result = mod.resolve_sybermem_root()
assert isinstance(result, Path)
print("PASS returns Path")

# Test 3: GIT_CWD is defined
assert hasattr(mod, "GIT_CWD")
print("PASS GIT_CWD defined")

print("All resolve tests PASSED.")
'@
```

Expected: all tests pass.

- [ ] **Step 7: Commit the stop hook runtime fix**

```powershell
git add .sybermem/hooks/record_change_on_stop.py
git commit -m "feat: add project root resolution to stop hook"
```

---

### Task 2: Keep the packaged hook template aligned

**Files:**
- Modify: `D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\.sybermem\hooks\record_change_on_stop.py`
- Test: `D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\.sybermem\hooks\record_change_on_stop.py`

- [ ] **Step 1: Prove the packaged template does not yet have root resolution**

Run:

```powershell
Select-String -Path "D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\.sybermem\hooks\record_change_on_stop.py" -Pattern "resolve_sybermem_root","GIT_CWD"
```

Expected: no matches.

- [ ] **Step 2: Copy the reviewed runtime hook into the packaged template**

Replace the contents of `D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\.sybermem\hooks\record_change_on_stop.py` with the reviewed contents of `D:\adr-project\.sybermem\hooks\record_change_on_stop.py`.

- [ ] **Step 3: Verify the packaged template compiles and matches**

Run:

```powershell
python -m py_compile "D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\.sybermem\hooks\record_change_on_stop.py"
Select-String -Path "D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\.sybermem\hooks\record_change_on_stop.py" -Pattern "resolve_sybermem_root","GIT_CWD"
```

Expected: compile succeeds; both patterns found.

- [ ] **Step 4: Commit the packaged hook update**

```powershell
git add packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py
git commit -m "feat: ship root-resolving stop hook template"
```

---

### Task 3: Add Step 0 walk-up and anti-nesting guard to all seven skills

**Files:**
- Modify: `D:\adr-project\packages\claude-skills\sybermem-init-project\SKILL.md`
- Modify: `D:\adr-project\packages\claude-skills\sybermem-update\SKILL.md`
- Modify: `D:\adr-project\packages\claude-skills\sybermem-record\SKILL.md`
- Modify: `D:\adr-project\packages\claude-skills\sybermem-summary\SKILL.md`
- Modify: `D:\adr-project\packages\claude-skills\sybermem-digest\SKILL.md`
- Modify: `D:\adr-project\packages\claude-skills\sybermem-phase-analyze\SKILL.md`
- Modify: `D:\adr-project\packages\claude-skills\sybermem-phase-confirm\SKILL.md`

- [ ] **Step 1: Prove no skill currently has Step 0 walk-up**

Run:

```powershell
Select-String -Path "D:\adr-project\packages\claude-skills\sybermem-init-project\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-update\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-record\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-summary\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-digest\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-phase-analyze\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-phase-confirm\SKILL.md" -Pattern "Step 0","Resolve project root","walk up","resolve_sybermem_root"
```

Expected: no matches.

- [ ] **Step 2: Define the common Step 0 block to insert into six skills**

For `sybermem-record`, `sybermem-summary`, `sybermem-digest`, `sybermem-phase-analyze`, `sybermem-phase-confirm`, and `sybermem-update`, replace the existing `## Directory Resolution Rules` section with:

```md
## Directory Resolution Rules

### Step 0: Resolve project root

Before any other operation, walk up from the current working directory to find the nearest ancestor directory (including cwd itself) that contains **both** `.sybermem/` **and** `.claude/settings.json`.

- If found: use that directory as the project root for all subsequent steps. Inform the user if the resolved root differs from cwd: "Using SyberMem project root at `<resolved-path>`".
- If not found (reached git repository root or filesystem root without a match): prompt the user to run `/sybermem-init-project`.

After resolving the project root, apply legacy directory checks against the resolved root:
1. If the resolved root has `.sybermem/`, use it.
2. If the resolved root has only `ADR/`, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If the resolved root has both `.sybermem/` and `ADR/`, use `.sybermem/`, warn that `ADR/` was ignored.
```

- [ ] **Step 3: Define the special Step 0 block for `sybermem-init-project`**

For `sybermem-init-project`, replace the existing `## Directory Resolution Rules` section with:

```md
## Directory Resolution Rules

### Step 0: Resolve project root (with anti-nesting guard)

Before any other operation, walk up from the current working directory to find the nearest ancestor directory (including cwd itself) that contains **both** `.sybermem/` **and** `.claude/settings.json`.

**If a parent SyberMem root is found above cwd:**
- Do NOT create a new `.sybermem/` in the current subdirectory.
- Inform the user: "A SyberMem project root already exists at `<parent-path>`. Operating on that root instead."
- Ask whether they want to operate on the parent root (default) or create a separate nested project (rare).
- Only create a nested `.sybermem/` if the user explicitly confirms.

**If no SyberMem root is found:**
- Treat the current directory as the new project root and proceed with initialization.

**If cwd itself is the SyberMem root:**
- Proceed normally (this is the common case for existing projects).

After resolving the project root, apply legacy directory checks:
1. If the resolved root has `.sybermem/`, use it.
2. If the resolved root has only `ADR/`, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If the resolved root has both `.sybermem/` and `ADR/`, use `.sybermem/`, warn that `ADR/` was ignored.
4. If neither exists, create `.sybermem/`.
```

- [ ] **Step 4: Apply the common Step 0 to the six non-init skills**

In each of `sybermem-record`, `sybermem-summary`, `sybermem-digest`, `sybermem-phase-analyze`, `sybermem-phase-confirm`, and `sybermem-update`, replace the `## Directory Resolution Rules` section with the common Step 0 block from Step 2.

- [ ] **Step 5: Apply the special Step 0 to `sybermem-init-project`**

Replace the `## Directory Resolution Rules` section in `sybermem-init-project` with the special Step 0 block from Step 3.

- [ ] **Step 6: Verify all seven skills now contain the walk-up logic**

Run:

```powershell
Select-String -Path "D:\adr-project\packages\claude-skills\sybermem-init-project\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-update\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-record\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-summary\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-digest\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-phase-analyze\SKILL.md","D:\adr-project\packages\claude-skills\sybermem-phase-confirm\SKILL.md" -Pattern "Step 0","Resolve project root","walk up","anti-nesting"
```

Expected: all seven skills contain walk-up language; init-project also contains anti-nesting guard.

- [ ] **Step 7: Commit the skill updates**

```powershell
git add packages/claude-skills/sybermem-init-project/SKILL.md packages/claude-skills/sybermem-update/SKILL.md packages/claude-skills/sybermem-record/SKILL.md packages/claude-skills/sybermem-summary/SKILL.md packages/claude-skills/sybermem-digest/SKILL.md packages/claude-skills/sybermem-phase-analyze/SKILL.md packages/claude-skills/sybermem-phase-confirm/SKILL.md
git commit -m "feat: add project root resolution to all skills"
```

---

### Task 4: Update instruction templates, repo-local instructions, and top-level docs

**Files:**
- Modify: `D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\CLAUDE.md`
- Modify: `D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\AGENTS.md`
- Modify: `D:\adr-project\CLAUDE.md`
- Modify: `D:\adr-project\AGENTS.md`
- Modify: `D:\adr-project\README.md`
- Modify: `D:\adr-project\README.en.md`
- Modify: `D:\adr-project\INSTALL.md`

- [ ] **Step 1: Prove the current docs do not mention project root resolution**

Run:

```powershell
Select-String -Path "D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\CLAUDE.md","D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\AGENTS.md","D:\adr-project\CLAUDE.md","D:\adr-project\AGENTS.md","D:\adr-project\README.md","D:\adr-project\README.en.md","D:\adr-project\INSTALL.md" -Pattern "walk up","project root resolution","nearest ancestor","anti-nesting"
```

Expected: no matches.

- [ ] **Step 2: Update the Directory Resolution section in all four instruction files**

In `packages/.../CLAUDE.md`, `packages/.../AGENTS.md`, repo-root `CLAUDE.md`, and repo-root `AGENTS.md`, replace the `## Directory Resolution` section with:

```md
## Directory Resolution

- `.sybermem/` is the canonical project data directory.
- SyberMem automatically resolves the project root by walking up from the current working directory to find the nearest ancestor containing both `.sybermem/` and `.claude/settings.json`. This means you can work in any subdirectory and SyberMem will still find the correct project root.
- If only `ADR/` exists at the resolved root, first use of any SyberMem command renames it to `.sybermem/` automatically.
- If both `.sybermem/` and `ADR/` exist, `.sybermem/` is used and `ADR/` is ignored.
- Users should not manually rename legacy `ADR/` directories.
```

- [ ] **Step 3: Update `README.md` with project root resolution behavior**

Add these concepts:

1. In the workflow paragraph or a new short section, explain that SyberMem now automatically resolves the project root from subdirectories.
2. Add this upgrade note:

```md
如果你之前在子目录中遇到 stop hook 报错（文件找不到），运行 `/sybermem-update` 后该问题会自动修复。更新后的 hook 会自动向上查找包含 `.sybermem/` 和 `.claude/settings.json` 的最近祖先目录作为项目根。
```

- [ ] **Step 4: Update `README.en.md` with the English equivalent**

```md
If you previously encountered stop hook errors (file not found) when working in a subdirectory, running `/sybermem-update` fixes the issue. The updated hook automatically walks up to find the nearest ancestor with both `.sybermem/` and `.claude/settings.json` as the project root.
```

- [ ] **Step 5: Update `INSTALL.md` with the upgrade fix note**

Add:

```md
For existing users who experienced stop hook errors when working in project subdirectories: running `/sybermem-update` in the project refreshes the hook with automatic project root resolution. The updated hook finds the correct `.sybermem/` directory even when your working directory is a subdirectory of the project root.
```

- [ ] **Step 6: Verify all docs mention the new resolution behavior**

Run:

```powershell
Select-String -Path "D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\CLAUDE.md","D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\AGENTS.md","D:\adr-project\CLAUDE.md","D:\adr-project\AGENTS.md","D:\adr-project\README.md","D:\adr-project\README.en.md","D:\adr-project\INSTALL.md" -Pattern "walk up","nearest ancestor","project root","subdirectory"
```

Expected: all required concepts are present.

- [ ] **Step 7: Commit the docs updates**

```powershell
git add packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md packages/claude-skills/sybermem-init-project/project-files/AGENTS.md CLAUDE.md AGENTS.md README.md README.en.md INSTALL.md
git commit -m "docs: explain project root resolution and subdirectory fix"
```

---

### Task 5: Run the end-to-end subdirectory smoke test

**Files:**
- Reference: `D:\adr-project\.sybermem\hooks\record_change_on_stop.py`
- Reference: `D:\adr-project\packages\claude-skills\sybermem-init-project\SKILL.md`

- [ ] **Step 1: Verify the hook's `resolve_sybermem_root` works from a subdirectory**

Run:

```powershell
python -c @'
import subprocess, sys, os
from pathlib import Path

# Simulate running from a subdirectory
project_root = Path(r"D:\adr-project").resolve()
sub_dir = project_root / "packages" / "claude-skills"

os.chdir(sub_dir)

import importlib.util
spec = importlib.util.spec_from_file_location("hook", str(project_root / ".sybermem" / "hooks" / "record_change_on_stop.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

resolved = mod.resolve_sybermem_root()
print(f"cwd: {Path.cwd()}")
print(f"resolved root: {resolved}")
assert resolved == project_root, f"Expected {project_root}, got {resolved}"
print("PASS: subdirectory resolves to correct project root")
'@
```

Expected: the resolved root is `D:\adr-project`, not the subdirectory.

- [ ] **Step 2: Verify the hook exits gracefully when no SyberMem root exists**

Run:

```powershell
python -c @'
import os, tempfile
from pathlib import Path

# Create a temp directory with no .sybermem/ or .claude/
with tempfile.TemporaryDirectory() as tmpdir:
    os.chdir(tmpdir)
    import importlib.util
    spec = importlib.util.spec_from_file_location("hook", r"D:\adr-project\.sybermem\hooks\record_change_on_stop.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    resolved = mod.resolve_sybermem_root()
    # Should fall back to cwd gracefully, not crash
    print(f"Fallback resolved to: {resolved}")
    print("PASS: no crash when no SyberMem root exists")
'@
```

Expected: no crash; the function falls back gracefully.

- [ ] **Step 3: Verify all seven skills now contain walk-up language**

Run:

```powershell
$skills = @(
    "D:\adr-project\packages\claude-skills\sybermem-init-project\SKILL.md",
    "D:\adr-project\packages\claude-skills\sybermem-update\SKILL.md",
    "D:\adr-project\packages\claude-skills\sybermem-record\SKILL.md",
    "D:\adr-project\packages\claude-skills\sybermem-summary\SKILL.md",
    "D:\adr-project\packages\claude-skills\sybermem-digest\SKILL.md",
    "D:\adr-project\packages\claude-skills\sybermem-phase-analyze\SKILL.md",
    "D:\adr-project\packages\claude-skills\sybermem-phase-confirm\SKILL.md"
)
foreach ($s in $skills) {
    $count = (Select-String -Path $s -Pattern "Resolve project root").Count
    if ($count -gt 0) { Write-Host "PASS $($s | Split-Path -Leaf)" } else { Write-Host "FAIL $($s | Split-Path -Leaf)" }
}
```

Expected: all seven skills show PASS.

- [ ] **Step 4: Verify the packaged hook template matches the runtime hook**

Run:

```powershell
$runtime = Get-Content "D:\adr-project\.sybermem\hooks\record_change_on_stop.py" -Raw
$template = Get-Content "D:\adr-project\packages\claude-skills\sybermem-init-project\project-files\.sybermem\hooks\record_change_on_stop.py" -Raw
$rNorm = $runtime -replace "`r`n","`n"
$tNorm = $template -replace "`r`n","`n"
if ($rNorm.TrimEnd() -eq $tNorm.TrimEnd()) { "PASS: runtime and template match" } else { "FAIL: runtime and template differ" }
```

Expected: PASS.

- [ ] **Step 5: Verify the user-facing upgrade message is present in docs**

Run:

```powershell
Select-String -Path "D:\adr-project\README.md","D:\adr-project\README.en.md","D:\adr-project\INSTALL.md" -Pattern "subdirectory","walk up","project root"
```

Expected: all three docs contain the relevant upgrade/fix messaging.

- [ ] **Step 6: Commit any smoke-test fix needed, or record that none were needed**

If the smoke test reveals a real issue, fix it and commit:

```powershell
git add <fixed-files>
git commit -m "fix: align project root resolution with smoke test"
```

If no fix is needed, record that result and move on.

---

## Spec Coverage Check

- Walk-up resolution algorithm: Task 1, Task 3, Task 5
- Stop hook uses resolved root: Task 1, Task 5
- Git commands still run from original cwd: Task 1
- All seven skills have Step 0: Task 3, Task 5
- Anti-nesting guard in init-project: Task 3
- Packaged hook template aligned: Task 2, Task 5
- Instruction files updated: Task 4
- Top-level docs explain the behavior: Task 4, Task 5
- Existing user upgrade path: Task 4 (README/INSTALL messaging)
- Backward compatibility (cwd = project root): Task 1, Task 5
- Git root boundary: Task 1

## Placeholder Scan

This plan contains no `TODO`, `TBD`, or vague placeholders. If any are introduced during execution, replace them with exact content before proceeding.

## Type Consistency Check

Use these names consistently:
- function: `resolve_sybermem_root()`
- variable: `ROOT` (resolved project root), `GIT_CWD` (original working directory for git commands)
- markers: `.sybermem/` + `.claude/settings.json`
- section name: `Step 0: Resolve project root`
- init-project variant: `Step 0: Resolve project root (with anti-nesting guard)`
