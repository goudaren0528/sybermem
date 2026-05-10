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

_Phase 1 完成，继续 Phase 2：核心 Skills_