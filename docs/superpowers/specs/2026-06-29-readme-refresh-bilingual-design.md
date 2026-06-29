# README Refresh（中英文同步）设计

> 刷新中英文 README，使文档与当前 SyberMem v2 能力对齐，重点补齐目录树、完整 skills 列表、日常工作流、以及平台支持状态说明。

**Date:** 2026-06-29
**Status:** Draft
**Scope:** 仅更新入口文档：`README.md`、`README.en.md`、`docs/zh/README.md`。不重写其他文档体系。

---

## 1. Background & Problem

SyberMem 近期连续完成了多轮能力扩展：
- Lifecycle Layer（SessionStart/Stop）
- Update Fast-Path
- Search & Relations
- Theme Digest Layer
- Topic governance / superseded handling
- Claude Code plugin + multi-platform entry files

但当前 README 文档仍存在几处落后：

1. **项目目录树过期**  
   还没有准确展示：
   - `.sybermem/theme-digests/`
   - `.sybermem/templates/theme-digest-template.md`
   - `.sybermem/hooks/check_project_health.py`
   - `.sybermem/hooks/launch_record_change_on_stop.py`
   - `INDEX.md` 中 `Archived Conclusions` / `Theme Digests` / `Topic Index` 标记语法

2. **仓库结构中的 skill 列表不全**  
   `packages/claude-skills/` 仍像旧时代一样只列部分技能，没有把 `sybermem-search`、`sybermem-link`、`sybermem-theme-digest` 等完整呈现出来。

3. **缺少“日常怎么用”入口**  
   用户知道 skill 名，但不知道最自然的日常链路：查历史、看当前 phase、记录工作、digest、theme digest。

4. **平台支持说明不够精确**  
   仓库实际上已有：
   - fully-supported runtime: Claude Code, OpenCode
   - entry files present: Gemini, Cursor, Codex, Kimi
   README 需要明确这种差异，避免误解为“所有平台都已完全 dogfood”。

5. **中英文不同步风险**  
   现在至少有 3 个入口文档面向用户：
   - `README.md`（中文主文档）
   - `README.en.md`（英文主文档）
   - `docs/zh/README.md`（中文备份/参考）
   它们需要一起更新，否则会再次漂移。

---

## 2. Design Goals

本次 refresh 只做“入口文档对齐”，不做大规模重写。

### 目标
- 让首次阅读 README 的用户能理解 **现在有什么能力、日常用哪些命令、在哪些平台可用**。
- 让 README 成为当前 v2 能力的准确入口，而不是历史遗留快照。
- 中英文同步更新，避免中文版和英文版漂移。

### 不做
- 不重构整个文档体系
- 不重写 INSTALL.md / docs/specs / docs/plans
- 不补所有历史文档的中英文翻译
- 不新增新功能，只更新说明

---

## 3. Files to Update

| 文件 | 角色 |
|---|---|
| `README.md` | 中文主入口文档 |
| `README.en.md` | 英文主入口文档 |
| `docs/zh/README.md` | 中文备份/参考文档 |

---

## 4. README 内容更新项

### 4.1 项目目录树（What gets created in your project）

把目录树更新为当前真实状态：

```text
.sybermem/
├── INDEX.md
├── changes/
├── decisions/
├── requirements/
├── bugs/
├── digests/
├── theme-digests/
├── analysis/
│   └── phase-index.md
├── hooks/
│   ├── record_change_on_stop.py
│   ├── session_start_context.py
│   ├── check_project_health.py
│   └── launch_record_change_on_stop.py
└── templates/
    ├── change-template.md
    ├── decision-template.md
    ├── requirement-template.md
    ├── bug-template.md
    ├── digest-template.md
    └── theme-digest-template.md
```

并补充说明 `INDEX.md` 里现在有：
- `Key Conclusions`
- `Archived Conclusions`
- `Stage Digests`
- `Theme Digests`
- `Topic Index`

### 4.2 Skills 列表

README 中应展示完整 11 个 skill：
- `/sybermem-init-project`
- `/sybermem-record`
- `/sybermem-summary`
- `/sybermem-digest`
- `/sybermem-theme-digest`
- `/sybermem-phase-analyze`
- `/sybermem-phase-confirm`
- `/using-sybermem`
- `/sybermem-update`
- `/sybermem-search`
- `/sybermem-link`

### 4.3 日常工作流（新 section）

新增一节，明确最自然的日常使用链路：

```text
查历史 → /sybermem-search
看现状 → /sybermem-summary
做完一段工作 → /sybermem-record
phase-index stale → /sybermem-phase-analyze
phase 收束 → /sybermem-digest
topic 跨 phase 收束 → /sybermem-theme-digest <topic>
```

这节要简洁，不变成教程，只做“推荐路径”。

### 4.4 平台支持说明

把当前真实状态说清楚：

| 平台 | 状态 | 说明 |
|---|---|---|
| Claude Code | fully supported | 插件安装（推荐）/脚本安装（兼容）都可运行完整能力 |
| OpenCode | fully supported | TypeScript plugin 提供 `session.created` / `idle` / `compacting` |
| Gemini CLI | entry file present | `GEMINI.md` 已提供，能力入口已存在，但未像 Claude/OpenCode 一样完整 dogfood |
| Cursor | metadata present | `.cursor-plugin/plugin.json` 已存在，未完整验证运行时 |
| Codex | metadata present | `.codex-plugin/plugin.json` 已存在，未完整验证运行时 |
| Kimi | metadata present | `.kimi-plugin/plugin.json` 已存在，未完整验证运行时 |

关键点：**不要把有入口文件的状态说成 fully supported**。

### 4.5 当前治理能力说明

README 应明确 v2 当前已有的治理能力：
- Active / Archived Conclusions
- phase lifecycle (`active` / `completed` / `archived`)
- Topic Index suffixes (`[active] [low] [deprecated → ...]`)
- `superseded_by` frontmatter

但只需点到为止，不展开成操作手册。

---

## 5. Language Sync Strategy

### 5.1 `README.md` 与 `README.en.md`

两者都作为主入口，需要：
- 同样的章节结构
- 同样的功能覆盖
- 只是语言不同

### 5.2 `docs/zh/README.md`

这个文件不是主 README，而是中文备份/参考。它应该同步更新到与 `README.md` 一致的功能描述，避免旧说明继续存在。

### 5.3 同步原则

- 中文主 README 为当前仓库的“默认入口”
- 英文 README 覆盖同样的信息，不省略新能力
- `docs/zh/README.md` 作为镜像说明，不允许落后于中文主 README 的功能描述

---

## 6. Success Criteria

1. 三个 README 文件都提到完整 11 个 skill。
2. 三个 README 文件都包含更新后的项目目录树。
3. 三个 README 文件都说明当前平台支持状态（fully supported vs entry-file-present）。
4. 至少中文主 README 和英文主 README 都新增“日常工作流”一节。
5. README 中关于治理能力的描述与当前实现一致（Archived Conclusions、phase lifecycle、topic suffixes、superseded_by）。
6. 不出现“所有平台 fully supported”这种不实表述。
