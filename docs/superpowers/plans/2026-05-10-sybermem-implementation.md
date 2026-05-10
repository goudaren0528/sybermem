# Sybermem 记忆系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建完整的 Sybermem 记忆系统，包括三层架构、项目注册中心、用户级注入机制、12个 Skills 和 3个 Hooks。

**Architecture:**
- sybermem 仓库作为记忆载体，包含开发者层、团队层、项目注册中心
- 项目层存储在各项目 `.sybermem/` 目录，独立不侵入用户原有文件
- 用户级注入通过追加 + 分隔标记合入 `~/.claude/CLAUDE.md`

**Tech Stack:** Markdown 文件、YAML frontmatter、Claude Code Skills、Claude Code Hooks

---

## 文件结构概览

### sybermem 仓库结构

```
D:/sybermem/
│
├── developer/                   # 开发者层
│   ├── preferences.md
│   ├── values.md
│   └── experiences/
│       ├── pitfalls/
│       ├── best-practices/
│       └── tools/
│
├── PROJECTS/                    # 项目注册中心
│   ├── INDEX.md
│   └── registered/
│
├── team/                        # 团队层
│   ├── conventions.md
│   ├── team-values.md
│   └── shared-experiences/
│       ├── pitfalls/
│       ├── best-practices/
│       ├── debug/
│       └── tools/
│
├── templates/                   # 模板文件
│   ├── overview-template.md
│   ├── decision-template.md
│   ├── requirement-template.md
│   ├── change-template.md
│   ├── experience-template.md
│   ├── special-case-template.md
│   └── progress-template.md
│
├── scripts/                     # 安装脚本
│   ├── install.sh
│   └── update.sh
│
├── skills/                      # Skills 源文件（复制到用户级）
│   ├── init-project/
│   ├── adapt-project/
│   ├── record-adr/
│   ├── record-change/
│   ├── record-experience/
│   ├── record-special/
│   ├── record-requirement/
│   ├── update-progress/
│   ├── update-overview/
│   ├── weekly-summary/
│   ├── monthly-summary/
│   ├── optimize-memory/
│   └── sync-experience/
│
├── hooks/                       # Hooks 源文件
│   ├── PostToolUse.md
│   ├── SessionEnd.md
│   └── PreCommit.md
│
├── README.md
├── INSTALL.md
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-09-sybermem-design.md  # 已存在
```

### 项目层结构模板

```
项目根目录/.sybermem/
│
├── OVERVIEW.md
├── PROGRESS.md
│
├── ADR/
│   ├── INDEX.md
│   └── decisions/
│
├── REQUIREMENTS/
│   ├── INDEX.md
│   └── *.md
│
├── CHANGELOG/
│   ├── INDEX.md
│   └── *.md
│
├── EXPERIENCES/
│   ├── INDEX.md
│   ├── pitfalls/
│   ├── debug/
│   ├── best-practices/
│   ├── tools/
│   ├── performance/
│   └── refactor/
│
├── SPECIAL-CASES/
│   ├── INDEX.md
│   ├── legacy/
│   ├── business/
│   ├── temporary/
│   ├── environment/
│   └── custom/
│
└── CLAUDE.md                   # 可选
```

---

## Phase 1：核心基础设施

### Task 1.1：创建 sybermem 仓库基础目录结构

**Files:**
- Create: `developer/` 目录
- Create: `developer/preferences.md`
- Create: `developer/values.md`
- Create: `developer/experiences/` 目录及子目录
- Create: `PROJECTS/` 目录
- Create: `PROJECTS/INDEX.md`
- Create: `PROJECTS/registered/` 目录
- Create: `team/` 目录及文件
- Create: `templates/` 目录

- [ ] **Step 1: 创建开发者层目录结构**

```bash
cd /d/sybermem
mkdir -p developer/experiences/pitfalls developer/experiences/best-practices developer/experiences/tools
mkdir -p PROJECTS/registered
mkdir -p team/shared-experiences/pitfalls team/shared-experiences/best-practices team/shared-experiences/debug team/shared-experiences/tools
mkdir -p templates
mkdir -p skills
mkdir -p hooks
mkdir -p scripts
```

- [ ] **Step 2: 创建 developer/preferences.md**

```markdown
# 开发者偏好

## 编辑器/IDE
- 主要使用：[请填写]
- 配置习惯：[请填写]

## 语言偏好
- 主要语言：[请填写]
- 风格偏好：[请填写]

## 工具偏好
- 包管理器：[请填写]
- 构建工具：[请填写]
- 测试框架：[请填写]

## 其他偏好
- 注释风格：[请填写]
- 变量命名：[请填写]
- 代码组织：[请填写]

---
_请根据个人习惯填写以上内容_
```

写入文件：`developer/preferences.md`

- [ ] **Step 3: 创建 developer/values.md**

```markdown
# 开发价值观

## 代码理念
- 代码质量标准：[请填写]
- 可维护性要求：[请填写]
- 性能优先级：[请填写]

## 架构理念
- 模块划分原则：[请填写]
- 接口设计原则：[请填写]
- 依赖管理原则：[请填写]

## 工作理念
- 文档态度：[请填写]
- 测试态度：[请填写]
- 重构态度：[请填写]

---
_请根据个人价值观填写以上内容_
```

写入文件：`developer/values.md`

- [ ] **Step 4: 创建 PROJECTS/INDEX.md**

```markdown
# 项目注册中心

记录开发者参与的所有项目，提供全局视角。

---

## 项目列表

| 项目名称 | 路径 | 技术栈 | 最后活动 | 状态 |
|----------|------|--------|----------|------|
<!-- 新项目注册时自动添加 -->

---

## 使用说明

- 执行 `/init-project` 或 `/adapt-project` 时自动注册项目
- 每个项目在 `registered/{project-name}/` 目录下有详细信息
- SessionEnd 时自动更新项目状态

---

_最后更新：2026-05-10_
```

写入文件：`PROJECTS/INDEX.md`

- [ ] **Step 5: 创建 team/conventions.md**

```markdown
# 团队约定

## 代码规范
- 代码风格标准：[请团队填写]
- 命名约定：[请团队填写]
- 注释规范：[请团队填写]

## Git 工作流
- 分支命名规范：[请团队填写]
- Commit 消息规范：[请团队填写]
- PR 流程规范：[请团队填写]

## 开发流程
- 需求评审流程：[请团队填写]
- 代码评审标准：[请团队填写]
- 发布流程：[请团队填写]

## 工具约定
- 统一使用的工具：[请团队填写]
- 配置规范：[请团队填写]

---
_团队成员请通过 PR 更新此文件_
```

写入文件：`team/conventions.md`

- [ ] **Step 6: 创建 team/team-values.md**

```markdown
# 团队价值观

## 代码理念
- 团队代码质量标准：[请团队填写]
- 可维护性要求：[请团队填写]

## 架构理念
- 团队架构原则：[请团队填写]
- 技术选型倾向：[请团队填写]

## 协作理念
- 沟通方式：[请团队填写]
- 文档态度：[请团队填写]
- 知识分享：[请团队填写]

---
_团队成员请通过 PR 更新此文件_
```

写入文件：`team/team-values.md`

- [ ] **Step 7: 验证目录结构**

```bash
cd /d/sybermem
find developer PROJECTS team templates -type f -o -type d | head -30
```

Expected: 显示所有创建的目录和文件

- [ ] **Step 8: 提交 Phase 1.1**

```bash
cd /d/sybermem
git add developer/ PROJECTS/ team/ templates/ skills/ hooks/ scripts/
git commit -m "feat: 创建 sybermem 仓库基础目录结构

- 开发者层：preferences.md、values.md、experiences/
- 项目注册中心：PROJECTS/INDEX.md、registered/
- 团队层：conventions.md、team-values.md、shared-experiences/
- 模板目录、Skills目录、Hooks目录、Scripts目录"
```

---

### Task 1.2：创建模板文件

**Files:**
- Create: `templates/overview-template.md`
- Create: `templates/decision-template.md`
- Create: `templates/requirement-template.md`
- Create: `templates/change-template.md`
- Create: `templates/experience-template.md`
- Create: `templates/special-case-template.md`
- Create: `templates/progress-template.md`
- Create: `templates/project-info-template.md`

- [ ] **Step 1: 创建 OVERVIEW 模板**

```markdown
# 项目全貌

## 项目定位
- 项目是什么：{{project_description}}
- 解决什么问题：{{problem_solved}}
- 目标用户：{{target_users}}

## 技术架构
- 技术栈列表：{{tech_stack}}
- 目录结构说明：{{directory_structure}}
- 关键模块关系：{{module_dependencies}}
- 数据流说明：{{data_flow}}

## 开发约定
- 编码规范摘要：{{code_style}}
- 分支策略：{{branch_strategy}}
- 命名约定：{{naming_convention}}
- Git 工作流：{{git_workflow}}
- 部署流程：{{deployment}}

## 核心功能
- 已实现功能清单：{{implemented_features}}
- 重要功能说明：{{key_features}}
- 功能间依赖关系：{{feature_dependencies}}

## 关键决策索引
<!-- AI 自动填充，指向 ADR/decisions/ -->

## 当前状态
- 开发阶段：{{development_stage}}
- 活跃模块：{{active_modules}}
- 待办事项摘要：{{pending_tasks}}

## 特殊处理提醒
<!-- AI 自动填充，指向 SPECIAL-CASES INDEX -->

## 更新日志
- 最后更新时间：{{last_updated}}
- 更新内容摘要：{{update_summary}}
```

写入文件：`templates/overview-template.md`

- [ ] **Step 2: 创建 ADR decision 模板**

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

### 方案A：{{option_a_name}}
优点：
{{option_a_pros}}
缺点：
{{option_a_cons}}

### 方案B：{{option_b_name}}
优点：
{{option_b_pros}}
缺点：
{{option_b_cons}}

### 方案C：{{option_c_name}}（如有）
优点：
{{option_c_pros}}
缺点：
{{option_c_cons}}

## 最终决策
{{decision}}
选择理由：{{reason}}

## 影响与后果
{{consequences}}

## 相关变更
<!-- 链接到 CHANGELOG -->

## 备注
{{notes}}
```

写入文件：`templates/decision-template.md`

- [ ] **Step 3: 创建 REQUIREMENT 模板**

```markdown
---
type: requirement
date: {{date}}
number: {{number}}
title: {{title}}
source: {{source}}
priority: {{priority}}
status: {{status}}
---

## 需求来源
{{requirement_source}}

## 需求内容
{{requirement_content}}

## 讨论过程

### 观点A
{{viewpoint_a}}

### 观点B
{{viewpoint_b}}

## 最终结论
{{conclusion}}

## 设计理念/限制
{{design_principles}}

## 相关决策/变更
<!-- 链接到 ADR 或 CHANGELOG -->
```

写入文件：`templates/requirement-template.md`

- [ ] **Step 4: 创建 CHANGELOG 模板**

```markdown
---
type: change
date: {{date}}
number: {{number}}
title: {{title}}
status: {{status}}
related_files: {{related_files}}
---

## 变更内容
{{change_content}}

## 变更原因
{{change_reason}}

## 影响范围
- 影响的模块/功能：{{affected_modules}}

## 实现方案
{{implementation}}

## 测试验证
{{test_verification}}

## 相关决策
<!-- 链接到 ADR（如有决策讨论） -->
```

写入文件：`templates/change-template.md`

- [ ] **Step 5: 创建 EXPERIENCE 模板**

```markdown
---
type: experience
category: {{category}}
date: {{date}}
title: {{title}}
tags: {{tags}}
impact: {{impact}}
---

## 场景描述
{{scenario}}

## 问题/内容
{{problem_or_content}}

## 解决方案/方法
{{solution}}

## 关键要点
{{key_points}}

## 相关代码
{{related_code}}

## 适用范围
{{applicable_scope}}
```

写入文件：`templates/experience-template.md`

- [ ] **Step 6: 创建 SPECIAL-CASE 模板**

```markdown
---
type: special-case
category: {{category}}
date: {{date}}
status: {{status}}
related_code: {{related_code}}
impact_level: {{impact_level}}
optimize_plan: {{optimize_plan}}
---

## 特殊处理描述
{{description}}

## 原因分析
{{reason}}

## 影响范围
{{affected_modules}}

## 注意事项
{{warnings}}

## 后续计划（如果是临时方案）
{{future_plan}}

## 相关决策/变更
<!-- 链接到 ADR 或 CHANGELOG -->
```

写入文件：`templates/special-case-template.md`

- [ ] **Step 7: 创建 PROGRESS 模板**

```markdown
# 项目进展

## 当前状态
- 当前阶段：{{current_stage}}
- 正在进行的任务：{{current_tasks}}
- 阻塞事项：{{blockers}}

## 今日进展
- 完成的任务列表：{{completed_tasks}}
- 创建的记录：{{created_records}}
- 遗留问题：{{remaining_issues}}

## 本周进展摘要
- 主要成果：{{weekly_results}}
- 关键决策：{{weekly_decisions}}
- 遇到的问题：{{weekly_issues}}

## 本月进展摘要
- 功能交付情况：{{monthly_deliveries}}
- 重要里程碑：{{monthly_milestones}}
- 经验总结：{{monthly_summary}}

## 下一步计划
- 待办事项：{{next_tasks}}
- 优先级排序：{{priority}}
```

写入文件：`templates/progress-template.md`

- [ ] **Step 8: 创建项目 INFO 模板（PROJECTS/registered 使用）**

```markdown
---
project_name: {{project_name}}
path: {{project_path}}
registered_date: {{registered_date}}
last_activity: {{last_activity}}
---

## 基本信息
- 项目名称：{{project_name}}
- 项目路径：{{project_path}}
- 技术栈摘要：{{tech_stack_summary}}
- 注册时间：{{registered_date}}

## 当前状态
- 开发阶段：{{development_stage}}
- 活跃模块：{{active_modules}}
- 最后活动时间：{{last_activity}}

## 关联配置
- sybermem 路径：{{sybermem_path}}
- 项目层目录：{{project_layer_path}}
```

写入文件：`templates/project-info-template.md`

- [ ] **Step 9: 验证模板文件**

```bash
cd /d/sybermem
ls -la templates/
```

Expected: 显示 7 个模板文件

- [ ] **Step 10: 提交 Task 1.2**

```bash
cd /d/sybermem
git add templates/
git commit -m "feat: 创建所有模板文件

- overview-template.md（含开发约定）
- decision-template.md（ADR）
- requirement-template.md
- change-template.md
- experience-template.md
- special-case-template.md
- progress-template.md
- project-info-template.md"
```

---

### Task 1.3：创建 INDEX 文件模板

**Files:**
- Create: `templates/adr-index-template.md`
- Create: `templates/experiences-index-template.md`
- Create: `templates/special-cases-index-template.md`
- Create: `templates/changelog-index-template.md`
- Create: `templates/requirements-index-template.md`

- [ ] **Step 1: 创建 ADR INDEX 模板**

```markdown
# ADR 决策索引

## 按时间排序
| 编号 | 日期 | 标题 | 状态 | 文件 |
|------|------|------|------|------|
<!-- 新记录在此添加 -->

---

## 按模块分类
<!-- AI 自动根据记录内容分类 -->

---

## 按标签分类
<!-- AI 自动提取标签 -->

---

## 高影响决策
<!-- impact=high 的决策 -->

---

_最后更新：{{last_updated}}_
```

写入文件：`templates/adr-index-template.md`

- [ ] **Step 2: 创建 EXPERIENCES INDEX 模板**

```markdown
# EXPERIENCES 经验索引

## 按模块分类
<!-- AI 自动根据 related_code 分类 -->

## 按类别分类
- pitfalls/：踩坑经验
- debug/：调试方法
- best-practices/：最佳实践
- tools/：工具技巧
- performance/：性能优化
- refactor/：重构经验

## 按标签分类
<!-- AI 自动提取标签 -->

## 最近更新
| 日期 | 标题 | 类别 | 文件 |
|------|------|------|------|
<!-- 新记录在此添加 -->

## 高价值标记
<!-- impact=high 的经验 -->

---

_最后更新：{{last_updated}}_
```

写入文件：`templates/experiences-index-template.md`

- [ ] **Step 3: 创建 SPECIAL-CASES INDEX 模板**

```markdown
# SPECIAL-CASES 特殊处理索引

## 按文件路径关联（关键）
<!-- AI 修改文件时检查此区域 -->
| 文件路径 | 特殊处理记录 | 影响级别 |
|----------|-------------|----------|
<!-- 新记录时自动添加路径关联 -->

---

## 按类别分类
- legacy/：历史遗留
- business/：业务特殊性
- temporary/：临时方案（待优化）
- environment/：环境限制
- custom/：客户定制

## 按模块分类
<!-- AI 自动分类 -->

## 高风险标记（AI 修改时必须加载）
<!-- impact_level=high 且 status=active -->

---

_最后更新：{{last_updated}}_
```

写入文件：`templates/special-cases-index-template.md`

- [ ] **Step 4: 创建 CHANGELOG INDEX 模板**

```markdown
# CHANGELOG 变更索引

## 按时间排序
| 编号 | 日期 | 标题 | 状态 | 影响模块 | 文件 |
|------|------|------|------|----------|------|
<!-- 新记录在此添加 -->

---

## 按模块分类
<!-- AI 自动分类 -->

---

_最后更新：{{last_updated}}_
```

写入文件：`templates/changelog-index-template.md`

- [ ] **Step 5: 创建 REQUIREMENTS INDEX 模板**

```markdown
# REQUIREMENTS 需求索引

## 按时间排序
| 编号 | 日期 | 标题 | 来源 | 优先级 | 状态 | 文件 |
|------|------|------|------|--------|------|------|
<!-- 新记录在此添加 -->

---

## 按状态分类
- pending：待处理
- in-progress：进行中
- completed：已完成
- cancelled：已取消

---

_最后更新：{{last_updated}}_
```

写入文件：`templates/requirements-index-template.md`

- [ ] **Step 6: 验证 INDEX 模板文件**

```bash
cd /d/sybermem
ls -la templates/*index*
```

Expected: 显示 5 个 INDEX 模板文件

- [ ] **Step 7: 提交 Task 1.3**

```bash
cd /d/sybermem
git add templates/*index*
git commit -m "feat: 创建 INDEX 文件模板

- adr-index-template.md
- experiences-index-template.md
- special-cases-index-template.md（含文件路径关联）
- changelog-index-template.md
- requirements-index-template.md"
```

---

### Task 1.4：创建 README 和 INSTALL 文档

**Files:**
- Create: `README.md`
- Create: `INSTALL.md`

- [ ] **Step 1: 创建 README.md**

```markdown
# Sybermem 记忆系统

一个可注入的记忆系统，为 Claude Code 和 OpenCode 提供项目认知能力。

## 核心功能

- **理解项目全貌** - 项目定位、架构、技术栈
- **追溯决策脉络** - 为什么做这个决定、考虑了哪些方案
- **追踪项目进展** - 当前状态、日/周/月进展
- **积累开发经验** - 踩坑经验、最佳实践、调试方法
- **记住特殊处理** - 因业务或历史原因的特殊逻辑
- **了解开发者偏好** - 个人编码风格、工具偏好、价值观
- **全局视角** - 了解参与的所有项目历史和沉淀

## 三层架构

```
sybermem/
├── developer/       # 开发者层（个人偏好、价值观）
├── PROJECTS/        # 项目注册中心（所有项目索引）
├── team/            # 团队层（团队约定、共享经验）
└── templates/       # 模板文件
```

项目层存储在各项目的 `.sybermem/` 目录。

## 快速开始

1. Fork 本仓库
2. 运行安装脚本：`./scripts/install.sh`
3. 在项目中执行 `/init-project` 或 `/adapt-project`

## 目录说明

| 目录 | 用途 | Git 同步 |
|------|------|----------|
| developer/ | 个人偏好和经验 | 用户私有，不提交上游 |
| PROJECTS/ | 项目注册中心 | 用户私有，不提交上游 |
| team/ | 团队约定和共享经验 | 团队共享，通过 PR 同步 |
| templates/ | 各类记录模板 | 团队共享 |

## 可用 Skills

- `/init-project` - 新项目注入记忆系统
- `/adapt-project` - 旧项目适配记忆系统
- `/record-adr` - 创建架构决策记录
- `/record-change` - 创建功能变更记录
- `/record-experience` - 创建经验记录
- `/record-special` - 创建特殊处理记录
- `/record-requirement` - 创建需求讨论记录
- `/update-progress` - 更新项目进展
- `/update-overview` - 更新项目全貌
- `/weekly-summary` - 生成周报
- `/monthly-summary` - 生成月报
- `/optimize-memory` - 执行记忆优化
- `/sync-experience` - 同步经验到团队层

## 设计文档

详见 `docs/superpowers/specs/2026-05-09-sybermem-design.md`

## 贡献

团队层内容（team/）可通过 PR 同步到上游。

## License

MIT
```

写入文件：`README.md`

- [ ] **Step 2: 创建 INSTALL.md**

```markdown
# Sybermem 安装指南

## 安装步骤

### 1. Fork 本仓库

在 GitHub 上 Fork sybermem 仓库到你的账户。

### 2. Clone 到本地

```bash
git clone https://github.com/{your-username}/sybermem.git
cd sybermem
```

### 3. 运行安装脚本

```bash
./scripts/install.sh
```

安装脚本会：
- 合入 `~/.claude/CLAUDE.md`（追加 + 分隔标记）
- 合入 `~/.claude/settings.json`
- 复制 Skills 到用户级目录

### 4. 配置开发者层

编辑 `developer/preferences.md` 和 `developer/values.md`，填写个人偏好和价值观。

### 5. 在项目中使用

在新项目中：
```
/init-project
```

在已有项目中：
```
/adapt-project
```

## 更新

运行更新脚本：
```bash
./scripts/update.sh
```

更新脚本会：
- 更新用户级 CLAUDE.md 中的 sybermem 区域
- 更新用户级 settings.json
- 同步 Skills

## 非侵入性保证

sybermem 不会删除或覆盖你的原有配置：
- 合入已有文件时，追加在末尾 + 分隔标记
- 项目层 `.sybermem/` 是新增目录，不修改项目原有文件

## 手动安装（可选）

如果脚本不可用，可手动配置：

### 合入 ~/.claude/CLAUDE.md

在你的 `~/.claude/CLAUDE.md` 末尾添加：

```markdown
---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 `sybermem update` 可更新        ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统

## 开发者偏好
{{请复制 developer/preferences.md 内容}}

## 开发价值观
{{请复制 developer/values.md 内容}}

## 团队约定
{{请复制 team/conventions.md 内容}}

## 可用 Skills
{{请列出 Skills}}
```

### 合入 ~/.claude/settings.json

在你的 `~/.claude/settings.json` 中添加：

```json
{
  "sybermem": {
    "path": "/path/to/your/sybermem",
    "version": "2.0.0"
  }
}
```

## 团队协作

团队成员：
- Fork 主仓库
- 修改 `team/` 目录内容
- 提交 PR 到主仓库

同步团队约定：
```bash
git pull upstream main
./scripts/update.sh
```
```

写入文件：`INSTALL.md`

- [ ] **Step 3: 提交 Task 1.4**

```bash
cd /d/sybermem
git add README.md INSTALL.md
git commit -m "feat: 创建 README 和 INSTALL 文档

- README.md：项目介绍、目录说明、Skills 列表
- INSTALL.md：安装步骤、非侵入性说明、团队协作"
```

---

## Phase 1 完成检查

- [ ] **验证 Phase 1 所有文件**

```bash
cd /d/sybermem
git log --oneline -10
ls -la developer/ PROJECTS/ team/ templates/
```

Expected: 显示所有提交和目录文件

---

## Phase 2：核心 Skills

### Task 2.1：创建 init-project Skill

**Files:**
- Create: `skills/init-project/SKILL.md`

- [ ] **Step 1: 创建 init-project/SKILL.md 目录**

```bash
cd /d/sybermem
mkdir -p skills/init-project
```

- [ ] **Step 2: 创建 init-project SKILL.md**

```markdown
---
name: init-project
description: 为新项目注入 Sybermem 记忆系统
---

# init-project Skill

为新项目创建 `.sybermem/` 目录结构，注入记忆系统。

## 使用方式

用户执行 `/init-project` 或 Claude 主动调用。

## 流程

### Step 1: 检查项目状态

检查当前项目是否已有 `.sybermem/` 目录：
- 如果已存在，提示用户并询问是否重新初始化
- 如果不存在，继续创建

### Step 2: 创建目录结构

创建完整的项目层目录结构：

```
.sybermem/
├── OVERVIEW.md
├── PROGRESS.md
├── ADR/
│   ├── INDEX.md
│   └── decisions/
├── REQUIREMENTS/
│   ├── INDEX.md
├── CHANGELOG/
│   ├── INDEX.md
├── EXPERIENCES/
│   ├── INDEX.md
│   ├── pitfalls/
│   ├── debug/
│   ├── best-practices/
│   ├── tools/
│   ├── performance/
│   └── refactor/
├── SPECIAL-CASES/
│   ├── INDEX.md
│   ├── legacy/
│   ├── business/
│   ├── temporary/
│   ├── environment/
│   └── custom/
```

### Step 3: 生成初始 OVERVIEW.md

基于项目名称和基本结构生成初始 OVERVIEW.md：
- 项目定位：根据项目名称推断
- 技术架构：根据目录结构分析
- 其他部分：提示用户补充

### Step 4: 生成 PROGRESS.md

使用 progress-template.md 创建初始 PROGRESS.md：
- 当前状态：初始化阶段
- 其他部分：待填充

### Step 5: 生成各模块 INDEX.md

使用对应的 INDEX 模板创建各模块 INDEX 文件：
- ADR/INDEX.md
- REQUIREMENTS/INDEX.md
- CHANGELOG/INDEX.md
- EXPERIENCES/INDEX.md
- SPECIAL-CASES/INDEX.md

### Step 6: 注册项目到 sybermem

在 sybermem 的 PROJECTS 中注册该项目：
1. 在 `PROJECTS/INDEX.md` 添加项目条目
2. 创建 `PROJECTS/registered/{project-name}/INFO.md`
3. 创建 `PROJECTS/registered/{project-name}/LINK.md`

### Step 7: 提示用户补充

提示用户：
- 补充 OVERVIEW.md 中的项目定位、技术架构等内容
- 补充 developer/preferences.md 和 developer/values.md

## 关键原则

- **不修改用户原有文件**：只创建新的 `.sybermem/` 目录
- **不修改项目根目录 CLAUDE.md**：项目层独立

## 模板引用

模板文件位置：`sybermem/templates/`

## 项目命名规范

项目名称使用目录名或用户指定的名称，格式：
- 小写字母
- 连字符分隔单词
- 例：`my-project`, `payment-service`
```

写入文件：`skills/init-project/SKILL.md`

- [ ] **Step 3: 验证 Skill 创建**

```bash
cat skills/init-project/SKILL.md
```

Expected: 显示 SKILL.md 完整内容

- [ ] **Step 4: 提交 Task 2.1**

```bash
git add skills/init-project/
git commit -m "feat: 创建 init-project Skill

为新项目注入 Sybermem 记忆系统：
- 创建 .sybermem/ 目录结构
- 生成初始 OVERVIEW.md 和 PROGRESS.md
- 生成各模块 INDEX.md
- 注册项目到 PROJECTS/"
```

---

### Task 2.2：创建 adapt-project Skill

**Files:**
- Create: `skills/adapt-project/SKILL.md`

- [ ] **Step 1: 创建 adapt-project/SKILL.md 目录**

```bash
mkdir -p skills/adapt-project
```

- [ ] **Step 2: 创建 adapt-project SKILL.md**

```markdown
---
name: adapt-project
description: 为已有代码的项目适配 Sybermem 记忆系统
---

# adapt-project Skill

为已有代码的项目创建记忆系统，并分析现有代码生成初始记录。

## 使用方式

用户执行 `/adapt-project` 或 Claude 主动调用。

## 流程

### Step 1: 检查项目状态

检查当前项目是否已有 `.sybermem/` 目录。

### Step 2: 扫描项目结构

扫描项目目录结构，分析：
- 目录层级
- 关键目录（src/, lib/, app/, tests/ 等）
- 配置文件（package.json, requirements.txt, pom.xml 等）
- 文件类型分布

使用 Glob 工具：
```
Glob pattern: "**/*.{js,ts,py,java,go,rs,json,yaml,yml,toml}"
```

### Step 3: 分析技术栈

根据配置文件分析技术栈：

| 配置文件 | 技术栈提示 |
|----------|-----------|
| package.json | Node.js/JavaScript/TypeScript |
| requirements.txt / pyproject.toml | Python |
| pom.xml / build.gradle | Java |
| go.mod | Go |
| Cargo.toml | Rust |

读取配置文件内容，提取依赖信息。

### Step 4: 生成 OVERVIEW.md

基于扫描和分析结果生成 OVERVIEW.md：
- 项目定位：根据目录名和配置推断
- 技术架构：根据技术栈和目录结构
- 目录结构说明：根据扫描结果
- 开发约定：推断或提示用户补充

### Step 5: 分析 Git 历史

分析 Git 历史，追溯关键决策点：
```bash
git log --oneline --all -50
git log --format="%h %s" --grep="feat:" --grep="add:" --grep="implement:" -20
```

提取：
- 重要功能添加记录
- 技术选型记录
- 架构变更记录

### Step 6: 创建历史 ADR 记录

根据 Git 历史，为重要决策创建 ADR 记录：
- 技术选型决策
- 架构变更决策
- 重要功能决策

格式：`ADR/decisions/YYYY-MM-DD-NNN-title.md`

### Step 7: 检测特殊处理代码

检测项目中可能存在的特殊处理代码：

扫描关键词：
```
Grep pattern: "hack|TODO|FIXME|workaround|temporary|legacy|special|custom|例外|临时"
```

为发现的特殊处理创建 SPECIAL-CASES 记录。

### Step 8: 创建目录结构和 INDEX

创建完整目录结构和各模块 INDEX.md（同 init-project）。

### Step 9: 注册项目到 sybermem

在 sybermem 的 PROJECTS 中注册该项目。

### Step 10: 提示用户确认

提示用户：
- 确认生成的 OVERVIEW.md 内容
- 确认创建的 ADR 记录
- 确认 SPECIAL-CASES 记录
- 补充遗漏内容

## 分析技巧

### 推断技术栈
```
if exists("package.json"):
  if "typescript" in dependencies:
    tech_stack = "TypeScript + Node.js"
  else:
    tech_stack = "JavaScript + Node.js"
```

### 推断项目类型
```
if exists("src/api/") or exists("app/api/"):
  project_type = "Web API Service"
elif exists("src/pages/") or exists("app/pages/"):
  project_type = "Web Application"
elif exists("src/components/"):
  project_type = "UI Library/Component"
```

## 关键原则

- **不修改用户原有文件**
- **追溯历史决策**：帮助理解项目演进
- **检测特殊处理**：避免误删重要逻辑
```

写入文件：`skills/adapt-project/SKILL.md`

- [ ] **Step 3: 提交 Task 2.2**

```bash
git add skills/adapt-project/
git commit -m "feat: 创建 adapt-project Skill

为已有代码的项目适配记忆系统：
- 扫描项目结构和分析技术栈
- 分析 Git 历史追溯决策
- 检测特殊处理代码
- 创建历史 ADR 和 SPECIAL-CASES 记录"
```

---

### Task 2.3：创建 record-adr Skill

**Files:**
- Create: `skills/record-adr/SKILL.md`

- [ ] **Step 1: 创建目录**

```bash
mkdir -p skills/record-adr
```

- [ ] **Step 2: 创建 SKILL.md**

```markdown
---
name: record-adr
description: 创建架构决策记录（ADR）
---

# record-adr Skill

创建架构决策记录，记录技术选型、架构设计等重要决策。

## 使用方式

- 用户执行 `/record-adr`
- PreCommit Hook 触发（检测到架构相关变更）

## 判断标准

ADR 只记录**架构层面**的决策：

| 符合 ADR | 不符合 ADR |
|----------|-----------|
| 技术选型（框架、库、工具） | 普通功能开发 |
| 架构设计（模块划分、数据流） | UI 样式调整 |
| 接口设计（API 规范） | 配置修改 |
| 长期影响决策 | 临时方案 |
| 多方案权衡 | Bug 修复 |

## 流程

### Step 1: 确认决策类型

询问或判断是否属于架构决策：
- 是否涉及技术选型？
- 是否涉及架构设计？
- 是否有长期影响？

如果不是，建议使用 `/record-change`。

### Step 2: 收集决策信息

收集必要信息：
- **背景**：决策的背景和问题
- **考虑的方案**：列出方案及优缺点
- **最终决策**：选择哪个方案、理由
- **影响与后果**：决策带来的影响

### Step 3: 获取下一个编号

检查 `ADR/decisions/` 目录：
```bash
ls .sybermem/ADR/decisions/ | grep "^YYYY-MM-DD" | tail -1
```

从现有最大编号 +1，或从 001 开始。

### Step 4: 使用模板生成文件

使用 `templates/decision-template.md`：
- date: 当前日期
- number: 下一个编号
- title: 决策标题
- status: accepted（新决策默认）
- 填充收集的内容

### Step 5: 创建文件

创建文件：`.sybermem/ADR/decisions/YYYY-MM-DD-NNN-title.md`

### Step 6: 更新 ADR INDEX

在 `.sybermem/ADR/INDEX.md` 添加新条目：
```markdown
| {{number}} | {{date}} | {{title}} | accepted | [链接](decisions/{{filename}}) |
```

### Step 7: 更新 OVERVIEW 关键决策索引

在 OVERVIEW.md 的"关键决策索引"部分添加链接。

### Step 8: 提示用户确认

提示用户确认记录内容。

## 标题命名建议

- 选择 xxx 作为 xx 框架
- 采用 xxx 架构模式
- 将 xx 模块迁移到 xxx
- 使用 xxx 作为数据存储方案

## 模板引用

模板位置：`sybermem/templates/decision-template.md`

## 必填字段

- 背景
- 考虑的方案（至少 2 个）
- 最终决策 + 理由
```

写入文件：`skills/record-adr/SKILL.md`

- [ ] **Step 3: 提交 Task 2.3**

```bash
git add skills/record-adr/
git commit -m "feat: 创建 record-adr Skill

创建架构决策记录：
- 判断是否属于架构决策
- 收集决策信息（背景、方案、决策）
- 自动编号、使用模板生成
- 更新 ADR INDEX 和 OVERVIEW"
```

---

### Task 2.4：创建 record-change Skill

**Files:**
- Create: `skills/record-change/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/record-change
```

```markdown
---
name: record-change
description: 创建功能变更记录（CHANGELOG）
---

# record-change Skill

创建功能变更记录，记录新增、修改、删除功能。

## 使用方式

- 用户执行 `/record-change`
- PreCommit Hook 触发（检测到功能变更）

## 判断标准

记录**功能性变更**：

| 符合 CHANGELOG | 不符合 |
|----------------|--------|
| 新增功能模块 | 简单格式调整 |
| 修改已有功能行为 | 注释修改 |
| 删除功能 | 配置微调 |
| API 变化 | Bug 修复（使用 EXPERIENCE） |
| 数据结构变化 | 重构（使用 EXPERIENCE/refactor） |

## 流程

### Step 1: 确认变更类型

判断是否属于功能变更。

### Step 2: 收集变更信息

收集必要信息：
- **变更内容**：做了什么变更
- **变更原因**：为什么需要
- **影响范围**：影响哪些模块/功能
- **相关文件**：涉及的文件路径

### Step 3: 获取下一个编号

检查 `CHANGELOG/` 目录，获取下一个编号。

### Step 4: 使用模板生成文件

使用 `templates/change-template.md`。

### Step 5: 创建文件

创建文件：`.sybermem/CHANGELOG/YYYY-MM-DD-NNN-title.md`

### Step 6: 更新 CHANGELOG INDEX

在 `.sybermem/CHANGELOG/INDEX.md` 添加新条目。

### Step 7: 提示用户确认

## 标题命名建议

- 添加 xxx 功能
- 修改 xxx 处理逻辑
- 删除 xxx 功能
- 更新 xxx API 接口

## 与 ADR 的区别

- ADR：架构决策（为什么选择这个方案）
- CHANGELOG：功能变更（做了什么变更）

如果变更涉及决策讨论，链接到相关 ADR。
```

写入文件：`skills/record-change/SKILL.md`

- [ ] **Step 2: 提交 Task 2.4**

```bash
git add skills/record-change/
git commit -m "feat: 创建 record-change Skill

创建功能变更记录：
- 判断是否属于功能变更
- 收集变更信息
- 自动编号、使用模板
- 更新 CHANGELOG INDEX"
```

---

### Task 2.5：创建 record-experience Skill

**Files:**
- Create: `skills/record-experience/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/record-experience
```

```markdown
---
name: record-experience
description: 创建开发经验记录
---

# record-experience Skill

创建开发经验记录，积累踩坑、最佳实践、调试方法等。

## 使用方式

- 用户执行 `/record-experience`
- PostToolUse Hook 触发（检测到踩坑或发现最佳实践）
- 用户主动分享经验时触发

## 经验类型

| 类别 | 目录 | 内容 |
|------|------|------|
| pitfalls | EXPERIENCES/pitfalls/ | 踩坑经验、反复出现的问题 |
| debug | EXPERIENCES/debug/ | 调试方法、排查思路 |
| best-practices | EXPERIENCES/best-practices/ | 最佳实践发现 |
| tools | EXPERIENCES/tools/ | 工具使用技巧 |
| performance | EXPERIENCES/performance/ | 性能优化经验 |
| refactor | EXPERIENCES/refactor/ | 重构经验、代码改进 |

## 流程

### Step 1: 确定经验类型

询问或判断经验类型：
- 踩坑？→ pitfalls
- 调试方法？→ debug
- 更好的做法？→ best-practices
- 工具技巧？→ tools
- 性能优化？→ performance
- 重构经验？→ refactor

### Step 2: 收集经验信息

收集必要信息：
- **场景描述**：什么情况下遇到
- **问题/内容**：踩坑问题 / 最佳实践内容
- **解决方案**：如何解决 / 如何应用
- **关键要点**：一句话概括
- **相关代码**：涉及的文件或模块
- **影响级别**：high / medium / low

### Step 3: 自动生成文件名

格式：`YYYY-MM-DD-title.md`
- 不使用编号，使用标题
- 标题转为小写连字符格式

### Step 4: 使用模板生成文件

使用 `templates/experience-template.md`。

### Step 5: 创建文件

创建文件：`.sybermem/EXPERIENCES/{category}/YYYY-MM-DD-title.md`

### Step 6: 更新 EXPERIENCES INDEX

在 `.sybermem/EXPERIENCES/INDEX.md` 添加条目：
- 按模块分类（如果有 related_code）
- 按标签分类（根据 tags）
- 最近更新列表

### Step 7: 判断是否同步团队层

如果 impact=high，提示用户：
> "这是一条高价值经验，是否同步到团队层？（执行 `/sync-experience`）"

## 标签建议

自动提取或手动添加标签：
- 模块名（payment, user, api）
- 技术类型（timeout, validation, auth）
- 问题类型（error, performance, security）

## 高价值判断

| 影响级别 | 触发条件 |
|----------|----------|
| high | 反复出现 3+ 次、影响核心功能、解决复杂问题 |
| medium | 常见问题、有用技巧 |
| low | 小技巧、临时问题 |
```

写入文件：`skills/record-experience/SKILL.md`

- [ ] **Step 2: 提交 Task 2.5**

```bash
git add skills/record-experience/
git commit -m "feat: 创建 record-experience Skill

创建开发经验记录：
- 支持 6 种经验类型
- 收集经验信息
- 自动生成文件名、使用模板
- 更新 EXPERIENCES INDEX
- 高价值经验提示同步团队层"
```

---

### Task 2.6：创建 record-special Skill

**Files:**
- Create: `skills/record-special/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/record-special
```

```markdown
---
name: record-special
description: 创建特殊处理记录（SPECIAL-CASES）
---

# record-special Skill

创建特殊处理记录，记录因业务现状或历史原因的特殊逻辑。

## 使用方式

- 用户执行 `/record-special`
- adapt-project 时自动检测
- 代码中发现特殊处理时提示

## 为什么重要

- 新人/AI 不理解原因，可能"优化"导致出错
- 临时方案容易被遗忘
- 重构时需要特别注意

## 特殊处理类型

| 类别 | 目录 | 内容 |
|------|------|------|
| legacy | SPECIAL-CASES/legacy/ | 历史遗留、兼容老系统 |
| business | SPECIAL-CASES/business/ | 业务特殊性、客户特殊规则 |
| temporary | SPECIAL-CASES/temporary/ | 临时方案（标记待优化） |
| environment | SPECIAL-CASES/environment/ | 环境限制、服务器配置 |
| custom | SPECIAL-CASES/custom/ | 客户定制功能 |

## 流程

### Step 1: 确定特殊处理类型

询问或判断类型。

### Step 2: 收集特殊处理信息

收集必要信息：
- **特殊处理描述**：做了什么特殊处理
- **原因分析**：为什么需要（业务现状/历史原因/临时妥协/环境限制）
- **影响范围**：哪些模块依赖
- **相关代码**：涉及的文件路径（关键！）
- **影响级别**：high / medium / low
- **注意事项**：修改时需要注意什么

如果是临时方案：
- **后续计划**：预计何时优化、优化方案

### Step 3: 生成文件名

格式：`YYYY-MM-DD-title.md`

### Step 4: 使用模板生成文件

使用 `templates/special-case-template.md`。

### Step 5: 创建文件

创建文件：`.sybermem/SPECIAL-CASES/{category}/YYYY-MM-DD-title.md`

### Step 6: 更新 SPECIAL-CASES INDEX（关键）

在 `.sybermem/SPECIAL-CASES/INDEX.md` 添加：

**按文件路径关联（最重要）：**
```markdown
| {{related_code}} | {{filename}} | {{impact_level}} |
```

AI 修改文件时会检查此区域，自动加载相关记录。

**按类别分类：**

**高风险标记（如果 impact=high）：**
```markdown
- {{filename}} (impact: high, related_files: [{{related_code}}])
```

### Step 7: 提示用户确认

提示用户：
- 确认相关代码路径是否正确
- 如果是临时方案，提醒标记待优化

## related_code 格式

可以是：
- 单个文件：`src/payment/order-service.ts`
- 多个文件：`src/payment/*.ts`
- 目录：`src/payment/`

文件路径关联是 AI 自动检测的关键。

## 重构提醒

当 AI 检测到用户要重构或删除相关代码时：
- 自动加载 SPECIAL-CASES 记录
- 提醒注意事项
- 避免误删特殊逻辑
```

写入文件：`skills/record-special/SKILL.md`

- [ ] **Step 2: 提交 Task 2.6**

```bash
git add skills/record-special/
git commit -m "feat: 创建 record-special Skill

创建特殊处理记录：
- 支持 5 种特殊处理类型
- 收集特殊处理信息和原因
- 关键：记录相关代码路径
- 更新 SPECIAL-CASES INDEX（含文件路径关联）
- 重构时自动提醒"
```

---

### Task 2.7：创建 update-progress Skill

**Files:**
- Create: `skills/update-progress/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/update-progress
```

```markdown
---
name: update-progress
description: 更新项目进展（PROGRESS.md）
---

# update-progress Skill

更新项目进展记录，记录今日任务和进展。

## 使用方式

- 用户执行 `/update-progress`
- SessionEnd Hook 自动触发
- 工作过程中手动调用

## 流程

### Step 1: 收集本次进展

收集本次会话/任务的信息：
- 完成的任务列表
- 创建的记录（ADR、CHANGELOG、EXPERIENCE 等）
- 遇到的问题
- 遗留事项

### Step 2: 读取现有 PROGRESS.md

读取 `.sybermem/PROGRESS.md` 内容。

### Step 3: 更新今日进展

在"今日进展"部分追加：
```markdown
- 完成任务：xxx, xxx
- 创建记录：ADR/xxx, CHANGELOG/xxx
- 遗留问题：xxx
```

如果当天已有记录，追加更新。

### Step 4: 检查是否需要更新本周/本月摘要

如果是一周开始（周一）：
- 重置本周进展摘要
- 追加上周总结链接

如果是一月开始：
- 重置本月进展摘要
- 追加上月总结链接

### Step 5: 更新当前状态

更新"当前状态"部分：
- 当前阶段
- 正在进行的任务
- 阻塞事项

### Step 6: 写入更新后的 PROGRESS.md

写入文件：`.sybermem/PROGRESS.md`

### Step 7: 更新 sybermem PROJECTS 状态

在 sybermem 的 `PROJECTS/registered/{project-name}/STATUS.md` 更新：
- 最后活动时间
- 活跃模块

## 自动触发时机

SessionEnd Hook：
- 会话结束时自动执行
- 收集本次会话操作摘要
- 自动更新 PROGRESS.md

## 今日进展格式

```markdown
## 今日进展（YYYY-MM-DD）
- 完成任务：
  - xxx
  - xxx
- 创建记录：
  - ADR/decisions/YYYY-MM-DD-NNN-xxx.md
  - CHANGELOG/YYYY-MM-DD-NNN-xxx.md
- 遗留问题：
  - xxx
```
```

写入文件：`skills/update-progress/SKILL.md`

- [ ] **Step 2: 提交 Task 2.7**

```bash
git add skills/update-progress/
git commit -m "feat: 创建 update-progress Skill

更新项目进展：
- 收集本次进展信息
- 更新今日进展部分
- 检查本周/本月摘要更新
- SessionEnd Hook 自动触发
- 更新 sybermem PROJECTS 状态"
```

---

## Phase 2 完成检查

- [ ] **验证 Phase 2 所有 Skills**

```bash
cd /d/sybermem
ls -la skills/
find skills -name "SKILL.md"
```

Expected: 显示 7 个 Skill 目录和 SKILL.md 文件

---

## Phase 3：扩展 Skills

### Task 3.1：创建 record-requirement Skill

**Files:**
- Create: `skills/record-requirement/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/record-requirement
```

```markdown
---
name: record-requirement
description: 创建需求讨论记录
---

# record-requirement Skill

创建需求讨论记录，记录需求来源、讨论过程、最终结论。

## 使用方式

- 用户执行 `/record-requirement`
- 收到需求时主动调用

## 流程

### Step 1: 收集需求信息

收集必要信息：
- **需求来源**：用户反馈 / 客户需求 / 内部讨论
- **需求内容**：具体需求描述
- **优先级**：high / medium / low

### Step 2: 记录讨论过程

如果有讨论过程，记录：
- 关键观点
- 疑问和限制条件
- 不同方案

### Step 3: 获取下一个编号

检查 `REQUIREMENTS/` 目录。

### Step 4: 使用模板生成文件

使用 `templates/requirement-template.md`。

### Step 5: 创建文件

创建文件：`.sybermem/REQUIREMENTS/YYYY-MM-DD-NNN-title.md`

### Step 6: 更新 REQUIREMENTS INDEX

在 `.sybermem/REQUIREMENTS/INDEX.md` 添加条目。

### Step 7: 链接相关决策/变更

需求完成后，链接到相关的 ADR 或 CHANGELOG。

## 状态追踪

| 状态 | 说明 |
|------|------|
| pending | 待处理 |
| in-progress | 进行中 |
| completed | 已完成 |
| cancelled | 已取消 |

状态变更时更新文件 frontmatter 和 INDEX。

## 与其他记录的关系

需求 → 讨论 → 决策（ADR） → 实施（CHANGELOG）

REQUIREMENTS 记录需求讨论过程，ADR 记录决策，CHANGELOG 记录实施。
```

写入文件：`skills/record-requirement/SKILL.md`

- [ ] **Step 2: 提交 Task 3.1**

```bash
git add skills/record-requirement/
git commit -m "feat: 创建 record-requirement Skill

创建需求讨论记录：
- 记录需求来源、讨论过程
- 状态追踪（pending/in-progress/completed/cancelled）
- 链接相关 ADR 或 CHANGELOG"
```

---

### Task 3.2：创建 update-overview Skill

**Files:**
- Create: `skills/update-overview/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/update-overview
```

```markdown
---
name: update-overview
description: 更新项目全貌（OVERVIEW.md）
---

# update-overview Skill

更新项目全貌，保持 OVERVIEW.md 与项目实际状态同步。

## 使用方式

- 用户执行 `/update-overview`
- AI 检测到需要更新时触发
- 定期触发（如一个月未更新）

## 触发条件

| 条件 | 说明 |
|------|------|
| 新模块未提及 | 新增模块目录，OVERVIEW 未记录 |
| 架构调整 | 技术栈或架构变化 |
| 新增重要功能 | 核心功能变化 |
| 更新时间过期 | 超过阈值（如 1 个月） |
| 用户手动触发 | 用户主动请求 |

## 流程

### Step 1: 扫描当前项目状态

扫描项目结构和技术栈：
- 目录结构变化
- 新增配置文件
- 新增模块

### Step 2: 对比现有 OVERVIEW.md

读取现有 OVERVIEW.md，对比：
- 技术架构部分是否准确
- 核心功能部分是否完整
- 目录结构说明是否更新

### Step 3: 识别需要更新的内容

列出需要更新的部分：
- 新增模块 → 技术架构部分
- 新增功能 → 核心功能部分
- 架构变化 → 技术栈列表

### Step 4: 增量追加新内容

**原则：不删除已有内容，只追加新内容**

追加方式：
```markdown
## 技术架构（更新于 YYYY-MM-DD）
原内容...
新增模块：xxx
```

### Step 5: 更新"最后更新时间"

在 OVERVIEW.md 末尾更新：
```markdown
## 更新日志
- 最后更新时间：YYYY-MM-DD
- 更新内容：新增 xxx 模块描述
```

### Step 6: 更新关键决策索引

检查是否有新 ADR，更新关键决策索引部分。

### Step 7: 更新特殊处理提醒

检查是否有新高风险 SPECIAL-CASES，更新特殊处理提醒部分。

### Step 8: 提示用户确认

提示用户确认更新内容。

## 自动检测实现

AI 在以下情况下主动判断是否需要更新：
- 创建新模块目录时
- 新增重要 ADR 时
- 技术栈变化时

判断逻辑：
```
if (new_directory not in OVERVIEW):
  suggest_update_overview()
```

## 增量更新原则

- **不删除**：保留原有内容
- **追加补充**：添加新信息
- **标记更新**：注明更新时间和内容
```

写入文件：`skills/update-overview/SKILL.md`

- [ ] **Step 2: 提交 Task 3.2**

```bash
git add skills/update-overview/
git commit -m "feat: 创建 update-overview Skill

更新项目全貌：
- 触发条件：新模块、架构调整、功能变化、时间过期
- 扫描对比现有内容
- 增量追加新内容（不删除原有）
- 更新索引和时间戳"
```

---

### Task 3.3：创建 weekly-summary Skill

**Files:**
- Create: `skills/weekly-summary/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/weekly-summary
```

```markdown
---
name: weekly-summary
description: 生成周报
---

# weekly-summary Skill

生成本周进展周报，汇总本周工作和成果。

## 使用方式

- 用户执行 `/weekly-summary`
- 定时触发（每周结束）
- 手动调用

## 流程

### Step 1: 读取 PROGRESS.md

读取 `.sybermem/PROGRESS.md`，获取本周进展信息。

### Step 2: 读取本周创建的记录

扫描本周创建的记录文件：
- ADR/decisions/
- CHANGELOG/
- EXPERIENCES/
- SPECIAL-CASES/
- REQUIREMENTS/

```bash
find .sybermem -name "YYYY-MM-DD*.md" | grep "本周日期范围"
```

### Step 3: 汇总本周成果

汇总内容：
- 主要成果：完成的任务列表
- 关键决策：本周 ADR 记录
- 遇到的问题：踩坑记录
- 经验总结：最佳实践发现

### Step 4: 生成周报内容

生成周报：
```markdown
# 本周进展周报（YYYY-WXX）

## 主要成果
- xxx
- xxx

## 关键决策
- ADR/xxx：xxx决策

## 遇到的问题
- EXPERIENCES/pitfalls/xxx：xxx问题

## 经验总结
- EXPERIENCES/best-practices/xxx：xxx实践

## 下周计划
- 待办事项
```

### Step 5: 输出周报

输出方式：
- 显示给用户确认
- 可选：保存到指定位置

### Step 6: 更新 PROGRESS 本周摘要

更新 PROGRESS.md 的"本周进展摘要"部分。

## 周报格式

周报为动态生成，不持久存储。用户可选择保存。

## 周报用途

- 个人总结
- 团队汇报
- 项目状态追踪
```

写入文件：`skills/weekly-summary/SKILL.md`

- [ ] **Step 2: 提交 Task 3.3**

```bash
git add skills/weekly-summary/
git commit -m "feat: 创建 weekly-summary Skill

生成周报：
- 读取 PROGRESS 和本周记录
- 汇总成果、决策、问题、经验
- 动态生成，不持久存储
- 更新 PROGRESS 本周摘要"
```

---

### Task 3.4：创建 monthly-summary Skill

**Files:**
- Create: `skills/monthly-summary/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/monthly-summary
```

```markdown
---
name: monthly-summary
description: 生成月报
---

# monthly-summary Skill

生成本月进展月报，汇总本月工作和里程碑。

## 使用方式

- 用户执行 `/monthly-summary`
- 定时触发（每月结束）
- 手动调用

## 流程

### Step 1: 读取 PROGRESS.md

读取本月进展信息。

### Step 2: 读取本月创建的记录

扫描本月所有记录。

### Step 3: 汇总本月成果

汇总内容：
- 功能交付情况：CHANGELOG 记录
- 重要里程碑：重要 ADR 或功能
- 经验沉淀：本月 EXPERIENCES
- 数据统计：新增记录数量

### Step 4: 生成月报内容

```markdown
# 本月进展月报（YYYY-MM）

## 功能交付情况
- 新增功能：xxx（CHANGELOG）
- 修改功能：xxx

## 重要里程碑
- 完成架构重构（ADR/xxx）
- 上线 xxx 功能

## 经验沉淀
- 踩坑经验：xx 条
- 最佳实践：xx 条

## 数据统计
- 新增 ADR：xx 条
- 新增 CHANGELOG：xx 条
- 新增 EXPERIENCES：xx 条

## 下月计划
- 待办事项
```

### Step 5: 输出月报

显示给用户，可选保存。

### Step 6: 更新 PROGRESS 本月摘要

更新 PROGRESS.md 的"本月进展摘要"部分。

## 月报用途

- 项目总结
- 团队汇报
- 绩效评估参考
```

写入文件：`skills/monthly-summary/SKILL.md`

- [ ] **Step 2: 提交 Task 3.4**

```bash
git add skills/monthly-summary/
git commit -m "feat: 创建 monthly-summary Skill

生成月报：
- 读取本月进展和记录
- 汇总功能交付、里程碑、经验沉淀
- 数据统计
- 更新 PROGRESS 本月摘要"
```

---

## Phase 3 完成检查

- [ ] **验证 Phase 3 所有 Skills**

```bash
cd /d/sybermem
find skills -name "SKILL.md" | wc -l
```

Expected: 显示 11 个 Skill（Phase 2: 7个 + Phase 3: 4个）

---

## Phase 4：Hooks 和自动化

### Task 4.1：创建 PostToolUse Hook

**Files:**
- Create: `hooks/PostToolUse.md`

- [ ] **Step 1: 创建 PostToolUse.md**

```markdown
---
name: PostToolUse
trigger: Edit, Write, Bash 工具调用后
---

# PostToolUse Hook

在 Edit、Write、Bash 工具调用后，AI 内部判断是否需要加载相关记忆。

## 核心原则

**用户无感知：** 所有加载都是 AI 内部执行，不打断用户。

用户只体验"AI 给出了更好的建议"，不感知加载过程。

## 触发时机

每次以下工具调用后：
- Edit：修改代码文件
- Write：创建新文件
- Bash：执行命令

## 执行逻辑

### 情况 1：Edit/Write 修改代码文件

```
if (tool == "Edit" || tool == "Write"):
  file_path = extract_file_path(operation)

  # 1. 检查 SPECIAL-CASES INDEX 的文件路径关联
  related_cases = check_special_cases_index(file_path)

  if related_cases:
    # AI 内部读取，作为上下文
    read(related_cases)
    # 不向用户提示，融入任务执行

  # 2. 检查 EXPERIENCES INDEX 的模块关联
  module = detect_module_from_path(file_path)
  related_experiences = check_experiences_index(module)

  if related_experiences:
    read(related_experiences)
```

### 情况 2：Bash 执行测试/构建失败

```
if (tool == "Bash" && result == "failure"):
  error_type = analyze_error(result)

  # 检查 EXPERIENCES/pitfalls + debug
  related_experiences = check_experiences_index(error_type)

  if related_experiences:
    read(related_experiences)
    # AI 参考历史踩坑经验调整修复策略
```

### 情况 3：读取代码发现问题

```
if (AI 分析代码发现潜在问题):
  problem_type = classify_problem(performance? logic? security?)

  # 加载对应类型 EXPERIENCES
  related_experiences = check_experiences_index(problem_type)

  if related_experiences:
    read(related_experiences)
```

### 情况 4：处理技术决策类任务

```
if (AI 判断这是"技术决策类任务"):
  # 加载 ADR + REQUIREMENTS + values/team-values
  read(".sybermem/ADR/INDEX.md")
  read(".sybermem/REQUIREMENTS/INDEX.md")
  # values/team-values 已在用户级 CLAUDE.md 中加载
```

## 检查 INDEX 文件方法

### SPECIAL-CASES INDEX 检查

```markdown
## 按文件路径关联
| 文件路径 | 特殊处理记录 | 影响级别 |
|----------|-------------|----------|
- src/payment/order-service.ts → temporary/payment-polling.md
- src/user/auth.ts → legacy/user-session-compat.md
```

匹配逻辑：
- 精确匹配：file_path == related_code
- 通配符匹配：file_path matches related_code pattern
- 目录匹配：file_path in related_code directory

### EXPERIENCES INDEX 检查

```markdown
## 按模块分类
- payment/
  - pitfalls: payment-timeout.md
  - debug: payment-log-analysis.md
```

匹配逻辑：
- 根据 file_path 推断模块名
- 查找模块对应的经验记录

## 实现方式

Hook 不直接执行读取，而是：
1. 判断是否需要加载
2. 如果需要，调用 Read 工具读取相关记录
3. 读取结果作为 AI 内部上下文
4. 继续执行任务

**关键：** 读取融入任务流程，不单独提示用户。

## 避免过度加载

控制策略：
- 每次加载量 < 3000 tokens
- 优先加载高影响级别（impact=high）记录
- 同类操作短时间内不重复加载
```

写入文件：`hooks/PostToolUse.md`

- [ ] **Step 2: 提交 Task 4.1**

```bash
git add hooks/PostToolUse.md
git commit -m "feat: 创建 PostToolUse Hook

AI 内部判断与加载记忆：
- Edit/Write 后检查 SPECIAL-CASES 和 EXPERIENCES
- Bash 失败后参考踩坑经验
- 用户无感知，融入任务执行"
```

---

### Task 4.2：创建 SessionEnd Hook

**Files:**
- Create: `hooks/SessionEnd.md`

- [ ] **Step 1: 创建 SessionEnd.md**

```markdown
---
name: SessionEnd
trigger: 会话结束时
---

# SessionEnd Hook

会话结束时，更新项目进展并生成日报摘要。

## 触发时机

会话结束：
- 用户退出
- 长时间无活动
- 用户主动触发结束

## 执行逻辑

### Step 1: 收集本次会话操作摘要

收集本次会话的操作：
- 完成的任务（Edit/Write 操作摘要）
- 创建的记录（扫描 .sybermem/ 目录变化）
- 遇到的问题

### Step 2: 检查是否有未记录的重要内容

判断是否需要创建记录：
- 功能变更 → 提示创建 CHANGELOG
- 技术决策 → 提示创建 ADR
- 踩坑经验 → 提示创建 EXPERIENCE
- 特殊处理 → 提示创建 SPECIAL-CASE

### Step 3: 更新 PROGRESS.md 今日进展

调用 update-progress Skill：
- 追加今日进展
- 更新当前状态

### Step 4: 生成日报摘要

动态生成日报（不持久存储）：
```markdown
# 今日进展摘要（YYYY-MM-DD）

## 完成任务
- xxx
- xxx

## 创建记录
- ADR/xxx
- CHANGELOG/xxx

## 遗留问题
- xxx

## 明日计划建议
- xxx
```

### Step 5: 更新 sybermem PROJECTS 状态

更新 `PROJECTS/registered/{project-name}/STATUS.md`：
- 最后活动时间
- 活跃模块
- 当前状态

### Step 6: 提示用户确认

提示用户：
- 显示日报摘要
- 确认是否需要创建遗漏记录
- 确认明日计划

## 自动执行流程

```
SessionEnd Hook:
├── collect_session_summary()
├── check_unrecorded_content()
│   └── if (功能变更): suggest("/record-change")
│   └── if (技术决策): suggest("/record-adr")
│   └── if (踩坑): suggest("/record-experience")
├── call(update-progress)
├── generate_daily_summary()
├── update_projects_status()
└── prompt_user_confirm()
```

## 日报用途

- 个人回顾
- 项目追踪
- 团队协作参考

日报为动态生成，不持久存储到 `.sybermem/` 目录。
```

写入文件：`hooks/SessionEnd.md`

- [ ] **Step 2: 提交 Task 4.2**

```bash
git add hooks/SessionEnd.md
git commit -m "feat: 创建 SessionEnd Hook

会话结束时执行：
- 收集本次会话摘要
- 检查未记录内容并提示
- 更新 PROGRESS.md
- 生成日报摘要
- 更新 PROJECTS 状态"
```

---

### Task 4.3：创建 PreCommit Hook

**Files:**
- Create: `hooks/PreCommit.md`

- [ ] **Step 1: 创建 PreCommit.md**

```markdown
---
name: PreCommit
trigger: Git commit 前
---

# PreCommit Hook

Git commit 前，检查是否有对应的 ADR 或 CHANGELOG 记录。

## 触发时机

Git commit 执行前。

## 检查逻辑

### Step 1: 分析 commit 内容

分析即将 commit 的变更：
- 查看变更文件列表
- 分析变更类型

```bash
git diff --cached --name-only
git diff --cached --stat
```

### Step 2: 判断变更类型

根据变更内容判断：

| 变变类型 | 应有记录 |
|----------|----------|
| 架构调整、技术选型 | ADR/decisions/ |
| 功能新增、修改、删除 | CHANGELOG/ |
| 配置调整、格式修改 | 无需记录 |
| Bug 修复 | EXPERIENCES/pitfalls/（可选） |

判断方法：
- 新增配置文件（package.json, tsconfig.json）→ ADR
- 新增模块目录 → ADR 或 CHANGELOG
- 新增功能文件 → CHANGELOG
- 修改功能实现 → CHANGELOG
- 删除功能 → CHANGELOG

### Step 3: 检查是否有对应记录

检查对应目录是否有相关记录：
```bash
ls .sybermem/ADR/decisions/ | grep "{{date}}"
ls .sybermem/CHANGELOG/ | grep "{{date}}"
```

### Step 4: 提示用户

如果缺失记录，提示：
> "本次 commit 涉及 xxx 变更，是否需要创建记录？
> - 架构变更 → 执行 `/record-adr`
> - 功能变更 → 执行 `/record-change`"

如果已有记录或无需记录，继续 commit。

### Step 5: 用户选择

用户选择：
- 创建记录 → 调用对应 Skill
- 不创建 → 继续 commit（标记为日常小修改）
- 取消 commit → 返回处理

## 避免过度提示

不触发的情况：
- 简单格式调整
- 注释修改
- 配置微调（无功能影响）
- .sybermem/ 目录本身的变更

## 例外情况

以下情况允许跳过记录：
- 用户明确表示"日常小修改"
- WIP commit（标记为 work-in-progress）
- 配置调整

## 实现方式

Hook 通过 Git pre-commit 钩子或 Claude Code Hook 机制实现。

```bash
# Git pre-commit 钩子示例
#!/bin/bash
# 检查是否有对应的 ADR 或 CHANGELOG
# 如缺失，提示用户
```
```

写入文件：`hooks/PreCommit.md`

- [ ] **Step 2: 提交 Task 4.3**

```bash
git add hooks/PreCommit.md
git commit -m "feat: 创建 PreCommit Hook

Git commit 前检查：
- 分析 commit 内容判断变更类型
- 检查是否有对应 ADR 或 CHANGELOG
- 缺失时提示用户创建记录
- 避免过度提示（格式调整、注释等不触发）"
```

---

## Phase 4 完成检查

- [ ] **验证 Phase 4 所有 Hooks**

```bash
cd /d/sybermem
ls -la hooks/
```

Expected: 显示 3 个 Hook 文件

---

## Phase 5：记忆优化

### Task 5.1：创建 optimize-memory Skill

**Files:**
- Create: `skills/optimize-memory/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/optimize-memory
```

```markdown
---
name: optimize-memory
description: 执行记忆优化，精简和整理记忆内容
---

# optimize-memory Skill

精简优化记忆内容，保持记忆系统质量。

## 使用方式

- 用户执行 `/optimize-memory`
- 定期触发（记录数量超过阈值）
- review-project 后执行

## 触发条件

| 条件 | 说明 |
|------|------|
| 记录数量超过阈值 | 如 ADR > 50 条 |
| 定期触发 | 每月执行一次 |
| review-project 后 | 评审发现需要优化 |
| 用户手动触发 | 用户主动请求 |

## 流程

### Step 1: 检查各目录记录数量

统计各目录记录数量：
- ADR/decisions/
- CHANGELOG/
- EXPERIENCES/
- SPECIAL-CASES/
- REQUIREMENTS/

```bash
find .sybermem/ADR/decisions -name "*.md" | wc -l
find .sybermem/CHANGELOG -name "*.md" | wc -l
...
```

### Step 2: 检查记录质量和价值

检查内容：
- **重复记录**：相同内容的记录
- **过时记录**：status=deprecated 或 superseded
- **低价值记录**：impact=low 且长时间未引用
- **已完成记录**：REQUIREMENTS 中 status=completed

### Step 3: 生成优化建议

生成优化建议列表：

| 操作类型 | 条件 | 示例 |
|----------|------|------|
| 合并 | 重复/相似内容 | ADR-005 和 ADR-008 内容相似 |
| 删除 | 低价值 + 未引用 | EXPERIENCES/tools/xxx 无引用 |
| 归档 | 已完成/废弃 | REQUIREMENTS-xxx 已 completed |
| 更新 INDEX | 删除记录后 | 更新 INDEX 文件 |

### Step 4: 用户确认优化方案

展示优化建议，用户确认：
- 同意合并 → 执行合并
- 同意删除 → 执行删除
- 同意归档 → 执行归档
- 暂不执行 → 保留现状

### Step 5: 执行优化操作

执行用户确认的操作：

**合并操作：**
- 选择主记录，保留
- 其他记录内容合并到主记录
- 删除其他记录文件
- 更新 INDEX

**删除操作：**
- 删除记录文件
- 更新 INDEX
- 可选：备份删除内容到归档目录

**归档操作：**
- 移动到 archive/ 目录（可选创建）
- 更新原 INDEX 标记为已归档

### Step 6: 更新 OVERVIEW 摘要

更新 OVERVIEW.md 的关键决策索引和特殊处理提醒部分。

### Step 7: 生成优化记录

生成优化执行记录：
```markdown
# 记忆优化记录（YYYY-MM-DD）

## 合并记录
- ADR-005 + ADR-008 → ADR-005（合并原因）

## 删除记录
- EXPERIENCES/tools/xxx（低价值）

## 归档记录
- REQUIREMENTS-xxx → archive/（已完成）

## 优化效果
- 记录数量：ADR 50 → 48
- 总记录数：xxx → xxx
```

## 保留原则

不删除的内容：
- 高影响级别记录（impact=high）
- 近期创建记录（最近 1 个月）
- 状态为 accepted 的 ADR
- 状态为 active 的 SPECIAL-CASES

## 安全策略

- 删除前备份（可选）
- 提示用户确认每项操作
- 可回滚（git 可恢复）

## 定期触发建议

建议每月执行一次 optimize-memory，保持记忆系统精简高效。
```

写入文件：`skills/optimize-memory/SKILL.md`

- [ ] **Step 2: 提交 Task 5.1**

```bash
git add skills/optimize-memory/
git commit -m "feat: 创建 optimize-memory Skill

执行记忆优化：
- 检查记录数量和质量
- 生成优化建议（合并、删除、归档）
- 用户确认后执行
- 更新 INDEX 和 OVERVIEW
- 安全策略：不删除高价值记录，删除前备份"
```

---

## Phase 5 完成检查

- [ ] **验证 Phase 5**

```bash
cd /d/sybermem
ls skills/optimize-memory/SKILL.md
```

---

## Phase 6：多层同步与项目注册中心

### Task 6.1：创建 sync-experience Skill

**Files:**
- Create: `skills/sync-experience/SKILL.md`

- [ ] **Step 1: 创建目录和 SKILL.md**

```bash
mkdir -p skills/sync-experience
```

```markdown
---
name: sync-experience
description: 同步高价值经验到团队层
---

# sync-experience Skill

将高价值经验从项目层同步到团队层，供团队共享。

## 使用方式

- 用户执行 `/sync-experience`
- record-experience 时提示（impact=high）
- 用户主动分享经验

## 流程

### Step 1: 筛选高价值经验

筛选条件：
- impact=high
- 适用于多项目
- 非项目特异

扫描项目层 EXPERIENCES：
```bash
find .sybermem/EXPERIENCES -name "*.md" -exec grep "impact: high" {} \;
```

### Step 2: 展示候选经验列表

展示候选经验：
```markdown
# 可同步到团队层的经验

| 经验标题 | 类别 | 适用范围 | 文件 |
|----------|------|----------|------|
| payment-timeout | pitfalls | 多项目 | EXPERIENCES/pitfalls/payment-timeout.md |
| git-commit-best-practice | best-practices | 所有项目 | EXPERIENCES/best-practices/git-commit.md |
```

### Step 3: 用户确认要同步的内容

用户选择：
- 全部同步
- 选择性同步（指定某几条）
- 不同步

### Step 4: 复制经验到团队层

复制选中的经验到 `sybermem/team/shared-experiences/`：

对应目录：
- pitfalls → team/shared-experiences/pitfalls/
- best-practices → team/shared-experiences/best-practices/
- debug → team/shared-experiences/debug/
- tools → team/shared-experiences/tools/

### Step 5: 创建 PR 等待团队审核

创建 Git 分支和 PR：

```bash
cd /path/to/sybermem
git checkout -b sync-experience-YYYY-MM-DD
git add team/shared-experiences/
git commit -m "feat: 同步高价值经验到团队层

- EXPERIENCES/pitfalls/payment-timeout.md → shared-experiences/pitfalls/
- EXPERIENCES/best-practices/git-commit.md → shared-experiences/best-practices/"
git push origin sync-experience-YYYY-MM-DD
# 创建 PR
```

### Step 6: 团队审核

团队成员审核 PR：
- 确认经验价值
- 确认适用范围
- 合并 PR

### Step 7: 更新 sybermem

PR 合并后：
- 拉取更新：`git pull upstream main`
- 运行更新脚本：`./scripts/update.sh`

团队层经验自动注入到所有项目。

## 同步判断标准

| 同步 | 不同步 |
|------|--------|
| impact=high | impact=low/medium |
| 通用经验（适用多项目） | 项目特异经验 |
| 团队受益 | 仅个人受益 |

## 经验修改建议

同步前可修改：
- 移除项目特定内容
- 调整适用范围描述
- 增加团队适用说明

## 团队层与项目层的关系

- 团队层：团队共享，所有项目可用
- 项目层：项目私有，仅当前项目使用

团队层经验通过用户级 CLAUDE.md 注入，所有项目启动时自动加载。
```

写入文件：`skills/sync-experience/SKILL.md`

- [ ] **Step 2: 提交 Task 6.1**

```bash
git add skills/sync-experience/
git commit -m "feat: 创建 sync-experience Skill

同步高价值经验到团队层：
- 筛选 impact=high 的经验
- 用户确认后复制到 team/shared-experiences/
- 创建 PR 等待团队审核
- 合并后更新 sybermem"
```

---

### Task 6.2：创建安装脚本

**Files:**
- Create: `scripts/install.sh`

- [ ] **Step 1: 创建 install.sh**

```bash
#!/bin/bash

# Sybermem 安装脚本
# 合入用户级配置，不破坏用户原有内容

SYBERMEM_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_CONFIG="$HOME/.claude"
CLAUDE_MD="$CLAUDE_CONFIG/CLAUDE.md"
SETTINGS_JSON="$CLAUDE_CONFIG/settings.json"
SKILLS_DIR="$CLAUDE_CONFIG/skills"

echo "=== Sybermem 安装脚本 ==="
echo "sybermem 路径: $SYBERMEM_PATH"

# Step 1: 检查并创建 ~/.claude/ 目录
if [ ! -d "$CLAUDE_CONFIG" ]; then
    echo "创建 ~/.claude/ 目录..."
    mkdir -p "$CLAUDE_CONFIG"
fi

# Step 2: 创建 skills 目录
if [ ! -d "$SKILLS_DIR" ]; then
    echo "创建 ~/.claude/skills/ 目录..."
    mkdir -p "$SKILLS_DIR"
fi

# Step 3: 合入 CLAUDE.md（追加 + 分隔标记）
if [ -f "$CLAUDE_MD" ]; then
    echo "检测到已有 ~/.claude/CLAUDE.md，追加 sybermem 内容..."

    # 检查是否已存在 sybermem 标记
    if grep -q "Sybermem 记忆系统注入" "$CLAUDE_MD"; then
        echo "sybermem 已注入，跳过"
    else
        # 追加分隔标记和内容
        cat >> "$CLAUDE_MD" << 'EOF'

---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 `sybermem update` 可更新        ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统

## 开发者偏好
请填写 sybermem/developer/preferences.md

## 开发价值观
请填写 sybermem/developer/values.md

## 团队约定
参考 sybermem/team/conventions.md

## 团队价值观
参考 sybermem/team/team-values.md

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

EOF
        echo "CLAUDE.md 已追加 sybermem 内容"
    fi
else
    echo "创建 ~/.claude/CLAUDE.md..."
    cat > "$CLAUDE_MD" << 'EOF'
# Claude Code 用户配置

---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 `sybermem update` 可更新        ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统

## 开发者偏好
请填写 sybermem/developer/preferences.md

## 开发价值观
请填写 sybermem/developer/values.md

## 团队约定
参考 sybermem/team/conventions.md

## 团队价值观
参考 sybermem/team/team-values.md

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

EOF
fi

# Step 4: 合入 settings.json
if [ -f "$SETTINGS_JSON" ]; then
    echo "检测到已有 ~/.claude/settings.json..."

    # 检查是否已存在 sybermem 配置
    if grep -q '"sybermem"' "$SETTINGS_JSON"; then
        echo "settings.json 已包含 sybermem 配置，跳过"
    else
        # 使用 jq 合入配置（如果 jq 可用）
        if command -v jq &> /dev/null; then
            jq '. + {"sybermem": {"path": "'"$SYBERMEM_PATH"'", "version": "2.0.0"}}' "$SETTINGS_JSON" > "$SETTINGS_JSON.tmp"
            mv "$SETTINGS_JSON.tmp" "$SETTINGS_JSON"
            echo "settings.json 已合入 sybermem 配置"
        else
            echo "提示：请手动在 settings.json 中添加以下配置："
            echo '  "sybermem": {"path": "'"$SYBERMEM_PATH"'", "version": "2.0.0"}'
        fi
    fi
else
    echo "创建 ~/.claude/settings.json..."
    cat > "$SETTINGS_JSON" << EOF
{
  "sybermem": {
    "path": "$SYBERMEM_PATH",
    "version": "2.0.0"
  }
}
EOF
fi

# Step 5: 复制 Skills 到用户级目录
echo "复制 Skills 到 ~/.claude/skills/..."
cp -r "$SYBERMEM_PATH/skills/"* "$SKILLS_DIR/" 2>/dev/null || true

echo ""
echo "=== 安装完成 ==="
echo ""
echo "下一步："
echo "1. 编辑 sybermem/developer/preferences.md 和 values.md"
echo "2. 在项目中执行 /init-project 或 /adapt-project"
echo ""
echo "非侵入性说明："
echo "- 已有 CLAUDE.md：追加在末尾 + 分隔标记"
echo "- 已有 settings.json：合入 sybermem 配置"
echo "- 用户原有内容完整保留"
```

写入文件：`scripts/install.sh`

- [ ] **Step 2: 设置脚本执行权限**

```bash
chmod +x scripts/install.sh
```

- [ ] **Step 3: 提交 Task 6.2**

```bash
git add scripts/install.sh
git commit -m "feat: 创建 install.sh 安装脚本

合入用户级配置：
- 检测已有文件，追加 + 分隔标记
- 不破坏用户原有内容
- 复制 Skills 到 ~/.claude/skills/
- 支持 jq 自动合入 settings.json"
```

---

### Task 6.3：创建更新脚本

**Files:**
- Create: `scripts/update.sh`

- [ ] **Step 1: 创建 update.sh**

```bash
#!/bin/bash

# Sybermem 更新脚本
# 更新用户级配置中的 sybermem 区域

SYBERMEM_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_CONFIG="$HOME/.claude"
CLAUDE_MD="$CLAUDE_CONFIG/CLAUDE.md"
SETTINGS_JSON="$CLAUDE_CONFIG/settings.json"
SKILLS_DIR="$CLAUDE_CONFIG/skills"

echo "=== Sybermem 更新脚本 ==="

# Step 1: 更新 CLAUDE.md 中的 sybermem 区域
if [ -f "$CLAUDE_MD" ]; then
    if grep -q "Sybermem 记忆系统注入" "$CLAUDE_MD"; then
        echo "更新 CLAUDE.md 中的 sybermem 区域..."

        # 提取用户原有内容（sybermem 标记之前）
        USER_CONTENT=$(sed -n '1,/^---$/p' "$CLAUDE_MD" | sed '$d')

        # 生成新的 sybermem 内容
        SYBERMEM_CONTENT="
---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 \`sybermem update\` 可更新      ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统

## 开发者偏好
$(cat "$SYBERMEM_PATH/developer/preferences.md" 2>/dev/null || echo "请填写")

## 开发价值观
$(cat "$SYBERMEM_PATH/developer/values.md" 2>/dev/null || echo "请填写")

## 团队约定
$(cat "$SYBERMEM_PATH/team/conventions.md" 2>/dev/null || echo "参考文件")

## 团队价值观
$(cat "$SYBERMEM_PATH/team/team-values.md" 2>/dev/null || echo "参考文件")

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
"

        # 合并写入
        echo "$USER_CONTENT$SYBERMEM_CONTENT" > "$CLAUDE_MD"
        echo "CLAUDE.md 已更新"
    else
        echo "CLAUDE.md 中未找到 sybermem 标记，请先运行 install.sh"
    fi
else
    echo "~/.claude/CLAUDE.md 不存在，请先运行 install.sh"
fi

# Step 2: 更新 settings.json
if [ -f "$SETTINGS_JSON" ]; then
    if command -v jq &> /dev/null; then
        jq '.sybermem.path = "'"$SYBERMEM_PATH'"' "$SETTINGS_JSON" > "$SETTINGS_JSON.tmp"
        mv "$SETTINGS_JSON.tmp" "$SETTINGS_JSON"
        echo "settings.json 已更新 sybermem 路径"
    fi
fi

# Step 3: 同步 Skills
echo "同步 Skills 到 ~/.claude/skills/..."
rm -rf "$SKILLS_DIR/"* 2>/dev/null || true
cp -r "$SYBERMEM_PATH/skills/"* "$SKILLS_DIR/" 2>/dev/null || true

echo ""
echo "=== 更新完成 ==="
```

写入文件：`scripts/update.sh`

- [ ] **Step 2: 设置脚本执行权限**

```bash
chmod +x scripts/update.sh
```

- [ ] **Step 3: 提交 Task 6.3**

```bash
git add scripts/update.sh
git commit -m "feat: 创建 update.sh 更新脚本

更新用户级配置：
- 提取用户原有内容，替换 sybermem 区域
- 更新 settings.json 路径
- 同步 Skills 到 ~/.claude/skills/"
```

---

## Phase 6 完成检查

- [ ] **验证 Phase 6 所有文件**

```bash
cd /d/sybermem
ls -la skills/sync-experience/SKILL.md scripts/
```

---

## 完整计划自检

### 1. Spec Coverage 检查

| Spec 要求 | 对应任务 |
|-----------|----------|
| sybermem 仓库结构 | Task 1.1 |
| 项目层目录结构 | Task 1.1（模板），init-project Skill 实现 |
| 用户级注入机制 | Task 6.2, 6.3（install.sh, update.sh） |
| OVERVIEW.md 模板 | Task 1.2 |
| ADR/decisions 模板 | Task 1.2 |
| INDEX 文件设计 | Task 1.3 |
| 12 个 Skills | Task 2.1-2.7, 3.1-3.4, 5.1, 6.1 |
| 3 个 Hooks | Task 4.1-4.3 |
| 非侵入性原则 | Task 6.2, 6.3（脚本实现） |
| PROJECTS 项目注册中心 | Task 1.1（结构），init-project/adapt-project 实现注册 |

### 2. Placeholder Scan

检查无 TBD、TODO、待填写等占位符。

### 3. Type Consistency

检查 Skill 名称、文件路径一致。

---

## 最终验证

- [ ] **验证所有文件**

```bash
cd /d/sybermem
git log --oneline -20
find developer PROJECTS team templates skills hooks scripts -type f | wc -l
```

Expected: 显示所有提交和文件数量

---

**计划完成。可选择执行方式：**

1. **Subagent-Driven (推荐)** - 每个 Task 分派独立 Subagent，任务间 Review
2. **Inline Execution** - 在当前会话执行，批量处理

请选择执行方式。