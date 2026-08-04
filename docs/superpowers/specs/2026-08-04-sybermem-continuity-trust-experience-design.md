# SyberMem 项目连续性与可信记忆体验方案

**Date:** 2026-08-04  
**Status:** Proposed  
**Scope:** Project / Hub / Team 的连续性恢复、任务召回、记录路由与发布可信度

## 1. 目标

在不改变 SyberMem 核心记忆模型的前提下，降低跨会话重启成本，让用户和管理 agent 能够判断召回内容是否可靠，并以更少的流程摩擦完成记录、纠正、digest 和 Team 发布。

本方案服务于四个目标：

1. 新会话快速恢复项目当前状态和下一步。
2. 任务召回只显示少量、相关、可解释的历史内容。
3. 记忆写入先分类和确认，避免探索过程污染长期记忆。
4. Project、Hub、Team 的摘要明确来源、新鲜度、冲突和审核状态。

## 2. 设计边界

### 保留

- `.sybermem/` Markdown 作为 Project canonical source。
- SQLite/FTS5 只作为可删除、可重建的派生索引。
- Project / Hub / Team 三作用域及项目自治原则。
- manual record、digest、auto-trail 的权威层级。
- 现有 `task_recall`、phase index、digest、relations、Team publish 管线。
- OpenCode 不支持逐次 prompt 自动注入时的手动搜索/compaction 备用路径。

### 不引入

- 第二套项目记忆目录或第二套 current-state 文件。
- 向量数据库、常驻 worker、后台 memory service。
- 对所有对话或 PostToolUse 内容进行静默全量捕获。
- 复杂 receipt/lease/provenance 状态机作为普通记录的前置条件。
- 自动把 inferred、imported 或 auto-trail 内容提升为 authoritative fact。

## 3. 方案选择

### 方案 A：局部增强现有能力

在现有 task recall、summary、record 和 Team publish 输出中增加少量字段与提示。

- 优点：改动小、风险最低、能快速验证。
- 缺点：恢复、召回、记录和发布的体验仍可能分散。

### 方案 B：轻量连续性体验层（推荐）

增加统一的只读 resume checkpoint 和 source-aware recall packet，但底层继续调用现有 search、retrieval、phase、digest 和 publish 能力。

- 优点：形成一致入口，不重复建设记忆存储；可以分阶段落地。
- 缺点：需要统一输出契约和状态语义。

### 方案 C：独立记忆引擎

新增独立 current-state、事件日志、写入协议和检索引擎。

- 优点：理论上可以形成完整新产品。
- 缺点：与现有 canonical records、digest、relations、Project/Hub/Team 重复，迁移和一致性成本高。

**选择：方案 B。** SyberMem 当前缺的主要是连续性体验包装、可信度展示和操作路由，不是另一套记忆存储。

## 4. 核心能力

### 4.1 Resume checkpoint

新增统一的只读恢复入口，支持自然语言和可选 skill/CLI 入口：

```text
继续这个项目
恢复当前项目上下文
从上次停下的地方继续
```

输出固定包含：

- project identity
- current active phase
- recent authoritative progress
- active risks / blockers
- recommended next action
- confidence
- freshness
- reason for the recommendation

读取分层：

- `fast`：项目身份、phase、当前状态、下一步。
- `standard`：fast + 当前 digest、关键风险、最新高权威记录。
- `deep`：standard + 用户明确要求的历史依据和完整记录。

Resume 只恢复和推荐，不自动执行 `next action`，也不自动写入记忆。

### 4.2 Source-aware recall packet

所有自动任务召回和主动搜索结果统一携带：

```json
{
  "record_id": "decision-002",
  "record_type": "decision",
  "source_kind": "manual",
  "authority": "authoritative",
  "lifecycle": "active",
  "freshness": "current",
  "match_reason": ["keyword", "relation"],
  "related_digest": null,
  "conflict_note": null
}
```

默认仍然最多返回 3 条紧凑结果；无高相关结果时静默。召回结果必须明确声明它们是 retrieval hints，不是新指令。

### 4.3 可信度与新鲜度

可信度是读取路由和用户判断信号，不是普通读取的硬阻塞。

建议状态：

- `current`：有效且无明显新旧冲突。
- `historical`：已完成阶段、归档或仅供历史参考。
- `stale`：存在更新的 authoritative record、digest 或 phase index 落后。
- `conflicted`：多个来源强度接近且无法安全判断优先级。

高影响操作才要求 review：digest promotion、cross-project promote、Team publish、覆盖当前状态和结构化修复。

### 4.4 Suggest → Plan → Confirm → Write

在现有 record intent 和 reminder-first 机制上统一记录路由：

1. `suggest`：生成脱敏候选，不写入。
2. `plan`：判断目标类型和最小写入路径。
3. `confirm`：需要确认时只问一个明确问题。
4. `write`：通过现有 Core/CLI 完成确定性写入。

记录类别：

- `change`
- `decision`
- `requirement`
- `bug`
- `digest`
- `no_write`
- `defer`
- `blocked`

重复内容应返回 duplicate/no-op；不稳定讨论应 defer；敏感内容应 blocked；普通探索不应主动写入。

### 4.5 Correction / Supersession

历史记录不静默覆盖。纠正流程创建新记录，并通过 `superseded_by`、`fixes` 或相关关系连接旧记录。

用户看到旧记录时，应明确显示：

```text
该记录已被 <new-record-id> 替代，当前应以新记录为准。
```

这条规则同时作用于 Project search、Hub search 和 Team summary。

### 4.6 Team publish trust envelope

Team 发布和管理摘要附带：

- source revision / source hash
- published-at
- source scope
- local changes after publish
- stale / conflict / review-required
- recommended next action

Team 只接收主动发布和审核后的内容；Project canonical truth 不被 Team 反向覆盖。

### 4.7 Lightweight preview binding

对 digest、theme digest、promote 和 Team publish 这类高影响动作：

1. 生成只读 preview。
2. 记录当前 workspace revision/source hash。
3. 执行前重新检查是否发生变化。
4. 变化后要求重新生成 preview。

普通 record 不要求复杂 receipt/lease；只使用现有 revision 和确定性 Core/CLI 写入能力。

## 5. 数据与调用流

```text
User prompt / resume request
  -> resolve project scope
  -> read current phase/status
  -> query existing search/retrieval index
  -> derive authority/lifecycle/freshness
  -> apply conflict and abstention rules
  -> build bounded resume or recall packet
  -> show reason and next action
```

记录路径：

```text
work signal
  -> record suggestion
  -> record plan
  -> explicit confirmation when required
  -> Core/CLI write
  -> update index / nudge / next-step router
```

发布路径：

```text
Project records/digests
  -> preview + revision check
  -> publish status
  -> Team current-status/meta/dashboard
  -> management summary
```

## 6. 失败安全规则

- 没有可靠命中时不注入。
- FTS 不可用时允许降级为文件搜索。
- 项目未初始化时静默或给出明确初始化建议，不阻塞业务任务。
- 召回失败不能阻塞用户工作。
- 历史记录不能被误标为 current。
- stale/conflicted 读取可继续，但高影响写入必须 review。
- Team 发布失败不得修改 Project canonical records。
- OpenCode 继续提供手动 `/sybermem-search` 和 compaction 路径。

## 7. 成功标准

1. 用户可以用一句自然语言恢复项目当前状态。
2. Resume 默认只返回当前状态、风险和下一步，不展开全量历史。
3. 每条召回结果能说明来源、权威性、生命周期、新鲜度和命中原因。
4. 弱相关或冲突结果默认不注入或明确标记 review。
5. 记录动作先分类和计划，不因普通探索静默写入。
6. 旧记录纠正后仍可审计，并能明确指向新记录。
7. Team 摘要能显示来源版本、未发布变更和审核状态。
8. Markdown/Git 仍是唯一 canonical source。
9. 删除派生索引后可以完全重建。
10. 不引入向量库、常驻 worker、第二套记忆目录或复杂普通写入协议。

## 8. 分阶段范围

### Phase 1：Resume 与可信召回包

只读、低风险。统一 resume 输出，补齐 source-aware recall packet、freshness 和 abstention。

### Phase 2：记录路由与纠正体验

复用现有 record intent、stop hook、relations，增加 suggest/plan/no-write/defer/blocked 语义和 supersession 提示。

### Phase 3：Hub/Team 可信状态

在 workspace search、portfolio、Team publish 和 management summary 中显示 stale/unpublished/conflict/review-required。

### Phase 4：高影响操作 preview

为 digest、promote、Team publish 增加轻量 preview revision/source hash 检查。

## 9. 不在本方案内

- 向量检索或 embedding provider。
- 全量对话记忆。
- 自动生成并自动发布 Team 经验。
- 后台 daemon / watcher / 常驻服务。
- 替换既有 record、digest、phase index 或 Team Git 模型。
