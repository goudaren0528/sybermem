# SyberMem Reminder-First Stop/Nudge 设计

> 将当前偏自动 trail 的 stop hook 机制重构为更贴近真实工作节奏的“提醒优先”机制：任务完成时轻提醒，会话结束时兜底提醒，并修正 `remind` 模式语义。

**Date:** 2026-07-03
**Status:** Draft
**Scope:** 只设计提醒机制本身：显式记录意图、任务完成轻提醒、Stop 兜底提醒、`auto/remind` 模式语义修正。不扩展 Team / publish / digest 存储能力。

---

## 1. Background & Problem

当前 SyberMem 的自动能力主要建立在：
- `.claude/settings.json` 中的 `SYBERMEM_RECORD_MODE`
- `Stop` hook 调用 `.sybermem/hooks/record_change_on_stop.py`

但实际使用中存在两个明显问题：

1. **提醒时机不对齐**
   - 当前主要在会话结束（Stop hook）时才发生
   - 用户在“完成一轮任务”时感知不到提醒

2. **`remind` 模式语义有缺口**
   - 现有实现里 `should_auto_record()` 仅当模式是 `auto` 时返回真
   - 这意味着 `remind` 模式几乎等于直接退出，既不自动记录，也不真正提醒

用户的真实需求不是“系统自动乱记”，而是：
- 做一些任务时获得记录提醒
- 如果事先说明“这轮要记录”，系统在关键节点更懂得提醒
- 会话结束时不要漏

因此，当前机制应从“自动 trail 优先”调整为：

> **提醒优先，自动 trail 兜底。**

---

## 2. Design Goal

重构当前的 stop/nudge 机制，使它更像一个：

> **任务结束提醒系统**

而不是单纯的：

> **自动 change trail 生成器**

新的机制应满足：
1. 工作中当一轮任务看起来已经完成时，给出一次轻提醒
2. 如果用户明确表达“这轮要记录”，提醒优先级明显提高
3. 会话结束时，如果仍未记录且本轮工作是高信号变化，再做一次兜底提醒
4. `remind` 模式必须真正只提醒、不自动写记录

---

## 3. Core Model

### 3.1 Two-Layer Reminder Model

#### Layer A: Task-completion nudge（轻提醒）
触发时机：
- 系统判断一轮任务/子任务已经完成
- 或者用户显式表达过“这轮要记录”

输出风格：
- 轻、非阻塞、不反复刷屏
- 例如：

```text
这轮工作已经形成高价值变更，建议稍后用 /sybermem-record 沉淀。
```

#### Layer B: Stop-time fallback nudge（兜底提醒）
触发时机：
- 当前会话结束时
- 本轮存在高信号变化
- 本轮还没有显式 `/sybermem-record`
- 且用户表达过记录意图，或变化模式足够重要

输出风格：

```text
这轮工作看起来值得记录为 SyberMem 项目记录。建议现在运行 /sybermem-record。
```

必要时也可补充：

```text
如果这轮属于一个已稳定阶段，也可以考虑 /sybermem-digest。
```

---

## 4. Explicit Record Intent

### 4.1 User-facing requirement

用户希望通过自然语言显式表达“这轮要记录”，而不是再记一个新命令。

### 4.2 First-version intent detection

第一版只做**可靠短语识别**，不做复杂 NLP 推断。

可识别的意图示例：
- “这轮结束提醒我记录”
- “这次要记一条 record”
- “做完这个要沉淀一下”
- “完成后提醒我 /sybermem-record”
- “这轮工作要记录到 sybermem”

### 4.3 Internal session state

一旦识别到这些短语，会话内设置：

```text
record_intent = true
```

该状态只在当前会话有效，用于：
- 增强轻提醒
- 增强 Stop 兜底提醒

第一版不要求把这个意图持久化到磁盘。

---

## 5. Mode Semantics Refactor

### 5.1 `auto`
保持：
- 自动 trail（change-only）
- 轻提醒
- Stop 兜底提醒

即：

```text
auto = 自动记录 + 提醒
```

### 5.2 `remind`
修正为：
- 不自动写 trail
- 但仍执行：
  - 任务完成轻提醒
  - Stop 兜底提醒

即：

```text
remind = 只提醒，不自动记录
```

### 5.3 Why this matters

这与用户直觉和文档描述一致：
- `auto` 更偏“系统帮你兜底”
- `remind` 更偏“你自己来决定是否记，但系统别忘了提醒你”

---

## 6. Trigger Heuristics

### 6.1 Task-completion nudge triggers

第一版建议满足任一条件即可：

1. `record_intent = true`
2. 当前一轮工作出现明确“完成信号”，例如：
   - “完成了”
   - “打通了”
   - “已经可以用了”
   - 某个 spec / plan / implementation / dogfood 闭环完成
   - 一条高价值 Team / Hub / digest / publish / summary 能力完成

### 6.2 Stop-time fallback triggers

在 Stop hook 中满足任一条件可提醒：
- `record_intent = true`
- 本轮高信号变化明显
- 当前变化已经形成 cluster，值得记录或 digest

### 6.3 De-duplication

轻提醒必须去重：
- 同一轮工作只提醒一次
- 避免每条消息都重复提示

Stop 兜底提醒也应避免短时间重复刷屏。

---

## 7. Relationship with Auto Trail

### Current role of auto trail

自动 trail 仍有价值：
- 防止完全没有历史
- 作为最弱兜底
- 捕获文件变化线索

### New role after refactor

它不再是主角，而是：

> **提醒机制的辅助层 / 最弱兜底层**

高价值工作仍应鼓励：
- `/sybermem-record`
- `/sybermem-digest`

---

## 8. UX Principles

1. **提醒优先，不是自动记录优先**
2. **轻提醒要像工作节奏提示，而不是打断**
3. **Stop 提醒只做兜底，不应成为唯一提醒时机**
4. **自然语言意图优先于纯文件模式推断**

---

## 9. Out of Scope

本轮不做：
- 新增 `/sybermem-mark-for-record` 命令
- Team / publish / digest 存储能力扩展
- 用复杂 LLM 推断用户是否想记录
- 自动为非 `change` 类型创建记录

---

## 10. Success Criteria

1. `remind` 模式真正可用：只提醒，不自动写记录
2. 用户自然语言表达“这轮要记录”后，系统在本轮任务完成时更容易提醒
3. 即使任务过程中没提醒到，会话结束时仍有兜底提醒
4. 提醒比当前更贴近工作完成时机，而不是只在 Stop hook 出现
5. 不需要新命令也能表达“这轮要记录”的意图
