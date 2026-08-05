# SyberMem 热路径与存储效率方案

**Date:** 2026-08-05
**Status:** Proposed
**Scope:** per-prompt hooks / project search / stop hook / auto-trail 存储
**Source:** docs/audit/2026-08-05-sybermem-comprehensive-audit.md §2（已复核属实，实测 ~517ms/prompt）

## 1. 背景与实测

审计 §2 已复核并实测确认：

- **每 prompt 双 hook 合计 ~517ms**（51 条记录时）：`detect_record_intent.py` (~188ms) + `task_recall.py` (~200ms) 两个独立 Python 进程，各自 read stdin / resolve root / import core。
- **项目搜索全扫非 FTS**：`search_project()` 每次 `[parse_record_file(rf) for rf in iter_record_files(root)]`（search.py:176）；`compact_project_search` 空结果时二次全扫（:218）。O(records) 且随记录线性增长。
- **stop hook 过重**：3 次 git 列举 + `count_commits_since_last_record()` 扫 4 目录（classify_followup 里可能调 2 次）+ `recommend_next_step()` 再 parse 全量 + `next_change_id` 扫 changes/ + 写 md + 重写 INDEX。全在 60s 同步路径。
- **auto-trail 污染**：51 条记录中 26 条 auto-trail，每次 stop 写一个 md + 重写 INDEX.md，且全程参与 parse/index/search/dedup。

## 2. 设计目标

按性价比排序，降低每 prompt / 每 stop 的固定与线性成本，不改变记忆语义与 canonical 存储。

1. 合并两个 prompt hook 为单进程（省一次进程启动 + import + root 解析）。
2. 项目搜索加会话级缓存，避免每 prompt 全量重解析 + 消除二次全扫。
3. stop hook 瘦身：next-id / 最新记录日期落 state；去重 commit-gap 重复计算。
4. auto-trail 改为有界滚动 journal，停止每 stop 写 markdown + 重写 INDEX（**范围决策点，见 §5**）。

## 3. 设计边界

### 保留
- `.sybermem/` Markdown 作为 canonical source。
- 两个 hook 的**对外行为**：intent 捕获写 `.record-intent.json`、recall 输出 `additionalContext` packet。
- hook「fail open」原则：任何异常/无项目根都静默返回 0，绝不阻塞 prompt。
- 现有 `compact_project_search` 的检索质量与排序。
- 三份 hook 分发副本的一致性（`.sybermem/hooks/`、两个 `project-files/.sybermem/hooks/`）。

### 不引入
- 常驻 worker / 后台服务 / 向量库。
- 破坏 hook 输出契约的改动。
- 把 auto-trail 语义从「派生证据」提升为「权威记录」。

## 4. 方案（分级，低风险优先）

### 4.1 项目搜索会话级缓存（低风险，高收益）

- 在 `search.py` 内对「解析后的记录集合」按 `(root, 记录目录 mtime 指纹)` 做进程内 memoize。
- 同一进程内多次 `search_project` / `compact_project_search` 复用已解析集合。
- `compact_project_search` 复用第一遍 `search_project` 已解析的 `all_rows`，**消除二次全扫**（当前 line 218 的重复 `iter_record_files`）。
- 失效：目录 mtime 变化即重解析。单 prompt 内 hook 只启动一次进程，缓存主要收益在「一次 prompt 内避免重复解析」+「消除 fallback 二次扫」。

> 注意：hook 是每 prompt 新进程，进程内缓存不跨 prompt。真正跨 prompt 的持久缓存（SQLite）收益更大但风险更高，列为**后续可选**，本方案先做进程内缓存 + 消除二次扫这两个确定性收益。

### 4.2 合并两个 prompt hook 为单进程（中风险，高收益）

- 新增单一入口（如 `.sybermem/hooks/user_prompt.py`），内部顺序执行：
  1. read stdin payload 一次。
  2. resolve root 一次。
  3. import core 一次。
  4. 先跑 intent 检测（廉价正则 + classifier），命中则写 `.record-intent.json`。
  5. 再跑 recall（`compact_project_search`），有结果则输出 `additionalContext` packet。
- `.claude/settings.json` 模板从两个 UserPromptSubmit hook block 改为一个。
- **保留两个旧文件**为兼容（或让新入口 import 旧模块的函数），避免破坏已安装项目。
- 同步更新三份分发副本 + settings 模板 + init/update 传播逻辑。

> 关键约束：intent 与 recall 的输出走 stdout 的方式不同（intent 写文件、recall 打印 JSON）。合并后必须保证 recall 的 stdout JSON 不被 intent 的任何输出污染（intent 正常不打 stdout）。

### 4.3 stop hook 瘦身（中风险，中收益）

- `next_change_id`：把最新 change 编号持久化到 `.auto-change-state.json`，避免每次 `glob("*.md")`。
- `count_commits_since_last_record`：在 `classify_followup` 内计算一次并复用，去掉 line 424+426 的重复调用。
- 最新记录日期：随记录写入时落 state，避免每次扫 4 目录。
- `recommend_next_step`：评估是否可延迟/缓存（低优先，先不动，避免破坏 router 行为）。

### 4.4 auto-trail 有界滚动 journal（高风险，见 §5 决策点）

- 用单个 `.sybermem/.auto-trail.jsonl`（有界，保留最近 N 条）替代「每 stop 一个 markdown + 重写 INDEX」。
- auto-trail 默认排除出 `search_project` / dedup / 注入。
- 只在跨显著性阈值时提升为正式 markdown change 记录。

## 5. 范围决策点（需确认）

**4.4（auto-trail journal）是本方案里唯一改变用户可见存储行为的改动**：
- 它会停止在 `.sybermem/changes/` 里继续堆 auto-trail markdown，改写 26+ 条既有记录的组织方式。
- 影响 INDEX.md 表格结构、既有 auto-trail 记录的迁移、以及可能依赖这些文件的下游（Team publish / digest 覆盖）。
- 风险显著高于 4.1–4.3。

**建议分两批落地：**
- **批次 A（本轮执行）**：4.1 搜索缓存 + 4.2 合并 hook + 4.3 stop 瘦身。纯性能，不改存储语义，可回归验证。
- **批次 B（独立评估）**：4.4 auto-trail journal。涉及存储迁移，需单独 spec + 迁移方案 + 对 Team/digest 的影响评估。

## 6. 验收标准（批次 A）

1. 合并后单 prompt hook 墙钟 < 原 ~517ms（目标：接近单个 hook 的 ~200ms + intent 开销，实测对比）。
2. `pytest packages/core packages/cli` 全绿。
3. intent 捕获行为不变：命中意图短语仍写 `.record-intent.json`。
4. recall 输出契约不变：有结果仍输出合法 `additionalContext` JSON，且不被 intent 输出污染。
5. 无项目根 / 异常时仍 fail open 返回 0。
6. `search_project` 结果与改造前一致（缓存不改变检索结果）。
7. 三份 hook 分发副本保持一致；`check-plugin-package.py`（若校验 hook）仍通过。
