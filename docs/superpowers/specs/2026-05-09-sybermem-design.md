---
title: Sybermem 记忆系统设计
date: 2026-05-09
status: approved
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

## 核心设计原则

- **严格 ADR 定义** - ADR 只记录架构决策，其他类型独立管理
- **三层分离** - 开发者层（个人）、团队层（共享）、项目层（注入）
- **AI 智能 + 人工确认** - 自动检测有价值内容，提示确认后记录
- **Git 流程管理** - 所有记忆都在 Git 仓库中，通过 PR/合并同步
- **增量更新** - 不重写已有内容，追加补充新信息
- **定期检查评审** - review-project + optimize-memory 保持记忆质量
- **分级记录策略** - 必须记录/建议记录/自动汇总/按需记录，避免记录成本过高
- **渐进式披露** - 概览→模块→细节→关联，分层加载避免信息过载
- **场景化读取** - 根据工作场景智能加载相关记录，作为context使用
- **高层级始终生效** - 开发者层和团队层作为"指导思想"始终加载
- **Agent辅助为主** - AI负责收集填充，开发者负责最终确认和价值判断

---

## 三层架构设计

### 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│  开发者层（Developer Layer）                                 │
│  存储位置：~/.claude/developer/ 或 sybermem 仓库个人分支      │
│  内容：preferences.md、values.md、experiences/               │
│  特点：个人私有，跨项目共享                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓ 读取
┌─────────────────────────────────────────────────────────────┐
│  团队层（Team Layer）                                        │
│  存储位置：sybermem 仓库主分支                                │
│  内容：conventions.md、shared-experiences/、team-values.md   │
│  特点：团队共享，通过 Git PR 同步                             │
└─────────────────────────────────────────────────────────────┘
                              ↓ 读取
┌─────────────────────────────────────────────────────────────┐
│  项目层（Project Layer）                                     │
│  存储位置：各项目内的 .sybermem/ 目录                         │
│  内容：OVERVIEW、ADR、PROGRESS、EXPERIENCES 等               │
│  特点：项目独立，注入到每个项目                               │
└─────────────────────────────────────────────────────────────┘
                              ↓ 读取
┌─────────────────────────────────────────────────────────────┐
│  AI Agent Context                                           │
│  Claude Code / OpenCode 启动时加载三层数据                   │
│  优先级：项目层 > 团队层 > 开发者层                           │
└─────────────────────────────────────────────────────────────┘
```

### 各层职责

| 层级 | 职责 | 内容范围 | 读写权限 |
|------|------|----------|----------|
| 开发者层 | 存储个人偏好和经验 | preferences、values、personal experiences | 开发者读写，AI读取 |
| 团队层 | 存储团队共识和共享经验 | conventions、team-values、shared experiences | 团队成员读写，需PR |
| 项目层 | 存储项目具体记忆 | OVERVIEW、ADR、PROGRESS、SPECIAL-CASES等 | AI写入，开发者审核 |

### 各层读取策略差异

**核心洞察：开发者层和团队层是"指导思想"，应始终生效；项目层是"具体信息"，应按需读取。**

| 层级 | 性质 | 读取策略 | 作用方式 | 加载时机 |
|------|------|----------|----------|----------|
| 开发者层 | 个人偏好/价值观 | **始终加载** | 作为AI理解开发者的"基础设定" | 启动时全量加载 |
| 团队层 | 团队约定/共识 | **始终加载** | 作为AI遵守的"默认规范" | 启动时全量加载 |
| 项目层 | 具体记录 | **概览+按需深入** | 根据场景选择性读取 | 启动时加载INDEX，工作时按需深入 |

**高层级内容如何影响工作：**

| 工作场景 | 高层级内容的作用 |
|----------|------------------|
| 生成代码时 | AI遵守 preferences（命名风格）+ conventions（代码规范） |
| 技术决策时 | AI引用 values（决策倾向）+ team-values（团队共识）作为指导思想 |
| 代码评审时 | AI基于 conventions（团队规范）+ preferences（开发者风格）检查 |
| 新人加入时 | 团队层重点加载，开发者层不加载（新人有自己的偏好） |

**新人模式 vs 熟手模式：**

| 模式 | 开发者层 | 团队层 | 项目层 | AI行为 |
|------|----------|--------|--------|--------|
| 熟手模式 | 全量加载 | 全量加载 | 概览+按需 | 遵守开发者偏好和团队约定 |
| 新人模式 | **不加载** | 重点加载 | 全量OVERVIEW | 只遵守团队约定，尊重新人偏好 |

识别方式：AI询问"你是项目成员还是刚加入的新人？"或检测开发者层配置文件是否存在。

### 数据流动

**读取流程（AI Agent 启动时）：**
```
开发者层 → 团队层 → 项目层 → AI Context
优先级：项目层可覆盖上层约定
```

**写入流程（工作过程中）：**
```
AI 写入 → 项目层 → [可选] 同步到团队层 → [可选] 沉淀到开发者层
同步策略：AI智能判断有价值内容 + 人工确认 + Git流程
```

---

## 项目层目录结构

```
.sybermem/
│
├── OVERVIEW.md                 # 项目全貌（定位、架构、技术栈）
├── PROGRESS.md                 # 当前进展追踪
│
├── ADR/                        # 架构决策记录（严格ADR）
│   └── decisions/              # 真正的架构决策
│       └── YYYY-MM-DD-NNN-title.md
│
├── REQUIREMENTS/               # 需求讨论（包含讨论过程）
│   └── YYYY-MM-DD-NNN-title.md
│
├── CHANGELOG/                  # 功能变更
│   └── YYYY-MM-DD-NNN-title.md
│
├── EXPERIENCES/                # 经验积累
│   ├── pitfalls/               # 踩坑经验
│   ├── debug/                  # 调试方法
│   ├── best-practices/         # 最佳实践
│   ├── tools/                  # 工具技巧
│   ├── performance/            # 性能优化
│   └── refactor/               # 重构经验
│
├── SPECIAL-CASES/              # 项目特异处理
│   ├── legacy/                 # 历史遗留
│   ├── business/               # 业务特殊性
│   ├── temporary/              # 临时方案（标记待优化）
│   ├── environment/            # 环境限制
│   └── custom/                 # 客户定制
│
├── CONVENTIONS/                # 开发约定
│   ├── code-style.md           # 代码风格
│   ├── naming.md               # 命名约定
│   └── git-workflow.md         # Git工作流
│
├── FEEDBACK/                   # 用户反馈
│   └── YYYY-MM-DD-source-title.md
│
├── SUMMARY/                    # 周期总结
│   ├── daily/YYYY-MM-DD.md
│   ├── weekly/YYYY-WXX.md
│   └── monthly/YYYY-MM.md
│
├── REVIEW/                     # 检查评审
│   ├── reviews/                # 定期评审记录
│   └── optimizations/          # 精简优化记录
│
└── CLAUDE.md                   # 项目规范（注入到AI Agent）
```

---

## 读取时机与场景化读取设计

### 设计背景

记录的价值在于"被读取"，而不是"被写入"。当前设计的盲点：
- 只关注如何写入，缺少何时读取、读什么、如何作为context使用
- 启动时全量加载会导致信息过载，AI无法有效理解
- 缺少渐进式披露机制：先概览，再深入
- 不同工作场景需要不同的context，缺少场景化读取

### 场景化读取设计

根据开发者当前的工作场景，智能加载相关的记录作为context：

| 工作场景 | 应该读取的内容 | 读取时机 | 作用 |
|----------|----------------|----------|------|
| 新项目开始 | OVERVIEW全量 + CONVENTIONS全量 + ADR INDEX | 首次启动 | 理解项目全貌、约定 |
| 功能开发 | OVERVIEW相关模块 + CHANGELOG + SPECIAL-CASES + ADR | 开始开发某模块时 | 了解模块历史、注意事项 |
| Bug修复 | EXPERIENCES/pitfalls + debug + BUGS历史 + SPECIAL-CASES | 开始调试时 | 参考踩坑经验、调试方法 |
| 技术讨论 | ADR/decisions + REQUIREMENTS + 团队层values + 开发者层values | 讨论开始时 | 参考历史决策、避免重复讨论 |
| 代码重构 | EXPERIENCES/refactor + **SPECIAL-CASES全量（重要）** + ADR | 重构前 | 避免误删特殊逻辑 |
| 性能优化 | EXPERIENCES/performance + OVERVIEW架构部分 + CHANGELOG | 优化前 | 参考优化经验 |
| 新人加入 | OVERVIEW全量 + CONVENTIONS全量 + SPECIAL-CASES INDEX + EXPERIENCES/best-practices | 首次启动 | 快速上手，避免踩坑 |

### 渐进式披露机制（4层）

不要一次加载所有内容，而是根据需要逐步深入：

**Level 1：概览层（启动时加载）**
- 内容：OVERVIEW.md 概览部分 + ADR INDEX + SPECIAL-CASES INDEX
- 目的：让AI知道项目有"哪些内容"，但不加载详细内容
- 大小控制：2000 tokens以内

**Level 2：模块层（开发某模块时加载）**
- 内容：OVERVIEW相关模块部分 + 相关CHANGELOG + 相关SPECIAL-CASES
- 目的：让AI理解当前模块的历史和注意事项
- 触发：开发者说"我要开发xxx模块"或AI检测到正在操作某模块

**Level 3：细节层（需要时按需加载）**
- 内容：具体的ADR decision文件、EXPERIENCE文件
- 目的：深入了解某个决策的详细过程或某个踩坑的解决方案
- 触发：AI或开发者明确请求"查看xxx决策的详细内容"

**Level 4：关联层（智能关联加载）**
- 内容：与当前操作可能相关的其他记录（通过标签/关键词关联）
- 目的：AI主动提示"这个问题之前遇到过，参考xxx"
- 触发：AI检测到当前操作与历史记录可能相关

### INDEX文件设计

每个模块目录都需要INDEX文件，作为"快速查找"的入口：

**需要INDEX的目录：**
- ADR/INDEX.md
- EXPERIENCES/INDEX.md
- SPECIAL-CASES/INDEX.md
- CHANGELOG/INDEX.md

**INDEX文件结构示例：**

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
- api: payment-api-error.md

## 最近更新
- 2026-05-09: payment-timeout.md (pitfalls)
- 2026-05-08: user-validation-flow.md (best-practices)

## 高价值标记
- payment-timeout.md (impact: high, referred: 5 times)
```

### 整体读取流程（4个Phase）

```
Phase 1：加载高层级指导（始终加载）
├── 开发者层：preferences.md + values.md
├── 团队层：conventions.md + team-values.md
├── 作用：作为AI的"默认设定"，影响所有生成和决策
├── 大小控制：合并压缩到3000 tokens以内

Phase 2：加载项目概览（启动时加载）
├── 项目层：OVERVIEW.md概览 + ADR INDEX + SPECIAL-CASES INDEX
├── 作用：让AI知道"项目有什么内容"，建立索引
├── 大小控制：2000 tokens以内

Phase 3：工作过程中按需加载（渐进式披露）
├── 功能开发 → 加载模块相关记录
├── Bug修复 → 加载pitfalls/debug
├── 重构 → 加载refactor + SPECIAL-CASES
├── 技术讨论 → 重点引用values/team-values

Phase 4：智能关联提示（AI主动）
├── 检测到修改某文件 → 检查是否有关联的SPECIAL-CASES
├── 检测到某问题 → 提示"这个问题之前遇到过，参考xxx"
├── 检测到决策讨论 → 提示"根据你的价值观倾向，建议考虑xxx"
```

### 智能关联机制

AI在工作过程中主动提示相关的历史记录：

**实现方式：**
- **标签系统** - 每条记录打标签（模块名、技术类型、问题类型）
- **关键词索引** - 建立"关键词→记录"的索引
- **模块关联** - 建立"模块→相关记录"的映射
- **代码引用** - 记录关联的代码文件路径，修改时自动提醒

**实际场景示例：**

```
开发者：我要修改支付模块的代码

AI：检测到支付模块有以下相关记录，请注意：
  - SPECIAL-CASES/temporary/payment-polling.md
    提示：支付回调使用轮询而非异步通知，这是临时方案
  - EXPERIENCES/pitfalls/payment-timeout.md
    提示：支付超时处理踩坑记录
  - ADR/decisions/2026-05-01-001-payment-provider-selection.md
    提示：支付渠道选择决策（为什么选当前渠道）

是否需要查看详细内容？
```

### load-context Skill

新增专门负责"读取"的Skill：

**用途：** 根据当前工作场景，加载相关的记录作为context

**调用方式：**
```
/load-context payment      # 加载支付模块相关记录
/load-context bug          # 加载Bug修复相关经验
/load-context refactor     # 加载重构相关经验和特殊处理
/load-context decision     # 加载历史决策参考
/load-context overview     # 加载项目概览（新人模式）
```

**自动触发时机：**
- 开发者说"我要开发xxx模块" → 自动加载模块相关
- 开发者说"有个bug" → 自动加载相关pitfalls/debug
- 开发者说"我想重构xxx" → 自动加载相关refactor + SPECIAL-CASES
- AI检测到正在修改某文件 → 检查是否有关联的SPECIAL-CASES

---

## 各模块详细设计

### 1. OVERVIEW.md - 项目全貌

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

## 开发约定
- 编码规范摘要
- 分支策略
- 部署流程

## 核心功能
- 已实现功能清单
- 重要功能说明
- 功能间依赖关系

## 关键决策索引
- 历史重要决策链接（指向 ADR/decisions/）
- 架构选择原因
- 放弃的方案及原因

## 当前状态
- 开发阶段（开发中/维护中/重构中）
- 活跃模块（当前正在开发的）
- 待办事项摘要

## 特殊处理索引
- 指向 SPECIAL-CASES/ 的关键条目
- 提醒新人注意的特殊逻辑

## 更新日志
- 最后更新时间
- 更新内容摘要
```

**触发更新：**
- AI 检测到新模块未提及
- 检测到架构调整
- 检测到新增重要功能
- 更新时间超过阈值（如1个月）
- 用户手动触发 `/update-overview`

**更新策略：** AI检测 + 提示确认 + 定期手动触发（混合）

---

### 2. PROGRESS.md - 当前进展追踪

**目的：** 记录项目当前状态和近期进展

**内容结构：**

```markdown
# 项目进展

## 当前状态
- 当前阶段
- 正在进行的任务
- 阻塞事项

## 今日进展
- 完成的任务列表
- 创建的 ADR 记录
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

**触发更新：**
- 每次 SessionEnd Hook 自动追加今日进展
- 每周自动生成周报摘要
- 每月自动生成月报摘要

---

### 3. ADR/decisions/ - 架构决策记录

**目的：** 记录架构决策及其背景、原因、结果

**严格定义：** 只记录架构层面的决策，不记录普通功能变更

**判断标准：**
- 是否涉及技术选型？（框架、库、工具）
- 是否涉及架构设计？（模块划分、数据流、接口设计）
- 是否涉及长期影响？（会影响后续开发的方向）
- 是否需要权衡多个方案？

**模板：**

```markdown
---
type: decision
date: YYYY-MM-DD
number: NNN
title: 决策标题
status: accepted | deprecated | superseded
supersedes: [被取代的决策编号，如有]
---

## 背景
描述决策的背景和问题。

## 考虑的方案
列出考虑过的方案及其优缺点。

### 方案A：xxx
优点：
缺点：

### 方案B：xxx
优点：
缺点：

### 方案C：xxx
优点：
缺点：

## 最终决策
选择哪个方案，理由是什么。

## 影响与后果
决策带来的影响（正面、负面、风险）。

## 相关变更
链接到相关的 CHANGELOG 记录。

## 备注
其他信息（如参考资料、讨论参与者等）。
```

---

### 4. REQUIREMENTS/ - 需求讨论

**目的：** 记录需求来源、讨论过程、最终结论

**模板：**

```markdown
---
type: requirement
date: YYYY-MM-DD
number: NNN
title: 需求标题
source: 用户反馈 | 客户需求 | 内部讨论 | 业务分析
priority: high | medium | low
status: pending | in-progress | completed | cancelled
---

## 需求来源
谁提出的需求，什么场景。

## 需求内容
具体需求描述。

## 讨论过程
记录讨论中的关键观点、疑问、限制条件。

### 观点A
...

### 观点B
...

## 最终结论
讨论结果和确定的方案。

## 设计理念/限制
重要的设计原则、约束条件、特殊要求。

## 相关决策/变更
链接到相关的 ADR decisions 或 CHANGELOG 记录。
```

---

### 5. CHANGELOG/ - 功能变更

**目的：** 记录功能性变更（新增、修改、删除）

**判断标准：**
- 新增功能模块
- 修改已有功能行为
- 删除功能
- API 变化
- 数据结构变化

**模板：**

```markdown
---
type: change
date: YYYY-MM-DD
number: NNN
title: 变更标题
status: implemented | planned | reverted
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
简要说明实现思路。

## 测试验证
如何验证变更正确性。

## 相关决策
链接到相关的 ADR decisions（如有决策讨论）。

## 备注
其他需要记录的信息。
```

---

### 6. EXPERIENCES/ - 经验积累

**目的：** 积累开发过程中的经验和技巧

**分类：**

| 子目录 | 内容 | 价值级别 |
|--------|------|----------|
| pitfalls/ | 踩坑经验 | 极高 |
| debug/ | 调试方法、排查思路 | 中 |
| best-practices/ | 最佳实践发现 | 极高 |
| tools/ | 工具使用技巧 | 中 |
| performance/ | 性能优化经验 | 高 |
| refactor/ | 重构经验、代码改进 | 高 |

**模板：**

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
踩坑的问题 / 最佳实践内容 / 工具技巧说明。

## 解决方案/方法
如何解决 / 如何应用。

## 关键要点
最重要的经验总结，一句话概括。

## 相关代码
涉及的代码文件或模块。

## 适用范围
这个经验适用于什么场景。

## 参考
相关链接或资料。
```

**同步策略：**
- AI 判断经验价值（根据影响级别、是否反复出现）
- 高价值经验提示"是否同步到团队层？"
- 确认后创建 PR 到团队 shared-experiences/

---

### 7. SPECIAL-CASES/ - 项目特异处理

**目的：** 记录因业务现状或历史原因的特殊处理逻辑

**为什么重要：**
- 新人/AI不理解原因，可能"优化"导致出错
- 临时方案容易被遗忘，变成永久问题
- 客户定制逻辑容易被误删或误改

**分类：**

| 子目录 | 内容 | 特点 |
|--------|------|------|
| legacy/ | 历史遗留处理 | 兼容老系统、历史数据 |
| business/ | 业务特殊性 | 客户特殊规则、流程差异 |
| temporary/ | 临时方案 | 标记待优化，防止遗忘 |
| environment/ | 环境限制 | 服务器配置、第三方限制 |
| custom/ | 客户定制 | 特定客户的定制功能 |

**模板：**

```markdown
---
type: special-case
category: legacy | business | temporary | environment | custom
date: YYYY-MM-DD
status: active | pending-optimize | resolved | deprecated
related_code: [涉及的文件/模块]
impact_level: high | medium | low
optimize_plan: [如果是临时方案，优化计划]
---

## 特殊处理描述
这段代码/逻辑做了什么特殊处理？

## 原因分析
为什么需要这样处理？

### 业务现状
...

### 历史原因
...

### 临时妥协
...

### 环境限制
...

## 影响范围
哪些模块/功能依赖这个特殊处理？如果改动会影响什么？

## 注意事项
修改时需要注意什么？不能做什么？

## 后续计划（如果是临时方案）
- 预计何时优化
- 优化方案是什么
- 依赖条件是什么

## 相关决策/变更
链接到相关的 ADR decisions 或 CHANGELOG 记录。
```

---

### 8. CONVENTIONS/ - 开发约定

**目的：** 记录项目的开发约定和规范

**内容：**

| 文件 | 内容 |
|------|------|
| code-style.md | 代码风格约定（缩进、命名、注释等） |
| naming.md | 命名约定（变量、函数、文件、目录等） |
| git-workflow.md | Git 工作流约定（分支命名、commit 规范、PR 流程） |

**来源：**
- 项目层约定（项目特有的）
- 团队层约定（从团队 conventions.md 继承）
- 项目层可覆盖团队层约定

---

### 9. FEEDBACK/ - 用户反馈

**目的：** 收集和记录用户反馈

**模板：**

```markdown
---
type: feedback
date: YYYY-MM-DD
source: 用户反馈 | 客户反馈 | 测试反馈 | 运维反馈
status: pending | processing | resolved | rejected
priority: high | medium | low
---

## 反馈内容
用户反馈的具体内容。

## 反馈来源
谁反馈的，什么场景。

## 分析
反馈问题的分析、原因。

## 处理方案
如何处理这个反馈。

## 处理结果
最终的处理结果。

## 相关记录
链接到相关的 REQUIREMENTS、ADR、CHANGELOG。
```

---

### 10. SUMMARY/ - 周期总结

**目的：** 自动生成周期性进展总结

**结构：**

```
SUMMARY/
├── daily/YYYY-MM-DD.md      # 日报
├── weekly/YYYY-WXX.md       # 周报
└── monthly/YYYY-MM.md       # 月报
```

**日报内容：**
- 今日完成任务列表
- 今日创建的记录（ADR、CHANGELOG等）
- 遗留问题
- 明日计划

**周报内容：**
- 本周主要成果
- 本周关键决策
- 本周遇到的问题和解决
- 本周经验总结
- 下周计划

**月报内容：**
- 本月功能交付情况
- 本月重要里程碑
- 本月经验沉淀
- 本月数据统计（新增记录数量等）
- 下月计划

---

### 11. REVIEW/ - 检查评审

**目的：** 保持记忆系统的质量和精简

**结构：**

```
REVIEW/
├── reviews/YYYY-MM-DD-review-NNN.md     # 定期评审记录
└── optimizations/YYYY-MM-DD-opt-NNN.md  # 精简优化记录
```

**评审记录模板：**

```markdown
---
type: review
date: YYYY-MM-DD
period: weekly | monthly | quarterly
---

## 评审范围
本次评审检查的内容范围。

## OVERVIEW 检查
- 是否准确反映当前状态
- 需要更新的内容

## ADR 检查
- 是否有过时的决策
- 是否有缺失的决策记录

## EXPERIENCES 检查
- 是否有低价值经验需要清理
- 是否有高价值经验需要同步到团队层

## SPECIAL-CASES 检查
- 临时方案是否已优化
- 是否有新的特殊处理未记录

## 发现的问题
评审发现的问题列表。

## 优化建议
建议的优化操作。

## 执行结果
评审后执行的操作。
```

**优化记录模板：**

```markdown
---
type: optimization
date: YYYY-MM-DD
trigger: periodic-review | manual | threshold-exceeded
---

## 优化内容
本次优化做了什么。

## 合并记录
合并的重复/相似记录列表。

## 删除记录
删除的过时/无价值记录列表。

## 归档记录
归档的已完成/废弃记录列表。

## 更新摘要
OVERVIEW 或 PROGRESS 的更新内容。

## 优化效果
优化后的变化（如记录数量减少等）。
```

---

### 12. CLAUDE.md - 项目规范

**目的：** 定义 AI Agent 在本项目的行为规范

**内容：**

```markdown
# 项目规范 - Sybermem 记忆系统

本项目使用 Sybermem 记忆系统，AI Agent 需遵循以下规范。

## 记忆系统结构

本项目记忆存储在 `.sybermem/` 目录，包含：
- OVERVIEW.md - 项目全貌
- PROGRESS.md - 当前进展
- ADR/decisions/ - 架构决策
- REQUIREMENTS/ - 需求讨论
- CHANGELOG/ - 功能变更
- EXPERIENCES/ - 经验积累
- SPECIAL-CASES/ - 特殊处理
- CONVENTIONS/ - 开发约定
- FEEDBACK/ - 用户反馈
- SUMMARY/ - 周期总结
- REVIEW/ - 检查评审

## 工作流程

### 1. 开始工作前
- 阅读 OVERVIEW.md 了解项目全貌
- 阅读 PROGRESS.md 了解当前进展
- 查阅相关目录的已有记录

### 2. 工作过程中
- 检测到架构决策时，提示创建 ADR 记录
- 检测到功能变更时，提示创建 CHANGELOG 记录
- 检测到踩坑/最佳实践时，提示创建 EXPERIENCE 记录
- 检测到特殊处理时，提示创建 SPECIAL-CASE 记录

### 3. 工作完成后
- 更新 PROGRESS.md 今日进展
- 检查是否需要更新 OVERVIEW.md

### 4. 会话结束时
- 自动生成今日进展摘要
- 检查是否有未记录的重要内容

## 记录触发判断

| 工作类型 | 触发条件 | 记录位置 |
|----------|----------|----------|
| 技术选型 | 涉及框架/库选择 | ADR/decisions/ |
| 架构设计 | 模块划分、数据流设计 | ADR/decisions/ |
| 功能新增 | 新增功能模块 | CHANGELOG/ |
| 功能修改 | 修改已有功能行为 | CHANGELOG/ |
| 踩坑经验 | 反复出现的问题 | EXPERIENCES/pitfalls/ |
| 最佳实践 | 发现更好的方法 | EXPERIENCES/best-practices/ |
| 特殊处理 | 因业务/历史原因的特殊逻辑 | SPECIAL-CASES/ |
| 用户反馈 | 收到用户反馈 | FEEDBACK/ |

## 例外情况

以下情况无需创建记录：
- 简单的代码格式调整
- 注释修改
- 配置文件微调（无功能影响）
- 简单问答（AI已知知识）
- 日常小修改（自动汇总到 PROGRESS）

## Skills 使用

可使用的 Skills：
- `/record-adr` - 创建 ADR 记录
- `/record-change` - 创建 CHANGELOG 记录
- `/record-experience` - 创建 EXPERIENCE 记录
- `/record-special` - 创建 SPECIAL-CASE 记录
- `/record-feedback` - 创建 FEEDBACK 记录
- `/update-progress` - 更新 PROGRESS.md
- `/update-overview` - 更新 OVERVIEW.md
- `/daily-summary` - 生成日报
- `/review-project` - 执行项目评审
- `/optimize-memory` - 执行记忆优化
```

---

## Skills 设计

### Skills 清单

| Skill | 用途 | 触发方式 |
|-------|------|----------|
| init-project | 新项目注入记忆系统 | 手动调用 |
| adapt-project | 旧项目适配记忆系统 | 手动调用 |
| record-adr | 创建架构决策记录 | 手动/Hook触发 |
| record-change | 创建功能变更记录 | 手动/Hook触发 |
| record-experience | 创建经验记录 | 手动/Hook触发 |
| record-special | 创建特殊处理记录 | 手动/Hook触发 |
| record-feedback | 创建用户反馈记录 | 手动调用 |
| update-progress | 更新项目进展 | 手动/SessionEnd |
| update-overview | 更新项目全貌 | 手动/AI检测 |
| daily-summary | 生成日报 | SessionEnd自动 |
| weekly-summary | 生成周报 | 定时/手动 |
| monthly-summary | 生成月报 | 定时/手动 |
| review-project | 执行项目评审 | 定时/手动 |
| optimize-memory | 执行记忆优化 | 评审后/手动 |
| sync-experience | 同步经验到团队层 | 手动确认 |

### 各 Skill 详细设计

#### init-project

**用途：** 为新项目注入记忆系统

**流程：**
1. 检查项目是否已有 `.sybermem/` 目录
2. 创建完整目录结构
3. 生成初始 OVERVIEW.md（基于项目名称和基本结构）
4. 创建空的各子目录
5. 生成 CLAUDE.md 项目规范
6. 提示用户补充 OVERVIEW.md 内容

#### adapt-project

**用途：** 为已有代码的项目适配记忆系统

**流程：**
1. 扫描项目结构（目录、文件）
2. 分析技术栈（依赖文件、代码特征）
3. 生成 OVERVIEW.md（基于扫描结果）
4. 分析 Git 历史，提取关键决策点
5. 创建历史 ADR 记录（追溯重要决策）
6. 检测特殊处理代码，创建 SPECIAL-CASES 记录
7. 生成 CLAUDE.md 项目规范

#### record-adr

**用途：** 创建架构决策记录

**流程：**
1. 收集决策信息（背景、方案、决策）
2. 检查 ADR/decisions/ 获取下一个编号
3. 使用模板生成文件内容
4. 创建文件 `ADR/decisions/YYYY-MM-DD-NNN-title.md`
5. 更新 OVERVIEW.md 的关键决策索引

#### record-experience

**用途：** 创建经验记录

**流程：**
1. 确定经验类型（pitfalls/debug/best-practices/tools/performance/refactor）
2. 收集经验内容
3. 检查目录获取下一个文件名
4. 创建记录文件
5. 判断价值级别，提示是否同步到团队层

#### update-overview

**用途：** 更新项目全貌

**触发条件：**
- 检测到新模块未提及
- 检测到架构调整
- 检测到新增重要功能
- 更新时间超过阈值
- 用户手动触发

**流程：**
1. 扫描当前项目状态
2. 对比现有 OVERVIEW.md
3. 识别需要更新的内容
4. 增量追加新内容（不删除已有内容）
5. 更新"最后更新时间"

#### review-project

**用途：** 定期检查记忆质量

**流程：**
1. 检查 OVERVIEW.md 是否准确
2. 检查 ADR 是否有缺失或过时
3. 检查 EXPERIENCES 是否有低价值内容
4. 检查 SPECIAL-CASES 临时方案状态
5. 生成评审报告
6. 提出优化建议

#### optimize-memory

**用途：** 精简优化记忆内容

**流程：**
1. 合并重复/相似记录
2. 删除过时/无价值记录
3. 归档已完成/废弃记录
4. 更新 OVERVIEW.md 摘要
5. 生成优化记录

#### sync-experience

**用途：** 同步高价值经验到团队层

**流程：**
1. 筛选高价值经验（impact=high）
2. 展示候选经验列表
3. 用户确认要同步的内容
4. 创建 Git 分支
5. 复制经验到团队 shared-experiences/
6. 创建 PR 等待团队审核

---

## Hooks 设计

### Hooks 清单

| Hook | 触发时机 | 用途 |
|------|----------|------|
| PostToolUse | Write/Edit/Bash 后 | 检测是否需要记录 |
| SessionEnd | 会话结束时 | 生成今日进展摘要 |
| PreCommit | Git commit 前 | 检查 ADR 记录完整性 |
| PrePR | PR 创建前 | 检查记忆系统状态 |

### PostToolUse Hook

**触发时机：** 每次 Write、Edit、Bash 工具调用后

**检测逻辑：**
1. 分析操作内容
2. 判断是否属于以下类别：
   - 架构决策相关（创建ADR）
   - 功能变更相关（创建CHANGELOG）
   - 踩坑/最佳实践（创建EXPERIENCE）
   - 特殊处理代码（创建SPECIAL-CASE）
3. 如果匹配，提示用户："检测到xxx，是否需要记录？"

**避免过度触发：**
- 简单格式调整不触发
- 注释修改不触发
- 配置微调不触发
- 同类操作短时间内只提示一次

### SessionEnd Hook

**触发时机：** 会话结束（用户退出或长时间无活动）

**执行逻辑：**
1. 收集本次会话的操作摘要
2. 检查是否有未记录的重要内容
3. 更新 PROGRESS.md 今日进展
4. 生成日报摘要（追加到 SUMMARY/daily/）
5. 提示用户确认

### PreCommit Hook

**触发时机：** Git commit 前

**检查逻辑：**
1. 分析 commit 内容
2. 检查是否有对应的记录：
   - 功能变更 → CHANGELOG
   - 架构调整 → ADR/decisions
3. 如果缺失，提示："本次 commit 涉及xxx，是否需要创建记录？"

### PrePR Hook

**触发时机：** PR 创建前

**检查逻辑：**
1. 检查 OVERVIEW.md 是否需要更新
2. 检查 PR 涉及的功能是否有 CHANGELOG
3. 检查 PR 涉及的架构是否有 ADR
4. 生成检查报告
5. 提示用户补充或确认

---

## 开发者层设计

### 存储位置

- `~/.claude/developer/` （本地）
- 或 `sybermem` 仓库的个人分支

### 目录结构

```
developer/
├── preferences.md           # 个人偏好
├── values.md                # 开发价值观
└── experiences/             # 个人经验积累
    ├── pitfalls/
    ├── best-practices/
    └── tools/
```

### preferences.md 模板

```markdown
# 开发者偏好

## 编辑器/IDE
- 主要使用：xxx
- 配置习惯：xxx

## 语言偏好
- 主要语言：xxx
- 风格偏好：xxx

## 工具偏好
- 包管理器：xxx
- 构建工具：xxx
- 测试框架：xxx

## 其他偏好
- 注释风格：xxx
- 变量命名：xxx
- 代码组织：xxx
```

### values.md 模板

```markdown
# 开发价值观

## 代码理念
- 代码质量标准
- 可维护性要求
- 性能优先级

## 架构理念
- 模块划分原则
- 接口设计原则
- 依赖管理原则

## 工作理念
- 文档态度
- 测试态度
- 重构态度
```

---

## 团队层设计

### 存储位置

- `sybermem` 仓库主分支
- 或团队的共享仓库

### 目录结构

```
team/
├── conventions.md           # 团队约定
├── team-values.md           # 团队价值观
└── shared-experiences/      # 共享经验
    ├── pitfalls/
    ├── best-practices/
    ├── debug/
    └── tools/
```

### conventions.md 模板

```markdown
# 团队约定

## 代码规范
- 代码风格标准
- 命名约定
- 注释规范

## Git 工作流
- 分支命名规范
- Commit 消息规范
- PR 流程规范

## 开发流程
- 需求评审流程
- 代码评审标准
- 发布流程

## 工具约定
- 统一使用的工具
- 配置规范
```

### 同步机制

- 高价值经验通过 PR 同步到团队层
- 团队约定变更需要团队评审
- 使用 Git 分支和 PR 流程管理

---

## 项目生命周期管理

### 新项目

**Skill：** init-project

**操作：**
1. 创建 `.sybermem/` 目录结构
2. 生成初始 OVERVIEW.md
3. 创建 CLAUDE.md 规范
4. 提示用户补充内容

### 旧项目

**Skill：** adapt-project

**操作：**
1. 扫描项目结构
2. 分析技术栈
3. 生成 OVERVIEW.md（基于现有代码）
4. 分析 Git 历史，追溯关键决策
5. 创建历史 ADR 记录
6. 检测特殊处理，创建 SPECIAL-CASES

### 持续更新

**Skill：** update-overview

**触发条件：**
- 新模块未提及
- 架构调整
- 新增重要功能
- 更新时间过期

**更新策略：** 增量追加，不删除已有内容

---

## 检查评审机制

### 定期评审

**频率：** 建议每周或每月

**Skill：** review-project

**检查内容：**
- OVERVIEW 准确性
- ADR 完整性和时效性
- EXPERIENCES 价值评估
- SPECIAL-CASES 状态检查

### 精简优化

**Skill：** optimize-memory

**优化操作：**
- 合并重复记录
- 删除低价值记录
- 归档过时记录
- 更新摘要

### 触发时机

- 定期评审后自动执行
- 记录数量超过阈值
- 用户手动触发

---

## 与 CC/OpenCode 的适配

### Claude Code 适配

**加载机制：**
- 启动时自动读取 `.sybermem/CLAUDE.md`
- CLAUDE.md 定义行为规范
- Skills 存放在 `.claude/skills/`

**Skills 目录：**

```
.claude/skills/
├── init-project/
│   └── SKILL.md
├── adapt-project/
│   └── SKILL.md
├── record-adr/
│   └── SKILL.md
│   └── templates/
│       └── decision.md
├── record-experience/
│   └── SKILL.md
│   └── templates/
│       └── experience.md
├── ... (其他 skills)
```

### OpenCode 适配

**加载机制：**
- 类似 Claude Code
- 可能需要适配不同的配置格式

**差异处理：**
- Skills 格式可能有差异
- Hooks 触发机制可能有差异
- 需要根据 OpenCode 文档适配

---

## 实现优先级

### Phase 1：核心基础设施

1. 项目层目录结构定义
2. CLAUDE.md 规范
3. OVERVIEW.md 模板
4. ADR/decisions 模板

### Phase 2：核心 Skills

1. init-project skill
2. adapt-project skill
3. record-adr skill
4. update-progress skill

### Phase 3：扩展 Skills

1. record-experience skill
2. record-special skill
3. update-overview skill
4. daily-summary skill

### Phase 4：Hooks 和自动化

1. PostToolUse Hook
2. SessionEnd Hook
3. PreCommit Hook

### Phase 5：检查评审

1. review-project skill
2. optimize-memory skill
3. PrePR Hook

### Phase 6：多层同步

1. 开发者层结构
2. 团队层结构
3. sync-experience skill

---

## 维护说明

- 所有记忆文件使用 Markdown 格式
- 使用 YAML frontmatter 存储元数据
- 文件命名：`YYYY-MM-DD-NNN-title.md`
- 编号在各目录内独立递增
- 记录创建后原则上不修改（除非状态变更）
- deprecated 或 superseded 状态的记录保留，不删除
- 模板文件可按项目需求定制调整