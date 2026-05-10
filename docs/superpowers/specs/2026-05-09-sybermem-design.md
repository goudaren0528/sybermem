---
title: Sybermem 记忆系统设计
date: 2026-05-10
status: approved
version: 2.0
---

# Sybermem 记忆系统设计

## 概述

Sybermem 是一个可注入的记忆系统，为 Claude Code 和 OpenCode 提供项目认知能力。核心目标是让 AI Agent 能够：

1. **理解项目全貌** - 项目定位、架构、技术栈、核心功能
2. **追溯决策脉络** - 为什么做这个决定、考虑了哪些方案、结果是什么
3. **追踪项目进展** - 当前状态、日/周/月进展汇总
4. **积累开发经验** - 踩坑经验、最佳实践、调试方法
5. **记住特殊处理** - 因业务现状或历史原因的特殊逻辑
6. **了解开发者偏好** - 个人编码风格、工具偏好、价值观
7. **全局视角** - 通过 sybermem 项目了解开发者参与的所有项目历史、沉淀和偏好

## 核心设计原则

- **严格 ADR 定义** - ADR 只记录架构决策，其他类型独立管理
- **三层分离** - 开发者层（个人）、团队层（共享）、项目层（注入）
- **项目注册中心** - sybermem 作为项目注册中心，记录开发者参与的所有项目
- **AI 内部自动判断** - AI 分析自己的操作行为，自动判断并加载相关记忆，用户无感知
- **Git 流程管理** - 所有记忆都在 Git 仓库中，通过 PR/合并同步
- **增量更新** - 不重写已有内容，追加补充新信息
- **非侵入性** - 合入用户已有文件时，追加在末尾 + 分隔标记，不破坏用户原有内容
- **渐进式披露** - 概览→模块→细节→关联，分层加载避免信息过载
- **高层级始终生效** - 开发者层和团队层作为"指导思想"始终加载
- **Agent辅助为主** - AI负责收集填充，开发者负责最终确认和价值判断

---

## 三层架构设计

### 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│  sybermem 仓库（用户 Fork）                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  开发者层（Developer Layer）                             ││
│  │  内容：preferences.md、values.md、experiences/           ││
│  │  特点：用户私有，跨项目共享                               ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  项目注册中心（PROJECTS/）                               ││
│  │  内容：INDEX.md、registered/{project-name}/              ││
│  │  特点：记录用户参与的所有项目                             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              ↓ 读取
┌─────────────────────────────────────────────────────────────┐
│  sybermem 仓库（主分支/团队共享）                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  团队层（Team Layer）                                    ││
│  │  内容：conventions.md、shared-experiences/、team-values.md││
│  │  特点：团队共享，通过 Git PR 同步                         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              ↓ 读取（用户级注入）
┌─────────────────────────────────────────────────────────────┐
│  用户级配置（~/.claude/）                                     │
│  内容：CLAUDE.md（合入开发者层 + 团队层）                      │
│  特点：所有项目共享，Claude Code 启动时加载                   │
└─────────────────────────────────────────────────────────────┘
                              ↓ 读取
┌─────────────────────────────────────────────────────────────┐
│  项目层（Project Layer）                                     │
│  存储位置：各项目内的 .sybermem/ 目录                         │
│  内容：OVERVIEW、ADR、PROGRESS、EXPERIENCES 等               │
│  特点：项目独立，新增目录不修改用户原有文件                   │
└─────────────────────────────────────────────────────────────┘
                              ↓ AI 内部自动判断加载
┌─────────────────────────────────────────────────────────────┐
│  AI Agent Context                                           │
│  Claude Code / OpenCode 工作时自动加载相关记忆               │
│  用户无感知，只体验"AI 更懂项目"                              │
└─────────────────────────────────────────────────────────────┘
```

### 各层职责

| 层级 | 职责 | 内容范围 | 读写权限 |
|------|------|----------|----------|
| 开发者层 | 存储个人偏好和经验 | preferences、values、personal experiences | 用户读写，AI读取 |
| 项目注册中心 | 记录参与的所有项目 | INDEX.md、项目路径、OVERVIEW快照 | 自动注册/更新 |
| 团队层 | 存储团队共识和共享经验 | conventions、team-values、shared experiences | 团队成员读写，需PR |
| 项目层 | 存储项目具体记忆 | OVERVIEW、ADR、PROGRESS、SPECIAL-CASES等 | AI写入，用户审核 |

### 各层读取策略

| 层级 | 性质 | 读取策略 | 加载时机 |
|------|------|----------|----------|
| 开发者层 | 个人偏好/价值观 | 始终加载（合入用户级 CLAUDE.md） | Claude Code 启动时 |
| 团队层 | 团队约定/共识 | 始终加载（合入用户级 CLAUDE.md） | Claude Code 启动时 |
| 项目注册中心 | 项目索引 | 在 sybermem 项目中加载，或切换项目时参考 | 需要全局视角时 |
| 项目层 | 具体记录 | AI 内部自动判断加载 | 工作过程中按需加载 |

---

## sybermem 仓库结构

用户 Fork sybermem 仓库后，获得完整的记忆系统载体：

```
sybermem/
│
├── developer/                   # 开发者层（用户私有）
│   ├── preferences.md           # 个人偏好
│   ├── values.md                # 开发价值观
│   └── experiences/             # 个人经验积累
│       ├── pitfalls/
│       ├── best-practices/
│       └── tools/
│
├── PROJECTS/                    # 项目注册中心（用户私有）
│   ├── INDEX.md                 # 所有项目总览
│   └── registered/              # 注册的项目信息
│       └── {project-name}/
│           ├── INFO.md          # 项目基本信息（路径、名称、技术栈摘要）
│           ├── OVERVIEW-SNAPSHOT.md  # 项目 OVERVIEW 的定期快照
│           ├── STATUS.md        # 当前状态（最后活动时间、活跃模块）
│           └── LINK.md          # 关联配置（指向项目实际路径）
│
├── team/                        # 团队层（团队共享）
│   ├── conventions.md           # 团队约定
│   ├── team-values.md           # 团队价值观
│   └── shared-experiences/      # 共享经验
│       ├── pitfalls/
│       ├── best-practices/
│       ├── debug/
│       └── tools/
│
├── README.md                    # 项目说明
└── INSTALL.md                   # 安装指南
```

**Git 同步策略：**

| 目录 | 提交到上游 | 说明 |
|------|-----------|------|
| `developer/` | 否 | 用户私有，在自己的 fork 中管理 |
| `PROJECTS/` | 否 | 用户私有，在自己的 fork 中管理 |
| `team/` | 是 | 团队共享，通过 PR 同步到上游 |

---

## 用户级注入机制

sybermem 通过用户级配置注入，所有项目共享，一次配置全局生效。

### 注入方式：合入已有文件

当用户已有 `~/.claude/CLAUDE.md` 或 `~/.claude/settings.json` 时，sybermem 采用**追加 + 分隔标记**的方式合入，不破坏用户原有内容。

**合入后的 ~/.claude/CLAUDE.md 示例：**

```markdown
# 用户原有内容（完整保留）
...用户自己的配置...

---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 `sybermem update` 可更新        ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统

## 开发者偏好
{{sybermem/developer/preferences.md 内容}}

## 开发价值观
{{sybermem/developer/values.md 内容}}

## 团队约定
{{sybermem/team/conventions.md 内容}}

## 团队价值观
{{sybermem/team/team-values.md 内容}}

## 可用 Skills
以下 Skills 在所有项目可用：
- /init-project - 新项目注入记忆系统
- /adapt-project - 旧项目适配记忆系统
- /record-adr - 创建架构决策记录
- /record-change - 创建功能变更记录
- /record-experience - 创建经验记录
- /record-special - 创建特殊处理记录
- /record-requirement - 创建需求讨论记录
- /update-progress - 更新项目进展
- /update-overview - 更新项目全貌
- /weekly-summary - 生成周报
- /monthly-summary - 生成月报
- /optimize-memory - 执行记忆优化
- /sync-experience - 同步经验到团队层
```

**合入后的 ~/.claude/settings.json 示例：**

```json
{
  // 用户原有配置（完整保留）
  "existing_user_setting": "...",

  // --- sybermem 注入区域 ---
  "sybermem": {
    "path": "/Users/xxx/sybermem",
    "version": "2.0.0"
  }
}
```

### 更新机制

当 sybermem 需要更新注入内容时：
1. 读取文件，找到分隔标记
2. 保留标记之前的内容（用户原有）
3. 替换标记之后的内容（sybermem 管理区域）
4. 写入更新后的文件

---

## 项目层目录结构

项目层存储在各项目的 `.sybermem/` 目录，与用户原有文件隔离，不修改项目根目录的 `CLAUDE.md` 等文件。

```
.sybermem/
│
├── OVERVIEW.md                 # 项目全貌 + 开发约定（合并 CONVENTIONS）
├── PROGRESS.md                 # 当前进展追踪
│
├── ADR/                        # 架构决策记录（仅架构决策）
│   ├── INDEX.md                # 决策索引
│   └── decisions/              # 决策文件
│       └── YYYY-MM-DD-NNN-title.md
│
├── REQUIREMENTS/               # 需求讨论（包含讨论过程）
│   ├── INDEX.md                # 需求索引
│   └── YYYY-MM-DD-NNN-title.md
│
├── CHANGELOG/                  # 功能变更（与 ADR 分开）
│   ├── INDEX.md                # 变更索引
│   └── YYYY-MM-DD-NNN-title.md
│
├── EXPERIENCES/                # 经验积累
│   ├── INDEX.md                # 经验索引
│   ├── pitfalls/               # 踩坑经验
│   ├── debug/                  # 调试方法
│   ├── best-practices/         # 最佳实践
│   ├── tools/                  # 工具技巧
│   ├── performance/            # 性能优化
│   └── refactor/               # 重构经验
│
├── SPECIAL-CASES/              # 项目特异处理
│   ├── INDEX.md                # 特殊处理索引（包含文件路径关联）
│   ├── legacy/                 # 历史遗留
│   ├── business/               # 业务特殊性
│   ├── temporary/              # 临时方案（标记待优化）
│   ├── environment/            # 环境限制
│   └── custom/                 # 客户定制
│
└── CLAUDE.md                   # 项目规范（可选，仅当项目有特殊规范时）
```

**模块说明：**

| 模块 | 用途 | INDEX 文件 |
|------|------|------------|
| OVERVIEW.md | 项目全貌、技术架构、开发约定 | 无（本身就是概览） |
| PROGRESS.md | 当前进展、今日/本周/本月任务 | 无 |
| ADR/decisions | 架构决策（技术选型、架构设计） | INDEX.md |
| REQUIREMENTS | 需求讨论过程、最终方案 | INDEX.md |
| CHANGELOG | 功能变更记录 | INDEX.md |
| EXPERIENCES | 踩坑、最佳实践、调试方法 | INDEX.md（按模块、标签分类） |
| SPECIAL-CASES | 特殊处理逻辑、历史原因 | INDEX.md（包含文件路径关联） |
| CLAUDE.md | 项目特殊规范（可选） | 无 |

---

## AI 内部自动判断与加载

### 设计理念

**核心原则：** AI 分析自己的操作行为，自动判断并加载相关记忆，用户完全无感知。

用户只体验"AI 更懂项目了"，不感知加载过程，不被打断。

### AI 内部执行流程

```
用户输入：我要修改支付模块的订单处理逻辑

AI 内部执行（用户看不到这些步骤）：
├── 1. 分析操作：判断涉及"支付模块" + "修改代码"
├── 2. 检查 OVERVIEW → 知道支付模块位置
├── 3. 检查 INDEX → 找到支付模块相关记录
├── 4. 自动读取（Read 工具，融入执行流程）：
│   ├── CHANGELOG 中支付模块历史变更
│   ├── SPECIAL-CASES 中支付模块特殊处理
│   ├── EXPERIENCES/pitfalls 中支付踩坑记录
│   └── ADR 中支付架构决策
├── 5. 这些内容作为 AI 上下文
└── 6. 基于上下文执行任务

AI 输出（用户只看到这个）：
"我来修改支付模块的订单处理逻辑..."
（AI 已知道该模块的历史、踩坑、特殊处理）
```

### 触发时机：AI 操作行为判断

| AI 操作 | AI 内部判断 | 自动加载 |
|----------|-------------|----------|
| **执行 Edit/Write 修改某文件** | 检查该文件路径是否在 SPECIAL-CASES INDEX 中有关联 | 如有关联，自动读取对应记录 |
| **执行 Bash 运行测试/构建** | 检查是否有相关的 EXPERIENCES/debug 或 pitfalls | 如有失败历史记录，参考相关踩坑经验 |
| **读取某个模块的代码文件** | 检查该模块在 INDEX 中的相关记录 | 加载该模块的 CHANGELOG + EXPERIENCES |
| **分析代码发现问题** | 判断问题类型（性能？逻辑？安全？） | 加载对应类型的 EXPERIENCES |
| **处理技术决策类任务** | 判断这是"决策类任务" | 加载 ADR + REQUIREMENTS + values/team-values |

### 渐进式披露机制（AI 内部执行）

| 层级 | 触发时机 | 加载内容 |
|------|----------|----------|
| **Level 1 概览** | Claude Code 启动时 | 用户级 CLAUDE.md（开发者层 + 团队层） + 项目 OVERVIEW 概览 |
| **Level 2 模块** | AI 检测到操作某模块 | 从 INDEX 查找 → 自动读取该模块相关 CHANGELOG + SPECIAL-CASES + EXPERIENCES |
| **Level 3 细节** | AI 需要深入了解某决策/踩坑 | 自动读取具体的 ADR 文件或 EXPERIENCE 文件 |
| **Level 4 关联** | AI 修改某文件时 | 检查 SPECIAL-CASES INDEX 的文件路径关联，如有则自动加载提醒 |

### INDEX 文件设计

INDEX 文件作为 AI 快速查找的入口，支持按模块、标签、文件路径分类：

**SPECIAL-CASES/INDEX.md 示例（关键：包含文件路径关联）：**

```markdown
# SPECIAL-CASES INDEX

## 按文件路径关联
- src/payment/order-service.ts → temporary/payment-polling.md
- src/user/auth.ts → legacy/user-session-compat.md
- src/api/handler.ts → environment/api-timeout.md

## 按模块分类
- payment/
  - temporary: payment-polling.md
  - business: payment-currency-rounding.md
- user/
  - legacy: user-session-compat.md

## 按标签分类
- temporary: payment-polling.md, api-timeout.md
- legacy: user-session-compat.md

## 高风险标记（AI 修改时必须加载）
- payment-polling.md (impact: high, related_files: [src/payment/*])
```

**EXPERIENCES/INDEX.md 示例：**

```markdown
# EXPERIENCES INDEX

## 按模块分类
- payment/
  - pitfalls: payment-timeout.md, payment-double-charge.md
  - debug: payment-log-analysis.md
- user/
  - pitfalls: user-session-expire.md
  - best-practices: user-validation-flow.md

## 按标签分类
- timeout: payment-timeout.md, user-session-expire.md
- validation: user-validation-flow.md

## 最近更新
- 2026-05-10: payment-timeout.md (pitfalls)

## 高价值标记
- payment-timeout.md (impact: high, referred: 5 times)
```

---

## 各模块详细设计

### 1. OVERVIEW.md - 项目全貌（含开发约定）

**目的：** 让 AI Agent 快速理解项目整体情况

**内容结构：**

```markdown
# 项目全貌

## 项目定位
- 项目是什么
- 解决什么问题
- 目标用户

## 技术架构
- 技术栈列表
- 目录结构说明
- 关键模块关系（依赖图）
- 数据流说明

## 开发约定（合并原 CONVENTIONS）
- 编码规范摘要
- 分支策略
- 命名约定
- Git 工作流
- 部署流程

## 核心功能
- 已实现功能清单
- 重要功能说明
- 功能间依赖关系

## 关键决策索引
- 历史重要决策链接（指向 ADR/decisions/）
- 架构选择原因

## 当前状态
- 开发阶段
- 活跃模块
- 待办事项摘要

## 特殊处理提醒
- 指向 SPECIAL-CASES INDEX 的关键条目
- 提醒新人注意的特殊逻辑

## 更新日志
- 最后更新时间
- 更新内容摘要
```

---

### 2. PROGRESS.md - 当前进展追踪

```markdown
# 项目进展

## 当前状态
- 当前阶段
- 正在进行的任务
- 阻塞事项

## 今日进展
- 完成的任务列表
- 创建的记录
- 遗留问题

## 本周进展摘要
- 主要成果
- 关键决策
- 遇到的问题

## 本月进展摘要
- 功能交付情况
- 重要里程碑
- 经验总结

## 下一步计划
- 待办事项
- 优先级排序
```

---

### 3. ADR/decisions/ - 架构决策记录

**严格定义：只记录架构层面的决策**

**判断标准：**
- 是否涉及技术选型？（框架、库、工具）
- 是否涉及架构设计？（模块划分、数据流、接口设计）
- 是否涉及长期影响？

**模板：**

```markdown
---
type: decision
date: YYYY-MM-DD
number: NNN
title: 决策标题
status: accepted | deprecated | superseded
supersedes: [被取代的决策编号]
---

## 背景
描述决策的背景和问题。

## 考虑的方案
列出考虑过的方案及其优缺点。

### 方案A
优点：
缺点：

### 方案B
优点：
缺点：

## 最终决策
选择哪个方案，理由是什么。

## 影响与后果
决策带来的影响。

## 相关变更
链接到相关的 CHANGELOG 记录。

## 备注
其他信息。
```

---

### 4. REQUIREMENTS/ - 需求讨论

**目的：** 记录需求来源、讨论过程、最终结论

```markdown
---
type: requirement
date: YYYY-MM-DD
number: NNN
title: 需求标题
source: 用户反馈 | 客户需求 | 内部讨论
priority: high | medium | low
status: pending | in-progress | completed | cancelled
---

## 需求来源
谁提出的需求，什么场景。

## 需求内容
具体需求描述。

## 讨论过程
记录讨论中的关键观点、疑问。

## 最终结论
讨论结果和确定的方案。

## 设计理念/限制
重要的设计原则、约束条件。

## 相关决策/变更
链接到相关的 ADR 或 CHANGELOG。
```

---

### 5. CHANGELOG/ - 功能变更

**目的：** 记录功能性变更（与 ADR 分开，ADR 只记录架构决策）

```markdown
---
type: change
date: YYYY-MM-DD
number: NNN
title: 变更标题
status: implemented | planned | reverted
related_files: [关联文件路径]
---

## 变更内容
简要描述做了什么变更。

## 变更原因
为什么需要这个变更。

## 影响范围
- 影响的模块/功能

## 实现方案
简要说明实现思路。

## 测试验证
如何验证变更正确性。

## 相关决策
链接到相关的 ADR（如有决策讨论）。
```

---

### 6. EXPERIENCES/ - 经验积累

```markdown
---
type: experience
category: pitfalls | debug | best-practices | tools | performance | refactor
date: YYYY-MM-DD
title: 经验标题
tags: [关键词标签]
impact: high | medium | low
---

## 场景描述
什么情况下遇到这个问题/发现这个技巧。

## 问题/内容
踩坑的问题 / 最佳实践内容。

## 解决方案/方法
如何解决 / 如何应用。

## 关键要点
最重要的经验总结。

## 相关代码
涉及的代码文件或模块。

## 适用范围
这个经验适用于什么场景。
```

---

### 7. SPECIAL-CASES/ - 项目特异处理

**目的：** 记录因业务现状或历史原因的特殊处理逻辑

**为什么重要：**
- 新人/AI不理解原因，可能"优化"导致出错
- 临时方案容易被遗忘
- 重构时需要特别注意

```markdown
---
type: special-case
category: legacy | business | temporary | environment | custom
date: YYYY-MM-DD
status: active | pending-optimize | resolved | deprecated
related_code: [涉及的文件路径]
impact_level: high | medium | low
optimize_plan: [如果是临时方案，优化计划]
---

## 特殊处理描述
这段代码/逻辑做了什么特殊处理。

## 原因分析
为什么需要这样处理。

## 影响范围
哪些模块依赖这个特殊处理。

## 注意事项
修改时需要注意什么，不能做什么。

## 后续计划（如果是临时方案）
- 预计何时优化
- 优化方案是什么

## 相关决策/变更
链接到相关的 ADR 或 CHANGELOG。
```

---

## Skills 设计

### Skills 清单（12个）

| Skill | 用途 | 触发方式 |
|-------|------|----------|
| init-project | 新项目注入记忆系统 | 手动调用 |
| adapt-project | 旧项目适配记忆系统 | 手动调用 |
| record-adr | 创建架构决策记录 | 手动/Hook触发 |
| record-change | 创建功能变更记录 | 手动/Hook触发 |
| record-experience | 创建经验记录 | 手动/Hook触发 |
| record-special | 创建特殊处理记录 | 手动/Hook触发 |
| record-requirement | 创建需求讨论记录 | 手动调用 |
| update-progress | 更新项目进展 | 手动/SessionEnd自动 |
| update-overview | 更新项目全貌 | 手动/AI检测触发 |
| weekly-summary | 生成周报 | 手动调用 |
| monthly-summary | 生成月报 | 手动调用 |
| optimize-memory | 执行记忆优化 | 手动/定期触发 |
| sync-experience | 同步经验到团队层 | 手动确认 |

### 核心 Skills 详细设计

#### init-project

**用途：** 为新项目注入记忆系统

**流程：**
1. 检查项目是否已有 `.sybermem/` 目录
2. 创建完整目录结构（不修改用户原有文件）
3. 生成初始 OVERVIEW.md
4. 在 sybermem 的 PROJECTS/ 中注册该项目
5. 提示用户补充 OVERVIEW.md 内容

#### adapt-project

**用途：** 为已有代码的项目适配记忆系统

**流程：**
1. 扫描项目结构、分析技术栈
2. 生成 OVERVIEW.md（基于扫描结果）
3. 分析 Git 历史，追溯关键决策
4. 创建历史 ADR 记录
5. 检测特殊处理代码，创建 SPECIAL-CASES 记录
6. 在 sybermem 的 PROJECTS/ 中注册该项目

#### record-*

**用途：** 创建各类记录

**流程：**
1. 收集记录信息
2. 检查对应目录获取下一个编号
3. 使用模板生成文件内容
4. 创建文件并更新 INDEX

---

## Hooks 设计

### Hooks 清单（3个）

| Hook | 触发时机 | 用途 |
|------|----------|------|
| PostToolUse | Edit/Write/Bash 后 | AI 内部判断是否需要加载记忆 |
| SessionEnd | 会话结束时 | 更新 PROGRESS + 自动生成日报摘要 |
| PreCommit | Git commit 前 | 检查是否有对应 ADR/CHANGELOG 记录 |

### PostToolUse Hook

**触发时机：** 每次 Edit、Write、Bash 工具调用后

**AI 内部执行逻辑：**

```
PostToolUse Hook:
  if (tool == "Edit" || tool == "Write"):
    file_path = extract_file_path(operation)
    # 检查 SPECIAL-CASES INDEX
    related_cases = check_special_cases_index(file_path)
    if related_cases:
      # 自动读取，作为内部上下文
      read(related_cases)
      # 不向用户提示，融入任务执行

  if (tool == "Bash" && result == "failure"):
    error_type = analyze_error(result)
    related_experiences = check_experiences_index(error_type)
    if related_experiences:
      read(related_experiences)
```

**关键：** 所有加载都是 AI 内部执行，不打断用户，用户只体验"AI 给出了更好的建议"。

### SessionEnd Hook

**触发时机：** 会话结束

**执行逻辑：**
1. 收集本次会话的操作摘要
2. 更新 PROGRESS.md 今日进展
3. 自动生成日报摘要（动态生成，不持久存储）
4. 更新 sybermem 的 PROJECTS 中该项目状态

### PreCommit Hook

**触发时机：** Git commit 前

**检查逻辑：**
1. 分析 commit 内容
2. 检查是否有对应的记录：
   - 功能变更 → CHANGELOG
   - 架构调整 → ADR
3. 如缺失，提示用户："本次 commit 涉及 xxx，是否需要创建记录？"

---

## 侵入性处理原则

**核心原则：** 任何 sybermem 对用户文件的操作，都要保证不破坏用户原有内容。

| 操作类型 | 处理方式 |
|----------|----------|
| **合入已有文件** | 追加在末尾 + 分隔标记区分，sybermem 只管理标记区域 |
| **创建新文件/目录** | 使用独立路径（`.sybermem/`），不影响用户原有结构 |
| **更新注入内容** | 只替换 sybermem 标记区域，保留用户原有部分 |

---

## 实现优先级

### Phase 1：核心基础设施

1. sybermem 仓库结构定义
2. 项目层目录结构定义
3. 用户级注入机制（合入 CLAUDE.md）
4. OVERVIEW.md 模板（含开发约定）
5. ADR/decisions 模板
6. 各模块 INDEX 文件设计

### Phase 2：核心 Skills

1. init-project skill
2. adapt-project skill
3. record-adr skill
4. record-change skill
5. record-experience skill
6. record-special skill
7. update-progress skill

### Phase 3：扩展 Skills

1. record-requirement skill
2. update-overview skill
3. weekly-summary skill
4. monthly-summary skill

### Phase 4：Hooks 和自动化

1. PostToolUse Hook（AI 内部记忆加载判断）
2. SessionEnd Hook
3. PreCommit Hook

### Phase 5：记忆优化

1. optimize-memory skill

### Phase 6：多层同步与项目注册中心

1. PROJECTS 项目注册中心机制
2. sybermem 安装/更新脚本
3. sync-experience skill

---

## 维护说明

- 所有记忆文件使用 Markdown 格式
- 使用 YAML frontmatter 存储元数据
- 文件命名：`YYYY-MM-DD-NNN-title.md`
- 编号在各目录内独立递增
- INDEX 文件支持按模块、标签、文件路径分类
- SPECIAL-CASES INDEX 必须包含文件路径关联，AI 修改文件时可自动检测
- deprecated 或 superseded 状态的记录保留，不删除