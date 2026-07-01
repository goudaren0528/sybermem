# SyberMem Phase 2.1 — Portfolio Polish 设计

> 修复 `sybermem portfolio` 未接线问题，并把它打磨成第一个真正可用的 Hub 日常入口。

**Date:** 2026-06-30
**Status:** Draft
**Scope:** 只处理 `portfolio` 接线与最小可读文本视图。不扩展 blocked/risk/search/Team/Lesson。
**Parent spec:** `docs/superpowers/specs/2026-06-30-sybermem-hub-mvp-phase2-design.md`

---

## 1. Background & Problem

Hub MVP（Phase 2）已经交付了：
- registry 强化
- SQLite 增量索引
- workspace search filters
- `project status` 结构化快照
- `portfolio` 设计与代码

但在真实 dogfood 中暴露出一个关键问题：

```text
sybermem portfolio --format json
→ invalid choice: 'portfolio' (choose from 'project', 'index', 'search')
```

这说明 Phase 2 的 `portfolio` 功能虽然设计和实现代码都存在，但 **CLI parser 没有接上**，用户无法真正调用它。

进一步看，Phase 2 即使修好接线，如果文本输出只是最小 JSON dump 或单行列表，也还不能让用户第一次感受到：

> Hub 不只是一个“跨项目 search patch”，而是真正能告诉我“我有哪些项目，它们现在怎样”的入口。

因此 Phase 2.1 的目标不是单纯补 bug，而是：

**修复 `portfolio` 接线，并在同一轮里把文本输出打磨到“日常可用”。**

---

## 2. Design Goal

让用户直接运行：

```bash
sybermem portfolio
sybermem portfolio --format json
```

并获得：
- 正常工作的 CLI 命令
- 对人友好的分组文本输出
- 对 AI / future integrations 友好的 JSON 输出

---

## 3. Scope Boundaries

### 本轮做
1. `portfolio` parser 接线
2. 文本输出按项目状态分组
3. JSON 输出保持结构化
4. 真实 dogfood 验证

### 本轮不做
- blocked / risk 自动抽取
- stale reason 的复杂判定
- search ranking 优化
- Windows 中文输出编码修复
- Team / Lesson / Promote / Obsidian
- rich/TUI/color formatting

---

## 4. Command Design

### 命令

```bash
sybermem portfolio
sybermem portfolio --format json
```

### 依赖

`portfolio` 只依赖：
- `~/.sybermem/projects.yaml`
- `project status` 内部逻辑

**不依赖 SQLite**。这意味着即使 `index build` 还没跑，portfolio 也能用。

---

## 5. Output Design

### 5.1 Text output (for humans)

按项目状态分组：

```text
[active]
- sybermem  → phase-010 Search, relations, and theme digest
- teamspark → phase-004 商品与库存能力完善

[stale]
- old-project → HEAD changed since last index build

[missing]
- removed-project → path not accessible
```

### 规则

- 只显示非空分组
- `active` 组：显示当前 phase id + phase name
- `stale` 组：显示“index stale”信息（第一版可只显示 phase，不要求具体 stale reason）
- `missing` 组：明确写 path 不可访问

### 5.2 JSON output (for AI / integrations)

```json
{
  "projects": [
    {
      "project_id": "prj_01...",
      "slug": "sybermem",
      "status": "active",
      "phase": {
        "id": "phase-010",
        "name": "Search, relations, and theme digest",
        "lifecycle": "active"
      }
    }
  ]
}
```

### 规则

- 文本模式 = 人类入口
- JSON 模式 = Skill / future integrations 入口
- 不改变已有字段名称

---

## 6. File Manifest

| 操作 | 文件 | 说明 |
|---|---|---|
| 修改 | `packages/cli/sybermem_cli/main.py` | 接上 `portfolio` parser，并优化文本输出 |
| 可选修改 | `packages/core/sybermem_core/portfolio.py` | 如果当前返回结构不适合文本分组，做最小调整 |
| 不动 | SQLite / registry schema | 本轮不扩字段 |

---

## 7. Success Criteria

1. `sybermem portfolio` 可以运行，不再报 invalid choice。
2. `sybermem portfolio --format json` 返回结构化 JSON。
3. 文本输出按 `active / stale / missing` 分组。
4. 真实 dogfood 时，至少能列出 `sybermem` 与 `teamspark` 这两个项目。
5. 用户第一次可以把 portfolio 当成“Hub 首页”来用。
