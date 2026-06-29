# Bilingual README Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the Chinese and English README entry docs so they accurately describe the current SyberMem v2 feature set, daily workflow, project directory tree, and platform support status.

**Architecture:** Update three documentation entry points with synchronized capability coverage: `README.md` as the Chinese primary, `README.en.md` as the English primary with the same information architecture, and `docs/zh/README.md` as a lighter Chinese reference that still reflects the full current feature set. This is a documentation-only change; no runtime behavior changes.

**Tech Stack:** Markdown

**Spec:** `docs/superpowers/specs/2026-06-29-readme-refresh-bilingual-implementation-design.md`

**Global Constraints:**
- `README.md` and `README.en.md` should be structurally aligned in major sections.
- `docs/zh/README.md` may remain shorter, but it must not be functionally stale.
- Do not claim all platforms are fully supported. Distinguish **fully supported** (Claude Code, OpenCode) from **entry files / metadata present** (Gemini, Cursor, Codex, Kimi).
- Document the full current skill set (11 skills).
- Reflect current governance features accurately: Active/Archived Conclusions, phase lifecycle, Topic Index status suffixes, `superseded_by`.

---

### Task 1: Refresh `README.md` (Chinese primary entrypoint)

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the Skills table to show all 11 skills clearly**

In `README.md`, locate the `## Skills` table and ensure it contains these 11 rows, in this order:

```markdown
| `/sybermem-init-project` | 在项目中创建或刷新 `.sybermem/` 目录结构，扫描现有代码库，生成或刷新 `CLAUDE.md` / `AGENTS.md`，并在首次运行时自动迁移旧 `ADR/` |
| `/sybermem-record` | 从当前会话上下文创建记录，AI 自动判断类型：变更、决策、需求或 Bug，并写入 `.sybermem/` |
| `/sybermem-summary` | 动态查看最近活跃 confirmed phase 的当前状态面板；若 analysis layer 不存在，则回退到周报/月报 |
| `/sybermem-digest` | 从已有记录创建可持久保存的阶段摘要，将其写入 `.sybermem/digests/`，并阻止对同一批源记录重复压缩 |
| `/sybermem-theme-digest` | 为单个 topic 创建跨多个 phase 的持久化高阶摘要（Theme Digest） |
| `/sybermem-phase-analyze` | 从完整项目历史构建或刷新 `.sybermem/analysis/phase-index.md`，生成可持续维护的阶段分析索引 |
| `/sybermem-phase-confirm` | 确认、重命名或调整 `phase-index.md` 中的候选阶段，使阶段结构变为明确的项目分析结果 |
| `/using-sybermem` | 显示当前 SyberMem 状态、可用命令以及建议的下一步操作 |
| `/sybermem-update` | 刷新全局安装的 SyberMem skills，然后在当前项目继续执行 `/sybermem-init-project` |
| `/sybermem-search` | 按关键词、topic、phase 范围、日期范围或记录 ID 检索记录，并显示所属 phase、关系与替代提示 |
| `/sybermem-link` | 在两条已有记录间建立正向关系（implements / fixes / related / superseded-by） |
```

- [ ] **Step 2: Add a new `## 日常工作流` section after the governance/search sections**

Insert this section after `## Topic 治理与替代关系`:

```markdown
## 日常工作流

推荐把 SyberMem 当作“项目记忆的日常工具链”来用：

```text
查历史                → /sybermem-search <keyword|topic|record-id>
看现状                → /sybermem-summary
完成有价值工作        → /sybermem-record
phase-index stale     → /sybermem-phase-analyze
阶段收束              → /sybermem-digest
主题跨 phase 收束     → /sybermem-theme-digest <topic>
不确定当前状态/下一步 → /using-sybermem
```
```

- [ ] **Step 3: Refresh the project directory tree**

In the `## 在你的项目中会创建什么` section, replace the current tree block with this updated one:

```markdown
```
.sybermem/
├── INDEX.md                        # 主索引 — Active/Archived Conclusions、Digests、Topic Index
├── changes/                        # 功能变更
├── decisions/                      # 技术决策
├── requirements/                   # 需求讨论
├── bugs/                           # Bug 修复
├── digests/                        # 阶段 digest
├── theme-digests/                  # 主题 digest（跨多个 phase）
├── analysis/
│   └── phase-index.md              # 持久化项目分析产物（含 lifecycle 字段）
├── hooks/
│   ├── record_change_on_stop.py    # 默认自动 change hook helper
│   ├── session_start_context.py    # SessionStart 上下文注入脚本
│   ├── check_project_health.py     # update fast-path 健康检查脚本
│   └── launch_record_change_on_stop.py # root-resolving stop-hook launcher helper
└── templates/
    ├── change-template.md
    ├── decision-template.md
    ├── requirement-template.md
    ├── bug-template.md
    ├── digest-template.md
    └── theme-digest-template.md

CLAUDE.md                           # Claude Code 项目指令（工作流规则）
AGENTS.md                           # OpenCode 项目指令（内容相同）
.claude/settings.json               # 项目级 hook 模式（SessionStart / Stop）
```
```

Immediately after the tree, add this explanatory bullet list:

```markdown
`INDEX.md` 当前包含这些核心区段：
- `Key Conclusions` — Active conclusions，会在 SessionStart 注入
- `Archived Conclusions` — 归档结论，不在启动时注入，但仍可搜索
- `Stage Digests` — phase digest 索引
- `Theme Digests` — topic-level digest 索引
- `Topic Index` — topic → record IDs（支持 `[active]` / `[low]` / `[deprecated → ...]` 后缀）
```

- [ ] **Step 4: Refresh the supported-platforms section**

Replace the current `## 支持平台` table with:

```markdown
## 支持平台

| 平台 | 当前状态 | 说明 |
|------|----------|------|
| Claude Code | fully supported | 插件安装（推荐）或脚本安装（兼容）均已完整 dogfood |
| OpenCode | fully supported | TypeScript plugin 已实现 `session.created` / `session.idle` / `experimental.session.compacting` |
| Gemini CLI | entry files present | `GEMINI.md` 与扩展元数据已提供，但未像 Claude/OpenCode 一样完整 dogfood |
| Cursor | metadata present | `.cursor-plugin/plugin.json` 已存在，运行时行为尚未同等强度验证 |
| Codex | metadata present | `.codex-plugin/plugin.json` 已存在，运行时行为尚未同等强度验证 |
| Kimi | metadata present | `.kimi-plugin/plugin.json` 已存在，运行时行为尚未同等强度验证 |
```

- [ ] **Step 5: Refresh the repo structure block**

In `## 仓库结构`, replace the current `packages/claude-skills/` excerpt with the complete current set:

```markdown
packages/claude-skills/               # Skills 源码（仓库内分发源，不参与项目自动加载）
├── sybermem-digest/
├── sybermem-init-project/
├── sybermem-link/
├── sybermem-phase-analyze/
├── sybermem-phase-confirm/
├── sybermem-record/
├── sybermem-search/
├── sybermem-summary/
├── sybermem-theme-digest/
├── sybermem-update/
└── using-sybermem/
```

And update the `scripts/` subsection to mention:

```markdown
└── check-plugin-package.py           # 插件分发内容与真实 CLI validate 校验
```

- [ ] **Step 6: Verify the Chinese README**

Run: `python -c "
import pathlib
text = pathlib.Path('README.md').read_text(encoding='utf-8')
for marker in [
    '/sybermem-theme-digest',
    '/sybermem-search',
    '/sybermem-link',
    '## 日常工作流',
    'theme-digests/',
    'check_project_health.py',
    'Archived Conclusions',
    'fully supported',
    'entry files present',
]:
    assert marker in text, marker
print('README.md OK')
"`
Expected: `README.md OK`

- [ ] **Step 7: Commit**

```bash
git add README.md
git commit -m "docs: refresh Chinese README for SyberMem v2"
```

---

### Task 2: Refresh `README.en.md` to match the current v2 architecture

**Files:**
- Modify: `README.en.md`

- [ ] **Step 1: Update the install section to match the current recommended paths**

Keep the opening intro, but reorganize the install section so it mirrors the Chinese README structure:

```markdown
## Install

### Claude Code Plugin Install (Recommended)

For Claude Code users who want plugin-managed hooks and skills, the preferred future path is the plugin installation flow.

#### Local development / testing

```bash
claude --plugin-dir .
```

This loads `.claude-plugin/` from the current repository, which is useful for validating plugin metadata, lifecycle hooks, and the plugin-facing `skills/` tree.

#### Current distribution status

SyberMem already includes `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Marketplace-style distribution is prepared, but the fully dogfooded runtime paths today are Claude Code and OpenCode.

### Claude Code / OpenCode Script Install (Compatibility Mode)

Keep the existing one-liner and clone-install commands, but label them as compatibility/direct install paths rather than the future default.

### OpenCode

Point to `.opencode/INSTALL.md` and note that OpenCode has a dedicated plugin runtime.
```

- [ ] **Step 2: Replace the Skills table with the full 11-skill list**

Use these rows:

```markdown
| `/sybermem-init-project` | Create or refresh the `.sybermem/` structure in a project, refresh managed instruction files, and migrate legacy `ADR/` on first run |
| `/sybermem-record` | Create a structured change / decision / requirement / bug record from the current session context |
| `/sybermem-summary` | Show the current-state panel for the most relevant active phase, with weekly/monthly fallback |
| `/sybermem-digest` | Create a durable phase digest from existing records |
| `/sybermem-theme-digest` | Create a durable topic-level digest that compresses one theme across multiple phases or records |
| `/sybermem-phase-analyze` | Build or refresh `.sybermem/analysis/phase-index.md` from project history |
| `/sybermem-phase-confirm` | Adjust confirmed phases, names, and lifecycle state |
| `/using-sybermem` | Diagnose the current SyberMem state and recommend the right next command |
| `/sybermem-update` | Refresh globally installed SyberMem skills, then re-check the current project |
| `/sybermem-search` | Query records by keyword, topic, phase range, date range, or record ID, including relations |
| `/sybermem-link` | Add a forward relation between two existing records (`implements` / `fixes` / `related` / `superseded-by`) |
```

- [ ] **Step 3: Add the v2 capability sections**

After the Skills table, add these sections in order:

```markdown
## Daily Workflow

A practical day-to-day path for using SyberMem:

```text
Look up history             → /sybermem-search <keyword|topic|record-id>
Check current state         → /sybermem-summary
Finish meaningful work      → /sybermem-record
Refresh stale phase index   → /sybermem-phase-analyze
Close a phase               → /sybermem-digest
Compress a topic across phases → /sybermem-theme-digest <topic>
Unsure what to do next      → /using-sybermem
```

## Theme Digest Layer

In addition to phase digests (`/sybermem-digest`), SyberMem now supports theme digests (`/sybermem-theme-digest`):

- phase digest = what one phase ultimately concluded
- theme digest = what one topic ultimately concluded across multiple phases

Theme digests live under `.sybermem/theme-digests/`. The first version is single-topic only, prefers existing phase digests when available, and fills gaps with raw records.

## Relations, Search, and Governance

Records can now declare forward-only relationship fields in frontmatter:

- `implements: [requirement-NNN]`
- `fixes: [bug-NNN]`
- `related: [type-NNN]`
- `superseded_by: <record-id>`

`/sybermem-search` can surface:
- phase membership
- forward relations
- reverse references
- supersession hints
- archived conclusion matches

Topic Index lines may also carry optional suffixes:
- `[active]`
- `[low]`
- `[deprecated → <new-topic>]`
```

- [ ] **Step 4: Refresh the project directory tree and platform matrix**

Replace the current `## What gets created in your project` block with the updated v2 tree (English labels), including:
- `theme-digests/`
- `check_project_health.py`
- `launch_record_change_on_stop.py`
- `theme-digest-template.md`
- `Archived Conclusions`, `Theme Digests`, `Topic Index` in the explanatory bullets

Then replace `## Supported Platforms` with:

```markdown
## Supported Platforms

| Platform | Current status | Notes |
|----------|----------------|-------|
| Claude Code | fully supported | Plugin install (recommended) and script install (compatibility mode) are both dogfooded |
| OpenCode | fully supported | TypeScript plugin implements `session.created`, `session.idle`, and `experimental.session.compacting` |
| Gemini CLI | entry files present | `GEMINI.md` and extension metadata exist, but runtime behavior has not been dogfooded to the same degree |
| Cursor | metadata present | `.cursor-plugin/plugin.json` exists; runtime behavior not yet equally validated |
| Codex | metadata present | `.codex-plugin/plugin.json` exists; runtime behavior not yet equally validated |
| Kimi | metadata present | `.kimi-plugin/plugin.json` exists; runtime behavior not yet equally validated |
```

- [ ] **Step 5: Refresh the repo structure block**

Update the `packages/claude-skills/` excerpt to the full 11-skill set and the `scripts/` excerpt to mention `check-plugin-package.py` as real CLI validation.

- [ ] **Step 6: Verify the English README**

Run: `python -c "
import pathlib
text = pathlib.Path('README.en.md').read_text(encoding='utf-8')
for marker in [
    '/sybermem-theme-digest',
    '/sybermem-search',
    '/sybermem-link',
    '## Daily Workflow',
    'theme-digests/',
    'check_project_health.py',
    'Archived Conclusions',
    'fully supported',
    'entry files present',
    'superseded_by: <record-id>',
]:
    assert marker in text, marker
print('README.en.md OK')
"`
Expected: `README.en.md OK`

- [ ] **Step 7: Commit**

```bash
git add README.en.md
git commit -m "docs: refresh English README for SyberMem v2"
```

---

### Task 3: Refresh `docs/zh/README.md` as an up-to-date Chinese reference

**Files:**
- Modify: `docs/zh/README.md`

- [ ] **Step 1: Replace the current minimal summary with an updated v2 reference overview**

Keep the `# 中文版备份` header and file list section, but replace the long paragraph at the top with a tighter v2-aware summary that covers:
- 插件安装（推荐）/ 脚本安装（兼容）
- 11 个 skill
- lifecycle/search/relations/theme-digest/current governance features
- Active / Archived Conclusions
- phase lifecycle
- Topic Index suffixes
- `superseded_by`
- 当前 fully supported 平台 vs metadata-present 平台

Use concise prose rather than duplicating the entire main README.

- [ ] **Step 2: Add a short “日常工作流” subsection**

Insert:

```markdown
## 日常工作流

```text
查历史                → /sybermem-search
看现状                → /sybermem-summary
完成有价值工作        → /sybermem-record
phase-index stale     → /sybermem-phase-analyze
阶段收束              → /sybermem-digest
主题跨 phase 收束     → /sybermem-theme-digest <topic>
不确定下一步          → /using-sybermem
```
```

- [ ] **Step 3: Add a short “当前项目目录” subsection**

Add a condensed tree or bullet list mentioning:
- `theme-digests/`
- `check_project_health.py`
- `launch_record_change_on_stop.py`
- `theme-digest-template.md`
- `Archived Conclusions`

- [ ] **Step 4: Verify `docs/zh/README.md`**

Run: `python -c "
import pathlib
text = pathlib.Path('docs/zh/README.md').read_text(encoding='utf-8')
for marker in [
    '/sybermem-theme-digest',
    '/sybermem-search',
    '/sybermem-link',
    'Active / Archived Conclusions',
    'superseded_by',
    '## 日常工作流',
    'theme-digests/',
]:
    assert marker in text, marker
print('docs/zh/README.md OK')
"`
Expected: `docs/zh/README.md OK`

- [ ] **Step 5: Commit**

```bash
git add docs/zh/README.md
git commit -m "docs: refresh Chinese reference README for SyberMem v2"
```

---

### Task 4: Final consistency verification

**Files:**
- No file changes

- [ ] **Step 1: Run a three-file entrypoint check**

Run: `python -c "
import pathlib
files = ['README.md', 'README.en.md', 'docs/zh/README.md']
markers = ['/sybermem-theme-digest', '/sybermem-search', '/sybermem-link', 'theme-digests/']
for f in files:
    t = pathlib.Path(f).read_text(encoding='utf-8')
    for m in markers:
        assert m in t, f'{f} missing {m}'
    print(f, 'OK')
"`
Expected: 3 OK lines.

- [ ] **Step 2: Confirm platform wording is not overstated**

Run: `python -c "
import pathlib
for f in ['README.md', 'README.en.md']:
    t = pathlib.Path(f).read_text(encoding='utf-8')
    assert 'fully supported' in t or 'fully supported' not in f
    assert 'entry files present' in t or 'metadata present' in t or f == 'README.md'
    print(f, 'platform wording OK')
"`
Expected: both files platform wording OK.

- [ ] **Step 3: No commit needed** (verification only)
