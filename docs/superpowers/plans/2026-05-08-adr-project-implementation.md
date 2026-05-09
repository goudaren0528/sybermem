# ADR 项目规范系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一套完整的 ADR（Architecture Decision Records）项目规范系统，包括目录结构、模板文件、CLAUDE.md 规范和 record-adr skill。

**Architecture:** 采用文件系统为基础的记录方案，通过模板标准化记录格式，通过 CLAUDE.md 定义 Claude Code 行为规范，通过自定义 skill 提供便捷的记录工具。

**Tech Stack:** Markdown 文件、YAML frontmatter、Claude Code skills

---

## 文件结构概览

```
D:/adr-project/
├── ADR/
│   ├── INDEX.md
│   ├── changes/
│   ├── decisions/
│   ├── requirements/
│   ├── bugs/
│   └── templates/
│       ├── change-template.md
│       ├── decision-template.md
│       ├── requirement-template.md
│       └── bug-template.md
├── CLAUDE.md
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-08-adr-project-spec-design.md (已存在)
│       └── plans/
│           └── 2026-05-08-adr-project-implementation.md (本文件)
└── .claude/
│   └── skills/
│       └── record-adr/
│           ├── SKILL.md
│           └── templates/
│               ├── change.md
│               ├── decision.md
│               ├── requirement.md
│               └── bug.md
```

---

### Task 1: 创建 ADR 基础目录结构

**Files:**
- Create: `ADR/` (目录)
- Create: `ADR/changes/` (目录)
- Create: `ADR/decisions/` (目录)
- Create: `ADR/requirements/` (目录)
- Create: `ADR/bugs/` (目录)
- Create: `ADR/templates/` (目录)

- [ ] **Step 1: 创建 ADR 主目录和子目录**

```bash
mkdir -p "D:/adr-project/ADR/changes" "D:/adr-project/ADR/decisions" "D:/adr-project/ADR/requirements" "D:/adr-project/ADR/bugs" "D:/adr-project/ADR/templates"
```

- [ ] **Step 2: 验证目录结构**

```bash
ls -la "D:/adr-project/ADR/"
```
Expected: 看到 changes, decisions, requirements, bugs, templates 五个目录

---

### Task 2: 创建 INDEX.md 索引文件

**Files:**
- Create: `ADR/INDEX.md`

- [ ] **Step 1: 写入 INDEX.md 内容**

```markdown
# ADR 索引

本文件汇总所有项目变更、决策、需求和Bug记录。

---

## 功能性变更

| 编号 | 日期 | 标题 | 状态 | 文件链接 |
|------|------|------|------|----------|
<!-- 新记录在此添加 -->

---

## 技术决策

| 编号 | 日期 | 标题 | 状态 | 文件链接 |
|------|------|------|------|----------|
<!-- 新记录在此添加 -->

---

## 讨论/需求记录

| 编号 | 日期 | 标题 | 来源 | 优先级 | 文件链接 |
|------|------|------|------|--------|----------|
<!-- 新记录在此添加 -->

---

## Bug修复记录

| 编号 | 日期 | 标题 | 严重程度 | 文件链接 |
|------|------|------|----------|----------|
<!-- 新记录在此添加 -->

---

## 使用说明

- **changes/**: 记录所有功能性变更
- **decisions/**: 记录重要技术决策及其原因
- **requirements/**: 记录讨论过程、需求来源、设计理念
- **bugs/**: 记录Bug问题分析和修复方案

新增记录时，请同步更新本索引文件。
```

写入文件 `D:/adr-project/ADR/INDEX.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/ADR/INDEX.md"
```
Expected: 显示 INDEX.md 完整内容

---

### Task 3: 创建功能性变更模板

**Files:**
- Create: `ADR/templates/change-template.md`

- [ ] **Step 1: 写入 change-template.md**

```markdown
---
type: change
date: YYYY-MM-DD
number: XXX
title: 变更标题
status: implemented | planned | reverted
author: 作者名
related_files: [关联文件路径列表]
---

## 变更内容
简要描述做了什么变更。

## 变更原因
为什么需要这个变更？（用户需求、业务目标等）

## 影响范围
- 影响的模块/功能
- 影响的用户群体

## 实现方案
简要说明实现思路（如有讨论过程，链接到 requirements 或 decisions）。

## 测试验证
如何验证变更正确性。

## 备注
其他需要记录的信息。
```

写入文件 `D:/adr-project/ADR/templates/change-template.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/ADR/templates/change-template.md"
```

---

### Task 4: 创建技术决策模板

**Files:**
- Create: `ADR/templates/decision-template.md`

- [ ] **Step 1: 写入 decision-template.md**

```markdown
---
type: decision
date: YYYY-MM-DD
number: XXX
title: 决策标题
status: accepted | deprecated | superseded
supersedes: [被取代的决策编号，如有]
---

## 背景
描述决策的背景和问题。

## 考虑的方案
列出考虑过的方案及其优缺点。

## 最终决策
选择哪个方案，理由是什么。

## 影响与后果
决策带来的影响（正面、负面、风险）。

## 相关变更
链接到相关的 change 记录。

## 备注
其他信息（如参考资料、讨论参与者等）。
```

写入文件 `D:/adr-project/ADR/templates/decision-template.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/ADR/templates/decision-template.md"
```

---

### Task 5: 创建讨论/需求记录模板

**Files:**
- Create: `ADR/templates/requirement-template.md`

- [ ] **Step 1: 写入 requirement-template.md**

```markdown
---
type: requirement
date: YYYY-MM-DD
number: XXX
title: 需求/讨论标题
source: 用户/客户/内部讨论
priority: high | medium | low
---

## 需求来源
谁提出的需求，什么场景。

## 需求内容
具体需求描述。

## 讨论过程
记录讨论中的关键观点、疑问、限制条件。

## 最终结论
讨论结果和确定的方案。

## 设计理念/限制
重要的设计原则、约束条件、特殊要求。

## 相关决策/变更
链接到相关的 decision 或 change 记录。
```

写入文件 `D:/adr-project/ADR/templates/requirement-template.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/ADR/templates/requirement-template.md"
```

---

### Task 6: 创建Bug修复记录模板

**Files:**
- Create: `ADR/templates/bug-template.md`

- [ ] **Step 1: 写入 bug-template.md**

```markdown
---
type: bug
date: YYYY-MM-DD
number: XXX
title: Bug标题
severity: critical | high | medium | low
---

## Bug描述
Bug的表现和影响。

## 问题原因
根本原因分析。

## 解决方案
如何修复的。

## 预防措施
如何避免类似问题再次发生。

## 相关变更
链接到相关的 change 记录。
```

写入文件 `D:/adr-project/ADR/templates/bug-template.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/ADR/templates/bug-template.md"
```

---

### Task 7: 创建 CLAUDE.md 项目规范文件

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: 写入 CLAUDE.md**

```markdown
# 项目规范 - ADR 记录系统

本项目使用 ADR（Architecture Decision Records）系统记录所有重要变更和决策。

## 核心原则

**每次工作结束必须记录变更**，确保未来的开发者（包括 AI agent）能理解项目演进脉络。

## ADR 目录结构

- `ADR/changes/` - 功能性变更
- `ADR/decisions/` - 技术决策
- `ADR/requirements/` - 讨论/需求记录
- `ADR/bugs/` - Bug修复记录

## 工作流程

### 1. 开始工作前
- 阅读 `ADR/INDEX.md` 了解项目历史
- 查阅相关文件夹内的已有记录

### 2. 工作过程中
- 涉及技术选型时，先创建 decision 记录草案
- 收到用户需求时，创建 requirement 记录
- 发现 Bug 时，创建 bug 记录

### 3. 工作完成后
- **必须** 创建对应的记录文件
- 更新 INDEX.md 索引
- 文件命名：`YYYY-MM-DD-编号-标题.md`
- 编号在每个文件夹内独立递增

## 记录类型判断

| 工作类型 | 记录位置 | 触发时机 |
|----------|----------|----------|
| 新增/修改/删除功能 | changes/ | 功能完成后 |
| 技术选型、架构设计 | decisions/ | 决策确定后 |
| 用户需求、讨论结果 | requirements/ | 需求确认后 |
| Bug修复 | bugs/ | 修复完成后 |

## 使用 record-adr skill

执行 `/record-adr` 可调用标准化记录工具，自动生成符合模板的记录文件。

## 例外情况

以下情况无需创建记录：
- 简单的代码格式调整
- 注释修改
- 配置文件微调（无功能影响）
```

写入文件 `D:/adr-project/CLAUDE.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/CLAUDE.md"
```

---

### Task 8: 创建 record-adr skill 目录结构

**Files:**
- Create: `.claude/skills/record-adr/` (目录)
- Create: `.claude/skills/record-adr/templates/` (目录)

- [ ] **Step 1: 创建 skill 目录**

```bash
mkdir -p "D:/adr-project/.claude/skills/record-adr/templates"
```

- [ ] **Step 2: 验证目录创建**

```bash
ls -la "D:/adr-project/.claude/skills/record-adr/"
```
Expected: 看到 templates 目录

---

### Task 9: 创建 record-adr SKILL.md 主文件

**Files:**
- Create: `.claude/skills/record-adr/SKILL.md`

- [ ] **Step 1: 写入 SKILL.md**

```markdown
---
name: record-adr
description: 创建 ADR 记录文件并更新索引，用于记录功能性变更、技术决策、讨论需求和Bug修复
---

# record-adr Skill

用于创建符合 ADR 规范的记录文件并自动更新索引。

## 使用方式

- 用户执行 `/record-adr`
- Claude 在完成工作后主动调用

## 流程

### Step 1: 确定记录类型

询问用户或根据上下文判断记录类型：
- `change` - 功能性变更
- `decision` - 技术决策
- `requirement` - 讨论/需求记录
- `bug` - Bug修复记录

### Step 2: 获取下一个编号

检查 `ADR/{type}/` 目录，找到下一个可用编号：
- 查看已有文件，确定最大编号
- 新编号 = 最大编号 + 1（格式：001, 002, ...）
- 如果目录为空，编号为 001

### Step 3: 收集必要信息

根据类型收集必填字段：

**change 类型**:
- 标题
- 变更内容
- 变更原因
- 影响范围
- 状态（implemented | planned | reverted）
- 作者（可选）
- 关联文件（可选）

**decision 类型**:
- 标题
- 背景
- 考虑的方案
- 最终决策
- 状态（accepted | deprecated | superseded）

**requirement 类型**:
- 标题
- 需求来源
- 需求内容
- 讨论过程（可选）
- 最终结论
- 优先级（high | medium | low）

**bug 类型**:
- 标题
- Bug描述
- 问题原因
- 解决方案
- 严重程度（critical | high | medium | low）

### Step 4: 生成记录文件

使用模板生成文件内容，创建文件：
```
ADR/{type}/{YYYY-MM-DD}-{number}-{title}.md
```

示例：`ADR/changes/2026-05-08-001-添加用户登录功能.md`

### Step 5: 更新 INDEX.md

在 `ADR/INDEX.md` 对应表格中添加新条目：

```markdown
| {number} | {date} | {title} | {status} | [链接](changes/{filename}.md) |
```

插入到对应表格的注释占位符下方。

## 必填字段检查

每种类型必须包含以下字段，否则拒绝创建：

| 类型 | 必填字段 |
|------|----------|
| change | 变更内容、变更原因、影响范围 |
| decision | 背景、考虑的方案、最终决策 |
| requirement | 需求来源、需求内容、最终结论 |
| bug | Bug描述、问题原因、解决方案 |

## 错误处理

- 如果 INDEX.md 不存在，提示用户先运行初始化
- 如果编号冲突，自动递增直到找到可用编号
- 如果必填字段缺失，提示用户补充

## 模板位置

模板文件位于 `.claude/skills/record-adr/templates/` 目录：
- `change.md`
- `decision.md`
- `requirement.md`
- `bug.md`
```

写入文件 `D:/adr-project/.claude/skills/record-adr/SKILL.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/.claude/skills/record-adr/SKILL.md"
```

---

### Task 10: 创建 skill 内嵌模板 - change.md

**Files:**
- Create: `.claude/skills/record-adr/templates/change.md`

- [ ] **Step 1: 写入 change.md 模板**

```markdown
---
type: change
date: {{date}}
number: {{number}}
title: {{title}}
status: {{status}}
author: {{author}}
related_files: {{related_files}}
---

## 变更内容
{{change_content}}

## 变更原因
{{change_reason}}

## 影响范围
{{impact_scope}}

## 实现方案
{{implementation}}

## 测试验证
{{test_verification}}

## 备注
{{notes}}
```

写入文件 `D:/adr-project/.claude/skills/record-adr/templates/change.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/.claude/skills/record-adr/templates/change.md"
```

---

### Task 11: 创建 skill 内嵌模板 - decision.md

**Files:**
- Create: `.claude/skills/record-adr/templates/decision.md`

- [ ] **Step 1: 写入 decision.md 模板**

```markdown
---
type: decision
date: {{date}}
number: {{number}}
title: {{title}}
status: {{status}}
supersedes: {{supersedes}}
---

## 背景
{{context}}

## 考虑的方案
{{alternatives}}

## 最终决策
{{decision}}

## 影响与后果
{{consequences}}

## 相关变更
{{related_changes}}

## 备注
{{notes}}
```

写入文件 `D:/adr-project/.claude/skills/record-adr/templates/decision.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/.claude/skills/record-adr/templates/decision.md"
```

---

### Task 12: 创建 skill 内嵌模板 - requirement.md

**Files:**
- Create: `.claude/skills/record-adr/templates/requirement.md`

- [ ] **Step 1: 写入 requirement.md 模板**

```markdown
---
type: requirement
date: {{date}}
number: {{number}}
title: {{title}}
source: {{source}}
priority: {{priority}}
---

## 需求来源
{{requirement_source}}

## 需求内容
{{requirement_content}}

## 讨论过程
{{discussion}}

## 最终结论
{{conclusion}}

## 设计理念/限制
{{design_principles}}

## 相关决策/变更
{{related_records}}
```

写入文件 `D:/adr-project/.claude/skills/record-adr/templates/requirement.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/.claude/skills/record-adr/templates/requirement.md"
```

---

### Task 13: 创建 skill 内嵌模板 - bug.md

**Files:**
- Create: `.claude/skills/record-adr/templates/bug.md`

- [ ] **Step 1: 写入 bug.md 模板**

```markdown
---
type: bug
date: {{date}}
number: {{number}}
title: {{title}}
severity: {{severity}}
---

## Bug描述
{{bug_description}}

## 问题原因
{{root_cause}}

## 解决方案
{{solution}}

## 预防措施
{{prevention}}

## 相关变更
{{related_changes}}
```

写入文件 `D:/adr-project/.claude/skills/record-adr/templates/bug.md`

- [ ] **Step 2: 验证文件创建**

```bash
cat "D:/adr-project/.claude/skills/record-adr/templates/bug.md"
```

---

### Task 14: 验证整体文件结构

**Files:**
- 验证所有已创建文件

- [ ] **Step 1: 检查完整目录结构**

```bash
find "D:/adr-project" -type f -name "*.md" | head -20
```
Expected: 显示所有创建的 .md 文件列表

- [ ] **Step 2: 检查 ADR 目录结构**

```bash
tree "D:/adr-project/ADR" 2>/dev/null || ls -R "D:/adr-project/ADR"
```
Expected: 显示完整的 ADR 目录树

- [ ] **Step 3: 检查 skill 目录结构**

```bash
ls -R "D:/adr-project/.claude/skills/record-adr"
```
Expected: 显示 SKILL.md 和 templates 目录及其内容

---

### Task 15: 创建示例记录文件（可选，用于测试）

**Files:**
- Create: `ADR/requirements/2026-05-08-001-创建ADR项目规范系统.md`

- [ ] **Step 1: 写入第一条需求记录（本次讨论）**

```markdown
---
type: requirement
date: 2026-05-08
number: 001
title: 创建ADR项目规范系统
source: 内部讨论
priority: high
---

## 需求来源
用户希望通过 Claude Code 创建一套项目规范，用于记录所有工作变更和决策过程。

## 需求内容
1. 每一次工作都要记录变更
2. 讨论过程决定的方案实施时要记录原因和决策因素
3. 目的是帮助未来的同事、自己、AI agent 理解项目决策脉络

## 讨论过程
- 确定使用 ADR（Architecture Decision Records）模式
- 讨论了变更记录方式：最终选择 CHANGELOG + ADR 结合
- 讨论了决策记录方式：最终选择 ADR 单文件 + 嵌入 CHANGELOG 结合
- 讨论了文件位置：最终选择新建 ADR 目录
- 讨论了目录结构：最终选择分类文件夹结构
- 讨论了文件命名：最终选择日期+编号命名
- 讨论了实现方案：最终选择组合方案（CLAUDE.md + 模板 + skill）

## 最终结论
采用 ADR 系统，包含：
- 四个分类目录：changes/, decisions/, requirements/, bugs/
- 每个类型有标准化模板
- INDEX.md 作为总索引
- CLAUDE.md 定义 Claude Code 行为规范
- record-adr skill 提供标准化记录工具

## 设计理念/限制
- 记录文件命名格式：YYYY-MM-DD-编号-标题.md
- 编号在每个文件夹内独立递增
- 必填字段确保记录质量
- 例外情况（格式调整、注释修改）无需记录
```

写入文件 `D:/adr-project/ADR/requirements/2026-05-08-001-创建ADR项目规范系统.md`

- [ ] **Step 2: 更新 INDEX.md 添加第一条记录**

在 INDEX.md 的 "讨论/需求记录" 表格中添加：

```markdown
| 001 | 2026-05-08 | 创建ADR项目规范系统 | 内部讨论 | high | [链接](requirements/2026-05-08-001-创建ADR项目规范系统.md) |
```

- [ ] **Step 3: 验证**

```bash
cat "D:/adr-project/ADR/INDEX.md"
cat "D:/adr-project/ADR/requirements/2026-05-08-001-创建ADR项目规范系统.md"
```

---

## 完成清单

全部任务完成后，项目结构应为：

```
D:/adr-project/
├── ADR/
│   ├── INDEX.md
│   ├── changes/
│   ├── decisions/
│   ├── requirements/
│   │   └── 2026-05-08-001-创建ADR项目规范系统.md
│   ├── bugs/
│   └── templates/
│       ├── change-template.md
│       ├── decision-template.md
│       ├── requirement-template.md
│       └── bug-template.md
├── CLAUDE.md
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-08-adr-project-spec-design.md
│       └── plans/
│           └── 2026-05-08-adr-project-implementation.md
└── .claude/
│   └── skills/
│       └── record-adr/
│           ├── SKILL.md
│           └── templates/
│               ├── change.md
│               ├── decision.md
│               ├── requirement.md
│               └── bug.md
```

---

## Self-Review 检查

1. **Spec coverage**: 所有设计文档中的内容都已覆盖
2. **Placeholder scan**: 无 TBD 或 TODO 占位符
3. **Type consistency**: 文件路径和命名一致