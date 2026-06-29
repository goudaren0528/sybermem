# SyberMem Install/Update Script Skill List Catch-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure all 6 install/update scripts distribute the 3 newer SyberMem skills (`sybermem-search`, `sybermem-link`, `sybermem-theme-digest`) and advertise them in their help output.

**Architecture:** This is a minimal repair of 6 hardcoded skill lists. We append the 3 missing skills to each copy loop and add 3 corresponding lines to each script's "Available Skills" / "可用 Skills" output. No script structure changes, no refactoring, no dynamic discovery.

**Tech Stack:** Bash, PowerShell

---

### Task 1: Update the 6 script copy loops to install 11 skills

**Files:**
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`
- Modify: `scripts/install-remote.sh`
- Modify: `scripts/install-remote.ps1`
- Modify: `scripts/update.sh`
- Modify: `scripts/update.ps1`

- [ ] **Step 1: Update `scripts/install.sh`**

In `scripts/install.sh`, find:

```bash
for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update; do
```

Replace with:

```bash
for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update sybermem-search sybermem-link sybermem-theme-digest; do
```

- [ ] **Step 2: Update `scripts/install.ps1`**

In `scripts/install.ps1`, find:

```powershell
foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update")) {
```

Replace with:

```powershell
foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest")) {
```

- [ ] **Step 3: Update `scripts/install-remote.sh`**

In `scripts/install-remote.sh`, find:

```bash
for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update; do
```

Replace with:

```bash
for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update sybermem-search sybermem-link sybermem-theme-digest; do
```

- [ ] **Step 4: Update `scripts/install-remote.ps1`**

In `scripts/install-remote.ps1`, find:

```powershell
foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update")) {
```

Replace with:

```powershell
foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest")) {
```

- [ ] **Step 5: Update `scripts/update.sh`**

In `scripts/update.sh`, find:

```bash
for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update; do
```

Replace with:

```bash
for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update sybermem-search sybermem-link sybermem-theme-digest; do
```

- [ ] **Step 6: Update `scripts/update.ps1`**

In `scripts/update.ps1`, find:

```powershell
foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update")) {
```

Replace with:

```powershell
foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest")) {
```

- [ ] **Step 7: Verify all 6 loops**

Run: `python -c "
files = ['scripts/install.sh','scripts/install.ps1','scripts/install-remote.sh','scripts/install-remote.ps1','scripts/update.sh','scripts/update.ps1']
for f in files:
    t = open(f, encoding='utf-8').read()
    for skill in ['sybermem-search','sybermem-link','sybermem-theme-digest']:
        assert skill in t, f'{f} missing {skill}'
    print(f, 'OK')
"`
Expected: 6 lines ending with `OK`.

- [ ] **Step 8: Commit**

```bash
git add scripts/install.sh scripts/install.ps1 scripts/install-remote.sh scripts/install-remote.ps1 scripts/update.sh scripts/update.ps1
git commit -m "fix: distribute search, link, and theme-digest skills in install/update scripts"
```

---

### Task 2: Update script help/output text to list the 3 new skills

**Files:**
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`
- Modify: `scripts/install-remote.sh`
- Modify: `scripts/install-remote.ps1`
- Modify: `scripts/update.sh`
- Modify: `scripts/update.ps1`

- [ ] **Step 1: Update the Chinese help blocks (`install.sh`, `install.ps1`, `update.sh`, `update.ps1`)**

In each of these 4 files, find the block ending with:

```text
/sybermem-update        — 更新全局 Skills 并重新检查当前项目
```

Add immediately after it:

```text
/sybermem-search        — 按关键词、topic、phase 范围、日期范围或记录 ID 检索记录
/sybermem-link          — 在两条已有记录间建立正向关系（implements / fixes / related / superseded-by）
/sybermem-theme-digest  — 为单个 topic 创建跨多个 phase 的持久化高阶摘要
```

- [ ] **Step 2: Update the English help blocks (`install-remote.sh`, `install-remote.ps1`)**

In each of these 2 files, find the block ending with:

```text
/sybermem-update        — Refresh global skills, then re-check the current project
```

Add immediately after it:

```text
/sybermem-search        — Search/query records by keyword, topic, phase range, date range, or record ID
/sybermem-link          — Add a forward relation between two existing records (implements / fixes / related / superseded-by)
/sybermem-theme-digest  — Create a durable topic-level digest that compresses one theme across multiple related phases or records
```

- [ ] **Step 3: Verify all 6 help blocks**

Run: `python -c "
files = ['scripts/install.sh','scripts/install.ps1','scripts/install-remote.sh','scripts/install-remote.ps1','scripts/update.sh','scripts/update.ps1']
for f in files:
    t = open(f, encoding='utf-8').read()
    assert '/sybermem-search' in t, f'{f} missing search help'
    assert '/sybermem-link' in t, f'{f} missing link help'
    assert '/sybermem-theme-digest' in t, f'{f} missing theme-digest help'
    print(f, 'OK')
"`
Expected: 6 lines ending with `OK`.

- [ ] **Step 4: Commit**

```bash
git add scripts/install.sh scripts/install.ps1 scripts/install-remote.sh scripts/install-remote.ps1 scripts/update.sh scripts/update.ps1
git commit -m "docs: list search, link, and theme-digest in install/update help text"
```

---

### Task 3: Smoke test the local update/install path

This is the critical runtime verification for the catch-up.

**Files:**
- No code changes (verification only)

- [ ] **Step 1: Run the local update script**

Run: `powershell -ExecutionPolicy Bypass -File scripts/update.ps1`
Expected: output lines include all 11 skills, including:
- `/sybermem-search`
- `/sybermem-link`
- `/sybermem-theme-digest`

- [ ] **Step 2: Verify the 3 new skills exist in Claude Code user directory**

Run: `python -c "
from pathlib import Path
base = Path.home() / '.claude' / 'skills'
for skill in ['sybermem-search','sybermem-link','sybermem-theme-digest']:
    p = base / skill
    assert p.is_dir(), f'missing {p}'
    print(p, 'OK')
"`
Expected: 3 OK lines.

- [ ] **Step 3: Verify the 3 new skills exist in OpenCode user directory**

Run: `python -c "
from pathlib import Path
base = Path.home() / '.config' / 'opencode' / 'skills'
for skill in ['sybermem-search','sybermem-link','sybermem-theme-digest']:
    p = base / skill
    assert p.is_dir(), f'missing {p}'
    print(p, 'OK')
"`
Expected: 3 OK lines.

- [ ] **Step 4: No commit needed** (verification only)
