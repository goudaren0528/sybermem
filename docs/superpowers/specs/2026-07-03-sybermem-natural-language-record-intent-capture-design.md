# SyberMem Natural-Language Record Intent Capture 设计

> 把用户自然语言中的“这轮要记录 / 做完提醒我记录”转成 stop hook 可消费的 `.record-intent.json` 状态，补齐 reminder-first 机制的最后一段闭环。

**Date:** 2026-07-03
**Status:** Draft
**Scope:** 只设计记录意图捕获层：明确短语直写、模糊表达确认、与 `/sybermem-record` / `/using-sybermem` / stop hook 协同。不扩展新的 Team / digest 存储能力。
**Parent spec:** `docs/superpowers/specs/2026-07-03-sybermem-reminder-first-stop-nudge-design.md`

---

## 1. Background & Problem

Reminder-first stop/nudge 机制已经有了消费端：
- Stop hook 能读取 `.record-intent.json`
- 在 `auto` / `remind` 模式下给出更强提醒

但目前缺少最关键的生产端：

> **谁来把用户自然语言里的“这轮要记录”写成 `.record-intent.json`？**

如果没有这层，record intent 只能靠手工写文件，无法形成真正的用户体验闭环。

---

## 2. Design Goal

让用户在对话中自然地说：
- “这轮结束提醒我记录”
- “这次要记一条 record”
- “做完这个提醒我 /sybermem-record”

系统就能：
1. 识别这是记录意图
2. 把意图写入：

```text
.sybermem/.record-intent.json
```

3. 后续由任务完成轻提醒 / Stop 兜底提醒消费

---

## 3. Design Choice

### 不选：新增显式命令（如 `/sybermem-mark-for-record`）
缺点：用户还要再记一个命令，不符合“自然语言表达”的偏好。

### 选择：自然语言优先
- **明确短语** → 直接写入 intent
- **模糊表达** → 先确认，再写入 intent

这样既不容易漏，也不容易误触发。

---

## 4. Intent Capture Rules

### 4.1 明确短语（直接捕获）

这类表达语义已经足够清楚，不需要再确认：
- “这轮结束提醒我记录”
- “这次要记一条 record”
- “做完这个提醒我 /sybermem-record”
- “这轮工作要记录到 sybermem”
- “这个完成后我要沉淀一下”

一旦识别到，系统直接写：

```json
{
  "record_intent": true,
  "source": "user-declared",
  "created_at": "2026-07-03T10:00:00+08:00",
  "phrase": "这轮结束提醒我记录"
}
```

### 4.2 模糊表达（先确认）

这类表达可能有记录意图，但不够明确：
- “这个挺重要的”
- “这个后面可能要留一下”
- “感觉这轮值得留痕”

系统先轻量确认：

```text
要不要把这轮工作标记为“结束时提醒我记录”？
```

如果用户确认，再写 `.record-intent.json`。

---

## 5. State File Shape

第一版保持轻量：

```json
{
  "record_intent": true,
  "source": "user-declared",
  "created_at": "2026-07-03T10:00:00+08:00",
  "phrase": "这轮结束提醒我记录"
}
```

### 字段说明
- `record_intent`：核心布尔值
- `source`：第一版至少支持 `user-declared`
- `created_at`：用于后续过期/调试
- `phrase`：保留原始用户表达，便于回溯和调试

---

## 6. Collaboration with Existing Flows

### 6.1 `/sybermem-record`
这是最强绑定关系。

规则：
- 一旦用户执行 `/sybermem-record` 成功完成
- 立即清除 `.record-intent.json`

原因：
- record intent 的目的就是提醒你别忘了记录
- 真正记录完成后，这个状态必须失效

### 6.2 `/sybermem-digest`
弱协同：
- 不自动把 record intent 升级成 digest intent
- 但提醒里可以额外建议“如果这一轮已稳定，也可以考虑 `/sybermem-digest`”

### 6.3 `/sybermem-team-publish`
弱协同：
- 如果当前项目已经有 Team 关联，可以在提醒里顺带提到“记录后也可 `/sybermem-team-publish`”
- 不把 Team publish 强耦合进 record intent 逻辑

### 6.4 `/using-sybermem`
建议未来可见：
- 报告 `Record intent: active / none`
- 如果 `active`，推荐下一步 `/sybermem-record`

---

## 7. Clearing Rules

第一版清除规则：

1. **提醒成功后清除**
   - Stop hook 已输出显式意图提醒后清除

2. **手动 `/sybermem-record` 后清除**
   - 闭环完成，状态失效

3. **不做长期保留**
   - 第一版不让 record intent 跨很多天存在，避免脏状态

---

## 8. De-duplication Rules

### A. 同一份 intent 只提醒一次
- 避免同一轮工作反复刷屏

### B. 已记录后不再提醒
- `/sybermem-record` 成功后必须清除意图状态

### C. 模糊表达未确认不写入
- 避免误触发

---

## 9. Integration Boundary

### 生产端
自然语言识别应发生在：
- 对话层 / skill 层

### 消费端
状态文件由以下层消费：
- 任务完成轻提醒
- Stop 兜底提醒
- `/using-sybermem` 状态报告（未来可见）

这保持了边界清晰：
- 对话层理解语言
- stop hook 执行提醒

---

## 10. Out of Scope

本轮明确不做：
- 新增 `/sybermem-mark-for-record`
- 复杂 NLP 推断
- Team / publish / digest 新存储行为
- 长期保留 record intent

---

## 11. Success Criteria

1. 明确短语可以直接激活 record intent
2. 模糊表达会先确认再激活
3. `.record-intent.json` 能被 stop hook 消费
4. `/sybermem-record` 完成后会清除意图状态
5. 用户不需要记新的标记命令，也能表达“这轮要记录”的意图
