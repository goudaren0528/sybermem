# README Refresh（中英文同步）实现说明设计

> 刷新 `README.md`、`README.en.md`、`docs/zh/README.md`，让入口文档与 SyberMem v2 当前功能和平台状态对齐。

**Date:** 2026-06-29
**Status:** Draft
**Scope:** 只更新 3 个入口文档，不触碰其他 docs/specs/plans/install scripts 的结构。

---

## 1. Background & Problem

SyberMem 在最近几轮迭代中已经升级为 v2：
- 生命周期 hooks（SessionStart / Stop）
- 更新 fast-path（`check_project_health.py`）
- Search / Link / Theme Digest
- Topic governance / superseded handling
- Active / Archived Conclusions
- phase lifecycle
- Claude Code plugin + 多平台入口文件

但 README 入口文档仍不完全同步：

1. **`README.md` 仍有局部过期**
   - 目录树缺少 `theme-digests/`、`theme-digest-template.md`、`check_project_health.py`、`launch_record_change_on_stop.py`
   - skill 源码树列表不完整
   - 缺少“日常工作流”入口
   - 平台支持没有明确区分 fully supported vs metadata present

2. **`README.en.md` 比中文主 README 落后更多**
   - 仍是旧的安装/技能/目录结构视图
   - 缺少 `search / link / theme-digest`
   - 缺少治理能力说明
   - 缺少当前插件安装路径与支持平台状态

3. **`docs/zh/README.md` 作为中文备份，也会误导**
   - 目前只是旧的摘要型说明
   - 如果不补齐，新用户和维护者会同时看到三套不同版本的信息

---

## 2. Design Goal

让三份入口文档形成清晰分工：

| 文件 | 角色 | 目标 |
|---|---|---|
| `README.md` | 中文主入口 | 完整、准确、面向当前用户 |
| `README.en.md` | 英文主入口 | 与中文主 README 结构对齐，信息等价 |
| `docs/zh/README.md` | 中文备份/参考 | 不必逐段完全镜像，但必须覆盖全部当前能力并明确它是参考文档 |

---

## 3. Design Choice

采用 **“双主文档完整对齐 + 中文备份做轻量同步”**：

- `README.md`：完整刷新
- `README.en.md`：完整刷新，对齐同样的信息架构
- `docs/zh/README.md`：保留“备份/参考”定位，但补齐所有 v2 能力与正确目录树

### 不采用的方案
- **最小补丁**：太容易继续漂移
- **三份完全逐段同步**：维护成本高，不适合 `docs/zh/README.md` 的“备份/参考”角色

---

## 4. README.md / README.en.md 结构（完整对齐）

两份主 README 都更新为以下章节结构：

1. 项目简介
2. 安装方式
   - Claude Code 插件安装（推荐）
   - Claude Code / OpenCode 脚本安装（兼容）
   - OpenCode 安装
3. 项目初始化
4. Skills（完整 11 个）
5. Theme Digest Layer
6. 记录关系与检索
7. Topic 治理与替代关系
8. **日常工作流**（新增）
9. 在你的项目中会创建什么（更新目录树）
10. 支持平台（更新状态说明）
11. 仓库结构（补全 skill 列表）
12. License

### 4.1 Skills 表必须包含 11 个技能

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

### 4.2 日常工作流（新增）

**中文：**
```text
查历史 → /sybermem-search
看现状 → /sybermem-summary
做完工作 → /sybermem-record
phase-index stale → /sybermem-phase-analyze
phase 收束 → /sybermem-digest
topic 跨 phase 收束 → /sybermem-theme-digest <topic>
```

**英文：**
```text
Look up history → /sybermem-search
Check current state → /sybermem-summary
Finish meaningful work → /sybermem-record
Refresh stale phase index → /sybermem-phase-analyze
Close a phase → /sybermem-digest
Compress a topic across phases → /sybermem-theme-digest <topic>
```

### 4.3 项目目录树更新

目录树要补齐当前真实状态：

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

并补充说明 `INDEX.md` 现在包含：
- `Key Conclusions`
- `Archived Conclusions`
- `Stage Digests`
- `Theme Digests`
- `Topic Index`

### 4.4 平台支持说明

明确区分：

| 状态 | 平台 |
|---|---|
| **Fully supported** | Claude Code, OpenCode |
| **Entry files / metadata present** | Gemini, Cursor, Codex, Kimi |

文案上必须明确：
- Claude Code / OpenCode 已完整 dogfood
- Gemini / Cursor / Codex / Kimi 目前是入口文件/metadata 已准备，但运行时尚未同等强度验证

---

## 5. docs/zh/README.md 的同步策略

这个文件保留“中文版备份/参考”定位，但必须更新到不误导：

### 必须补齐的内容
- v2 功能全景（11 个 skill）
- Search / Link / Theme Digest
- Active / Archived Conclusions
- phase lifecycle
- topic status suffixes
- `superseded_by`
- 当前目录树
- 平台支持说明
- 推荐安装方式（plugin 推荐，脚本兼容）
- 日常工作流（可简短）

### 不要求
- 不要求逐段完全复制主 README 的篇幅
- 但不能继续停留在旧版本概述

---

## 6. Success Criteria

1. `README.md` 包含完整 11 个 skill。
2. `README.en.md` 包含完整 11 个 skill，并与中文主 README 结构基本对齐。
3. `docs/zh/README.md` 明确反映 v2 当前能力，不再停留在旧版概述。
4. 三个文档都包含更新后的项目目录树。
5. 至少 `README.md` 与 `README.en.md` 都新增“日常工作流”一节。
6. 平台支持说明正确区分 fully supported 与 entry-files-present。
7. 文档中关于治理能力的描述与当前实现一致：
   - Active / Archived Conclusions
   - phase lifecycle
   - topic status suffixes
   - `superseded_by`

---

## 7. Out of Scope

- 不改 `INSTALL.md`
- 不改 `docs/specs/`、`docs/plans/`
- 不补历史中英文文档的全面翻译
- 不借 README refresh 顺手重写整个品牌/叙事风格
