# SyberMem CLI Installability / UX Phase 1.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the SyberMem CLI usable as a normal `sybermem ...` command by installing it into `~/.claude/sybermem/cli/`, while keeping the current launcher-based hook runtime unchanged.

**Architecture:** Extend the 6 install/update scripts so they create a dedicated CLI runtime under `~/.claude/sybermem/cli/`, install the Phase 1 `packages/core` and `packages/cli` packages there, and generate `sybermem` / `sybermem.cmd` wrappers. Then update docs and the workspace-search skill so user-facing invocations switch from `PYTHONPATH=... python -m ...` to `sybermem ...`.

**Tech Stack:** Python 3.10+, venv, Bash, PowerShell, Markdown

---

### Task 1: Create CLI runtime wrappers and install steps in the 6 install/update scripts

**Files:**
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`
- Modify: `scripts/install-remote.sh`
- Modify: `scripts/install-remote.ps1`
- Modify: `scripts/update.sh`
- Modify: `scripts/update.ps1`

- [ ] **Step 1: Add CLI path variables to each script**

Add these variables near the existing `LauncherDir` / `LAUNCHER_DIR` definitions:

**Bash scripts (`install.sh`, `install-remote.sh`, `update.sh`):**
```bash
CLI_DIR="$HOME/.claude/sybermem/cli"
CLI_VENV="$CLI_DIR/venv"
CLI_WRAPPER="$CLI_DIR/sybermem"
```

**PowerShell scripts (`install.ps1`, `install-remote.ps1`, `update.ps1`):**
```powershell
$CliDir = Join-Path $env:USERPROFILE ".claude\sybermem\cli"
$CliVenv = Join-Path $CliDir "venv"
$CliWrapper = Join-Path $CliDir "sybermem.cmd"
```

- [ ] **Step 2: Add CLI installation steps to local scripts (`install.sh`, `install.ps1`, `update.sh`, `update.ps1`)**

After the launcher copy block, add:

**Bash:**
```bash
mkdir -p "$CLI_DIR"
python -m venv "$CLI_VENV"
"$CLI_VENV/bin/python" -m pip install --upgrade pip
"$CLI_VENV/bin/pip" install "$ADR_PATH/packages/core" "$ADR_PATH/packages/cli"
cat > "$CLI_WRAPPER" <<'EOF'
#!/bin/bash
SYBERMEM_HOME="$HOME/.claude/sybermem/cli"
exec "$SYBERMEM_HOME/venv/bin/sybermem" "$@"
EOF
chmod +x "$CLI_WRAPPER"
echo "  [Claude Code] 已安装 sybermem CLI: $CLI_WRAPPER"
```

**PowerShell:**
```powershell
if (-not (Test-Path $CliDir)) { New-Item -ItemType Directory -Path $CliDir -Force | Out-Null }
python -m venv $CliVenv
& (Join-Path $CliVenv "Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $CliVenv "Scripts\pip.exe") install (Join-Path $AdrPath "packages\core") (Join-Path $AdrPath "packages\cli")
@'
@echo off
set "SYBERMEM_HOME=%USERPROFILE%\.claude\sybermem\cli"
"%SYBERMEM_HOME%\venv\Scripts\sybermem.exe" %*
'@ | Set-Content -Path $CliWrapper -Encoding ASCII
Write-Host "  [Claude Code] 已安装 sybermem CLI: $CliWrapper"
```

- [ ] **Step 3: Add CLI installation steps to remote scripts (`install-remote.sh`, `install-remote.ps1`)**

Use the extracted temp directory paths instead of `ADR_PATH`:

**install-remote.sh:**
- packages source: `"$TMPDIR/$ARCHIVE_PREFIX/packages/core"` and `.../packages/cli`

**install-remote.ps1:**
- packages source: `Join-Path $TmpDir "$ArchivePrefix\packages\core"` and `...\cli`

Then use the same venv + pip + wrapper pattern as Step 2.

- [ ] **Step 4: Add CLI install/update messages to script output**

In all 6 scripts, after the skills list and/or install summary, add one line:

**Chinese scripts:**
```text
sybermem CLI 已安装，可直接运行：sybermem project init --register
```

**English scripts:**
```text
sybermem CLI is installed. You can now run: sybermem project init --register
```

- [ ] **Step 5: Verify wrapper generation on this machine**

Run:
```powershell
& .\scripts\update.ps1
Test-Path "$env:USERPROFILE\.claude\sybermem\cli\venv"
Test-Path "$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd"
```

Expected:
- update script completes successfully
- both `Test-Path` calls return `True`

- [ ] **Step 6: Commit**

```bash
git add scripts/install.sh scripts/install.ps1 scripts/install-remote.sh scripts/install-remote.ps1 scripts/update.sh scripts/update.ps1
git commit -m "feat: install sybermem CLI runtime and wrappers in install/update scripts"
```

---

### Task 2: Verify the installed CLI actually runs the Phase 1 commands

**Files:**
- No code changes (verification only)

- [ ] **Step 1: Run `sybermem project init --register` via the installed wrapper**

Run:
```powershell
& "$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd" project init --register --format json
```

Expected: valid JSON containing `status`, `project_id`, `slug`, `path`, `remote`.

- [ ] **Step 2: Run `sybermem index build` via the installed wrapper**

Run:
```powershell
& "$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd" index build --format json
```

Expected: JSON with `projects` and `records`, and `~/.sybermem/index/sybermem.db` exists.

- [ ] **Step 3: Run `sybermem search` via the installed wrapper**

Run:
```powershell
& "$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd" search hooks --scope workspace --format json
```

Expected: JSON result set containing the `sybermem` project and matching records.

- [ ] **Step 4: No commit needed** (verification only)

---

### Task 3: Update user-facing docs and the search skill to use `sybermem ...`

**Files:**
- Modify: `packages/claude-skills/sybermem-search/SKILL.md`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/zh/README.md`
- Modify: `docs/superpowers/specs/2026-06-30-sybermem-core-phase1-design.md`
- Modify: `docs/superpowers/plans/2026-06-30-sybermem-core-phase1.md`

- [ ] **Step 1: Update `sybermem-search` workspace-scope invocation text**

In `packages/claude-skills/sybermem-search/SKILL.md`, ensure the workspace-scope guidance says:

```text
sybermem search <query> --scope workspace --format json
```

and does **not** mention `PYTHONPATH=... python -m ...`.

- [ ] **Step 2: Update README examples**

In all three README files, replace any Phase 1 CLI example of the form:

```text
PYTHONPATH=packages/core;packages/cli python -m sybermem_cli.main ...
```

with:

```text
sybermem ...
```

If the README currently has no Phase 1 CLI examples, add a short note in the install/CLI section:

**Chinese:**
```markdown
安装或更新后，可直接运行：

```bash
sybermem project init --register
sybermem index build
sybermem search hooks --scope workspace
```
```

**English:**
```markdown
After install or update, you can run:

```bash
sybermem project init --register
sybermem index build
sybermem search hooks --scope workspace
```
```

- [ ] **Step 3: Update the Core Phase 1 spec + plan examples**

In these two docs:
- `docs/superpowers/specs/2026-06-30-sybermem-core-phase1-design.md`
- `docs/superpowers/plans/2026-06-30-sybermem-core-phase1.md`

replace user-facing command examples from the explicit `PYTHONPATH=... python -m sybermem_cli.main ...` form to the installed `sybermem ...` form.

Do **not** rewrite the architecture sections — only update the invocation examples and verification commands where they are meant for users/operators.

- [ ] **Step 4: Verify no user-facing `PYTHONPATH=` examples remain in these files**

Run:
```powershell
git grep -n "PYTHONPATH=packages/core;packages/cli" -- packages/claude-skills/sybermem-search/SKILL.md README.md README.en.md docs/zh/README.md docs/superpowers/specs/2026-06-30-sybermem-core-phase1-design.md docs/superpowers/plans/2026-06-30-sybermem-core-phase1.md
```

Expected: no matches.

- [ ] **Step 5: Commit**

```bash
git add packages/claude-skills/sybermem-search/SKILL.md README.md README.en.md docs/zh/README.md docs/superpowers/specs/2026-06-30-sybermem-core-phase1-design.md docs/superpowers/plans/2026-06-30-sybermem-core-phase1.md
git commit -m "docs: switch Phase 1 CLI examples to installed sybermem command"
```

---

### Task 4: Confirm hooks still work unchanged after CLI installability changes

**Files:**
- No code changes (verification only)

- [ ] **Step 1: Verify SessionStart launcher still works**

Run:
```powershell
python "$env:USERPROFILE\.claude\sybermem\launch_session_start_context.py"
```

Expected: valid JSON `hookSpecificOutput.additionalContext` output.

- [ ] **Step 2: Verify Stop launcher still works**

Run:
```powershell
python "$env:USERPROFILE\.claude\sybermem\launch_record_change_on_stop.py"
```

Expected: exit 0; may emit a non-blocking SyberMem note depending on workspace state.

- [ ] **Step 3: No commit needed** (verification only)
