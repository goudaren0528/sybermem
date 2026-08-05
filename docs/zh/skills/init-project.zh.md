---
name: sybermem-init-project
description: 为新项目或已有代码项目初始化 SyberMem 记录系统，或处理仍在使用旧 ADR 存储、旧本地指令文件的项目。
---

# sybermem-init-project Skill

在目标项目中初始化或刷新 SyberMem 项目记录系统。`.sybermem/` 是规范项目数据目录。

## 使用方式

用户在目标项目目录中执行 `/sybermem-init-project`。

## 目录解析规则

在执行其他操作前，先解析项目数据目录：

1. 如果 `.sybermem/` 已存在，直接使用。
2. 如果只有 `ADR/`，将 `ADR/` 重命名为 `.sybermem/`，并告知用户旧目录已自动迁移。
3. 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，警告 `ADR/` 已被忽略，不自动合并。
4. 如果两者都不存在，则创建 `.sybermem/`。

## 流程

### Step 1: 解析现有状态

- 先应用上面的目录解析规则。
- 如果 `.sybermem/INDEX.md` 已存在，视为项目已经初始化。
- 在继续之前，检查项目根目录的 `AGENTS.md` 和 `CLAUDE.md` 是否需要刷新。

### Step 1.1: 检查项目指令文件

使用以下模板作为标准版本：

- `packages/claude-skills/sybermem-init-project/project-files/AGENTS.md`
- `packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md`
- `packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json`

将项目文件分为四类：

- **missing**：文件不存在
- **fresh**：已经使用 `.sybermem/` 规则，并引用 `/sybermem-init-project`、`/sybermem-record`、`/sybermem-summary`、`/sybermem-digest`、`/sybermem-update`
- **stale SyberMem-managed**：仍然引用旧 `/init-project`、`/record`、`/summary`，或仍然是旧 ADR 文案
- **custom**：文件存在，但看起来不是 SyberMem 管理的项目指令

处理规则：

1. **missing** → 直接按模板创建。
2. **fresh** → 保持不变。
3. **stale SyberMem-managed** → 询问用户是否刷新。刷新前先创建同目录备份，例如 `AGENTS.md.backup`、`CLAUDE.md.backup`，再替换为最新模板。
4. **custom** → 不自动覆盖，先向用户解释并确认。

如果项目已经初始化，且只需要刷新项目指令文件，可以跳过扫描代码步骤，直接输出总结。

### Step 1.2: 补齐缺失的 digest 能力

对于已经存在 `.sybermem/INDEX.md` 的项目，还要检查 digest 支持是否齐全：

- `.sybermem/digests/`
- `.sybermem/templates/digest-template.md`
- `.sybermem/INDEX.md` 中的 `## Phase Digests` 区段

如果缺少其中任何一项：

- 创建缺失的 `digests/` 目录
- 从标准模板创建缺失的 `digest-template.md`
- 在 `INDEX.md` 中插入缺失的 `## Phase Digests` 区段

这个补齐过程必须是幂等的：不要重复插入区段，不要在未确认的情况下覆盖已有的 digest 模板，也不要因为缺少 digest 支持就重新初始化整个项目。

### Step 2: 判断项目类型

仅在尚未初始化时，检查是否有代码文件（排除 node_modules、.git 等）。

### Step 3: 创建目录结构

创建 `.sybermem/` 目录结构及 `INDEX.md`；其中 digest 支持包括 `.sybermem/digests/` 和 `.sybermem/templates/digest-template.md`。在启用默认自动模式时，还需要创建 `.sybermem/hooks/record_change_on_stop.py`。

### Step 4: 生成 INDEX.md

包含关键结论区、`## Phase Digests` 区段和四类记录表格。

### Step 5: 扫描已有代码项目

识别技术栈、扫描最近 Git 历史、检测 TODO/FIXME/HACK/workaround，并将关键信息写入 `.sybermem/INDEX.md`。

### Step 6: 检测已有记录文件

扫描 changelog、ADR/决策文档、需求设计文档、Bug 跟踪文件，并询问用户是导入整理、仅建立索引，还是跳过。

### Step 7: 创建或刷新项目指令文件

- 缺失的 `CLAUDE.md` / `AGENTS.md` 直接创建
- 缺失的项目级 `.claude/settings.json` 直接按模板创建，用于默认的 SyberMem `auto` / `remind` 模式
- 缺失的 `.sybermem/hooks/record_change_on_stop.py` 直接按模板创建，作为默认自动 `change` hook helper
- 默认模板中的自动模式只自动写入基于工作区文件变更的 `change` 记录；`decision` / `requirement` / `bug` 仍由 `/sybermem-record` 处理
- `/sybermem-summary` 用于动态周报/月报；当一个有意义的阶段结束时，使用 `/sybermem-digest` 将可持久保存的阶段总结写入 `.sybermem/digests/`
- 用户同意后刷新旧版 SyberMem 管理文件
- 已存在的 `.claude/settings.json` 若看起来不是 SyberMem 管理模板，则视为自定义配置，不自动覆盖
- 自定义文件只有在用户明确同意时才替换

### Step 8: 输出总结

提示下一步使用：
- `/sybermem-record`
- `/sybermem-summary`
- `/sybermem-digest`
- `/sybermem-update`

并在需要时提醒用户：仅更新全局 skills 并不会自动为当前项目启用 digest 支持；如果要使用 `/sybermem-digest`，应先在该项目中运行 `/sybermem-update`。这一步只会创建缺失的 digest 相关结构，不会悄悄覆盖项目自有文件。

## 关键原则

- `.sybermem/` 是规范目录
- 兼容旧项目，旧 `ADR/` 会自动迁移
- digest 支持通过补齐缺失结构来启用，不静默覆盖项目自有文件
- 项目指令刷新必须显式确认，并保留备份
- 已有代码只扫描并给出建议，不自动创建记录
- 重复执行不应破坏已有 `.sybermem/` 数据或自定义项目指令

