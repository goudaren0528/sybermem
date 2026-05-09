---
title: Claude Code 项目 ADR 规范设计
date: 2026-05-08
status: approved
---

# Claude Code 项目 ADR 规范设计

## 概述

创建一套适用于所有项目的 ADR（Architecture Decision Records）系统，用于记录功能性变更、技术决策、讨论需求和 Bug 修复，帮助未来的开发者（包括 AI agent）理解项目演进脉络。

## 核心需求

1. **每次工作都要记录变更**：功能性变更必须记录到 CHANGELOG 系统
2. **决策原因可追溯**：讨论过程中的方案选择和决策因素必须记录
3. **目的**：让未来的同事、自己、AI agent 能理解过往决策和功能缘由

## 设计方案

### 1. 目录结构

```
项目根目录/
├── ADR/
│   ├── INDEX.md              # 总索引文件
│   ├── changes/              # 功能性变更记录
│   │   ├── 2026-05-08-001-xxx.md
│   │   └── 2026-05-08-002-xxx.md
│   ├── decisions/            # 技术决策记录
│   │   ├── 2026-05-08-001-xxx.md
│   │   └── 2026-05-08-002-xxx.md
│   ├── requirements/         # 讨论/需求记录
│   │   ├── 2026-05-08-001-xxx.md
│   │   └── 2026-05-08-002-xxx.md
│   ├── bugs/                 # Bug修复记录
│   │   ├── 2026-05-08-001-xxx.md
│   │   └── 2026-05-08-002-xxx.md
│   └── templates/            # 模板文件
│       ├── change-template.md
│       ├── decision-template.md
│       ├── requirement-template.md
│       └── bug-template.md
└── CLAUDE.md                 # Claude Code 项目规范
```

**命名规则**：
- 每个文件夹内独立编号，从 001 开始递增
- 文件名格式：`YYYY-MM-DD-编号-标题.md`
- 编号在每个文件夹内独立递增，不跨文件夹共享

### 2. 记录类型与内容范围

| 类型 | 文件夹 | 内容范围 | 触发时机 |
|------|--------|----------|----------|
| 功能性变更 | changes/ | 新增、修改、删除功能 | 功能完成后 |
| 技术决策 | decisions/ | 架构选型、技术栈、设计模式 | 决策确定后 |
| 讨论/需求 | requirements/ | 用户需求、讨论结果、设计理念 | 需求确认后 |
| Bug修复 | bugs/ | Bug描述、原因分析、解决方案 | 修复完成后 |

### 3. 各类型模板设计

#### 3.1 功能性变更模板 (change-template.md)

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

**必填字段**：变更内容、变更原因、影响范围

#### 3.2 技术决策模板 (decision-template.md)

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

**必填字段**：背景、考虑的方案、最终决策

#### 3.3 讨论/需求记录模板 (requirement-template.md)

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

**必填字段**：需求来源、需求内容、最终结论

#### 3.4 Bug修复记录模板 (bug-template.md)

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

**必填字段**：Bug描述、问题原因、解决方案

### 4. INDEX.md 索引文件结构

```markdown
# ADR 索引

本文件汇总所有项目变更、决策、需求和Bug记录。

---

## 功能性变更

| 编号 | 日期 | 标题 | 状态 | 文件链接 |
|------|------|------|------|----------|
| 001 | 2026-05-08 | 添加用户登录功能 | implemented | [链接](changes/...) |

---

## 技术决策

| 编号 | 日期 | 标题 | 状态 | 文件链接 |
|------|------|------|------|----------|
| 001 | 2026-05-08 | 选择React作为前端框架 | accepted | [链接](decisions/...) |

---

## 讨论/需求记录

| 编号 | 日期 | 标题 | 来源 | 优先级 | 文件链接 |
|------|------|------|------|--------|----------|
| 001 | 2026-05-08 | 用户登录需求 | 用户反馈 | high | [链接](requirements/...) |

---

## Bug修复记录

| 编号 | 日期 | 标题 | 严重程度 | 文件链接 |
|------|------|------|----------|----------|
| 001 | 2026-05-08 | 登录页面无法提交 | high | [链接](bugs/...) |

---

## 使用说明

- **changes/**: 记录所有功能性变更
- **decisions/**: 记录重要技术决策及其原因
- **requirements/**: 记录讨论过程、需求来源、设计理念
- **bugs/**: 记录Bug问题分析和修复方案

新增记录时，请同步更新本索引文件。
```

### 5. CLAUDE.md 项目规范

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

### 6. record-adr Skill 设计

**Skill 名称**: `record-adr`

**触发方式**: 用户执行 `/record-adr` 或 Claude 主动调用

**Skill 文件结构**:

```
.claude/skills/record-adr/
├── SKILL.md          # Skill 主文件
└── templates/        # 内嵌模板
    ├── change.md
    ├── decision.md
    ├── requirement.md
    └── bug.md
```

**SKILL.md 核心流程**:

```markdown
---
name: record-adr
description: 创建 ADR 记录文件并更新索引
---

## 使用方式

用户执行 `/record-adr` 或在完成工作后 Claude 主动调用。

## 流程

1. 确定记录类型（change/decision/requirement/bug）
2. 检查对应文件夹，获取下一个编号
3. 询问标题和必要字段
4. 使用模板生成内容
5. 创建文件：ADR/{type}/{YYYY-MM-DD}-{number}-{title}.md
6. 更新 ADR/INDEX.md，添加新条目到对应表格

## 必填字段检查

每种类型必须包含：
- change: 变更内容、变更原因、影响范围
- decision: 背景、方案、最终决策
- requirement: 需求来源、需求内容、最终结论
- bug: Bug描述、问题原因、解决方案

## 错误处理

- 如果 INDEX.md 不存在，提示用户先初始化 ADR 目录
- 如果编号冲突，自动递增直到找到可用编号
```

## 实现方案

采用**组合方案**：

1. **CLAUDE.md 规范文件**：定义 Claude Code 的行为规范
2. **模板文件**：ADR/templates/ 目录下的标准化模板
3. **record-adr skill**：自定义 skill 提供标准化记录工具

## 交付物清单

| 文件 | 路径 | 说明 |
|------|------|------|
| INDEX.md | ADR/INDEX.md | 索引文件模板 |
| change-template.md | ADR/templates/change-template.md | 功能变更模板 |
| decision-template.md | ADR/templates/decision-template.md | 技术决策模板 |
| requirement-template.md | ADR/templates/requirement-template.md | 需求记录模板 |
| bug-template.md | ADR/templates/bug-template.md | Bug修复模板 |
| CLAUDE.md | 项目根目录/CLAUDE.md | Claude Code 规范 |
| SKILL.md | .claude/skills/record-adr/SKILL.md | Skill 主文件 |

## 使用场景示例

### 场景 1：新增功能

用户请求添加用户登录功能，Claude 完成开发后：

1. 调用 `/record-adr` 或遵循 CLAUDE.md 规范
2. 选择类型 `change`
3. 填写变更内容、原因、影响范围
4. 创建 `ADR/changes/2026-05-08-001-添加用户登录功能.md`
5. 更新 INDEX.md 的功能性变更表格

### 场景 2：技术选型讨论

用户讨论是否使用 React 或 Vue，讨论后决定使用 React：

1. 在讨论过程中，创建 requirement 记录需求来源
2. 决策确定后，创建 decision 记录
3. decision 中记录考虑的方案、最终选择、原因
4. 两个记录相互链接

### 场景 3：AI agent 接手项目

新的 AI agent 接手项目：

1. 自动读取 CLAUDE.md，了解需要遵循 ADR 规范
2. 阅读 INDEX.md，了解项目历史
3. 根据历史记录理解设计理念和决策原因
4. 开始工作时遵循规范创建新记录

## 维护说明

- INDEX.md 需手动或通过 skill 自动更新
- 记录文件创建后不应修改（除非状态变更）
- deprecated 或 superseded 状态的记录保留，不删除
- templates 文件可按项目需求定制调整