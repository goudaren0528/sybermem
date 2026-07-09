# SyberMem README Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `README.md` and `README.en.md` so they explain the current SyberMem product clearly — what it is, what it can do now, and how to use it today — without overemphasizing ADR history or implementation milestones.

**Architecture:** This is a docs-only restructuring pass. Keep both READMEs aligned around the same information architecture: current capabilities, install paths, daily workflow, Team workflow, reminder modes, repo structure, and links to deeper docs. Historical migration and phase-by-phase implementation detail should be reduced or moved out of the main narrative.

**Tech Stack:** Markdown, bilingual documentation

---

### Task 1: Rewrite the Chinese README around current capabilities and usage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the current opening sections with a concise product framing**

Rewrite the top of `README.md` so the first sections become:

```markdown
**中文** | [English](README.en.md)

# SyberMem

SyberMem 是一个面向 AI 工作流的项目 / 团队工程记忆系统。

它帮助你把：
- 项目进展
- 技术决策
- 阶段性沉淀
- 团队摘要

保存成结构化记忆，让项目 owner、管理者与管理 agent 可以在不同会话中持续消费这些内容。

## 当前能力

### Project
- 结构化 records（change / decision / requirement / bug）
- phase index
- phase digest / theme digest
- relations / superseded / archived conclusions
- search / link / summary

### Hub
- project registry
- workspace search
- portfolio / project status

### Team
- team init
- team publish
- team overview
- team summary
- digest history layer
```

- [ ] **Step 2: Rewrite the workflow section around real usage roles**

Replace the current long “工作流程 / 老用户升级说明 / 迁移说明” emphasis with a role-based flow:

```markdown
## 日常使用

### 项目 owner
- `/sybermem-record` — 完成一轮有价值工作后记录
- `/sybermem-summary` — 看当前状态
- `/sybermem-digest` — 阶段稳定后沉淀摘要
- `/sybermem-team-publish` — 将项目摘要同步到 Team memory

### 管理者 / 管理 agent
- `/sybermem-team-summary` — 生成团队管理摘要

### 不确定下一步时
- `/using-sybermem` — 查看当前状态与推荐命令
```

- [ ] **Step 3: Keep migration notes, but shrink them**

Retain ADR migration only as a short compatibility note rather than a large section. For example:

```markdown
## 兼容说明

- `.sybermem/` 是规范目录
- 如果项目里仍是旧的 `ADR/`，首次运行 `/sybermem-init-project` / `/sybermem-record` 等命令时会自动迁移
- 更多升级与兼容细节见 `INSTALL.md`
```

- [ ] **Step 4: Preserve install instructions, but simplify the narration**

Keep the actual install commands, but reduce historical explanations like “未来正式安装路径” and phase-progress tone. Focus on:
- plugin install (recommended)
- script install (compatibility)
- OpenCode install

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: refocus Chinese README on current SyberMem usage"
```

---

### Task 2: Rewrite the English README to match the new Chinese structure

**Files:**
- Modify: `README.en.md`

- [ ] **Step 1: Align the opening structure**

Make the English README open with the same information architecture as the Chinese README:

```markdown
[中文](README.md) | **English**

# SyberMem

SyberMem is an AI-oriented project and team engineering-memory system.

It helps you store:
- project progress
- technical decisions
- phase-level conclusions
- team-facing summaries

as structured memory that project owners, managers, and management agents can keep consuming across sessions.

## Current Capabilities

### Project
...

### Hub
...

### Team
...
```

- [ ] **Step 2: Align the role-based usage section**

Add:

```markdown
## Daily Usage

### Project owner
- `/sybermem-record` — record meaningful work
- `/sybermem-summary` — inspect current status
- `/sybermem-digest` — capture a stable phase conclusion
- `/sybermem-team-publish` — publish the project summary into Team memory

### Manager / management agent
- `/sybermem-team-summary` — generate the Team management summary

### If you're unsure what to do next
- `/using-sybermem` — inspect the current state and get the recommended next command
```

- [ ] **Step 3: Shrink migration/history-heavy sections**

Keep ADR compatibility and upgrade notes, but reduce their prominence and remove repeated historical explanation. Point deeper details to `INSTALL.md`.

- [ ] **Step 4: Keep the Team section, but reframe it as “current workflow” not milestone history**

Instead of emphasizing Team phases as progress reporting, frame them as current Team workflow stages already available today.

- [ ] **Step 5: Commit**

```bash
git add README.en.md
git commit -m "docs: refocus English README on current SyberMem usage"
```

---

### Task 3: Final verification and alignment pass

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Verify both READMEs still cover the key entrypoints**

Check that both versions clearly mention:
- `/sybermem-init-project`
- `/sybermem-record`
- `/sybermem-summary`
- `/sybermem-digest`
- `/sybermem-team-publish`
- `/sybermem-team-summary`
- `/using-sybermem`

- [ ] **Step 2: Verify both READMEs de-emphasize history**

Check that:
- ADR migration is short and clearly secondary
- phase-by-phase implementation history is not the main narrative
- the README reads like a product/usage guide, not a project diary

- [ ] **Step 3: Verify both READMEs point to deeper docs rather than duplicating them**

Check that deep details now live behind pointers to:
- `INSTALL.md`
- `docs/superpowers/specs/`
- `docs/zh/`

- [ ] **Step 4: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: align bilingual README structure around current SyberMem capabilities"
```
