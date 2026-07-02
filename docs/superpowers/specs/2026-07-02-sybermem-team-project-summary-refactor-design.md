# SyberMem Team Project Summary Refactor 设计

> 将 Team repo 中的 `current-status.md` 从“薄状态快照”升级为“团队可直接消费的项目摘要”，优先回答：最近做了什么、当前在解决什么、风险和下一步。

**Date:** 2026-07-02
**Status:** Draft
**Scope:** 只重构 Team repo 单项目 `current-status.md` 的内容语义与生成逻辑；不改变 Team repo 目录结构，不引入新文件名，不扩展 lesson/review/search。
**Parent specs:**
- `docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseB-design.md`
- `docs/superpowers/specs/2026-07-02-sybermem-team-agent-consumption-layer-phaseE-design.md`

---

## 1. Background & Problem

当前 Team repo 中的单项目文件形态是：

```markdown
# sybermem — Current Status
- Updated at: ...
- Source commit: ...

## Active Phase
- phase-010 — Search, relations, and theme digest

## Recent Records
- change-019
- change-020
- change-021

## Open Bugs
- bug-001

## Open Requirements
- requirement-003
- requirement-002
- requirement-001

## Next
- none
```

这个结构能表达“系统记录了什么”，但不能回答管理视角真正关心的问题：
- 最近做了什么进展？
- 当前在解决什么问题/目标？
- 风险和注意事项是什么？
- 下一步是什么？

结果是：
- 对人类管理者不友好
- 对管理 agent 也不够友好
- 只能作为机械状态快照，难以作为治理输入

---

## 2. Design Goal

保留文件路径不变：

```text
projects/<slug>/current-status.md
```

但将它的内容升级为：

> **Team Project Summary**

使它优先回答三类问题：
1. 最近做了什么进展
2. 当前在解决什么问题 / 目标
3. 风险和下一步

而 phase / open bugs / open requirements / digest source 降级为辅助信号。

---

## 3. Design Choice

### 不选：新增 `manager-summary.md`
优点：不破坏现有 `current-status.md`
缺点：入口分裂；项目目录下文件变多；管理 agent 仍要知道读哪个。

### 不选：保留现状，只在 `current-status.md` 里插入少量 digest 片段
优点：改动小
缺点：结构容易混杂，主叙事仍旧被 record IDs 与状态项淹没。

### 选择：保留文件名 `current-status.md`，重构为 Team Project Summary
优点：
- 不改变 Team repo 结构
- 入口最清晰
- 直接服务管理视角
- 最利于 Phase E 的 summary 继续下钻

---

## 4. New `current-status.md` Shape

### 目标结构

```markdown
# sybermem — Team Project Summary

- Updated at: 2026-07-02T12:12:05+08:00
- Source commit: 8ed4e25

## Current Focus
- 正在把多项目工程记忆稳定汇总到 Team repo
- 当前重点是夯实管理 agent 的低成本消费层入口

## Recent Progress
- 完成了 Team MVP Phase D：项目自动记住 Team 关联
- 完成了 Team MVP Phase E：生成 management summary 消费层
- 已将 teamspark 接入 Team repo 并完成多项目 dogfood

## Risks / Attention
- teamspark 仍缺高质量 digest，Team 侧输入质量不均衡
- 全局 CLI 与当前仓库能力偶尔存在版本滞后

## Next
- 提升 teamspark 的 phase / digest 质量
- 继续验证多项目 publish cadence 的稳定性

## Supporting Signals
- Active Phase: phase-010 — Search, relations, and theme digest
- Open Bugs: 1
- Open Requirements: 3
- Source Digests: phase digest available, theme digest available
```

---

## 5. Data Sources and Priority

### Layer A: digest / theme digest（最高优先级）
如果当前项目有：
- phase digest
- theme digest

则优先从中提炼：
- `Current Focus`
- `Recent Progress`
- `Risks / Attention`
- `Next`

### Layer B: recent records（补缺）
当 digest 不存在或信息不足时，从最近的：
- change
- decision
- bug
- requirement

提炼出 2~4 条对管理视角有意义的项目进展和风险。

### Layer C: project status signals（兜底）
现有 `project status` 结构继续保留，但只用于：
- Active Phase
- Open Bugs
- Open Requirements
- Next（若结构中有可靠内容）

并统一收纳到 `Supporting Signals`。

---

## 6. Section Rules

### 6.1 `Current Focus`
- 优先来自最新 phase/theme digest 的主题句
- 若无 digest，则从 recent changes/decisions/requirements 聚类后提炼 1~2 条
- 不直接写 phase id 当主叙事

### 6.2 `Recent Progress`
- 优先使用 digest 中已经沉淀的结果条目
- 否则从 recent records 中挑 2~4 条最有管理意义的变化
- 不允许直接展示 `change-019` / `decision-001` 这类 ID 作为主条目

### 6.3 `Risks / Attention`
来源包括：
- open bugs / open requirements
- stale / no active phase
- recent bug/requirement records 的风险语义

只保留 1~3 条最值得管理关注的事项。

### 6.4 `Next`
来源包括：
- digest 中明确提到的下一步
- active/completed phase 的自然后续
- `project status.next`

不允许默认写 `none` 作为唯一内容，除非确实没有任何可判断的下一步。

### 6.5 `Supporting Signals`
保留结构化指标，但降级为辅助信息：
- Active Phase
- Open Bugs
- Open Requirements
- Source Digests

---

## 7. Cost / UX Principles

### 成本控制
- 每个区块只生成少量 bullet：
  - Current Focus：1~2 条
  - Recent Progress：2~4 条
  - Risks / Attention：1~3 条
  - Next：1~2 条
- 优先重用已有 digest，而不是每次全量重读 raw records

### 体验原则
- 打开项目摘要文件时，第一眼先看到“在做什么 / 做了什么 / 风险 / 下一步”
- IDs 和结构化状态项不消失，但退居辅助区

### 兼容性
- 文件路径不变
- Team repo 下游结构不变
- Phase E 的 `latest-management-summary.*` 仍可继续读取该文件，只需适配新的 section 解析规则

---

## 8. Out of Scope

本轮明确不做：
- 重命名 `current-status.md`
- 新增 `manager-summary.md`
- 引入自然语言长段落总结
- 发布 digest 正文到 Team repo
- lesson/review/search 新能力

---

## 9. Success Criteria

1. Team repo 中的 `current-status.md` 不再以 record IDs 作为主内容
2. 单项目摘要优先展示：
   - Recent Progress
   - Current Focus
   - Risks / Attention
   - Next
3. 管理者阅读单个项目文件时，能一眼看懂“这个项目最近在做什么”
4. Phase E 的 Team summary 后续可以基于这个更高质量摘要继续生成
