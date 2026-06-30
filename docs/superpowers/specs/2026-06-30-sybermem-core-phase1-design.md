# SyberMem Core Phase 1 设计

> 建立 `packages/core/` 与 `packages/cli/` 的基础形态，并交付最小可用命令：`sybermem project init`、`sybermem index build`、`sybermem search`。

**Date:** 2026-06-30
**Status:** Draft
**Scope:** Requirement-003 / Phase 1。交付 Project Identity、Hub Registry、Workspace Search 的最小 CLI 闭环。不做 Team / Lesson / Portfolio / Obsidian / Context Router。

---

## 1. Background & Problem

跨项目与团队记忆扩展方案（requirement-003）已经确认了三作用域模型：

```text
Project → Hub → Team
```

同时也明确了当前 SyberMem 的局限：
- 现有 Skill 在项目内工作很好，但跨项目搜索仍依赖 AI 逐项目 Grep
- 记录写入、身份、索引、检索等确定性逻辑仍散落在 Skill 与 Hook 中
- 如果直接跳到 Team / Lesson / Portfolio，会在缺少稳定 Core 的情况下把复杂度抬得过高

Phase 0.5 已经提供了过渡桥：
- `.sybermem/project.yaml`
- `~/.sybermem/projects.yaml`
- `/sybermem-search --scope workspace` 的概念设计

下一步应该把这些桥接能力沉到一个真正的 Core / CLI 中。

---

## 2. Design Goal

Phase 1 只做三件事：

1. **`sybermem project init`**
   - 生成/确认 `.sybermem/project.yaml`
   - 可选注册到 `~/.sybermem/projects.yaml`

2. **`sybermem index build`**
   - 读取 `~/.sybermem/projects.yaml`
   - 为已注册项目构建 SQLite 索引

3. **`sybermem search`**
   - 提供 `--scope project|workspace`
   - project 直接查当前项目
   - workspace 走 SQLite

目标不是替换所有现有 Skill，而是建立一个最小但稳定的核心契约：

```text
Skill 负责语义
CLI 负责确定性
```

---

## 3. Directory Layout

第一版建议新增：

```text
packages/
├── core/
│   ├── pyproject.toml
│   └── sybermem_core/
│       ├── __init__.py
│       ├── identity.py
│       ├── project.py
│       ├── registry.py
│       ├── records.py
│       ├── index.py
│       ├── search.py
│       ├── storage.py
│       └── formats.py
│
├── cli/
│   ├── pyproject.toml
│   └── sybermem_cli/
│       ├── __init__.py
│       └── main.py
│
schemas/
├── project.yaml.example
├── projects.yaml.example
└── search-result.schema.json
```

### File responsibilities

| File | Responsibility |
|------|----------------|
| `identity.py` | `project_id` 生成、slug 推导、project.yaml 读写 |
| `project.py` | 项目根解析、Project 初始化流程 |
| `registry.py` | `~/.sybermem/projects.yaml` 读写与注册/更新 |
| `records.py` | 扫描 `.sybermem/` records、Key Conclusions、Topic Index |
| `index.py` | SQLite 初始化、全量 rebuild |
| `search.py` | `project` / `workspace` 检索逻辑 |
| `storage.py` | 路径 helpers、原子写入 helpers |
| `formats.py` | text / json 输出格式化 |
| `main.py` | CLI 入口与参数解析 |

---

## 4. Command Design

### 4.1 `sybermem project init`

#### CLI shape

```bash
sybermem project init
sybermem project init --register
sybermem project init --format json
```

#### Behavior

1. 向上解析最近的项目根：要求同时存在 `.sybermem/` 与 `.claude/settings.json`
2. 若无 `.sybermem/`，报错并建议先跑 `/sybermem-init-project`
3. 若有 `.sybermem/project.yaml`：读取并返回现有身份，不覆盖
4. 若无：
   - 生成 `project_id`
   - 推导 `slug`
   - 读取 git remote / default branch
   - 写入 `.sybermem/project.yaml`
5. 若指定 `--register`：同步更新 `~/.sybermem/projects.yaml`

#### `project.yaml`

```yaml
schema_version: 1
project_id: prj_<ULID>
slug: <derived>
name: <derived>
repository:
  remote: <git remote url or empty>
  default_branch: <branch or empty>
created_at: <ISO8601>
```

#### Output (json)

```json
{
  "status": "created",
  "project_id": "prj_01J6SYBERMEM0001",
  "slug": "sybermem",
  "path": "D:/adr-project",
  "remote": "github.com/goudaren0528/sybermem"
}
```

---

### 4.2 `sybermem index build`

#### CLI shape

```bash
sybermem index build
sybermem index build --project sybermem
sybermem index build --format json
```

#### Behavior

1. 读取 `~/.sybermem/projects.yaml`
2. 对每个项目检查：
   - `path` 是否存在
   - `.sybermem/INDEX.md` 是否存在
3. 扫描项目 `.sybermem/` 中的：
   - records
   - Key Conclusions
   - Topic Index
   - `project.yaml`
4. 把结果写入 SQLite：
   - `projects`
   - `records`
   - `conclusions`
   - `topics`
5. 第一版使用**全量重建**，不做增量索引

#### SQLite path

```text
~/.sybermem/index/sybermem.db
```

#### Minimal indexed fields

`records` 表第一版最小字段：
- `project_id`
- `slug`
- `record_id`
- `type`
- `title`
- `content`
- `topics`
- `path`
- `created_at`

这足以支持 workspace search。

---

### 4.3 `sybermem search`

#### CLI shape

```bash
sybermem search barcode
sybermem search barcode --scope workspace
sybermem search hooks --project sybermem
sybermem search requirement-002 --format json
```

#### Scopes

| Scope | Behavior |
|------|----------|
| `project` | 直接搜索当前项目 `.sybermem/`（不依赖 SQLite） |
| `workspace` | 依赖 `~/.sybermem/index/sybermem.db`，跨所有已注册项目搜索 |

#### `project` behavior

- 向后兼容现有 project-local 搜索语义
- 直接扫描当前项目 `.sybermem/`

#### `workspace` behavior

- 如果 SQLite 不存在：提示先跑 `sybermem index build`
- 按项目分组返回命中结果
- 第一版不做跨项目 ranking，只做简单相关度排序

#### Output (json)

```json
{
  "query": "barcode",
  "scope": "workspace",
  "results": [
    {
      "project_id": "prj_01JXYZ...",
      "slug": "eszyzu",
      "record_id": "decision-012",
      "type": "decision",
      "title": "移动端扫码降级策略",
      "path": "D:/workspace/eszyzu/.sybermem/decisions/...",
      "score": 0.91
    }
  ]
}
```

#### Output (text)

```text
[eszyzu]
- decision-012 移动端扫码降级策略
- change-045 添加 ZXing fallback
```

---

## 5. Registry Design

### `~/.sybermem/projects.yaml`

```yaml
schema_version: 1
projects:
  - project_id: prj_01JXYZ...
    slug: eszyzu
    path: D:/workspace/eszyzu
    remote: github.com/example/eszyzu
    registered_at: 2026-06-30T10:00:00+08:00
  - project_id: prj_01JABC...
    slug: sybermem
    path: D:/adr-project
    remote: github.com/goudaren0528/sybermem
    registered_at: 2026-06-30T10:00:00+08:00
```

### Rules

- keyed by `project_id`
- if `project_id` already exists, update `path`
- if registry file missing, create it
- user-local only; not version-controlled

---

## 6. SessionStart Integration

现有 `session_start_context.py` 已经注入：
- Key Conclusions
- Topic Index summary
- phase-index status

Phase 1 让它额外注入：

```text
Project: sybermem (prj_01J6SYBERMEM0001)
```

这样 AI 在每个会话一开始就知道当前项目身份，后续跨项目检索能更容易解释结果。

---

## 7. Integration with Existing Skills

### Immediate integration

Phase 1 完成后，最先接入 CLI 的 Skill 是：

#### `/sybermem-search`

- `--scope project`：保留现有实现
- `--scope workspace`：优先调用 `sybermem search --scope workspace --format json`
- AI 只负责解释结果，不再自己遍历所有项目

### Deferred integration

以下 Skill 暂不迁移：
- `sybermem-record`
- `sybermem-digest`
- `sybermem-theme-digest`
- `sybermem-phase-analyze`
- `sybermem-phase-confirm`

理由：Phase 1 先把**检索**跑通，写入型能力后续再迁移到 Core。

---

## 8. Out of Scope

Phase 1 明确不做：
- Team scope / team repo
- Lesson / promote
- Portfolio
- Obsidian
- Context Router
- SQLite 增量更新
- Vector search
- Full Skill-to-CLI migration

---

## 9. Implementation Order

推荐实施顺序：

1. 建 `packages/core/` 与 `packages/cli/` 目录骨架
2. 实现 `project init`
3. 实现 `index build`
4. 实现 `search`
5. 更新 `sybermem-search` Skill 的 `--scope workspace`
6. 用 SyberMem 自身仓库做 dogfood

---

## 10. Success Criteria

1. `sybermem project init --register` 为当前项目生成/确认 `project.yaml` 并更新 `~/.sybermem/projects.yaml`
2. `sybermem index build` 能构建 `~/.sybermem/index/sybermem.db`
3. `sybermem search hooks --scope workspace` 能搜到多个已注册项目的结果
4. `session_start_context.py` 注入 project slug / project_id
5. 默认 search 行为（不加 `--scope`）不变
6. 不需要等待 Core 全量开发完成，就能验证 Hub 的核心价值
