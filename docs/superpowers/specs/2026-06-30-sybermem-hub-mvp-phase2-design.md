# SyberMem Hub MVP（Phase 2）设计

> 在 Phase 0.5 的过渡桥和 Phase 1 的 Core/CLI 雏形之上，交付第一个真正的 Hub：Registry + Incremental Index + Workspace Search + Project Status + Portfolio。

**Date:** 2026-06-30
**Status:** Draft
**Scope:** Requirement-003 / Phase 2。做完整 Hub MVP，但不进入 Team / Lesson / Obsidian / Context Router。
**Parent specs:**
- `docs/superpowers/specs/2026-06-29-sybermem-cross-project-and-team-memory-spec.md`
- `docs/superpowers/specs/2026-06-29-phase-0.5-cross-project-search-bridge-design.md`
- `docs/superpowers/specs/2026-06-30-sybermem-core-phase1-design.md`

---

## 1. Background & Problem

### 已有能力

Phase 0.5 已经交付：
- `.sybermem/project.yaml`
- `~/.sybermem/projects.yaml`
- `session_start_context.py` 注入 project slug
- `/sybermem-search --scope workspace` 的概念与 Skill 文档

Phase 1 已经交付：
- `packages/core/`
- `packages/cli/`
- `sybermem project init --register`
- `sybermem index build`（SQLite 全量 rebuild）
- `sybermem search --scope project|workspace`

### 当前问题

虽然现在已经可以跨项目搜索，但还不能说有了真正的 Hub。因为还缺：

1. **Registry 只是最小注册表**  
   还不能表达项目的最后索引时间、最后看到的 commit、是否失联。

2. **SQLite 只有全量重建**  
   每次都重扫所有项目，效率差，不适合长期使用。

3. **Workspace Search 仍然粗糙**  
   缺少项目过滤、类型过滤、状态过滤等基础能力。

4. **没有结构化项目状态快照**  
   Hub 无法回答“这个项目现在在做什么”。

5. **没有 portfolio 视图**  
   用户看不到所有已注册项目的全局状态，只能一个个搜。

Hub MVP 的价值应该同时回答两个问题：

```text
A. 我在哪些项目里见过类似问题？
B. 我现在有哪些项目，它们分别进行到哪里了？
```

---

## 2. Design Goal

Phase 2 交付的 Hub MVP 包含 5 个能力：

1. **Registry 强化**
2. **SQLite 增量索引**
3. **Workspace Search 完善**
4. **`sybermem project status`**
5. **`sybermem portfolio`**

这 5 项一起构成第一个真正可用的 Hub。

---

## 3. Scope Boundaries

### 本阶段做
- `~/.sybermem/projects.yaml` 字段增强
- `~/.sybermem/index/index-state.json`
- SQLite 按项目 commit 级别增量更新
- `sybermem search --scope workspace` 走 SQLite
- `sybermem project status`
- `sybermem portfolio`

### 本阶段不做
- Team
- Lesson / Promote
- Publication / Review
- Obsidian
- Context Router
- 向量检索
- 复杂风险/阻塞抽取
- 细粒度文件级增量索引

---

## 4. Registry 强化

### 文件

```text
~/.sybermem/projects.yaml
```

### 现有结构

```yaml
schema_version: 1
projects:
  - project_id: prj_01...
    slug: sybermem
    path: D:/adr-project
    remote: github.com/goudaren0528/sybermem
    registered_at: 2026-06-29T18:00:00+08:00
```

### 新结构

```yaml
schema_version: 1
projects:
  - project_id: prj_01J6SYBERMEM0001
    slug: sybermem
    name: sybermem
    path: D:/adr-project
    remote: github.com/goudaren0528/sybermem
    registered_at: 2026-06-29T18:00:00+08:00
    last_indexed_at: 2026-06-30T09:00:00+08:00
    last_seen_commit: 756e687
    status: active
```

### 新字段语义

| 字段 | 含义 |
|------|------|
| `name` | 用户可读项目名（默认等于 slug） |
| `last_indexed_at` | 最近一次成功写入 SQLite 的时间 |
| `last_seen_commit` | 最近一次索引时读取到的 `git rev-parse HEAD` |
| `status` | `active` / `missing` / `stale` |

### 状态定义

- `active` — path 存在，`.sybermem/INDEX.md` 存在，最近索引成功
- `missing` — path 不存在或不可访问
- `stale` — path 可访问，但 HEAD 已变化且尚未重建索引

---

## 5. SQLite 增量索引

### 位置

```text
~/.sybermem/index/
├── sybermem.db
└── index-state.json
```

### 增量粒度

第一版只做 **项目级 commit 粒度**：

```text
if current_head == last_seen_commit:
    skip project
else:
    rebuild that project’s rows
```

不做：
- 文件级 hash
- per-record 增量 patch
- SQLite merge conflict recovery

### index-state.json

```json
{
  "schema_version": 1,
  "projects": {
    "prj_01J6SYBERMEM0001": {
      "path": "D:/adr-project",
      "last_seen_commit": "756e687",
      "last_indexed_at": "2026-06-30T09:00:00+08:00"
    }
  }
}
```

这是派生缓存，不是权威数据。

### SQLite 表

#### `projects`
- `project_id`
- `slug`
- `name`
- `path`
- `remote`
- `status`
- `last_seen_commit`
- `last_indexed_at`

#### `records`
- `project_id`
- `slug`
- `record_id`
- `type`
- `title`
- `content`
- `topics`
- `path`
- `created_at`
- `lifecycle`
- `review_status`
- `superseded_by`

#### FTS
保留一个 `records_fts` 虚表。

### 重建策略

`sybermem index build`：
- 默认遍历全部已注册项目
- 对于未变化项目：跳过
- 对于变化项目：
  - 删除其旧 rows
  - 重扫 `.sybermem/`
  - 重写该项目 rows

---

## 6. Workspace Search 完善

### 命令形态

```bash
sybermem search barcode --scope workspace
sybermem search hooks --scope workspace --project sybermem
sybermem search auth --scope workspace --type decision
sybermem search phase-002 --scope workspace --project-status active
```

### 新增过滤器

- `--project <slug>`
- `--type <change|decision|requirement|bug>`
- `--project-status <active|missing|stale>`

### 执行路径

- `--scope project`：继续直扫当前项目（无需 SQLite）
- `--scope workspace`：必须走 SQLite
  - 无 db → 提示先 `sybermem index build`

### 输出

文本输出按项目分组：

```text
[sybermem]
- change-010 SyberMem v2 ...
- change-008 Add Claude Code plugin skeleton

[eszyzu]
- decision-012 移动端扫码降级策略
```

JSON 输出保留 `query` / `scope` / `results[]` 结构，并新增可选 metadata：

```json
{
  "query": "barcode",
  "scope": "workspace",
  "filters": {
    "project": null,
    "type": null,
    "project_status": "active"
  },
  "results": [...]
}
```

---

## 7. `sybermem project status`

### 目标

从单个项目中提取最小但有用的状态快照，让 Hub 能聚合它。

### 命令

```bash
sybermem project status
sybermem project status --format json
```

### 输出来源优先级

1. `phase-index.md` 中 `lifecycle: active` 的 phase
2. 最近 records
3. open bugs / requirements（第一版只列 ID，不做智能归纳）
4. 若无 active phase → fallback 到最近 confirmed phase

### JSON 输出

```json
{
  "project_id": "prj_01J6SYBERMEM0001",
  "slug": "sybermem",
  "as_of": "2026-06-30T10:00:00+08:00",
  "phase": {
    "id": "phase-010",
    "name": "Search, relations, and theme digest",
    "lifecycle": "active"
  },
  "recent_records": ["change-010"],
  "open_bugs": [],
  "open_requirements": [],
  "next": [
    "Run sybermem index build after new record batches",
    "Continue requirement-003 Phase 2 work"
  ]
}
```

### 第一版限制

- 不自动抽取 `blocked` / `risk`
- 不做复杂 NLP 总结
- 重点是提供 **结构化快照**，足够给 portfolio 用

---

## 8. `sybermem portfolio`

### 命令

```bash
sybermem portfolio
sybermem portfolio --format json
```

### 行为

- 读取 `~/.sybermem/projects.yaml`
- 对每个 `status != missing` 的项目，调用内部 `project status` 逻辑
- 对 `missing` 项目直接标记不可用

### 文本输出

```text
[active]
- sybermem → phase-010 Search, relations, and theme digest
- eszyzu   → phase-004 商品与库存能力完善

[stale]
- old-project → HEAD changed since last index build

[missing]
- removed-project → path not accessible
```

### JSON 输出

```json
{
  "projects": [
    {
      "project_id": "prj_01J6SYBERMEM0001",
      "slug": "sybermem",
      "status": "active",
      "phase": "phase-010"
    }
  ]
}
```

---

## 9. File Manifest

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `packages/core/sybermem_core/registry.py` | registry 字段增强 |
| 修改 | `packages/core/sybermem_core/index.py` | 增量索引 + index-state.json |
| 修改 | `packages/core/sybermem_core/records.py` | record 解析增强（topics/lifecycle/review_status/superseded_by） |
| 新增 | `packages/core/sybermem_core/status.py` | project status 逻辑 |
| 新增 | `packages/core/sybermem_core/portfolio.py` | portfolio 聚合逻辑 |
| 修改 | `packages/core/sybermem_core/search.py` | workspace filters |
| 修改 | `packages/cli/sybermem_cli/main.py` | add `project status` + `portfolio` + richer search args |
| 修改 | `packages/claude-skills/sybermem-search/SKILL.md` | 明确 workspace search 依赖 CLI filters |
| 同步 | `skills/` | plugin tree |
| 修改 | `schemas/search-result.schema.json` | 扩展 filters / metadata |

---

## 10. Backward Compatibility

- `projects.yaml` 缺少新字段时，默认：
  - `name = slug`
  - `status = active`
- `index build` 若发现旧 registry，会补写新字段
- `project status` 不依赖 Team / Lesson / Obsidian
- 现有 `sybermem search --scope project` 行为不变

---

## 11. Out of Scope

Phase 2 仍然不做：
- Team
- Lesson / Promote
- Publish / Review
- Obsidian
- Context Router
- 向量检索
- 复杂 blocked / risk 自动抽取
- 文件级 hash 增量更新

---

## 12. Success Criteria

1. `projects.yaml` 有 `name` / `last_indexed_at` / `last_seen_commit` / `status`
2. `sybermem index build` 能跳过未变化项目
3. `sybermem search --scope workspace` 支持 `--project` / `--type` / `--project-status`
4. `sybermem project status` 能输出结构化快照
5. `sybermem portfolio` 能列出所有已注册项目并显示状态
6. 用户第一次真正能感受到：Hub 知道我有哪些项目、能搜它们、能概览它们
