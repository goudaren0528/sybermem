# SyberMem Workflow Router / Next-Step Nudge Layer 设计

> 在不继续扩功能范围的前提下，强化当前核心能力之间的衔接：做完一轮工作后，系统优先判断你现在更该 `/sybermem-record`、`/sybermem-digest`，还是 `/sybermem-team-publish`。

**Date:** 2026-07-03
**Status:** Draft
**Scope:** 只设计下一步动作的路由与提醒层，不新增新的业务能力；目标是提高入口清晰度、提醒节奏和摘要原料质量。

---

## 1. Background & Problem

当前 SyberMem 的核心能力已经很多：
- `/sybermem-record`
- `/sybermem-digest`
- `/sybermem-team-publish`
- `/sybermem-team-summary`
- `/using-sybermem`

问题不再是“没有功能”，而是：

> **做完一轮工作后，用户经常不知道此刻最应该先做哪个动作。**

典型困惑：
- 这轮应该先 `/sybermem-record` 吗？
- 还是已经积累 enough material，应先 `/sybermem-digest`？
- 还是项目已经很久没同步到 Team memory，应先 `/sybermem-team-publish`？

如果系统不帮用户做这个优先级判断，就会出现：
- 漏掉 record
- record 很多了但没有 digest
- digest 已经有了但迟迟不 publish
- Team summary 质量偏薄

---

## 2. Design Goal

在现有能力上加一层：

> **Workflow Router / Next-Step Nudge Layer**

作用不是执行新业务，而是：
- 判断当前最值得的下一步动作
- 在合适入口提示用户
- 一次只推荐一个最优先动作

---

## 3. Core Priority Order

优先级固定为：

```text
record > digest > team-publish
```

### 3.1 `/sybermem-record`（最高优先级）
如果一轮高价值工作还没有正式记录，则优先提醒 `record`。

原因：
- record 是所有下游动作的原料层
- 没有高质量 record，digest 和 Team publish 都会变薄

### 3.2 `/sybermem-digest`（第二优先级）
如果当前 phase 已积累 enough material，但还没有 digest，则优先提醒 `digest`。

原因：
- digest 能显著提高项目级和 Team 级摘要质量
- publish 不应优先推送还没沉淀好的内容

### 3.3 `/sybermem-team-publish`（第三优先级）
如果项目内信息已整理好，但较久未同步到 Team memory，则提醒 `team-publish`。

原因：
- Team publish 是分发，不是原料生产
- 它应该排在 record 和 digest 之后

---

## 4. Trigger Conditions

### 4.1 Trigger for `/sybermem-record`
满足任一条件：
- 本轮工作形成高价值实现/决策/修复/打通
- 只有 auto trail，没有正式高信号记录
- 用户显式说过“这轮要记录”

### 4.2 Trigger for `/sybermem-digest`
满足任一条件：
- 当前 phase 相关 records 已明显积累
- 当前阶段已经有 completed / stable 信号
- recent same-theme cluster 达阈值
- Team summary / current-status 仍然很薄，缺 digest 支撑

### 4.3 Trigger for `/sybermem-team-publish`
满足任一条件：
- 项目已有关联 Team repo
- 距离上次 publish 超过阈值（例如 1~2 天）
- 本轮已经新增高质量 record / digest / summary 变化

---

## 5. Surface / Entry Points

### 5.1 `/using-sybermem`
这是主动诊断入口，应成为最稳定、最权威的下一步推荐面。

输出中明确包含：

```md
## Recommended next step
- /sybermem-record
```

或：

```md
## Recommended next step
- /sybermem-digest
```

### 5.2 任务完成轻提醒
这是即时 nudges 层，主要用于：
- `/sybermem-record`
- `/sybermem-digest`

不建议在这里优先推 `team-publish`，因为 publish 更偏分发动作，通常在项目内信息整理好之后才更合理。

### 5.3 Stop hook 兜底提醒
这是最后一道防线。若用户结束会话时仍未处理高优先级动作，则按优先级只提醒一个：
- record
- digest
- team-publish

### 5.4 Team publish / Team summary 之后的顺手建议
这些不是主提醒入口，只用于轻量后续提示：
- publish 之后可建议 `team-summary`
- team-summary 之后可建议某个项目先补 digest

---

## 6. Anti-Noise Rules

### Rule 1: 同一轮工作只提醒一次
如果任务完成轻提醒已经提示过 `/sybermem-record`，则 Stop hook 不应立即重复同一条提醒，除非用户仍未处理且会话真的要结束。

### Rule 2: 相同类型提醒要有 cooldown
例如：
- 今天刚提示过 digest
- 如果没有明显新增变化，则不要频繁重复提醒 digest

### Rule 3: 一次只推荐一个动作
不要同时丢给用户：
- record
- digest
- publish

必须帮用户排优先级，只给一个最优先动作。

### Rule 4: 提醒文案目标导向
好的提醒：

```text
这轮工作已经形成高价值变化，建议先 /sybermem-record。
```

不要出现：

```text
你也许可以 record、digest、publish。
```

---

## 7. Why This Matters

这一层不会增加新业务能力，但会显著改善：
- **入口清晰度**：减少“我现在该做哪个”的犹豫
- **提醒节奏**：更贴近真实工作完成时机
- **摘要质量**：因为高优先级的 record/digest 更不容易漏掉

也就是说，它是一个：

> **以用户工作节奏为中心的能力强化层**

而不是另一个功能扩张层。

---

## 8. Out of Scope

本轮明确不做：
- 新增 Team / digest / publish 能力
- 新增新的业务命令
- 改 Team repo 数据模型
- 自动执行 record/digest/publish（只做提醒和路由）

---

## 9. Success Criteria

1. 系统可以在合适入口判断当前最值得的下一步动作
2. 优先级固定为：`record > digest > team-publish`
3. 每次只给用户一个最优先动作
4. 提醒不会太吵，有去重和 cooldown
5. 用户在一轮工作完成后，不再经常犹豫“先 record、digest，还是 publish”
