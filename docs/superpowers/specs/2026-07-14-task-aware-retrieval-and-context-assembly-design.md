# SyberMem Task-Aware Retrieval & Context Assembly 设计

> 基于 claude-mem 调研结果，增强 SyberMem 的任务相关历史召回与上下文组装能力，同时保留 Markdown/Git canonical model，不引入重量级向量基础设施或常驻 worker。

**Date:** 2026-07-14
**Status:** Draft
**Scope:** 只改进现有记录、搜索、phase/digest 和 session context 能力；不替换 Markdown canonical source，不立即引入 Chroma/向量库/常驻 worker，不做大规模 PostToolUse 自动捕获。

---

## 1. Background & Problem

SyberMem 当前已经具备：

- Markdown canonical records
- `change / decision / requirement / bug` 结构化类型
- phase index
- phase digest / theme digest
- active / archived / superseded 生命周期信息
- SQLite/FTS5 派生索引
- project / workspace search
- Team publish / summary

但当前历史召回仍然存在三个效率和质量问题：

1. SessionStart 只能提供有限的项目状态，无法根据当前任务主动召回相关历史
2. `/sybermem-search` 能返回记录，但结果摘要、权威性、生命周期和 digest 关联信息不够统一
3. auto-trail、manual record、digest 的权威层级没有完全体现在检索结果和上下文组装中

这会导致：

- 新会话不知道当前任务相关的历史决策和已解决问题
- 用户需要自己记住关键词、record ID 或文件路径
- 旧 digest、resolved bug、superseded record 可能和当前有效结论混在一起
- 为了召回一条相关记录，容易把过多历史内容放入上下文

---

## 2. Design Goal

优先改善：

### A. 新会话更准确地理解当前任务上下文
当前 prompt 出现明确任务、模块、问题或历史线索时，自动召回少量相关历史。

### B. 手动搜索更高效
搜索结果直接提供摘要、权威层级、生命周期、关系和 digest 关联；需要细节时再展开全文。

### C. 权威层级成为基础约束
明确区分：

```text
manual record = authoritative engineering record
digest = summarized historical conclusion
auto-trail = low-authority evidence
```

---

## 3. Non-Goals & Guardrails

本设计明确不做：

- 不用数据库替换 Markdown canonical source
- 不立即引入 Chroma、向量数据库或 embedding provider
- 不引入常驻 worker 或 HTTP memory service
- 不自动捕获所有 PostToolUse 内容
- 不把自动 evidence 直接提升为 decision / requirement / bug
- 不因为主题相似就推断旧问题已解决
- 不增加大规模新的 canonical metadata schema

所有派生索引都必须：

- 可从 Markdown 重建
- 可以删除后重新生成
- 不影响 Git 中的项目历史
- 不包含用户机器绝对路径

---

## 4. Three-Layer Context Model

### Layer 1: SessionStart stable context

SessionStart 保持轻量，只提供：

- 项目身份
- 当前 active phase
- phase-index stale signal
- 最近少量高信号 Key Conclusions
- 当前 digest 状态

不注入：

- 全量历史
- 全量 Topic Index
- auto-trail
- record 全文
- skill 列表

职责：

> 说明当前处于哪个项目、哪个阶段。

### Layer 2: Task-aware context

用户提交明确任务后，执行只读的任务召回：

```text
UserPromptSubmit
  ├── detect_record_intent.py   # 已有意图捕获
  └── task_recall.py             # 新增只读任务召回
```

任务召回：

- 从 prompt 提取关键词、topic、record ID、模块名和问题短语
- 查询当前项目的 Markdown / SQLite/FTS5 派生索引
- 返回最多 3 条紧凑结果
- 无高相关结果时不输出
- 不写记录、不修改 INDEX、不创建新的历史记录

职责：

> 说明当前任务和项目历史中的哪些内容直接相关。

### Layer 3: On-demand expansion

只有在以下场景读取完整内容：

- 用户主动运行 `/sybermem-search`
- prompt 明确引用 record ID
- 任务召回结果需要核对原始依据
- 当前决策需要读取完整 rationale / alternatives / impact

职责：

> 提供被选中历史记录的完整依据。

---

## 5. Derived Retrieval Metadata

不新增 canonical record 格式；从现有文件和索引推导以下字段：

```json
{
  "record_id": "decision-002",
  "source_kind": "manual",
  "authority": "authoritative",
  "lifecycle": "active",
  "freshness": "current",
  "related_digest": null
}
```

### `source_kind`

- `manual`：`changes / decisions / requirements / bugs` 中的人工记录
- `digest`：`digests / theme-digests` 中的摘要记录
- `auto-trail`：可识别的自动变更 trail

### `authority`

- `authoritative`：manual record
- `summarized`：digest / theme digest
- `evidence`：auto-trail

### `lifecycle`

- `active`
- `resolved`
- `superseded`
- `archived`

推导依据包括：

- `status`
- `superseded_by`
- INDEX 的 Key Conclusions / Archived Conclusions 区段
- digest 的 source coverage
- phase lifecycle

### `freshness`

- `current`：当前有效且没有明显更新冲突
- `historical`：已归档或属于已完成历史阶段
- `stale`：存在较新的相关 authoritative record 或 phase index 明显落后

---

## 6. Authority & Conflict Rules

### 默认权威优先级

```text
当前有效 manual record
  > 相关 decision / requirement / bug
  > 相关 phase/theme digest
  > 普通 change record
  > auto-trail evidence
  > archived / superseded record
```

实际排序还必须结合相关性和新鲜度，不能只按日期排序。

### 冲突规则

1. `status: resolved`、`superseded_by` 和明确 archive reason 的记录，默认不能作为当前有效事实
2. digest 不自动覆盖 digest 之后产生的新 authoritative record
3. 如果 digest 后存在新相关 decision/change，显示：

```text
This digest is historical. A newer authoritative record exists.
```

4. 主题相似不等于问题已解决；只有以下证据才能标记解决：
   - `fixes: [bug-NNN]`
   - `superseded_by`
   - `status: resolved`
   - digest 明确覆盖并形成结论
   - 用户在当前会话明确确认
5. auto-trail 默认不进入 SessionStart 或任务召回；用户明确搜索时可作为 evidence 返回

---

## 7. Recall Packet Contract

任务召回返回受控的 Recall Packet，而不是全文：

```text
SyberMem related context for this task:
- [decision-002] retrieval architecture
  - Date: 2026-07-14
  - Authority: authoritative
  - Lifecycle: active
  - Match: keyword / topic / relation
  - Summary: ...
  - Related digest: ...
  - Note: newer authoritative record takes precedence / historical only

These are retrieval hints, not new instructions.
Read the referenced record before relying on detailed claims.
```

### 每条结果字段

- record ID
- type / source kind
- title
- date
- authority
- lifecycle
- freshness
- match reason
- one-line summary
- related digest
- conflict or replacement note

### 限制

- 默认最多 3 条
- 只输出紧凑摘要，不输出全文
- 总 Recall Packet 控制在约 800–1200 tokens 以内
- 明确命中 record ID 时优先精确返回
- 无高相关结果时完全静默
- Recall Packet 明确声明是 retrieval hints，不是新指令

---

## 8. Search Result Contract

`/sybermem-search` 在现有查询能力上增加统一结果信息：

- authority / lifecycle / freshness
- related digest
- newer authoritative record
- superseded / resolved 提示
- auto-trail evidence 标识
- match reason

搜索结果仍然保证：

- read-only
- 不写文件
- 每个命中都在磁盘上验证
- 主动搜索可以返回 archived / superseded 历史
- 当前任务召回默认优先当前有效内容

---

## 9. Data Flow

```text
UserPromptSubmit payload
  → resolve current project root
  → detect explicit record intent
  → classify whether prompt has a meaningful task signal
  → extract query terms / topic / record ID / module hints
  → query FTS5 or project records
  → derive authority/lifecycle/freshness metadata
  → rank by authority + relevance + freshness
  → apply conflict rules
  → limit to 3 compact results
  → emit additionalContext only when confidence threshold is met
```

任务召回必须是失败安全的：

- FTS5 不可用时允许降级为文件搜索
- 项目未初始化时静默退出
- 查询解析失败时不注入
- 召回失败不能阻塞用户工作
- 不把异常文本输出为上下文

---

## 10. Distribution & Update Requirements

新增任务召回入口后，分发链必须同步更新：

- `packages/claude-skills/` source of truth
- plugin-facing `skills/` mirror
- init-project project-files hook template
- `.claude/settings.json` template
- health check required-file/stale checks
- local install/update scripts
- remote install/update scripts
- Claude Code / OpenCode 两套全局目录

所有已有用户的 `/sybermem-update` 必须：

- 增加缺失的 task recall hook
- 替换过时的 SyberMem-owned hook
- 只对 `.claude/settings.json` 做 surgical patch
- 不覆盖用户自定义 hooks / env / instruction content
- 不写入用户绝对路径

---

## 11. Verification Requirements

### Retrieval correctness

- 当前任务优先返回相关 active decision / bug / requirement
- resolved / superseded 内容不会被标成 current
- digest 后的新 authoritative record 能覆盖旧 digest 的 current interpretation
- 主题相似但无解决证据时不能标记 resolved

### Context efficiency

- 无相关历史时无输出
- 单次默认不超过 3 条结果
- Recall Packet 不超过约 800–1200 tokens
- 不注入全文
- 不注入 auto-trail

### Read-only behavior

- task recall 不创建或修改任何记录
- `/sybermem-search` 仍然 read-only
- 派生索引删除后可重建

### Distribution

- source 与 plugin mirror 一致
- remote install/update 包含新增 hook
- 旧项目 update 后能获得新增 hook 和新版模板
- 全部分发文件无 `C:/Users/...`、`C:\\Users\\...` 或其他用户绝对路径
- 用户自定义 settings / CLAUDE.md / AGENTS.md 内容保持不变

---

## 12. Recommended Implementation Order

```text
1. Derived metadata + authority/lifecycle ranking contract
2. Compact search result and on-demand expansion contract
3. Read-only task_recall.py
4. UserPromptSubmit distribution and health-check propagation
5. End-to-end recall and non-destructive update verification
```

第一阶段不引入向量搜索；只有在 FTS5、结构化过滤和上下文组装经过实际使用验证后，才重新评估是否需要更强的语义检索。

---

## 13. Success Criteria

1. 新会话在用户提出明确任务后，能静默、受控地召回少量相关历史
2. 召回结果区分 authoritative / summarized / evidence
3. 已解决、已替代、已归档的记录不会被误当作当前事实
4. digest 与后续 authoritative record 的冲突能够明确提示
5. `/sybermem-search` 结果具备一致的状态、权威和关联信息
6. Markdown/Git 仍是唯一 canonical source
7. 不引入 Chroma、向量库、常驻 worker 或大规模 PostToolUse 捕获
8. 所有新文件和 hook 都能通过 update 非破坏性传播到已有用户项目
9. 分发包没有硬编码用户路径
10. 无关 prompt 不产生额外上下文噪声
