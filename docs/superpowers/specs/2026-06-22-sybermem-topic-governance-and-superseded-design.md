# SyberMem Topic Governance & Superseded Handling 设计

> 在已有的 Active/Archived Conclusions 与 phase lifecycle 之上，增加 topic 治理与 superseded 关系治理，降低项目记忆噪音并提升历史可追溯性。

**Date:** 2026-06-29
**Status:** Draft
**Scope:** D 组第二步。包含 topic 治理、`superseded_by` frontmatter、`/sybermem-link superseded-by`、search 命中提示。不包含自动归档建议。

---

## 1. Background & Problem

在 D 组第一步完成后，SyberMem 已具备：
- `## Key Conclusions` / `## Archived Conclusions` 分层
- phase `lifecycle: active|completed|archived`
- SessionStart 只注入 active conclusions

但仍有 3 个明显问题：

1. **Topic Index 只增不减**  
   旧 topic 会持续堆积，用户和 AI 都不知道哪些 topic 仍活跃，哪些只是历史别名。

2. **记录被替代后缺少结构化标记**  
   例如旧 decision 被新 decision 替代时，只能靠人工理解。没有明确的“旧 → 新”关系，search 也不会主动提醒。

3. **归档仍是人工语义，不是结构化治理**  
   现在可以把某条 conclusion 移到 `## Archived Conclusions`，但“为什么归档、被谁替代、topic 是否已废弃”缺少统一规则。

目标：在不引入数据库、不增加自动后台写入的前提下，用最小语法扩展完成 topic 和 superseded 治理。

---

## 2. Design Decisions

| 决策点 | 选择 | 理由 |
|---|---|---|
| Topic 治理 | Topic Index 行尾轻量标记 | 保持纯 markdown，可人工可机读 |
| Superseded 关系 | 记录 frontmatter `superseded_by: <id>` | 单值字段，清晰表示旧 → 新 |
| superseded 写入入口 | 扩展 `/sybermem-link` 支持 `superseded-by` | 复用现有关系管理 skill，降低心智负担 |
| 自动归档建议 | 本步不做 | 控制范围，先把显式治理语法立起来 |
| Search 行为 | 不隐藏 deprecated / superseded 结果，只提示 | 用户查历史时仍需要看到旧记录 |

---

## 3. Topic Index 治理语法

当前 Topic Index：

```markdown
## Topic Index

- architecture: requirement-001
- hooks: change-003, change-005, bug-001, change-008
- skills: change-002, change-006
```

改为支持行尾可选标记：

```markdown
## Topic Index

<!-- Optional suffix: [active] [low] [deprecated → <new-topic>] -->
- architecture: requirement-001 [active]
- hooks: change-003, change-005, bug-001, change-008 [active]
- skills: change-002, change-006 [low]
- ADR: requirement-001 [deprecated → architecture]
```

### 3.1 语义

| 标记 | 含义 | search 行为 |
|---|---|---|
| 无标记 | 默认视为 `active` | 正常返回 |
| `[active]` | 当前仍活跃 | 正常返回 |
| `[low]` | 低活跃度，仍可用 | 顶部提示 `low activity` |
| `[deprecated → <new-topic>]` | 已被另一个 topic 替代 | 顶部提示用 `<new-topic>` |

### 3.2 规则

- 本步 **不自动** 生成这些标记，由用户或维护者手动编辑 Topic Index。
- `sybermem-record` 若检测到用户/AI 想写入一个已 `deprecated` 的 topic，应提示用新 topic 代替。
- 旧项目没有这些标记时，所有 topic 视为 `active`，行为不变。

---

## 4. Superseded frontmatter 字段

为 record frontmatter 新增可选字段：

```yaml
superseded_by: decision-007
```

### 4.1 语义

- 表示当前记录已被 `<new-id>` 替代
- 方向固定为 **旧 → 新**
- 单值字段，不是数组

### 4.2 适用类型

| 类型 | 是否常见 |
|---|---|
| `decision` | 最常见 |
| `requirement` | 常见 |
| `change` | 偶尔 |
| `bug` | 少见 |

### 4.3 向后兼容

- 没有 `superseded_by` 的记录保持不变
- 可与 `implements` / `fixes` / `related` 同时存在，不冲突

---

## 5. `/sybermem-link` 扩展支持 `superseded-by`

当前：

```text
/sybermem-link <source-id> <relation> <target-id>
```

关系集合扩展为：

```text
implements | fixes | related | superseded-by
```

### 5.1 行为差异

前三种关系：
- 只写 source frontmatter
- 不改 INDEX.md
- 不改 target

`superseded-by`：**复合操作**
1. 在 old 记录 frontmatter 写 `superseded_by: <new-id>`
2. 在 `INDEX.md` 中找到 old 的 active conclusion
3. 把该行从 `## Key Conclusions` 移到 `## Archived Conclusions`
4. 在该行末尾追加 `[superseded by <new-id>]`
5. 不动 new 记录

### 5.2 验证规则

执行前必须验证：
- old 和 new 记录都存在
- `old != new`
- relation 只能是 `superseded-by`
- old 若已有 `superseded_by`：
  - 相同值 → no-op
  - 不同值 → 提示用户确认覆盖

### 5.3 幂等行为

- 如果 old conclusion 已在 `## Archived Conclusions` 中并已带 `[superseded by <new-id>]`，则不重复移动。
- 如果 old 记录前序已写相同 `superseded_by`，则报告无变化。

---

## 6. Search 命中提示行为

`/sybermem-search` 在 3 类情况下增加提示。

### 6.1 deprecated topic 查询

输入：

```text
/sybermem-search #ADR
```

输出顶部：

```markdown
⚠️ Topic `ADR` is deprecated → use `architecture` instead.
```

仍返回 legacy 结果，不拒绝查询。

### 6.2 low activity topic 查询

输入：

```text
/sybermem-search #skills
```

输出顶部：

```markdown
ℹ️ Topic `skills` is marked low-activity.
```

### 6.3 superseded 记录命中

当某条命中记录带 `superseded_by`：

```markdown
1. **[decision-003]** ...
   - Phase: phase-002
   - File: ...
   - Superseded by: decision-007 — one-line conclusion
```

### 6.4 命中新版本记录时的反向提示

如果别的记录把当前命中记录作为 `superseded_by` 目标：

```markdown
1. **[decision-007]** ...
   - Phase: phase-005
   - File: ...
   - Supersedes: decision-003 — archived old conclusion
```

### 6.5 结果原则

- 不隐藏 deprecated 或 superseded 结果
- 不自动重排结果
- 只增加上下文提示，帮助用户理解记录状态

---

## 7. 模板与文档影响

### 7.1 记录模板

- `decision.md` / `requirement.md` 模板注释增加：
  - `superseded_by: <id>`
- `change.md` / `bug.md` 可不加（本步保持最小范围）

### 7.2 INDEX 模板

在 `Topic Index` section 上方增加注释：

```markdown
<!-- Optional suffix: [active] [low] [deprecated → <new-topic>] -->
```

### 7.3 README / instruction catalogs

本步不新增 skill，仅是扩展现有 `/sybermem-link` 和 `/sybermem-search` 行为，因此：
- README 增加一小节说明 topic 标记和 superseded 语法
- `CLAUDE.md` / `AGENTS.md` skill 名单无需新增条目

---

## 8. File Manifest

| 操作 | 文件 | 说明 |
|---|---|---|
| 修改 | `packages/claude-skills/sybermem-link/SKILL.md` | 增加 `superseded-by` 关系及复合操作说明 |
| 修改 | `packages/claude-skills/sybermem-search/SKILL.md` | 增加 deprecated/low topic 提示与 superseded 命中说明 |
| 修改 | `packages/claude-skills/sybermem-record/templates/decision.md` | 注释新增 `superseded_by` |
| 修改 | `packages/claude-skills/sybermem-record/templates/requirement.md` | 同上 |
| 修改 | `.sybermem/INDEX.md` | Topic Index 注释增加标记说明（本项目自身） |
| 修改 | `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md` | 模板同上 |
| 修改 | `README.md` | 文档化 topic 标记与 superseded |
| 同步 | `skills/` | 通过 sync 脚本同步 plugin tree |

---

## 9. Backward Compatibility

- 无 topic 标记的项目：topic 全部视为 `active`
- 无 `superseded_by` 字段的记录：行为不变
- `superseded-by` 是 `/sybermem-link` 的新增 relation，不影响 `implements`/`fixes`/`related`
- 不引入任何新依赖

---

## 10. Out of Scope

本步明确不做：
- 自动归档建议
- `/sybermem-housekeep` skill
- 自动 topic 活跃度计算
- `change` / `bug` 模板的 superseded_by 注释
- phase lifecycle 第二层治理

---

## 11. Success Criteria

1. Topic Index 支持 `[active]` / `[low]` / `[deprecated → <new>]` 标记语法。
2. `/sybermem-search #old-topic` 会提示 deprecated 替代 topic。
3. `/sybermem-search` 命中 superseded 记录时会显示 `Superseded by:`。
4. `/sybermem-search` 命中替代者时会显示 `Supersedes:`。
5. `/sybermem-link old superseded-by new` 会写 `superseded_by` 到 old 记录，并把 old conclusion 移到 Archived Conclusions。
6. decision / requirement 模板文档化 `superseded_by`。
7. 旧项目行为保持不变。
