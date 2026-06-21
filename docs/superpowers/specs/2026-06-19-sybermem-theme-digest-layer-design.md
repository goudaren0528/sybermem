# SyberMem Theme Digest Layer 设计

> 在 phase digest 之上增加一个按 topic 聚合的持久化压缩层,解决 10+ 个 phase digest 再次变成新列表的问题。

**Date:** 2026-06-19
**Status:** Draft
**Scope:** C 组第一版 —— 更高层压缩。只做 theme digest,不做 phase hierarchy。

---

## 1. Background & Problem

SyberMem 当前知识层是:

```text
record
  → key conclusion
  → phase
  → phase digest
```

这在 10-20 条记录、几个 phase 时很好用,但在 50-100 条记录、10+ 个 confirmed phases 时会出现新的问题:

- `phase digest` 本身又变成新的列表
- 某条能力线(比如 `hooks` / `plugin` / `memory`)常常跨多个 phase
- 想回忆某个主题的整体演进时,需要读多个 phase digest 和 raw records

核心问题:

> phase digest 压缩了 phase,但没有东西再压缩跨多个 phase 的同一主题。

目标:增加一个 **Theme Digest Layer** —— 按 topic 聚合的、位于 phase digest 之上的持久化压缩层。

---

## 2. Design Decisions

| 决策点 | 选择 | 理由 |
|---|---|---|
| 第一版先做什么 | 更高层压缩 | 比 phase hierarchy 更直接解决当前痛点 |
| 聚合依据 | 主题(topic slug) | 最符合能力线演进的直觉 |
| 数据来源 | phase digests 优先, raw records 补缺 | 兼顾压缩质量和覆盖完整性 |
| 双向索引 | 不做 | 第一版最小闭环,避免额外维护层 |
| 命令语义 | 新增 `/sybermem-theme-digest` | 不混淆现有 `/sybermem-digest` 的 phase digest 语义 |

---

## 3. Theme Digest 的角色

Theme Digest 回答的问题不是:
- "phase-003 发生了什么?"(这是 phase digest / summary)
- "最近两周发生了什么?"(这是 weekly/monthly summary)

而是:
- "`hooks` 这条能力线跨多个 phase 最终沉淀了什么?"
- "`plugin` 这个主题从开始到现在形成了哪些稳定结论?"
- "如果我只想回忆某一主题,不想读 6 个 phase digest,应该看什么?"

新的知识层:

```text
record
  → key conclusion
  → phase
  → phase digest
  → theme digest
```

---

## 4. 数据来源与 coverage strategy

Theme Digest 使用 **双源压缩**:

### 第一优先:已有 phase digests

如果某个 topic 相关的 phase 已经有 digest,优先读取 digest,因为 digest 已经是压缩后的高质量材料。

例如 topic=`hooks`:
- phase-001 digest (如果有)
- phase-004 digest (如果有)
- phase-005 digest (如果有)

### 第二优先:raw records 补缺

如果相关 phase 没有 digest,或者有关键 record 没被 digest 覆盖,则补读:
- `.sybermem/INDEX.md` 的 Key Conclusions
- `.sybermem/analysis/phase-index.md` coverage map
- 对应 raw records
- 可选:Topic Index 对应的 record IDs

### Coverage strategy

Theme Digest 的 frontmatter 明确声明:

```yaml
coverage_strategy: phase-digests-first-then-records
```

这保证主题压缩层是可审计的,而不是黑盒摘要。

---

## 5. 主题归属规则

第一版默认按 **topic tag** 聚合。

来源优先级:
1. 记录自己的 `#topic` tag (来自 Key Conclusion / Topic Index)
2. phase 覆盖的 record topics 聚合
3. 已有 phase digest 的主题判断

规则:
- 一个 theme digest 对应一个 `topic slug`
- 不做模糊主题合并 (`hooks` ≠ `automation`)
- 一个 topic 可跨多个 phase
- 第一版不支持多 topic 聚合

---

## 6. 去重规则

Theme Digest 必须避免重复把同一条记录当成多份证据。

### 6.1 record 去重
按 record ID 去重:
- `change-003` 只算一次
- `bug-001` 只算一次

### 6.2 digest 覆盖优先
如果某条 record 已被某个 phase digest 覆盖,Theme Digest 优先引用该 phase digest,而不是重复展开 raw record 细节。

即:
- digest 是摘要层
- raw record 是补缺层

### 6.3 source list 去重
frontmatter 中的 `source_phases`、`source_digests`、`source_records` 都必须去重。

---

## 7. Theme Digest 数据模型

新增目录:

```text
.sybermem/theme-digests/
```

文件命名:

```text
YYYY-MM-DD-NNN-topic-slug.md
```

例如:
- `2026-06-001-hooks.md`
- `2026-06-002-plugin.md`
- `2026-06-003-memory.md`

### Frontmatter

```yaml
---
type: theme-digest
date: 2026-06-19
number: 001
theme: hooks
status: completed
source_topics: [hooks]
source_phases: [phase-001, phase-004, phase-005]
source_digests:
  - digest-001
source_records:
  - change-003
  - change-005
  - bug-001
  - change-008
coverage_strategy: phase-digests-first-then-records
---
```

### 正文结构

```markdown
# Theme Digest: hooks

## Theme
- hooks

## Why This Theme Matters
- ...

## What Stabilized
- ...

## Cross-Phase Evolution
- phase-001: ...
- phase-004: ...
- phase-005: ...

## Current Reusable Conclusions
- ...

## Open Edges
- ...

## Source Coverage
- Digests used: digest-001
- Raw records used: change-003, change-005, bug-001, change-008
```

重点:
- phase digest 讲的是"某阶段发生了什么"
- theme digest 讲的是"某主题跨多个阶段最终沉淀了什么"

---

## 8. 与现有系统协作

### 8.1 与 INDEX.md

新增 section:

```markdown
## Theme Digests

| Number | Date | Theme | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
| 001 | 2026-06-19 | hooks | completed | 3 phases, 1 digest, 4 records | [link](theme-digests/2026-06-19-001-hooks.md) |
<!-- add new theme digest records here -->
```

最终 INDEX 结构:

```text
Key Conclusions
Stage Digests
Theme Digests   ← 新增
Feature Changes
Technical Decisions
Requirements / Discussions
Bug Fix Records
Topic Index
```

### 8.2 与 Topic Index

Topic Index 继续负责:
```text
topic -> record IDs
```

Theme Digest 负责:
```text
topic -> durable synthesized conclusion
```

也就是说:
- Topic Index = 导航目录
- Theme Digest = 目录背后的正文

第一版不改 Topic Index 结构,只用它发现候选 records。

### 8.3 与 phase-index

Theme Digest 不改变 `phase-index.md` 的 phase 结构。

只读取:
- confirmed phases
- coverage map (record → phase)
- current phase 边界信息

即:
- phase-index 仍是结构源
- theme digest 是跨 phase 的压缩层

### 8.4 与 `/sybermem-summary`

第一版不改 summary 行为。

未来可扩展:
```text
/sybermem-summary theme hooks
```

但第一版不做,避免 scope 膨胀。

### 8.5 与 `/sybermem-digest`

`/sybermem-digest` 继续表示 **phase digest**。

新增独立 skill:
```text
/sybermem-theme-digest <topic>
```

理由:
- phase digest 和 theme digest 回答的问题不同
- 独立 skill 保持命令语义清晰

---

## 9. 第一版命令形状

新增 skill:

```text
/sybermem-theme-digest hooks
```

第一版只支持:
- 一个 topic slug
- 自动发现相关 phases / digests / records
- 生成一个持久化 theme digest 文件
- 更新 INDEX.md Theme Digests table

未来可扩展但第一版不做:
- `--phases phase-001,phase-004`
- `--records change-003,bug-001`
- 多 topic 聚合
- 时间聚合

---

## 10. File Manifest

| 操作 | 文件 | 说明 |
|---|---|---|
| 新增 | `packages/claude-skills/sybermem-theme-digest/SKILL.md` | 新 skill |
| 新增 | `packages/claude-skills/sybermem-init-project/project-files/.sybermem/templates/theme-digest-template.md` | 模板 |
| 修改 | `packages/claude-skills/sybermem-init-project/SKILL.md` | 初始化时创建 `theme-digests/` 和模板 |
| 修改 | `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md` 模板或 section 插入逻辑 | 新增 Theme Digests section |
| 修改 | 现有项目的 `.sybermem/INDEX.md` | 插入 `## Theme Digests` |
| 新增 | `.sybermem/theme-digests/` | 新目录 |
| 修改 | `README.md` | 文档化 Theme Digest Layer |
| 同步 | `scripts/sync-plugin-skills.py` 触发后的 `skills/` | 同步新 skill 到 plugin 树 |

---

## 11. Backward Compatibility

- 没有 theme digest 的项目继续正常工作。
- phase-index、Topic Index、phase digest 格式不变。
- 不引入数据库、索引服务或外部依赖。
- Theme Digest section 缺失时,`/sybermem-theme-digest` 可以创建并补齐。

---

## 12. Out of Scope

第一版明确不做:
- 多 topic 聚合
- 时间聚合(月度/季度 theme digest)
- phase hierarchy / parent-child relationships
- summary 的 theme mode
- 自动推荐"哪些 topic 应该 digest"
- 反向链接回写到 record / phase / digest
- C 组之外的 D 组(record lifecycle, topic hygiene)

---

## 13. Success Criteria

1. 能运行 `/sybermem-theme-digest hooks` 生成 `.sybermem/theme-digests/YYYY-MM-DD-NNN-hooks.md`
2. Theme Digest section 被加入 INDEX.md 并有 table row
3. Theme Digest frontmatter 包含 `source_phases` / `source_digests` / `source_records` / `coverage_strategy`
4. 如果 phase digest 存在,优先使用;不存在时补读 raw records
5. record / digest / phase 来源都去重
6. 不改变现有 `/sybermem-digest` 语义
7. 零新依赖
