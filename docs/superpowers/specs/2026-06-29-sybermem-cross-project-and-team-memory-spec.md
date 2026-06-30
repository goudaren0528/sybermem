# SyberMem 跨项目与团队记忆扩展规范

> 把 SyberMem 从"一人 + 一项目 + 一个 AI"扩展为"一人多项目 + 团队协作"的分布式认知系统。

**Date:** 2026-06-29
**Status:** Confirmed — MVP 范围已收窄
**Scope:** 四层架构 · 三作用域 · Hub MVP → Team Git
**Related:** requirement-003, change-010

---

## 目录

1. [背景与动机](#1-背景与动机)
2. [四层架构模型](#2-四层架构模型)
3. [三种数据作用域](#3-三种数据作用域)
4. [关键设计原则](#4-关键设计原则)
5. [数据模型扩展](#5-数据模型扩展)
6. [Skill 设计](#6-skill-设计)
7. [Core/CLI 设计](#7-corecli-设计)
8. [核心工作流](#8-核心工作流)
9. [索引与检索设计](#9-索引与检索设计)
10. [Obsidian 集成](#10-obsidian-集成)
11. [并发、兼容与迁移](#11-并发兼容与迁移)
12. [分阶段实施计划](#12-分阶段实施计划)
13. [已确认决策](#13-已确认决策)

---

## 1. 背景与动机

SyberMem v2 在单项目记忆方面已建立完整能力：记录、检索、关系、digest、theme digest、生命周期治理。但其所有设计都围绕"一个人 + 一个项目 + 一个 AI"展开。

**用户目标已扩展**：从"个人项目记忆"升级为"个人跨项目知识整合 + 团队公用协作"。

扩展后需要解决的新问题：

| 问题域 | 具体挑战 |
|--------|----------|
| 身份 | 项目 ID 全局唯一、用户身份跨平台一致 |
| 作用域 | 哪些记录属于项目、哪些属于用户、哪些属于团队 |
| 来源追踪 | 团队记录的来源、版本、哈希 |
| 跨项目索引 | 在多个项目中检索相关经验 |
| 发布与审核 | 个人经验如何提升为团队知识 |
| 同步 | 多设备、多成员之间的一致性 |
| 权限 | 私有 Hub 内容不自动共享 |
| 上下文路由 | AI 会话中注入哪个作用域的上下文 |

---

## 2. 四层架构模型

```text
┌─────────────────────────────────────────────────────────┐
│         Agent Adapter（Claude Code / OpenCode / Codex）  │
│         ↓ 调用 Skill（JSON CLI 接口）                    │
├─────────────────────────────────────────────────────────┤
│         SyberMem Project（单项目事实记忆）                │
│         存储：<repo>/.sybermem/                          │
│         所有者：项目 / 仓库                               │
├─────────────────────────────────────────────────────────┤
│         SyberMem Hub（单用户跨项目索引与个人经验）         │
│         存储：~/.sybermem/                               │
│         所有者：用户个人                                  │
├─────────────────────────────────────────────────────────┤
│         SyberMem Team（经发布、审核的团队共享认知）        │
│         存储：独立 Git 仓库（每团队一个）                  │
│         所有者：团队                                      │
├─────────────────────────────────────────────────────────┤
│         Obsidian / Dashboard（统一阅读与治理界面）         │
│         角色：视图层，只读展示，不持有数据源               │
└─────────────────────────────────────────────────────────┘
```

### 层间数据流

```text
Project → Hub：Hub 自动索引（读），不修改项目文件
Hub → Team：用户主动发布（Push），经审核后合并
Team → Agent：Context Router 注入当前会话
Project ← Team：团队经验可被 AI 在项目会话中引用（只读）
```

**核心原则**：数据只向上流动（Project → Hub → Team），不向下覆写。

---

## 3. 三种数据作用域

| 作用域 | 存储位置 | 所有者 | 数据进入方式 | 默认可见性 | 删除影响 |
|--------|----------|--------|-------------|-----------|---------|
| **Project** | `<repo>/.sybermem/` | 项目/仓库 | 自动（record/hook）| project 内 | 仅影响本项目 |
| **Hub** | `~/.sybermem/` | 用户个人 | 自动索引 + 主动 promote | private | 不影响 Team |
| **Team** | 独立 Git 仓库 | 团队 | 主动发布 + 审核通过 | team | 独立治理 |

### Project 作用域

- 继续使用 `.sybermem/` 目录，格式完全向后兼容
- 新增 `project.yaml`（Project Identity）
- 所有现有 Skill 在 Project 作用域继续工作，无需修改

### Hub 作用域

- 目录：`~/.sybermem/`
- 子目录：`registry/`（已注册项目列表）、`lessons/`（个人经验）、`index/`（SQLite FTS）
- Hub 只索引 Project 数据，不持有数据副本（引用方式）
- 个人经验（Lesson）存储在 Hub，不自动同步到 Team

### Team 作用域

- 独立 Git 仓库：`git@team-host:org/team-memory.git`
- 子目录：`lessons/`（团队经验）、`publications/`（发布记录）、`reviews/`（审核记录）
- 数据进入：用户主动 publish → 审核（trust/review 双模式）→ 合并
- 团队成员通过 `git pull` 同步

---

## 4. 关键设计原则

### 原则 1：项目自治

`.sybermem/` 继续作为项目事实源（single source of truth）。Hub 和 Team 不替代、不覆写项目记录。删除 Hub 索引不影响项目数据。

### 原则 2：逻辑分层，产品不拆分

Project / Hub / Team 三个逻辑层共用：
- 一个 Core（Python 实现）
- 一个 CLI（`sybermem` 命令）
- 一套 Schema（frontmatter + YAML 规范）

用户无需安装三个不同工具。

### 原则 3：Skill 负责语义，Core 负责确定性

| 层 | 职责 |
|----|------|
| Skill（AI 交互层） | 理解用户意图、收集参数、展示结果 |
| Core/CLI（记忆引擎） | ID 生成、schema 校验、文件写入、索引、发布同步 |

所有文件写入的原子性和幂等性由 Core 保证，AI 不直接操作文件。

### 原则 4：自动索引，主动共享

- Hub 自动索引用户注册的项目（不需要用户手动触发）
- Team 只接收主动发布（显式 publish），不自动吸收个人记录

### 原则 5：Markdown 长期载体，SQLite 派生索引

- Markdown 文件是唯一持久数据源
- SQLite 是检索加速的派生产物
- 删除 SQLite，可从 Markdown 完全重建
- 不依赖 SQLite 的工作流（AI-only 搜索）保持可用

### 原则 6：团队经验必须有适用边界

每条团队 Lesson 必须声明：
- `applies_when`：适用场景
- `does_not_apply_when`：不适用场景
- `counterexamples`：反例或例外

防止经验被过度泛化应用。

---

## 5. 数据模型扩展

### 5.1 Project Identity（project.yaml）

新文件，位于 `<repo>/.sybermem/project.yaml`。

```yaml
# SyberMem Project Identity
project_id: 01HXXXXXXXXXXXXXXXXXXXXXX    # ULID，全局唯一，生成后不变
slug: my-project                         # 可读短标识，建议 kebab-case
display_name: My Project                 # 显示名称
repo_remote: git@github.com:org/repo.git # Git remote URL（可选）
team_id: team-platform                   # 所属团队（可选）
created_at: 2026-06-29
sybermem_version: "2.0"
```

**规则**：
- `project_id` 使用 ULID，由 Core 生成，不手动填写
- `slug` 在用户的 Hub 注册表中唯一
- `repo_remote` 用于跨设备识别同一项目
- `team_id` 为空则表示该项目不关联团队

### 5.2 User Identity（identity.yaml）

新文件，位于 `~/.sybermem/identity.yaml`。

```yaml
# SyberMem User Identity
user_id: 01HYYYYYYYYYYYYYYYYYYYY         # ULID，全局唯一
handle: alice                            # 用户短标识
display_name: Alice Zhang                # 显示名称
created_at: 2026-06-29
```

### 5.3 Global URI

所有记录可用全局 URI 引用：

```text
sybermem://project/<project_id>/record/<local-id>
sybermem://hub/<user_id>/lesson/<lesson-id>
sybermem://team/<team_id>/lesson/<lesson-id>
```

示例：
```text
sybermem://project/01HXXX.../record/change-010
sybermem://team/team-platform/lesson/2026-06-29-001-prefer-ulid-for-ids.md
```

### 5.4 Lesson（经验记录）

Lesson 区别于 Theme Digest（项目主题总结），是跨项目通用经验。

```yaml
---
type: lesson
id: lesson-001
date: 2026-06-29
title: 优先使用 ULID 作为全局 ID
scope: hub                               # hub（个人）或 team（团队）
source_ref: sybermem://project/01HXXX.../record/change-010
source_hash: sha256:abc123...
promoted_by: alice
promoted_at: 2026-06-29
applies_when:
  - 需要全局唯一 ID 且要求时序可排序
does_not_apply_when:
  - 短期临时 ID，无跨系统引用需求
counterexamples:
  - 数据库主键若已有自增 ID 体系，迁移成本高于收益
tags: [id-design, ulid, distributed]
---

## 经验描述

[经验正文...]

## 来源上下文

来源于项目 my-project 中 change-010 的实践总结。
```

### 5.5 Publication（发布记录）

记录从 Hub 到 Team 的发布动作。

```yaml
---
type: publication
id: pub-001
date: 2026-06-29
source_ref: sybermem://hub/01HYYY.../lesson/lesson-001
source_hash: sha256:abc123...
submitted_by: alice
review_status: pending                   # pending | approved | rejected
reviewed_by: ~
reviewed_at: ~
team_id: team-platform
---
```

### 5.6 Current Status（项目状态）

结构化项目状态快照，供 Portfolio 视图使用。

```json
{
  "project_id": "01HXXX...",
  "slug": "my-project",
  "generated_at": "2026-06-29T12:00:00Z",
  "phase": "phase-003",
  "phase_label": "Hub MVP 开发",
  "completed": [
    "project.yaml 生成",
    "Hub registry 手动注册"
  ],
  "blocked": [],
  "risks": [
    "SQLite FTS 集成尚未验证"
  ],
  "next_action": "实现 Core CLI search 命令"
}
```

---

## 6. Skill 设计

### 6.1 保留现有 11 个 Project Skills（不变）

| Skill | 功能 |
|-------|------|
| `/sybermem-record` | 创建记录（change/decision/requirement/bug）|
| `/sybermem-search` | 检索记录（扩展 scope 参数）|
| `/sybermem-link` | 建立记录间关系 |
| `/sybermem-summary` | 生成周/月报告 |
| `/sybermem-digest` | 创建阶段 digest |
| `/sybermem-theme-digest` | 创建主题 digest |
| `/sybermem-phase-analyze` | 构建/刷新 phase 索引 |
| `/sybermem-phase-confirm` | 确认/调整 phase |
| `/sybermem-init-project` | 初始化 SyberMem |
| `/sybermem-update` | 刷新托管文件 |
| `/using-sybermem` | 显示当前状态 |

### 6.2 新增约 6 个 Hub/Team Skills

| Skill | 功能 | 作用域 |
|-------|------|--------|
| `/sybermem-hub-init` | 初始化用户 Hub（`~/.sybermem/`、identity.yaml）| Hub |
| `/sybermem-project-register` | 在 Hub 中注册当前项目 | Hub |
| `/sybermem-portfolio` | 展示用户所有项目的状态组合视图 | Hub |
| `/sybermem-promote` | 将项目记录显式提升为个人 Lesson | Hub |
| `/sybermem-publish` | 将 Hub Lesson 发布到 Team 仓库 | Team |
| `/sybermem-team-sync` | 从 Team 仓库拉取最新团队知识 | Team |

### 6.3 扩展 `/sybermem-search` 支持 Scope

```text
/sybermem-search auth                          # 默认：当前项目
/sybermem-search auth --scope project          # 当前项目
/sybermem-search auth --scope workspace        # 所有注册项目（跨项目）
/sybermem-search auth --scope team             # 团队知识库
/sybermem-search auth --scope all              # 全部作用域
```

MVP（Phase 0.5）中，`--scope workspace` 先用 Grep 跨项目搜索实现，无需 SQLite。

---

## 7. Core/CLI 设计

### 7.1 实现语言

**Python 先行**。理由：
- 已有 `.sybermem/hooks/record_change_on_stop.py` 的 Python 先例
- 原型速度快，迭代成本低
- 团队 AI 工具链中 Python 生态成熟

后续如出现真实性能瓶颈（如大规模 FTS），再评估 Go/Rust 重写热路径。

### 7.2 CLI 结构

```bash
sybermem project init                    # 生成 project.yaml
sybermem project status                  # 显示项目状态
sybermem hub init                        # 初始化 Hub
sybermem hub register [<repo-path>]      # 注册项目到 Hub
sybermem hub portfolio                   # 显示所有项目状态
sybermem index build                     # 构建/刷新 SQLite 索引
sybermem index rebuild                   # 从 Markdown 完全重建索引
sybermem search <query> [--scope]        # 跨项目检索
sybermem lesson promote <record-id>      # 提升为 Personal Lesson
sybermem lesson publish <lesson-id>      # 发布到 Team
sybermem team sync                       # 拉取 Team 最新知识
sybermem team review list                # 列出待审核 publication
sybermem team review approve <pub-id>    # 审核通过
sybermem context inject                  # 生成 AI 会话上下文注入片段
sybermem health                          # 健康检查
sybermem migrate                         # 迁移旧格式数据
```

### 7.3 Skill → Core 调用协议

所有 Skill 通过 JSON CLI 调用 Core，AI 不直接操作文件：

```bash
# Skill 调用示例
sybermem --json project init --slug my-project --team-id team-platform
```

```json
{
  "status": "ok",
  "project_id": "01HXXX...",
  "file_written": ".sybermem/project.yaml"
}
```

错误时：
```json
{
  "status": "error",
  "code": "PROJECT_ALREADY_EXISTS",
  "message": "project.yaml already exists at .sybermem/project.yaml"
}
```

### 7.4 Core 模块划分

| 模块 | 职责 |
|------|------|
| `identity` | ULID 生成、project.yaml / identity.yaml 读写 |
| `schema` | frontmatter 校验、schema 版本管理 |
| `storage` | 文件原子写入、幂等保护 |
| `index` | SQLite FTS 构建、增量更新、重建 |
| `search` | 跨作用域查询引擎 |
| `relations` | 关系字段读写、反向引用扫描 |
| `promote` | Record → Lesson 转换 |
| `publish` | Lesson → Team Publication |
| `review` | 审核状态管理 |
| `sync` | Git 仓库同步（Team） |
| `context` | AI 会话上下文注入生成 |
| `obsidian` | Obsidian Vault 视图文件生成 |
| `migrate` | 旧格式数据迁移 |
| `health` | 完整性检查 |

---

## 8. 核心工作流

### 8.1 项目记录工作流（Project Record）

```text
用户在项目中工作
    → /sybermem-record 创建记录
    → Core 写入 .sybermem/{type}/YYYY-MM-DD-NNN-title.md
    → Core 更新 .sybermem/INDEX.md
    → Hub 索引器在后台更新 ~/.sybermem/index/sqlite.db（增量）
```

### 8.2 跨项目检索工作流（Cross-Project Search）

**Phase 0.5（无 SQLite）**：
```text
用户：/sybermem-search auth --scope workspace
    → AI 读取 ~/.sybermem/projects.yaml 获取所有项目路径
    → AI 用 Grep 在各项目 .sybermem/ 中搜索
    → 汇总结果，标注来源项目
```

**Phase 2 后（有 SQLite FTS）**：
```text
用户：/sybermem-search auth --scope workspace
    → Skill 调用 Core：sybermem search "auth" --scope workspace
    → Core 查询 ~/.sybermem/index/sqlite.db FTS 表
    → 返回命中记录列表（带 project_id + global URI）
    → Skill 格式化输出
```

### 8.3 提升为经验工作流（Promote to Lesson）

```text
用户：/sybermem-promote change-010
    → Skill 显示 change-010 内容，请用户填写经验描述
    → 用户确认 applies_when / does_not_apply_when / counterexamples
    → Core 在 ~/.sybermem/lessons/ 生成 lesson-NNN.md
    → Core 在 lesson frontmatter 写入 source_ref + source_hash
    → Hub 索引更新
```

### 8.4 发布到团队工作流（Publish to Team）

```text
用户：/sybermem-publish lesson-001
    → Skill 显示 lesson-001 摘要版本（不含原始 Record）
    → 用户确认发布
    → Core 在 Team Git 仓库生成 publications/pub-NNN.md
    → Core 创建 Git commit + push（或 PR，取决于 review mode）
    → trust mode（≤5人）：直接合并
    → review mode（>5人）：创建 PR，等待审核
```

### 8.5 团队审核工作流（Team Review）

```text
审核者：sybermem team review list
    → 列出 review_status: pending 的 publication
审核者：sybermem team review approve pub-001
    → Core 更新 pub-001 的 review_status → approved
    → Core 在 Team 仓库中生成最终 lesson 文件
    → Core 创建 Git commit
```

### 8.6 上下文注入工作流（Context Injection）

```text
AI 会话开始时（通过 hook 或手动）：
    sybermem context inject --scope project,team
    → 输出：当前项目 Key Conclusions（前 N 条）
             + 相关团队 Lesson（按 tag 匹配）
             + 当前 phase 摘要
    → AI 将此片段注入会话上下文
```

---

## 9. 索引与检索设计

### 9.1 SQLite FTS 表结构

```sql
-- 记录全文搜索表
CREATE VIRTUAL TABLE records_fts USING fts5(
    record_id,          -- "change-010"
    project_id,         -- ULID
    project_slug,       -- "my-project"
    scope,              -- "project" | "hub" | "team"
    type,               -- "change" | "decision" | "requirement" | "bug" | "lesson"
    title,
    tags,               -- 空格分隔
    content,            -- Markdown 正文（去 frontmatter）
    date,               -- "2026-06-29"
    tokenize = "unicode61"
);

-- 关系表（正向存储）
CREATE TABLE relations (
    source_id   TEXT NOT NULL,  -- Global URI
    relation    TEXT NOT NULL,  -- "implements" | "fixes" | "related"
    target_id   TEXT NOT NULL,  -- Global URI
    PRIMARY KEY (source_id, relation, target_id)
);

-- 项目注册表
CREATE TABLE hub_projects (
    project_id  TEXT PRIMARY KEY,
    slug        TEXT UNIQUE,
    path        TEXT NOT NULL,  -- 本地绝对路径
    team_id     TEXT,
    last_indexed_at TEXT
);
```

### 9.2 索引构建策略

| 场景 | 命令 | 描述 |
|------|------|------|
| 全量构建 | `sybermem index build` | 首次或大规模变更后 |
| 完全重建 | `sybermem index rebuild` | 从 Markdown 重建，丢弃旧索引 |
| 增量更新 | 自动（stop hook）| 每次 AI 会话结束时增量同步 |

### 9.3 检索优先级

```text
1. Global URI 精确匹配（最快）
2. record_id 精确匹配
3. title FTS（权重高）
4. tags FTS（权重中）
5. content FTS（权重低）
```

### 9.4 Phase 0.5 过渡方案（无 SQLite）

在 Core CLI 完成前，使用 AI + Grep 实现跨项目检索：

1. AI 读取 `~/.sybermem/projects.yaml` 获取路径列表
2. 对每个路径执行 Grep 搜索
3. 汇总结果，按相关度排序

```yaml
# ~/.sybermem/projects.yaml（手动维护的过渡注册表）
projects:
  - slug: my-project
    path: /Users/alice/code/my-project
    project_id: 01HXXX...
  - slug: other-project
    path: /Users/alice/code/other-project
    project_id: 01HYYY...
```

---

## 10. Obsidian 集成

### 10.1 定位

Obsidian 是**视图层**，不是数据源。SyberMem 生成 Obsidian Vault 文件，用户在 Obsidian 中阅读和浏览，但编辑操作回到 SyberMem CLI/Skill。

### 10.2 Vault 结构

```text
~/.sybermem/obsidian-vault/          # 单一统一 Vault
├── projects/
│   ├── my-project/
│   │   ├── INDEX.md                 # 项目 KEY Conclusions 镜像
│   │   ├── changes/                 # change 记录镜像（只读）
│   │   ├── decisions/
│   │   ├── requirements/
│   │   └── bugs/
│   └── other-project/
├── lessons/                         # 个人 Lesson（Hub）
├── team/
│   └── team-platform/               # 团队知识（Team）
│       └── lessons/
└── PORTFOLIO.md                     # 所有项目状态汇总
```

### 10.3 生成方式

```bash
sybermem obsidian generate           # 生成/刷新所有 Vault 文件
sybermem obsidian generate --project my-project  # 只刷新一个项目
```

### 10.4 MVP 延后

Obsidian 集成是 MVP 后阶段特性，在 Hub MVP 验证后展开。

---

## 11. 并发、兼容与迁移

### 11.1 并发控制

| 场景 | 策略 |
|------|------|
| 多 AI 并发写同一项目 | 文件级原子写（Core 保证），INDEX.md 行追加幂等 |
| Hub 索引并发更新 | SQLite WAL 模式，写锁超时重试 |
| Team Git 并发 publish | Git pull-rebase 策略，冲突时提示用户手动解决 |

### 11.2 向后兼容

- 所有新字段（project.yaml、Global URI、Lesson frontmatter）对现有记录完全可选
- 未初始化 project.yaml 的项目，所有 Project Skills 继续正常工作
- 未初始化 Hub 的用户，Hub 相关命令报清晰错误，不影响 Project 功能
- SQLite 删除不影响 Markdown 数据

### 11.3 迁移路径

| 迁移场景 | 命令 | 说明 |
|----------|------|------|
| ADR → .sybermem | `sybermem migrate adr` | 自动（已有机制）|
| 旧项目添加 project.yaml | `sybermem project init` | 幂等，已有则跳过 |
| 手动注册表 → Hub registry | `sybermem hub migrate` | 将 projects.yaml 导入 SQLite |
| SQLite 重建 | `sybermem index rebuild` | 从 Markdown 完全重建 |

---

## 12. 分阶段实施计划

### Phase 0：架构确认 + Schema RFC（当前）

**目标**：确认所有架构决策，完成数据模型设计。

**产出**：
- 本规范文档
- requirement-003 需求记录
- 各确认决策的书面记录

**验收标准**：所有 8 条架构决策和 9 条选择性决策已确认。

---

### Phase 0.5：过渡桥（无需等待 Core 完成）

**目标**：在 Core CLI 开发完成前，提供可用的跨项目搜索能力。

**产出**：
1. 新项目自动生成 `project.yaml`（更新 `/sybermem-init-project`）
2. `~/.sybermem/projects.yaml` 手动注册表规范
3. `/sybermem-search --scope workspace` 扩展（Grep 实现）
4. `/sybermem-project-register` Skill（写入 projects.yaml）

**验收标准**：
- 用户可在两个已注册项目中执行跨项目关键词搜索
- 结果标注来源项目

---

### Phase 1：Core CLI 基础

**目标**：建立 Python Core 最小可运行闭环。

**产出**：
1. `sybermem` CLI 基础框架（Python，JSON 输出模式）
2. `sybermem project init` — 生成 project.yaml（ULID）
3. `sybermem hub init` — 初始化 `~/.sybermem/`、identity.yaml
4. `sybermem index build` — 构建 SQLite FTS 索引
5. `sybermem search <query>` — 基础检索（单项目）

**验收标准**：
- `sybermem project init` 生成合法 project.yaml
- `sybermem index build` 构建 SQLite，包含当前项目所有记录
- `sybermem search auth` 返回命中记录

---

### Phase 2：Hub MVP

**目标**：跨项目索引与检索最小闭环。

**产出**：
1. Hub Project Registry（SQLite `hub_projects` 表）
2. `sybermem hub register` — 注册项目
3. `sybermem search --scope workspace` — SQLite FTS 跨项目检索
4. `/sybermem-project-register` Skill 更新（调用 Core 而非写 YAML）
5. `/sybermem-search` Skill 扩展（scope 参数 → Core）

**验收标准**：
- 注册 3 个项目后，跨项目检索返回来自不同项目的命中记录
- 结果包含 project_id、slug、Global URI

---

### Phase 3：Promote + Personal Lesson

**目标**：个人经验提炼工作流。

**产出**：
1. `sybermem lesson promote <record-id>` — 生成 lesson frontmatter
2. `/sybermem-promote` Skill（引导用户填写适用边界）
3. Hub Lesson 检索（`--scope hub`）
4. Lesson → Project 记录的关系追踪（`source_ref`）

**验收标准**：
- 从 change-010 提升一条 lesson，包含 applies_when 和 counterexamples
- `/sybermem-search --scope hub` 检索到该 lesson

---

### Phase 4：Team Git MVP

**目标**：团队知识发布与审核最小闭环。

**产出**：
1. Team 仓库初始化规范
2. `sybermem lesson publish <lesson-id>` — 发布到 Team
3. Trust mode（自动合并）
4. Review mode（PR 流程）
5. `sybermem team sync` — 拉取团队知识
6. `/sybermem-publish`、`/sybermem-team-sync` Skill

**验收标准**：
- trust mode：publish → Team 仓库立即出现 lesson 文件
- review mode：publish → Team PR 创建 → approve → lesson 文件合并
- sync 后本地可用 `--scope team` 检索到团队 lesson

---

### Phase 5：Context Router

**目标**：AI 会话中的智能上下文注入。

**产出**：
1. `sybermem context inject` — 生成上下文注入片段
2. Stop hook 扩展：会话结束时更新 Hub 索引
3. 会话开始 hook：注入相关项目 + 团队上下文

**验收标准**：
- 新 AI 会话自动收到：当前项目 Key Conclusions + 相关团队 Lesson
- 注入内容长度可控（Token 预算参数）

---

### Phase 6：服务化评估

**触发条件**：Phase 4 的 Git 模式出现真实瓶颈（如大团队高频发布导致延迟）。

**候选方案**：
- 轻量 REST API（FastAPI）替代 Git 模式 Team 存储
- gRPC 接口供高性能场景

**原则**：MVP 验证前不进入 Phase 6 讨论。Git 模式对小团队（< 20 人）已足够。

---

## 13. 已确认决策

### 架构决策（全部确认 ✅）

| # | 决策 | 状态 |
|---|------|------|
| 1 | 采用 Project / Hub / Team 三作用域模型 | ✅ 确认 |
| 2 | Hub 自动索引、Team 主动发布（不自动共享）| ✅ 确认 |
| 3 | Skill 作为交互层，Core 作为记忆引擎（渐进迁移）| ✅ 确认 |
| 4 | 项目 `.sybermem/` 继续作为项目事实源 | ✅ 确认 |
| 5 | Team 第一版采用独立 Git 仓库（每团队一个）| ✅ 确认 |
| 6 | Obsidian 主要作为视图层（MVP 可延后）| ✅ 确认 |
| 7 | 先 Hub 后 Team 的实施顺序 | ✅ 确认 |
| 8 | 不自动共享个人 Hub 内容到 Team | ✅ 确认 |

### 选择性决策（全部已确定方向 ✅）

| # | 决策点 | 选择 | 理由 |
|---|--------|------|------|
| 9 | Core 语言 | **Python 先行** | 现有 hook 已用 Python，迭代快；性能瓶颈出现后再评估 Go/Rust |
| 10 | Team 仓库粒度 | **每团队一个仓库** | 权限边界清晰，简化同步逻辑 |
| 11 | Hub Git 同步 | **MVP 不做** | 单用户场景 Hub 数据不跨设备同步，降低 MVP 复杂度 |
| 12 | Team 审核模式 | **双模式**：trust（≤5人）/ review（>5人）| 小团队不需要正式 PR 流程，大团队需要质量控制 |
| 13 | 项目状态发布 | **自动生成 + 手动提交** | 自动生成降低摩擦，手动提交保持用户控制权 |
| 14 | Codex 第一阶段 | **Skill 兼容即可** | JSON CLI 接口设计天然支持 Codex，无需专项适配 |
| 15 | Obsidian Vault | **单一统一 Vault** | 子文件夹区分项目和团队，统一导航 |
| 16 | Lesson 自动生成 | **不自动，只做显式 `/sybermem-promote`** | 防止低质量经验污染知识库，保持 Lesson 的有意为之 |
| 17 | 原始 Record 发布 | **只发布摘要版本** | 原始 Record 可能含敏感项目细节；摘要经用户确认，适合跨团队共享 |

### MVP 范围（评审后收窄）

**Phase 0.5（过渡桥，无需等待 Core 完成）**：
- [ ] 所有新项目生成 `project.yaml`
- [ ] `~/.sybermem/projects.yaml` 手动注册表
- [ ] `/sybermem-search --scope workspace` 先用 Grep 跨项目搜索

**Hub MVP（Core 最小闭环）**：
- [ ] Project Identity（`project.yaml` + ULID）
- [ ] Core CLI 基础（`project init` + `index build` + `search`）
- [ ] Hub Project Registry（SQLite `hub_projects` 表）
- [ ] SQLite FTS 跨项目检索

**Hub MVP 验证后展开**：
- [ ] Portfolio 项目组合视图
- [ ] Promote 为 Personal Lesson
- [ ] Obsidian 视图生成

**Team Git MVP**：在 Hub MVP 验证后进入 Phase 4。

---

*本规范由 requirement-003 驱动，对应 change-010（SyberMem v2 升级）的扩展方向。*
*详细需求背景见 `.sybermem/requirements/2026-06-29-003-sybermem-cross-project-team-memory-extension.md`。*
