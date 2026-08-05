# SyberMem Workspace 索引陈旧检测方案（批次 F）

**Date:** 2026-08-05
**Status:** Proposed
**Scope:** workspace 搜索查询时的索引新鲜度提示
**Source:** docs/audit/2026-08-05-sybermem-comprehensive-audit.md §2-e（复核精确化：查询时不校验 HEAD）

## 1. 背景与问题

审计 §2-e 精确化结论：workspace 索引有 FTS，但只靠手动 `sybermem index build` 刷新。`search_workspace` 查询时**不比对 indexed HEAD vs current HEAD**，所以某项目提交了新记录但没重建索引时，陈旧结果会一直返回，用户无从知晓。

- 索引构建时（`index.py`）会把每个项目的 HEAD 存入 `projects.last_seen_commit`（并同步 registry）。
- 但查询路径（`search_workspace`）完全不读这个字段。

## 2. 设计目标

在**查询时**给出轻量、非破坏性的陈旧提示，让用户知道哪些项目的索引落后于其当前 HEAD，而不改变搜索结果本身，也不自动重建（自动重建成本高、有副作用，超出本方案）。

1. 提供一个轻量函数，检测哪些已注册项目的 `last_seen_commit` != `current_head(path)`。
2. CLI 的 workspace 搜索在返回结果的同时，打印一条陈旧提示（列出过期项目 + 建议 `sybermem index build`）。
3. 不改 `search_workspace` 的返回类型与结果内容（向后兼容）。

## 3. 设计边界

### 保留
- `search_workspace(query, ...) -> list[SearchRow]` 签名与结果不变。
- 现有 `WorkspaceIndexIncompatibleError` / `FileNotFoundError` 行为不变。
- registry / index schema 不变。

### 不引入
- 查询时自动重建索引（成本 + 副作用，独立决策）。
- 阻塞式失败（陈旧只提示，不报错）。
- 对 project-scope search 的改动（本方案只针对 workspace scope）。

## 4. 方案

### 4.1 新增 staleness 检测函数

在 `workspace_search.py`（或 index/registry 层）新增：
```
def workspace_index_staleness() -> list[dict]:
    """Return per-project staleness: [{slug, project_id, indexed_commit, current_commit, stale: bool}] for registered projects whose indexed HEAD differs from current HEAD."""
```
- 读 registry（`load_registry`）拿每个项目的 `path` + `last_seen_commit`。
- 对每个存在的 path 调 `current_head(path)`。
- 只返回 `stale == True` 的条目（indexed != current，且 current 非空）。
- 完全只读、fail-open（拿不到 HEAD 的项目跳过）。

### 4.2 CLI 集成

`cmd_search`（scope=workspace）在打印结果后：
- 调 `workspace_index_staleness()`；若有 stale 项目，向 **stderr** 打印一条提示：
  `note: N project(s) have a stale workspace index (indexed HEAD != current HEAD); run 'sybermem index build' to refresh: slug1, slug2, ...`
- 不改变 exit code（提示性质），json 格式下把 staleness 放进 payload 的一个字段（不破坏结果字段）。

### 4.3 json 输出

workspace 搜索的 json payload 增加一个可选字段 `index_staleness`（stale 项目列表）。text 模式走 stderr 提示。不改既有 `results` 字段。

## 5. 验收标准

1. `workspace_index_staleness()` 对「已构建索引且 HEAD 未变」的项目返回空；对「索引后又有新提交」的项目返回该项。
2. `search_workspace` 结果与签名不变（回归）。
3. CLI workspace 搜索在有 stale 项目时打印 stderr 提示，无 stale 时静默；exit code 不变。
4. json 模式含 `index_staleness` 字段，不破坏 `results`。
5. 单测覆盖：fresh（无 stale）与 stale（indexed != current）两种情形。
6. `pytest packages/core packages/cli` 全绿；`check-plugin-package.py` `OK`。

## 6. 明确不做

- 查询时自动重建索引。
- 对 project-scope 搜索加陈旧检测（project search 已按 mtime 缓存，语义不同）。
