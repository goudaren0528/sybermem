---
name: init-project
description: 为新项目或已有代码项目初始化 SyberMem 记录系统，或处理仍在使用旧 ADR/ 存储的项目。
---

# init-project Skill

在目标项目中初始化 SyberMem 项目记录系统。生成的用户项目统一使用 `.sybermem/` 作为规范项目数据目录。

## 使用方式

用户在目标项目目录中执行 `/init-project`。

## 目录解析规则

在执行其他操作前，先解析项目数据目录：

1. 如果 `.sybermem/` 已存在，直接使用。
2. 如果只有 `ADR/`，将 `ADR/` 重命名为 `.sybermem/`，并告知用户旧目录已自动迁移。
3. 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，警告 `ADR/` 已被忽略，不自动合并。
4. 如果两者都不存在，则创建 `.sybermem/`。

## 流程

### Step 1: 解析现有状态

- 先应用上面的目录解析规则。
- 如果解析完成后 `.sybermem/INDEX.md` 已存在，视为项目已经初始化，询问用户是否要刷新模板或指令文件。
- 如果尚未初始化，继续后续步骤。

### Step 2: 判断项目类型

检查是否有代码文件（排除 node_modules、.git 等）：

| 情况 | 处理 |
|------|------|
| 空目录 / 无代码文件 | 新项目 → 创建基础结构 |
| 存在代码文件 | 已有项目 → 创建结构 + 扫描分析 |

### Step 3: 创建目录结构

```
.sybermem/
├── INDEX.md
├── changes/
├── decisions/
├── requirements/
├── bugs/
└── templates/
    ├── change-template.md
    ├── decision-template.md
    ├── requirement-template.md
    └── bug-template.md
```

### Step 4: 生成 INDEX.md

使用标准格式，包含：
- `## 关键结论` 区域 + `<!-- add new conclusions here -->` 占位符（AI 会话启动时读取此区获取项目上下文）
- 4 个类型的表格 + `<!-- add new records here -->` 占位符

### Step 5（已有代码项目额外执行）: 扫描分析

1. **识别技术栈**（通过 package.json / requirements.txt / go.mod 等）
2. **扫描 Git 历史**（最近 20 条 commit）
3. **检测特殊代码**（TODO、FIXME、HACK、workaround）
4. 将发现输出给用户，并建议创建对应记录

### Step 5.1: 持久化扫描发现

将 Step 5 扫描到的关键信息写入 `.sybermem/INDEX.md` 的 `## 关键结论` 区域，格式：

```
- [init] 技术栈：TypeScript + React + Vite，测试使用 Vitest (日期)
- [init] 项目采用 monorepo 结构，pnpm workspace (日期)
- [init] 发现 12 处 TODO/FIXME，集中在 src/auth/ 和 src/api/ (日期)
```

写入原则：
- 技术栈必写（语言、框架、构建工具、测试框架）
- 项目结构特征必写（monorepo、微服务、单体等）
- TODO/FIXME 集中区域值得写（帮助后续会话快速定位问题区域）
- Git 历史中的重大变更值得写（近期重构、迁移等）

### Step 5.2: 检测已有记录文件

扫描项目中常见的记录/文档文件：

| 检测目标 | 常见路径 |
|----------|----------|
| Changelog | `CHANGELOG.md`, `CHANGES.md`, `HISTORY.md` |
| ADR/决策记录 | `docs/adr/`, `docs/decisions/`, `adr/`, `doc/architecture/` |
| 需求/设计文档 | `docs/design/`, `docs/specs/`, `docs/rfcs/` |
| Bug 追踪 | `BUGS.md`, `KNOWN_ISSUES.md` |

**找到后，用 AskUserQuestion 询问用户**：

> 检测到项目中已有以下记录文件：
> - `CHANGELOG.md`（47 条记录）
> - `docs/adr/`（5 个决策文件）
>
> 是否要将这些内容整理到 SyberMem 体系中？
> 1. **导入并整理** — 将内容按类型拆分到 `.sybermem/` 对应目录，原文件保留备份
> 2. **仅建立索引** — 不移动文件，在 `.sybermem/INDEX.md` 中添加指向原文件的链接
> 3. **跳过** — 不处理，后续手动整理

处理规则：
- **导入并整理**：解析已有记录，按 change/decision/requirement/bug 分类，用模板格式重写到 `.sybermem/` 目录，原文件重命名为 `*.backup.md`
- **仅建立索引**：在关键结论区添加 `- [existing] 项目原有 CHANGELOG.md 包含 47 条变更记录，详见原文件`，并在对应表格中添加链接行
- **跳过**：不做任何操作

### Step 6: 创建 CLAUDE.md / AGENTS.md（如不存在）

在项目根目录创建 `CLAUDE.md`（Claude Code）和 `AGENTS.md`（OpenCode），包含 SyberMem 工作流规则。
如果已存在其中一个，只创建缺失的那个。

### Step 7: 输出总结

```markdown
## SyberMem 系统初始化完成

**项目类型：** [新项目 / 已有代码项目]

**存储目录：** [.sybermem/ 新建 / ADR/ 已自动迁移到 .sybermem/ / 复用已有 .sybermem/]

**已创建或更新：**
- `.sybermem/` 目录结构
- `INDEX.md`（含关键结论）
- 模板文件
- `CLAUDE.md` / `AGENTS.md`

**项目上下文（已有项目）：**
- 技术栈：[识别结果]
- 已有记录：[导入/索引/跳过 结果]
- 待关注：[TODO/FIXME 热点]

**下一步：**
- 开始工作后使用 `/record` 创建记录
```

## 技术栈识别

| 配置文件 | 技术栈 |
|----------|--------|
| package.json | Node.js / JavaScript / TypeScript |
| requirements.txt / pyproject.toml | Python |
| go.mod | Go |
| Cargo.toml | Rust |
| pom.xml / build.gradle | Java |

## 关键原则

- **`.sybermem/` 是规范目录**：新记录统一写入 `.sybermem/`
- **兼容旧项目**：旧 `ADR/` 会在首次使用时自动迁移，用户无需手动改名
- **处理分裂状态**：如果 `.sybermem/` 与 `ADR/` 同时存在，使用 `.sybermem/` 并警告 `ADR/` 已被忽略
- **已有代码只扫描，不自动创建记录**：输出建议，由用户决定
- **幂等安全**：重复执行不会破坏已有 `.sybermem/` 记录
