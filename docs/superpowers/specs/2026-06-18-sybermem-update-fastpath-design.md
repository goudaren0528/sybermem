# SyberMem Update Fast-Path 设计

> 把 `/sybermem-update` 的耗时从"模型逐文件读取判断"变成"脚本批量检查 → 模型只处理差异"。

**Date:** 2026-06-18
**Status:** Draft
**Scope:** 优化 `/sybermem-update` 和 `/sybermem-init-project` 的执行速度

---

## 1. Background & Problem

当前 `/sybermem-update` 流程：

1. 运行 `update.sh` / `update.ps1` 刷新全局 skills（快，几秒）
2. 调用 `/sybermem-init-project`（慢，主要瓶颈）

`/sybermem-init-project` 的瓶颈：

- 模型逐个读取每个 managed file（CLAUDE.md、AGENTS.md、settings.json、hooks、templates、digests/、analysis/...）
- 每个文件都要：Read → 和模板对比 → 判断 missing/fresh/stale/custom
- 一个正常的已初始化项目需要 15-25 次 tool call
- 大部分时候结论是"已是最新，无需操作"

核心问题：**模型在做脚本能做的事。**

---

## 2. Design

### 2.1 新增 `check_project_health.py`

一个 Python 脚本，一次性检查所有 managed files 的状态，输出 JSON 报告。

**位置：** `.sybermem/hooks/check_project_health.py`（项目级）+ 对应的 init-project 模板

**不需要全局 launcher。** 这个脚本由模型在 init-project 流程内直接运行，不是 hook。

**输入：** 项目根目录（通过 cwd 自动解析）

**输出：** JSON 到 stdout

```json
{
  "root": "/path/to/project",
  "overall": "fresh",
  "files": {
    "CLAUDE.md": {
      "status": "fresh",
      "has_protocol_block": true
    },
    "AGENTS.md": {
      "status": "fresh",
      "has_protocol_block": true
    },
    ".claude/settings.json": {
      "status": "stale",
      "has_session_start_hook": false,
      "has_stop_hook": true,
      "has_auto_mode": true
    },
    ".sybermem/hooks/record_change_on_stop.py": {
      "status": "fresh"
    },
    ".sybermem/hooks/session_start_context.py": {
      "status": "missing"
    },
    ".sybermem/hooks/launch_record_change_on_stop.py": {
      "status": "fresh"
    },
    ".sybermem/INDEX.md": {
      "status": "fresh",
      "has_conclusions_anchor": true,
      "has_digest_anchor": true,
      "has_records_anchors": true,
      "has_topic_index": true
    },
    ".sybermem/digests/": {
      "status": "present"
    },
    ".sybermem/analysis/phase-index.md": {
      "status": "present"
    },
    ".sybermem/templates/digest-template.md": {
      "status": "present"
    }
  },
  "capabilities": {
    "digest": true,
    "analysis": true,
    "auto_record_hook": true,
    "session_start_hook": false,
    "protocol_block": true
  },
  "actions_needed": [
    "create .sybermem/hooks/session_start_context.py from template",
    "add SessionStart hook entry to .claude/settings.json"
  ]
}
```

### 2.2 文件分类逻辑

每个文件的 `status` 判定规则：

| 文件 | fresh 条件 | stale 条件 | missing 条件 |
|---|---|---|---|
| `CLAUDE.md` | 存在 + 包含 `SYBERMEM_SESSION_PROTOCOL:START` | 存在 + 不包含 protocol block | 不存在 |
| `AGENTS.md` | 同上 | 同上 | 不存在 |
| `.claude/settings.json` | 存在 + 有 `SessionStart` hook + 有 `Stop` hook + 有 `SYBERMEM_RECORD_MODE` | 存在但缺少任一项 | 不存在 |
| `.sybermem/hooks/record_change_on_stop.py` | 存在 + 包含 `NUDGE_STATE_PATH` 指向 `.nudge-state.json` | 存在但指向旧路径 | 不存在 |
| `.sybermem/hooks/session_start_context.py` | 存在 | — | 不存在 |
| `.sybermem/hooks/launch_record_change_on_stop.py` | 存在 | — | 不存在 |
| `.sybermem/INDEX.md` | 存在 + 有 conclusions anchor + digest anchor + records anchors | 存在但缺少 anchor | 不存在 |
| `.sybermem/digests/` | 目录存在 | — | 不存在 |
| `.sybermem/analysis/phase-index.md` | 存在 | — | 不存在 |
| `.sybermem/templates/digest-template.md` | 存在 | — | 不存在 |

**custom 检测：** 脚本不判断 custom（需要模型语义理解）。如果文件存在但不匹配 fresh 的关键标记，报告为 `stale`。模型在需要覆盖 stale 文件时才读取内容来判断是 stale-managed 还是 custom。

**overall 判定：**
- `"fresh"` — 所有文件 status 都是 `fresh` 或 `present`
- `"needs_update"` — 任何文件是 `missing` 或 `stale`
- `"not_initialized"` — `.sybermem/INDEX.md` 不存在

### 2.3 非破坏性更新规则

**核心约束：更新不能破坏用户原有文件内容。**

用户的 `CLAUDE.md`、`AGENTS.md`、`.claude/settings.json` 可能包含与 SyberMem 无关的自定义内容。更新操作必须只修改 SyberMem 拥有的部分，保留其他所有内容。

#### 按文件类型的安全更新策略

| 文件 | 更新方式 | 禁止 |
|---|---|---|
| `CLAUDE.md` / `AGENTS.md` | **只操作 protocol block**：找到 `SYBERMEM_SESSION_PROTOCOL:START` 和 `END` 标记，替换标记之间的内容；如果标记不存在，在文件顶部插入整个 block。文件其余内容原样保留。 | 整体覆盖文件 |
| `.claude/settings.json` | **只操作 SyberMem 拥有的字段**：`env.SYBERMEM_RECORD_MODE`、`hooks.SessionStart`（SyberMem 的那个 entry）、`hooks.Stop`（SyberMem 的那个 entry）。其他 env 变量、其他 hooks、其他顶层字段全部保留。 | 整体覆盖文件 |
| `.sybermem/INDEX.md` | **只插入缺失的 section**（如 `## Stage Digests`、`## Topic Index`）。已有的 Key Conclusions、记录表、用户数据原样保留。 | 重新生成整个文件 |
| `.sybermem/hooks/*.py` | **可以整体替换**——这些是 SyberMem 完全拥有的执行文件，不含用户自定义内容。 | — |
| `.sybermem/templates/*.md` | **可以整体替换**——模板文件是 SyberMem 拥有的。 | — |

#### check_project_health.py 报告增强

脚本对 `CLAUDE.md` 和 `AGENTS.md` 额外报告 `"is_sybermem_only"` 字段：

```json
"CLAUDE.md": {
  "status": "stale",
  "has_protocol_block": false,
  "is_sybermem_only": false
}
```

`is_sybermem_only` 判定：文件内容去掉 protocol block 后，剩余部分是否和 SyberMem 模板完全匹配。
- `true` → 整体刷新安全（该文件是纯 SyberMem managed）
- `false` → 只能操作 protocol block，不能整体覆盖

#### actions_needed 精确描述更新方式

```json
"actions_needed": [
  "insert protocol block into CLAUDE.md (preserve existing content)",
  "insert protocol block into AGENTS.md (preserve existing content)",
  "add SessionStart hook entry to .claude/settings.json (preserve other hooks)",
  "create .sybermem/hooks/session_start_context.py from template"
]
```

每条 action 都明确标注是 "insert"（部分更新）还是 "create"（新建）还是 "replace"（整体替换，仅限 SyberMem 完全拥有的文件）。

### 2.4 init-project fast-path

在 init-project SKILL.md 的 Step 1 开头加一个 fast-path：

```text
Step 0.5: Run check_project_health.py

运行 `python .sybermem/hooks/check_project_health.py`（如果脚本存在）。

如果 overall == "fresh":
  → 输出 "SyberMem project is up to date. No changes needed."
  → 跳过所有后续步骤，skill 完成。

如果 overall == "needs_update":
  → 只处理 actions_needed 列表中的操作。
  → 对于 stale 文件：读取文件内容判断是 stale-managed 还是 custom。
  → stale-managed → 备份 + 刷新。
  → custom → 问用户。
  → 创建 missing 文件。
  → 输出精简总结。

如果 overall == "not_initialized" 或脚本不存在:
  → 走完整的现有流程（兼容旧项目）。
```

### 2.5 sybermem-update 流程简化

更新后的 `/sybermem-update` 流程：

```text
Step 1: 运行 update.sh/ps1（不变）
Step 2: 运行 /sybermem-init-project
  → init-project 自动先跑 check_project_health.py
  → 如果 fresh：一句话完成
  → 如果 needs_update：精准修几个文件
  → 如果 not_initialized：完整流程
```

---

## 3. 脚本实现要点

### 3.1 Root resolution

复用已有的 `resolve_sybermem_root()` 模式。

### 3.2 检查逻辑

全部是文件存在性 + 简单字符串包含检查，不需要模板内容对比或哈希。

关键标记检查：

```python
# CLAUDE.md / AGENTS.md protocol block
"SYBERMEM_SESSION_PROTOCOL:START" in content

# settings.json hooks
"launch_session_start_context" in content  # SessionStart hook
"launch_record_change_on_stop" in content  # Stop hook
"SYBERMEM_RECORD_MODE" in content          # auto/remind mode

# record_change_on_stop.py unified nudge state
'".nudge-state.json"' in content           # new unified path

# INDEX.md anchors
"<!-- add new conclusions here -->" in content
"<!-- add new digest records here -->" in content
"<!-- add new records here -->" in content

# INDEX.md topic index
"## Topic Index" in content
```

### 3.3 actions_needed 生成

脚本根据 status 自动推导需要的操作，action 文本明确标注更新方式：

```python
actions = []

# SyberMem 完全拥有的文件：可以 create/replace
if files["session_start_context"]["status"] == "missing":
    actions.append("create .sybermem/hooks/session_start_context.py from template")
if files["record_change_on_stop"]["status"] == "stale":
    actions.append("replace .sybermem/hooks/record_change_on_stop.py from template")

# 用户可能有自定义内容的文件：只能 insert/patch
if not files["claude_md"].get("has_protocol_block"):
    actions.append("insert protocol block into CLAUDE.md (preserve existing content)")
if not files["agents_md"].get("has_protocol_block"):
    actions.append("insert protocol block into AGENTS.md (preserve existing content)")
if files["settings_json"]["status"] == "stale":
    if not files["settings_json"]["has_session_start_hook"]:
        actions.append("add SessionStart hook entry to .claude/settings.json (preserve other hooks)")
    if not files["settings_json"]["has_stop_hook"]:
        actions.append("add Stop hook entry to .claude/settings.json (preserve other hooks)")
```

### 3.4 settings.json 外科手术式更新

模型在处理 `add ... hook entry to .claude/settings.json` 时，必须：

1. `json.load` 读取现有内容
2. 只在 `hooks` 对象下添加/替换 SyberMem 的 entry
3. 保留其他所有字段和 hooks
4. `json.dump` 写回

```python
# 模型执行示意（不是脚本，是模型的操作指导）
import json
settings = json.load(open(".claude/settings.json"))
settings.setdefault("hooks", {})
settings["hooks"]["SessionStart"] = [{"hooks": [{"type": "command", ...}]}]
# 不动 settings 里的其他内容
json.dump(settings, open(".claude/settings.json", "w"), indent=2)
```

### 3.5 退出码

- `0` — 总是成功退出（即使 needs_update）
- JSON 输出到 stdout
- 错误信息到 stderr（不影响 JSON 解析）

---

## 4. File Manifest

| 操作 | 文件 | 说明 |
|---|---|---|
| **新增** | `.sybermem/hooks/check_project_health.py` | 批量健康检查脚本 |
| **新增** | `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py` | init-project 模板 |
| **修改** | `packages/claude-skills/sybermem-init-project/SKILL.md` | 加 fast-path Step 0.5 |
| **不动** | `packages/claude-skills/sybermem-update/SKILL.md` | update 流程不变，受益来自 init-project 加速 |

---

## 5. Backward Compatibility

- 旧项目没有 `check_project_health.py` → init-project 检测脚本不存在 → 走完整流程 → 在 Step 7 时创建该脚本
- 新项目初始化后就有该脚本 → 后续 update 走 fast-path
- 脚本只做检查，不做任何写入操作 → 安全

---

## 6. Success Criteria

1. 已是最新的项目跑 `/sybermem-update`：1 次脚本调用 + 1 句 "up to date" 输出，<15 秒
2. 缺少 1-2 个文件的项目：1 次脚本 + 精准创建缺失文件
3. 全新项目：完整流程，不受影响
4. 旧项目（无 check 脚本）：完整流程，同时安装 check 脚本以加速后续 update

---

## 7. Out of Scope

- 不修改 `/sybermem-update` SKILL.md 本身（受益来自 init-project 加速）
- 不修改 update.sh/ps1 安装脚本
- 不做远程版本对比（只做本地 managed-file 状态检查）
