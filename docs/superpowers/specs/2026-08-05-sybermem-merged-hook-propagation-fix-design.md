# SyberMem 合并 Hook 分发传播修复方案（批次 G）

**Date:** 2026-08-05
**Status:** Proposed
**Scope:** check_project_health.py / init-project 传播 / sybermem-update 文案 —— 让批次 A 的合并 `user_prompt.py` hook 能通过 `/sybermem-update` 传播到已有项目
**Source:** 分发链核实(本会话)——发现批次 A 的分发缺口

## 1. 背景与已确认的缺口

批次 A（commit d237bc7 之前的 d210cba）把两个 UserPromptSubmit hook（`detect_record_intent.py` + `task_recall.py`）合并为单进程 `user_prompt.py`，并改了运行时 settings、模板 settings、插件委托器、check-plugin-package。但**遗漏了 `check_project_health.py`**（`/sybermem-init-project` 增量更新路径的检测器）。

**已实测确认的严重后果**：本项目已正确迁移到单 `user_prompt.py` hook，但 `check_project_health.py` 判定 `needs_update`，并生成两条 action：
- "add UserPromptSubmit hook entry to .claude/settings.json"
- "add task_recall UserPromptSubmit entry to .claude/settings.json"

即：**任何已装项目跑 `/sybermem-update` 会被倒退回双 hook 结构，主动抵消批次 A。** 且新装项目虽从模板拿到单 hook settings，随后 health check 也会误判为 stale。

根因：`check_settings_json`（line 124-128）检测 settings 里是否含 `detect_record_intent.py` + `task_recall.py`，而新 settings 只含 `user_prompt.py`。

## 2. 设计目标

让 health check 与 init-project 传播对齐批次 A 的单 hook 结构，且对旧双 hook 项目提供**非破坏**迁移，不误判、不倒退。

1. health check 把「有单 `user_prompt.py` UserPromptSubmit hook」视为 fresh 的正确状态。
2. 旧双 hook settings 识别为「stale，建议迁移到单 user_prompt.py」，迁移只改 UserPromptSubmit 块，保留其它。
3. health check 检测项目缺 `user_prompt.py` 文件时创建它。
4. `sybermem-update` SKILL Step 2 文案补上 user_prompt.py + 单 hook 迁移。
5. 已确认无需改的：术语(Phase Digests 已随 skill 复制传播)、journal(record_change_on_stop.py 走 stop-hook stale 检测 `has_unified_nudge`，模板已更新)——本方案聚焦 user_prompt 缺口。

## 3. 设计边界

### 保留
- `detect_record_intent.py` / `task_recall.py` 作为 user_prompt.py 复用的向后兼容模块（仍随模板分发，仍被 health check 当作应存在的文件）。
- settings 非破坏补丁原则：只改识别到的 SyberMem UserPromptSubmit 块。
- 现有 stop / session-start / auto-mode 检测不变。

### 不引入
- 删除 detect_record_intent/task_recall 模块。
- 破坏 settings 里的自定义 hook/env。
- 改 publish/status/search 语义。

## 4. 方案

### 4.1 `check_settings_json` 增加 user_prompt 检测

- 新增 `has_user_prompt_hook = "user_prompt.py" in content`。
- UserPromptSubmit 的"就绪"判定改为：`has_user_prompt_hook`（单 hook 是目标状态）。
- 保留 `has_record_intent_hook` / `has_task_recall_hook` 作为诊断字段（用于识别"旧双 hook 需迁移"）。
- `all_present` 里的 UserPromptSubmit 条件从 `has_record_intent_hook and has_task_recall_hook` 改为 `has_user_prompt_hook`。
- 返回新增 `has_user_prompt_hook` 字段。

### 4.2 actions 生成

- 若 settings 缺 `has_user_prompt_hook`：
  - 若检测到旧 `has_record_intent_hook`/`has_task_recall_hook`（旧双 hook）→ action："migrate UserPromptSubmit to the merged user_prompt.py hook in .claude/settings.json (replace the detect_record_intent + task_recall entries with a single user_prompt.py entry; preserve other hooks)"。
  - 否则（完全缺失）→ action："wire UserPromptSubmit to .sybermem/hooks/user_prompt.py in .claude/settings.json (preserve other hooks)"。
- 移除会导致倒退的旧两条 action（`add UserPromptSubmit hook entry` / `add task_recall UserPromptSubmit entry`）——由上面的单 hook action 取代。

### 4.3 `user_prompt.py` 文件检测

- 加 `user_prompt.py` 到 SyberMem-owned hook 的 create/replace 列表（与 detect_record_intent 并列），missing→create，stale→replace。
- 定义其 stale 判定：文件存在但缺合并契约标志（如缺同时 import 两模块的编排）——保守用 existence + 关键串检测。

### 4.4 init-project Step 7（已覆盖，验证即可）

init-project SKILL 的 Step 7（line 135）已列出创建 user_prompt.py 并优先 wire 单 hook。本方案确认它与 health check 一致即可，无需再改。

### 4.5 sybermem-update SKILL 文案

Step 2 的项目本地传播列表（line 78）补充 user_prompt.py 与单 hook 迁移的描述。

### 4.6 三副本同步

改动 `check_project_health.py` 后同步到 3 处（运行时 + 2 模板）；settings 模板已是单 hook（批次 A 已改），无需再改。

## 5. 验收标准

1. 本项目跑 `check_project_health.py` → 不再因 UserPromptSubmit 报 `needs_update`（当前单 hook settings 视为 fresh）。
2. 模拟旧双 hook 项目 → health check 生成"迁移到 user_prompt.py"单条 action，而非倒退的两条 add。
3. 缺 `user_prompt.py` 文件的项目 → health check 生成 create action。
4. detect_record_intent/task_recall 仍被当作应存在的兼容模块（不被删）。
5. 三副本 check_project_health.py 一致。
6. `pytest packages/core packages/cli` 全绿；`check-plugin-package.py` `OK`。
7. sybermem-update SKILL Step 2 文案提及 user_prompt.py。

## 6. 已确认无缺口的传播路径（无需改）

- **skill 内容（速览层、Phase Digests 术语）**：走 update.sh 的 `sync_skills` 从 `packages/claude-skills` 全量复制 14 个 skill → 全局 skills；已验证镜像一致。
- **journal（batch B）**：`record_change_on_stop.py` 模板已更新为 journal 版；health check 的 stop-hook stale 检测基于 `.nudge-state.json` 串，journal 版仍含该串（保持 fresh 判定），且模板 replace 会带上 journal 逻辑。
- **平台 manifest / CI / LICENSE / VERSION（批次 D/P1）**：属仓库级文件,通过 git 分发,不经 skill/init 传播。
