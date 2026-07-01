# SyberMem Team MVP Phase C 设计

> 让 Team memory 从“能存项目状态”进化为“能自动生成团队统一总览”，服务管理 agent 的统一入口。

**Date:** 2026-07-01
**Status:** Draft
**Scope:** Requirement-003 / Team MVP Phase C。只做 publish 后自动重建 `dashboards/current-overview.md`，不做 team sync / review / team search / lessons。
**Parent spec:** `docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseB-design.md`

---

## 1. Background & Problem

Phase B（修正版）已经让 Team repo 能接收单个项目的：
- `project.md`
- Team-facing `current-status.md`
- `meta.json`

这已经完成了“把项目记忆汇总到 Team 存储里”的第一步。

但当前 Team repo 仍然缺一个真正给**你和你的管理 agent**看的统一入口。现在它的状态是：

```text
Team repo 里有很多 projects/<slug>/... 文件
但没有一个 team-wide 的总览视图
```

这意味着：
- 你知道项目已经“进来了”
- 但其他 agent 还不能很方便地从 Team repo 一眼看出：
  - 哪些项目活跃
  - 哪些项目最近更新了
  - 哪些项目 stale
  - 哪些项目需要关注
  - 哪些项目已经有 digest，可提取经验

所以 Phase C 的目标是：

> **在每次 `publish status` 后，自动重建一个 Team 统一总览文件，作为管理 agent 的稳定入口。**

---

## 2. Design Goal

当任一项目运行：

```bash
sybermem publish status --team-path <team-repo>
```

除了更新单项目的：
- `projects/<slug>/project.md`
- `projects/<slug>/current-status.md`
- `projects/<slug>/meta.json`

还会自动重建：

```text
<team-repo>/dashboards/current-overview.md
```

这个文件是：
- 团队状态的统一入口
- 面向人类与 agent 的稳定 Markdown surface
- 可完全重建的生成视图

---

## 3. Input Sources

`current-overview.md` 的数据来源**只来自 Team repo 已发布内容**，不直接读取各项目原始 `.sybermem/`。

### 每个项目可用输入

```text
projects/<slug>/
├── project.md
├── current-status.md
└── meta.json
```

### 角色分工

| 文件 | 作用 |
|------|------|
| `project.md` | 项目身份信息 |
| `current-status.md` | 项目当前状态摘要 |
| `meta.json` | 结构化 machine-readable 索引 |

### 为什么不直接读原始 `.sybermem/`

因为 Team memory 的意义就是：
- Project repo 负责生产摘要
- Team repo 负责聚合和消费摘要

如果 Team summary 直接跨项目读原始 `.sybermem/`，那 Team repo 就不再是统一入口，而只是一个旁路缓存。

---

## 4. Trigger Model

### 第一版触发方式

**每次 `publish status` 成功后，自动重建一次 `current-overview.md`。**

即：

```text
publish status
  → 更新单项目 Team files
  → rebuild dashboards/current-overview.md
```

### 第一版不做
- 不用 cron / scheduler
- 不单独暴露 `sybermem team summary` 给用户
- 不做后台 watcher

### 为什么
因为你的需求已经很清楚：
- 项目每 1~2 天汇总到 Team memory
- 最自然的触发点就是“项目 publish 时”

所以 Phase C 的最佳 UX 不是多一个命令，而是让 `publish` 顺手完成 Team summary 更新。

---

## 5. `current-overview.md` Structure

文件路径：

```text
<team-repo>/dashboards/current-overview.md
```

### 固定模板

```markdown
# Team Overview

- Updated at: 2026-07-01T10:00:00+08:00
- Team: team_rental_platform

## Active Projects
- sybermem → phase-010 Search, relations, and theme digest
- teamspark → phase-004 商品与库存能力完善

## Recently Updated
- sybermem — 2026-07-01
- teamspark — 2026-06-30

## Needs Attention
- teamspark — open bugs: 2
- old-project — status: stale
- scanner-demo — no active phase

## Published Sources
- sybermem → phase digest available, theme digest available
- teamspark → no digest published
```

### 区块说明

#### Active Projects
- 所有有 active phase 的项目
- 显示：`slug → phase-id + phase name`

#### Recently Updated
- 按 `meta.json.published_at` 从新到旧排序
- 第一版列全部已发布项目

#### Needs Attention
触发条件：
- stale
- no active phase
- open bugs > 0
- open requirements > 0

#### Published Sources
来源：
- `meta.json.source_phase_digest`
- `meta.json.source_theme_digest`

显示：
- `phase digest available`
- `theme digest available`
- `no digest published`

---

## 6. Generation Rules

### 6.1 Rebuild strategy

第一版采用 **full rebuild**：
- 扫描 `projects/*/meta.json`
- 读取对应 `current-status.md`
- 重新生成整个 `dashboards/current-overview.md`

### 6.2 为什么不做 partial patch

- 项目数量在 MVP 阶段不多
- full rebuild 更稳
- 更容易调试和重放
- 避免并发 publish 时 overview 局部错乱

### 6.3 项目状态分类规则

| 显示状态 | 规则 |
|----------|------|
| active | `current-status.md` 中有 active phase |
| stale | `published_at` 超过阈值（第一版先固定为 > 3 天） |
| missing-phase | `current-status.md` 里 phase 为 `(no phase)` |
| published-with-digest | `meta.json` 有 `source_phase_digest` 或 `source_theme_digest` |

这些只用于生成 overview，不反写回项目。

---

## 7. Why This MVP Matters

这一步完成后，Team memory 才真正具备：

```text
多项目状态发布
    → Team repo
    → 一个统一的 team-wide 管理视图
    → 其他 agent 可以基于它做汇总 / 报告 / 风险提示
```

也就是说，Team repo 从：

```text
许多项目的状态文件集合
```

变成：

```text
真正的团队工程记忆首页
```

---

## 8. Out of Scope

Phase C 明确不做：
- `team sync`
- `team review`
- Team search
- digest / lesson / decision 的发布
- 自然语言“本周总结”生成
- dashboard 历史版本
- richer/TUI/HTML rendering

---

## 9. Success Criteria

1. `publish status` 成功后会自动生成/更新 `dashboards/current-overview.md`
2. `current-overview.md` 包含：
   - Active Projects
   - Recently Updated
   - Needs Attention
   - Published Sources
3. 该文件只依赖 Team repo 中已发布的 `project.md` / `current-status.md` / `meta.json`
4. 你和管理 agent 可以把它作为团队统一入口使用
5. 不需要额外手动运行 `team summary`
