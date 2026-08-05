# SyberMem Auto-Trail 滚动 Journal 方案（批次 B）

**Date:** 2026-08-05
**Status:** Proposed
**Scope:** stop hook 的 auto-trail 写入；`.sybermem/changes/` 与 INDEX.md 污染治理
**Source:** docs/audit/2026-08-05-sybermem-comprehensive-audit.md §2 批次 B（复核属实）+ 下游依赖调研（explore ses_02fb94f8）

## 1. 背景与调研结论

审计 §2 复核确认：51 条记录中 26 条是 auto-trail 噪声，每次 stop 写一个 markdown + 重写 INDEX.md，全程参与 parse/index/search/dedup。

下游依赖调研（explore）确认了迁移的真实约束：

- **auto-trail 深度嵌入 canonical 记录枚举**：`iter_record_files` 遍历 `changes/*.md`，`status` 计数、`publish` 的 `source_hash`/`selected_records`、`search`、`snapshot` 全依赖它。移出会**改变 publish source_hash 与 status 计数语义**（不崩溃但行为变）。
- **8 个旧 auto-trail 文件被 digest 的 `source_records` 引用**（007/009/011/012/013/015/018/027）—— 删除会破坏 digest provenance。
- **好消息**：INDEX 的 `## Feature Changes` 表**无任何下游读取**；`next_change_number` 读文件名不读 INDEX；`compact_project_search` 已过滤 `authority == 'evidence'`（auto-trail 已被排除出召回）。
- **stop hook 会 breaks-if-moved**：numbering / overlap-dedup / INDEX 写入都扫 `changes/*.md`，必须与存储移动同步改。

## 2. 设计目标（已确认范围）

用户确认采取**最低风险路径**：**只停未来写入 + 源头治理，既有 26 条保留不动，journal 不喂统计**。

1. stop hook 的 auto 模式**不再**向 `.sybermem/changes/` 写 markdown、**不再**向 INDEX.md 加行。
2. 改为 append 到一个**有界滚动** journal `.sybermem/.auto-trail.jsonl`（保留最近 N 条）。
3. 既有 26 条 auto-trail markdown + INDEX 行 **原样保留**（不迁移、不删除、不归档）—— 彻底避开 digest provenance、publish/status 语义、search archived 逻辑的改动。
4. journal **不参与** status/publish/search 计数（auto-trail 本就是低信号 evidence，compact recall 已过滤）。
5. stop hook 的去重（overlap dedup）改为从 journal 读，而非扫 markdown。
6. reminder / digest-cluster nudge 信号**保持不变**（它们基于 `.nudge-state.json`，本就不依赖 markdown 计数）。

## 3. 设计边界

### 保留
- 既有 26 条 auto-trail markdown 文件与 INDEX.md 中它们的行（零改动）。
- `iter_record_files` / status / publish / search / snapshot 对既有记录的现有行为（因既有文件不动，语义完全不变）。
- `count_commits_since_last_record`（扫真实记录目录）—— auto-trail 停写后它反而更准。
- reminder-first 与 digest-cluster nudge 逻辑（基于 nudge-state）。
- `remind` 模式行为（本就不写 markdown）。

### 不引入
- 对既有 markdown 记录的迁移 / 归档 / 删除。
- 对 digest `source_records`、publish hash、status 计数逻辑的任何改动。
- journal 参与 canonical 检索或 Team publish。
- 新的 core 模块（journal 读写只在 stop hook 内，保持 hook 自足）。

## 4. 方案

### 4.1 journal 格式与有界性

- 路径：`.sybermem/.auto-trail.jsonl`（点文件，与 `.auto-change-state.json` / `.nudge-state.json` 同级，非 canonical 记录）。
- 每行一条 JSON：`{"date": "YYYY-MM-DD", "files": [...], "areas": [...], "followup_hint": "record|digest|none"}`。
- 有界：保留最近 `AUTO_TRAIL_JOURNAL_MAX`（如 200）条，append 后截断头部。
- `.gitignore`：journal 是运行时状态，应被忽略（与其它 `.sybermem/.*-state.json` 一致处理）。确认当前 gitignore 对 `.sybermem/.*` 状态文件的策略后对齐。

### 4.2 stop hook 写入分支改造

当前 `main()` 的 auto 分支（约 line 601-604）：
```
record_path.write_text(render_record(...))
update_index(record_date, number, ...)
save_state(...)
```
改为：
```
append_auto_trail_journal(record_date, files, areas, followup_hint)
save_state(...)   # last_fingerprint 语义保留，用于连续相同变更去重
```
- 删除对 `render_record` / `update_index` / `next_change_id` 的调用（auto 分支不再需要编号与 markdown）。
- 保留 `remind` 分支不变。

### 4.3 去重改造

`overlaps_recent_auto_trails(files)` 当前读 `CHANGES_DIR` 最近 3 个 auto-trail markdown 的 `related_files`。改为读 `.auto-trail.jsonl` 最近 `AUTO_TRAIL_DEDUP_WINDOW`(3) 条的 `files` 做同样的 >80% overlap 判断。逻辑与阈值不变，只换数据源。

### 4.4 保留但不再触发的函数

- `render_record` / `update_index` / `next_change_id` / `next_change_number`：auto 分支不再调用。**保留函数定义**（避免大改，且 `next_change_number` 可能被其它路径/测试引用），只是不再从 stop 主流程触发写 markdown。

### 4.5 三副本同步

改动 `.sybermem/hooks/record_change_on_stop.py` 后，同步到：
- `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py`
- `skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py`

## 5. 验收标准

1. auto 模式下跑 stop hook：**不再**在 `.sybermem/changes/` 新增 markdown，**不再**向 INDEX.md 加行。
2. 每次有意义 stop 向 `.sybermem/.auto-trail.jsonl` append 一条，且文件有界（≤ MAX 条）。
3. 去重仍生效：>80% overlap 的连续相同变更不重复记入 journal。
4. reminder / digest-cluster nudge 行为与改造前一致（基于 nudge-state）。
5. 既有 26 条 auto-trail markdown + INDEX 行 **零改动**；`git diff` 不触及它们。
6. status / publish / search 对既有记录行为不变（因既有文件未动）。
7. `pytest packages/core packages/cli` 全绿。
8. 三副本 stop hook 一致；`check-plugin-package.py` `OK`。
9. `remind` 模式行为不变。

## 6. 明确不做（本方案边界外）

- 不迁移/归档/删除既有 auto-trail markdown。
- 不改 digest source_records、publish hash、status 计数。
- 不把 journal 接入 canonical 检索或 Team publish。
- 未来若要真正清理既有 26 条并让 status/publish 从 journal 重算，是更大范围的独立决策（批次 C），不在此。
