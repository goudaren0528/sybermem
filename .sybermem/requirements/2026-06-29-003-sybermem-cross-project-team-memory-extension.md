---
type: requirement
date: 2026-06-29
number: 003
title: SyberMem 跨项目与团队记忆扩展方案
source: 内部方案评审
priority: high
related: [change-010]
---

## 需求来源

用户目标从"个人项目记忆"扩展为"个人和团队公用协作"。当前 SyberMem v2 的所有能力（记录、检索、关系、digest、theme digest、生命周期治理）都围绕"一个人 + 一个项目 + 一个 AI"设计。扩展到跨项目和团队后，需要解决身份、作用域、来源、索引、发布、审核、同步、权限和上下文路由等新问题。

## 需求内容

### 核心架构：四层模型

```text
Agent Adapter（Claude Code / OpenCode / Codex）
        ↓
SyberMem Project（单项目事实记忆）
        ↓
SyberMem Hub（单用户跨项目索引与个人经验）
        ↓
SyberMem Team（经发布、审核的团队共享认知）
        ↓
Obsidian / Dashboard（统一阅读与治理界面）
```

### 三种数据作用域

| 作用域 | 存储 | 所有者 | 数据进入 | 默认可见性 |
|--------|------|--------|----------|-----------|
| Project | `<repo>/.sybermem/` | 项目 | 自动（record/hook） | project |
| Hub | `~/.sybermem/` | 用户 | 自动索引 | private |
| Team | 独立 Git 仓库 | 团队 | 主动发布 + 审核 | team |

### 关键设计原则

1. **项目自治**：`.sybermem/` 继续是项目事实源，Hub/Team 不替代它
2. **逻辑分层，产品不拆分**：Project/Hub/Team 共用一个 Core、一个 CLI、一套 Schema
3. **Skill 负责语义，Core 负责确定性**：ID 生成、schema 校验、文件写入、索引、发布同步由 Core/CLI 统一处理
4. **自动索引，主动共享**：Hub 自动索引用户项目，Team 只接收主动发布
5. **Markdown 是长期载体，SQLite 是派生索引**：删除 SQLite 可从 Markdown 完全重建
6. **团队经验必须有适用边界**：applies_when / does_not_apply_when / counterexamples

### 新增数据模型

- **Project Identity**：`project.yaml` 含 `project_id`（ULID）、slug、repo remote、team_id
- **User Identity**：`identity.yaml` 含 `user_id`、handle、display_name
- **Global URI**：`sybermem://project/<id>/record/<local-id>`
- **Lesson**：跨项目经验，区别于 Theme Digest（项目主题总结）
- **Publication**：发布记录，含 source_ref、source_hash、review_status
- **Current Status**：结构化项目状态 JSON（phase、completed、blocked、risks）

### Skill 设计

保留现有 11 个 Project Skills 不变。新增约 6 个用户入口：
- `/sybermem-hub-init`
- `/sybermem-project-register`
- `/sybermem-portfolio`
- `/sybermem-promote`
- `/sybermem-publish`
- `/sybermem-team-sync`

扩展现有 `/sybermem-search` 支持 `--scope project|workspace|team`。

### Core/CLI 设计

Python 实现，统一处理：身份、Schema、存储、索引、检索、关系、Promote、Publish、Review、Sync、Context、Obsidian 视图生成、迁移、健康检查。

所有 Skill 通过 JSON CLI 调用 Core，不再由 AI 直接负责文件写入的原子性和幂等性。

## 评审结论与已确认决策

### 架构决策（全部确认）

1. ✅ 认同 Project / Hub / Team 三作用域
2. ✅ 认同 Hub 自动索引、Team 主动发布
3. ✅ 认同 Skill 交互层、Core 记忆引擎（渐进迁移）
4. ✅ 认同项目 `.sybermem/` 继续作为项目事实源
5. ✅ 认同 Team 第一版采用独立 Git 仓库
6. ✅ 认同 Obsidian 主要作为视图（MVP 可延后）
7. ✅ 认同先 Hub 后 Team 的实施顺序
8. ✅ 认同不自动共享个人 Hub 内容

### 选择性决策（已确定方向）

| 决策 | 选择 |
|------|------|
| Core 语言 | Python 先行，后续有性能需求再评估 Go/Rust |
| Team 仓库粒度 | 每团队一个 |
| Hub Git 同步 | MVP 不做 |
| Team 审核模式 | trust mode（2-5 人）/ review mode（5+ 人）双模式 |
| 项目状态发布 | 自动生成 + 手动提交 |
| Codex 第一阶段 | Skill 兼容即可 |
| Obsidian Vault | 一个统一 Vault，子文件夹区分 |
| Lesson 自动生成 | 不自动，只做显式 `/sybermem-promote` |
| 原始 Record 发布 | 只发布摘要版本，不发原始 Record |

### MVP 范围（评审后收窄）

Phase 0.5（过渡期，无需等 Core 完成）：
1. 所有新项目生成 `project.yaml`
2. `~/.sybermem/projects.yaml` 手动注册表
3. `/sybermem-search --scope workspace` 先用 Grep 跨项目搜索

MVP（Core 最小闭环）：
1. Project Identity（`project.yaml`）
2. Core CLI 基础（`project init` + `index build` + `search`）
3. Hub Project Registry
4. SQLite FTS 跨项目检索

MVP 验证后再展开：
5. Portfolio 项目组合视图
6. Promote 为 Personal Lesson
7. Obsidian 生成视图

Team Git MVP 在 Hub MVP 验证后进入。

## 推荐实施顺序

```text
Phase 0：确认架构决策 + Schema RFC ← 当前
Phase 0.5：project.yaml + 手动注册 + Grep 跨项目搜索（过渡桥）
Phase 1：Core CLI 基础（project init / index build / search）
Phase 2：Hub MVP（registry + SQLite FTS + workspace search）
Phase 3：Promote + Personal Lesson
Phase 4：Team Git MVP
Phase 5：Context Router
Phase 6：服务化评估（仅在 Git 模式出现真实瓶颈后）
```

## 完整方案文档

详见 `docs/superpowers/specs/2026-06-29-sybermem-cross-project-and-team-memory-spec.md`。
