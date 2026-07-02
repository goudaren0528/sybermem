# SyberMem Team Agent Consumption Layer（Phase E）设计

> 基于当前真实 Team repo，建立一层面向管理 agent 的低成本消费面：先读 overview，再增量生成 management summary，必要时再下钻单项目摘要与 digest。

**Date:** 2026-07-02
**Status:** Draft
**Scope:** 在现有 Team MVP A/B/C/D 之上，只做管理 agent 消费层：`sybermem team summary`、增量基线、management summary 双产物。不做 team sync / review / lesson 发布。
**Parent spec:** `docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseC-design.md`

---

## 1. Background & Problem

当前 Team repo 已经具备：
- `projects/<slug>/project.md`
- `projects/<slug>/current-status.md`
- `projects/<slug>/meta.json`
- `dashboards/current-overview.md`
- 自动 commit + push 到远程 Team 仓库

这意味着：

```text
项目状态和摘要已经能进入 Team memory
```

但现在还缺一层面向**你自己 / 管理 agent**的消费面。没有这一层时：
- agent 每次都需要自己读 overview 再判断是否深挖
- 缺少一个固定产物来表达“自上次管理 summary 以来发生了什么”
- 很难在低成本下稳定生成：
  - 进展汇总
  - 需要关注
  - 值得深挖的项目

所以 Phase E 的目标不是继续加强 Team 存储，而是：

> **让 Team repo 产生一个面向管理 agent 的低成本、可重放、增量式 management summary 消费层。**

---

## 2. Design Goal

新增一个消费层命令：

```bash
sybermem team summary --team-path D:/team-memory
```

生成三个文件：

```text
<team-repo>/dashboards/
├── latest-management-summary.md
├── latest-management-summary.json
└── .summary-state.json
```

目标：
- markdown 给你和管理 agent 直接阅读
- json 给后续 agent / 自动化再消费
- state 文件记录“上次 summary 的基线”

---

## 3. Design Choice

### 不选：只生成一份 markdown
缺点：后续 agent 还得重复 parse，浪费 token。

### 不选：每次 publish 时自动生成 management summary
缺点：成本高、噪音大，容易把 publish 层和消费层混在一起。

### 选择：独立 `team summary` 命令 + markdown/json 双产物 + 基线文件
优点：
- 结构清晰
- 成本可控
- 最适合先手动验证格式，再接管理 agent / 定时器

---

## 4. Input Sources

Phase E 不直接读原始项目 `.sybermem/`。只读 Team repo 已发布产物：

```text
projects/<slug>/
├── current-status.md
└── meta.json

dashboards/current-overview.md
```

### 为什么
与前面 Team MVP 的原则一致：
- Project repo 负责生产摘要
- Team repo 负责聚合与消费摘要

management summary 是 Team repo 的**第二层消费视图**。

---

## 5. Output Files

### 5.1 `latest-management-summary.md`

固定结构的管理摘要，面向人类和管理 agent：

```markdown
# Team Management Summary

- Generated at: 2026-07-02T10:00:00+08:00
- Team: team_rental_platform
- Baseline: since last summary
- Recent window: last 48 hours

## Progress Since Last Summary
- sybermem — published 2 updates; current phase remains phase-010
- teamspark — new digest-backed summary published

## Attention Needed
- teamspark — open bugs: 2
- scanner-demo — no active phase
- old-project — stale for 4 days

## Worth Deeper Review
- sybermem — new phase digest available
- teamspark — multiple recent updates

## Recently Updated Projects
- sybermem — 2026-07-02
- teamspark — 2026-07-01
```

### 5.2 `latest-management-summary.json`

结构化 machine-readable 输出：

```json
{
  "generated_at": "2026-07-02T10:00:00+08:00",
  "team_id": "team_rental_platform",
  "baseline": "since_last_summary",
  "recent_window_hours": 48,
  "progress": [
    {
      "slug": "sybermem",
      "change_type": "status_update",
      "published_at": "2026-07-02T09:00:00+08:00",
      "phase": "phase-010"
    }
  ],
  "attention": [
    {
      "slug": "teamspark",
      "reason": "open_bugs",
      "count": 2
    }
  ],
  "deep_review_candidates": [
    {
      "slug": "sybermem",
      "reason": "new_phase_digest"
    }
  ],
  "recent_updates": [
    {
      "slug": "sybermem",
      "published_at": "2026-07-02T09:00:00+08:00"
    }
  ]
}
```

### 5.3 `.summary-state.json`

内部基线状态文件：

```json
{
  "last_generated_at": "2026-07-02T10:00:00+08:00",
  "last_seen_projects": {
    "sybermem": "2026-07-02T09:00:00+08:00",
    "teamspark": "2026-07-01T20:00:00+08:00"
  }
}
```

它不面向人类阅读，只用于下一次生成 summary 时计算：
- 自上次 summary 以来有哪些项目变化

---

## 6. Time Model

### 主视角：自上次 summary 以来
这是最经济的增量视角。

### 辅助视角：最近 48 小时
用于提供“近况窗口”，避免某些项目虽未比上次 summary 变化更多，但仍然最近很活跃。

---

## 7. Section Rules

### 7.1 `Progress Since Last Summary`
触发条件：
- 当前项目 `published_at` 晚于 `.summary-state.json` 中记录的该项目时间

### 7.2 `Attention Needed`
任一条件进入：
- stale（例如距当前 > 3 天）
- no active phase
- open bugs > 0
- open requirements > 0

### 7.3 `Worth Deeper Review`
任一条件进入：
- 有新的 phase digest
- 有新的 theme digest
- 近 48h 内更新频繁
- 同时存在 open bugs + open requirements
- phase 发生变化

### 7.4 `Recently Updated Projects`
条件：
- `published_at` 在最近 48 小时内

---

## 8. Trigger Model

### 第一版触发方式
手动运行：

```bash
sybermem team summary --team-path D:/team-memory
```

### 为什么不自动
- 先验证 summary 格式是否有价值
- 避免过早把消费层和 publish 层耦合
- 成本更可控

### 后续可扩展
- 管理 agent 调用
- `/loop` 定时调用
- cron 调度

---

## 9. Consumption Strategy

### Layer 1: 低成本入口
先读：
- `dashboards/current-overview.md`
- `dashboards/latest-management-summary.md`

### Layer 2: 深读升级
如果 `Worth Deeper Review` 提到某项目，再读：
- `projects/<slug>/current-status.md`
- `projects/<slug>/meta.json`
- 对应 digest

这保证了：
- 体验好
- 读取成本低
- token 经济性高

---

## 10. Out of Scope

Phase E 明确不做：
- team sync
- team review
- lesson 发布
- 经验候选自动确认
- HTML/TUI dashboard
- AI 自由文本长总结（第一版仍以结构化规则优先）

---

## 11. Success Criteria

1. `sybermem team summary --team-path ...` 可以运行
2. 生成：
   - `latest-management-summary.md`
   - `latest-management-summary.json`
   - `.summary-state.json`
3. summary 包含：
   - Progress Since Last Summary
   - Attention Needed
   - Worth Deeper Review
   - Recently Updated Projects
4. 默认只读少量 Team 文件即可得到低成本管理视图
5. 需要时可按项目深挖，不必每次全量读取 Team repo
