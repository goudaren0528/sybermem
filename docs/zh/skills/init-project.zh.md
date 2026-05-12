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

将项目文件分为四类：

- **missing**：文件不存在
- **fresh**：已经使用 `.sybermem/` 规则，并引用 `/sybermem-init-project`、`/sybermem-record`、`/sybermem-summary`、`/sybermem-update`
- **stale SyberMem-managed**：仍然引用旧 `/init-project`、`/record`、`/summary`，或仍然是旧 ADR 文案
- **custom**：文件存在，但看起来不是 SyberMem 管理的项目指令

处理规则：

1. **missing** → 直接按模板创建。
2. **fresh** → 保持不变。
3. **stale SyberMem-managed** → 询问用户是否刷新。刷新前先创建同目录备份，例如 `AGENTS.md.backup`、`CLAUDE.md.backup`，再替换为最新模板。
4. **custom** → 不自动覆盖，先向用户解释并确认。

如果项目已经初始化，且只需要刷新项目指令文件，可以跳过扫描代码步骤，直接输出总结。

### Step 2: 判断项目类型

仅在尚未初始化时，检查是否有代码文件（排除 node_modules、.git 等）。

### Step 3: 创建目录结构

创建 `.sybermem/` 目录结构及 `INDEX.md`。

### Step 4: 生成 INDEX.md

包含关键结论区和四类记录表格。

### Step 5: 扫描已有代码项目

识别技术栈、扫描最近 Git 历史、检测 TODO/FIXME/HACK/workaround，并将关键信息写入 `.sybermem/INDEX.md`。

### Step 6: 检测已有记录文件

扫描 changelog、ADR/决策文档、需求设计文档、Bug 跟踪文件，并询问用户是导入整理、仅建立索引，还是跳过。

### Step 7: 创建或刷新项目指令文件

- 缺失的 `CLAUDE.md` / `AGENTS.md` 直接创建
- 用户同意后刷新旧版 SyberMem 管理文件
- 自定义文件只有在用户明确同意时才替换

### Step 8: 输出总结

提示下一步使用：
- `/sybermem-record`
- `/sybermem-summary`
- `/sybermem-update`

## 关键原则

- `.sybermem/` 是规范目录
- 兼容旧项目，旧 `ADR/` 会自动迁移
- 项目指令刷新必须显式确认，并保留备份
- 已有代码只扫描并给出建议，不自动创建记录
- 重复执行不应破坏已有 `.sybermem/` 数据或自定义项目指令
