# SyberMem Team MVP Phase B 设计（修正版）

> Team repo 不应接收机械的空状态快照，而应接收“足够有意义”的项目级摘要。`publish status` 成为一个带前置补齐能力的编排入口。

**Date:** 2026-07-01
**Status:** Draft
**Scope:** Requirement-003 / Team MVP Phase B（修正版）。发布 team-facing project summary + project.md，并在需要时自动补 phase digest。 
**Parent spec:** `docs/superpowers/specs/2026-06-30-sybermem-team-mvp-phaseA-design.md`

---

## 1. Background & Problem

原始 Phase B 设计假设：
- 发布 `project.md`
- 发布 `current-status.md`

但这会产生一个问题：

> 如果项目只有很薄的 current-status，而没有 digest / theme digest / recent records 的有意义沉淀，那么 Team repo 里只是空壳状态文件，后续 agent 很难基于它做进展管理、经验提取和规范总结。

因此，Team MVP 的核心目标应改为：

```text
发布“足够有意义”的项目级摘要
而不是机械地发布所有项目的状态文件
```

---

## 2. Design Goal

`sybermem publish status` 成为编排入口：

```bash
sybermem publish status --team-path D:/team-memory
```

它的行为不是“直接发 status”，而是：

```text
1. 判断当前项目是否已有可用 digest / theme digest
2. 如果没有，判断是否有足够内容自动补 digest
3. 如果内容仍不足，则默认不同步
4. 如果有足够内容，则生成 team-facing project summary 并发布到 Team repo
```

---

## 3. 发布阈值（已确认）

用户接受的第一版阈值：

### 满足任一条件才允许自动补 digest 并发布
- 至少 **2 条 record**
- 或者存在 **1 条 decision**
- 或者存在 **1 条 completed phase**

如果三项都不满足，则默认：

```text
不发布
```

并提示：

```text
Project does not yet have enough meaningful material to publish to Team memory.
```

---

## 4. Publish 编排规则

### 4.1 有 digest / theme digest

优先使用它们作为 source material。

```text
phase digest / theme digest
  → 提取决策 / 改进 / 教训 / 风险 / 下一步
  → 生成 team-facing project summary
```

### 4.2 没有 digest，但内容足够

自动触发：
- 优先补 **phase digest**
- 只有在 phase 不适合、但 topic 已明显成熟时才考虑 theme digest（第一版可先不自动补 theme digest）

然后再继续 publish。

### 4.3 没有 digest，且内容不足

默认不同步。

### 4.4 用户强制要求

未来可支持：

```bash
sybermem publish status --team-path D:/team-memory --force
```

此时允许直接做一次轻量提炼而不创建正式 digest。

**第一版不做 `--force`，只保留设计空间。**

---

## 5. 发布产物重定义

### 5.1 `project.md`

稳定身份卡片，变化少：

```markdown
# sybermem

- Project ID: prj_01J6SYBERMEM0001
- Slug: sybermem
- Name: sybermem
- Repository: https://github.com/goudaren0528/sybermem
- Team: team_rental_platform
- Registered at: 2026-06-29T18:00:00+08:00
```

### 5.2 `current-status.md` → 升级为 team-facing project summary

它不再只是薄薄的 status 快照，而是：

```markdown
# sybermem — Team Project Summary

- Updated at: 2026-07-01T10:00:00+08:00
- Source commit: 20d1cc4

## Active Phase
- phase-010 — Search, relations, and theme digest

## Progress
- 已完成 Theme Digest Layer
- 已完成 Topic governance / superseded handling
- 已完成 Hub MVP 与 portfolio polish

## Key Decisions
- Team MVP should precede full Hub experience for Requirement-003

## Notable Improvements
- 新增跨项目 search
- 新增 team init / publish status

## Lessons / Pitfalls
- Windows 输出编码仍需单独处理
- 未分析项目需要避免 phase 模板回退误判

## Open Issues / Risks
- team sync 尚未实现
- team-level search 尚未实现

## Next
- continue Team MVP Phase C
```

这个文件要足够让其他 agent 直接消费，用于：
- 进展汇总
- 跨项目状态比较
- 后续经验提取和规范总结

### 5.3 `meta.json`

保留结构化索引：

```json
{
  "status": "published",
  "team_id": "team_rental_platform",
  "project_id": "prj_01J6SYBERMEM0001",
  "slug": "sybermem",
  "published_at": "2026-07-01T10:00:00+08:00",
  "source_commit": "20d1cc4",
  "source_digest": "digests/2026-07-001-...md"
}
```

用于未来的 Team search / sync / dashboard，不需要现在就全面启用。

---

## 6. Team Repo 结构（修正版）

```text
<team-repo>/projects/<slug>/
├── project.md
├── current-status.md      # 团队可消费摘要
└── meta.json
```

`latest-phase-digest.md` / `latest-theme-digest.md` 第一版不直接复制过去，而是作为 source material 内部使用。避免 Team repo 里立刻堆满 digest 文件。

---

## 7. CLI 形态

### 第一版命令

```bash
sybermem publish status --team-path D:/team-memory
sybermem publish status --team-path D:/team-memory --format json
```

### 行为流程

1. 解析当前项目 root
2. 读取 `.sybermem/project.yaml`
3. 读取 Team repo 的 `team.yaml`
4. 判断是否满足最小阈值
5. 如果已有 digest / theme digest → 用它们做摘要来源
6. 如果没有，但阈值满足 → 自动补 phase digest
7. 生成 `project.md` + `current-status.md` + `meta.json`
8. 输出结果

---

## 8. 为什么这才是 MVP

这样做之后，Team repo 里存的不是“所有项目都一刀切的薄 status”，而是：

> **所有有意义项目的团队可消费摘要**

这就让其他 agent 可以真正基于 Team memory 做：
- 项目管理
- 进展汇总
- 风险提示
- 经验提取
- 规范总结

也更符合你的真实成功标准：

```text
各项目的进展会每 1~2 天汇总到 Team 记忆库
其他 agent 再基于它做分析和反馈
```

---

## 9. Out of Scope

第一版仍然不做：
- `team sync`
- `team review`
- 发布 lessons / digests 原文
- team-level search
- `--force` 直接提炼

---

## 10. Success Criteria

1. `publish status` 会先判断是否有足够材料发布
2. 若已有 digest → 直接用作高质量 source
3. 若无 digest 且内容足够 → 自动补 phase digest 再发布
4. 若内容不足 → 默认不发布并说明原因
5. Team repo 中得到：
   - `project.md`
   - `current-status.md`（团队可消费摘要）
   - `meta.json`
6. 其他 agent 可以直接基于 `current-status.md` 做跨项目管理/汇总/提炼
