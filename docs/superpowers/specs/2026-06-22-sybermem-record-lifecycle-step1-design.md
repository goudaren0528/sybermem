# SyberMem 记录生命周期治理第一步设计

> Key Conclusions 分层 + Phase lifecycle 字段，解决启动 token 膨胀、过时记录被引用、phase 活跃/完成模糊三个痛点。

**Date:** 2026-06-22
**Status:** Draft
**Scope:** D 组第一步。只做 Key Conclusions 分层 + Phase lifecycle。不做 topic 治理、record superseded frontmatter、自动归档。

---

## 1. Background & Problem

实际项目使用中已出现 4 个痛点：

1. **过时记录仍被引用**：旧 decision/requirement 被新的替代，但 AI 启动时仍读到旧结论。
2. **Topic 堆积**：Topic Index 只增不减，噪声增长。（本次不解决，留第二步。）
3. **Phase 活跃/完成模糊**：所有 phase 都是 `confirmed`，summary 不知道展示哪个。
4. **Key Conclusions 膨胀**：50+ 条 conclusions 全部注入 SessionStart，大部分已不相关。

本次解决 1、3、4。

---

## 2. Design

### 2.1 Key Conclusions 分层

#### INDEX.md 结构变更

当前：

```markdown
## Key Conclusions
- [change-010] ...
- [requirement-001] ...
<!-- add new conclusions here -->
```

改为：

```markdown
## Key Conclusions
<!-- Active conclusions — injected at session start -->
- [change-010] #lifecycle #search — SyberMem v2... (2026-06-22)
<!-- add new conclusions here -->

## Archived Conclusions
<!-- Not injected at session start; findable via /sybermem-search -->
<!-- add new archived conclusions here -->
```

#### 归档标记语法

归档的 conclusion 行尾加标记说明原因：

- `[superseded by <id>]` — 被另一条记录替代
- `[compressed in <theme-digest-id>]` — 已被 theme digest 覆盖
- `[archived]` — 手动归档（超过 90 天无关联活动等）

例：

```markdown
## Archived Conclusions
- [requirement-001] #architecture — Adopted ADR system... (2026-05-08) [compressed in theme-digest-001]
- [decision-003] #auth — Chose JWT... (2026-05-20) [superseded by decision-007]
```

#### 行为规则

| 组件 | 行为 |
|---|---|
| `session_start_context.py` | 只读 `## Key Conclusions` section 到下一个 `##` 之间的内容。不读 `## Archived Conclusions`。 |
| `/sybermem-record` | 新 conclusion 写入 `## Key Conclusions`（active）。 |
| `/sybermem-search` | 搜索全部 conclusions（active + archived）。Archived 结果标注归档状态。 |
| `check_project_health.py` | 检测 `## Archived Conclusions` section 是否存在（新的 managed section）。 |

#### 归档操作

第一版是**手动**操作：把一行从 `## Key Conclusions` 剪切到 `## Archived Conclusions`，并加标记。

未来可由 `/sybermem-update` 的 health check 建议哪些 conclusions 该归档，但第一步不做自动建议。

---

### 2.2 Phase lifecycle 字段

#### phase-index 结构变更

在 confirmed phase block 加 `lifecycle` 字段：

```markdown
### Phase: Lifecycle layer and cross-platform integration
- phase_id: phase-008
- status: confirmed
- lifecycle: completed
- covered_records: [...]
- completed_at: 2026-06-22
```

#### 三个值

| 值 | 含义 | summary 行为 | digest 行为 |
|---|---|---|---|
| `active` | 当前正在进行 | 默认展示 | 不主动建议 |
| `completed` | 工作已结束 | 不默认展示 | 优先建议 digest |
| `archived` | 已有 digest 且不再活跃 | 跳过 | 跳过 |

#### 规则

- `/sybermem-phase-analyze` 新创建的 phase 默认 `lifecycle: active`。
- `/sybermem-phase-confirm` 支持设置 lifecycle 值（例如 `/sybermem-phase-confirm phase-008 lifecycle completed`）。
- **向后兼容：没有 `lifecycle` 字段的 phase 视为 `active`**。
- `completed_at` 字段在标记为 completed 时写入日期。

---

## 3. File Manifest

| 操作 | 文件 | 说明 |
|---|---|---|
| 修改 | `.sybermem/hooks/session_start_context.py` | `parse_conclusions` 只读到 `## Archived Conclusions` 或下一个 `##` 之前 |
| 修改 | `.sybermem/hooks/check_project_health.py` | 检测 `## Archived Conclusions` section |
| 修改 | `packages/claude-skills/sybermem-record/SKILL.md` | Step 8 加注释：写入 `## Key Conclusions`，不写 Archived |
| 修改 | `packages/claude-skills/sybermem-phase-analyze/SKILL.md` | 新 phase 默认 `lifecycle: active` |
| 修改 | `packages/claude-skills/sybermem-phase-confirm/SKILL.md` | 支持设置 lifecycle |
| 修改 | `packages/claude-skills/sybermem-summary/SKILL.md` | 默认只展示 `lifecycle: active` |
| 修改 | `packages/claude-skills/sybermem-digest/SKILL.md` | 优先建议 `lifecycle: completed` |
| 修改 | `packages/claude-skills/sybermem-search/SKILL.md` | 搜索 archived 时标注状态 |
| 修改 | `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py` | 同上（模板） |
| 修改 | `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py` | 同上（模板） |
| 修改 | `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md` | 加 `## Archived Conclusions` section |
| 修改 | `.sybermem/INDEX.md` | 加 `## Archived Conclusions` section（本项目自身） |
| 修改 | `.sybermem/analysis/phase-index.md` | 给已有 phase 补 `lifecycle` 字段（本项目自身） |
| 同步 | `skills/`（通过 sync 脚本） | 同步修改后的 skills 到 plugin 树 |

---

## 4. Backward Compatibility

- 没有 `## Archived Conclusions` section 的项目：SessionStart hook 仍正常工作，只是读到 `## Key Conclusions` 的全部内容（和以前一样）。
- 没有 `lifecycle` 字段的 phase：视为 `active`（默认行为不变）。
- 记录文件本身不改——归档只影响 INDEX.md 的 conclusion 行位置。
- 不引入任何新依赖。

---

## 5. Out of Scope

第一步明确不做：
- Topic 活跃度标记 / deprecated / 合并
- Record frontmatter 的 `superseded_by` 字段
- 自动归档建议（`/sybermem-housekeep`）
- 自动 conclusion 归档触发

---

## 6. Success Criteria

1. SessionStart hook 只注入 `## Key Conclusions` 里的活跃结论，不注入 `## Archived Conclusions`。
2. `/sybermem-summary` 默认只展示 `lifecycle: active` 的 phase。
3. `/sybermem-digest` 优先建议 `lifecycle: completed` 的 phase。
4. `/sybermem-search` 能搜到 archived conclusions 并标注归档状态。
5. 没有 `## Archived Conclusions` 或没有 `lifecycle` 字段的旧项目行为不变。
6. 健康检查能检测到缺失的 `## Archived Conclusions` section。
