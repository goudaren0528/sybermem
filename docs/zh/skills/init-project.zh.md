---
name: init-project
description: 为项目初始化 ADR 记录系统（自动判断新项目或已有代码项目）
---

# init-project Skill

在项目中创建 ADR 记录目录结构。自动判断新项目或已有代码项目。

## 使用方式

用户在目标项目目录中执行 `/init-project`。

## 流程

### Step 1: 检查现有状态

- 如果已有 `ADR/` 目录 → 提示用户，询问是否重新初始化
- 如果不存在 → 继续

### Step 2: 判断项目类型

检查是否有代码文件（排除 node_modules, .git 等）：

| 情况 | 处理 |
|------|------|
| 空目录 / 无代码文件 | 新项目 → 创建基础结构 |
| 存在代码文件 | 已有项目 → 创建结构 + 扫描分析 |

### Step 3: 创建目录结构

```
ADR/
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
- `## 关键结论` 区域 + `<!-- 新结论在此添加 -->` 占位符（AI 会话启动时读取此区获得项目全貌）
- 4 个类型的表格 + `<!-- 新记录在此添加 -->` 占位符

### Step 5（已有代码项目额外执行）: 扫描分析

1. **识别技术栈**（通过 package.json / requirements.txt / go.mod 等）
2. **扫描 Git 历史**（最近 20 条 commit）
3. **检测特殊代码**（TODO, FIXME, HACK, workaround）
4. 将发现输出给用户，建议创建对应记录

### Step 5.1: 持久化扫描发现

将 Step 5 扫描到的关键信息写入 `ADR/INDEX.md` 的 `## 关键结论` 区域，格式：

```
- [初始化] 技术栈：TypeScript + React + Vite，测试用 Vitest (日期)
- [初始化] 项目使用 monorepo 结构，pnpm workspace (日期)
- [初始化] 发现 12 处 TODO/FIXME，集中在 src/auth/ 和 src/api/ (日期)
```

写入原则：
- 技术栈必写（包含语言、框架、构建工具、测试框架）
- 项目结构特征必写（monorepo、微服务、单体等）
- TODO/FIXME 集中区域值得写（帮助后续会话快速定位问题区）
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
> 是否要将这些内容整理到 ADR/ 体系中？
> 1. **导入并整理** — 将内容按类型拆分到 ADR/ 对应目录，原文件保留备份
> 2. **仅建立索引** — 不移动文件，在 INDEX.md 中添加指向原文件的链接
> 3. **跳过** — 不处理，后续手动整理

处理规则：
- **导入并整理**：解析已有记录，按 change/decision/requirement/bug 分类，用模板格式重写到 ADR/ 目录，原文件重命名为 `*.backup.md`
- **仅建立索引**：在 INDEX.md 关键结论区添加 `- [已有] 项目原有 CHANGELOG.md 包含 47 条变更记录，详见原文件`，在对应表格中添加链接行
- **跳过**：不做任何操作

### Step 6: 创建 CLAUDE.md / AGENTS.md（如不存在）

在项目根目录创建 CLAUDE.md（Claude Code）和 AGENTS.md（OpenCode），包含 ADR 工作流规则。
如果已存在其中一个，只创建缺失的那个。

### Step 7: 输出总结

```markdown
## ADR 系统初始化完成

**项目类型：** [新项目 / 已有代码项目]

**已创建：**
- ADR/ 目录结构
- INDEX.md（含关键结论）
- 模板文件
- CLAUDE.md / AGENTS.md

**项目上下文（已有项目）：**
- 技术栈：[识别结果]
- 已有记录：[导入/索引/跳过 结果]
- 待关注：[TODO/FIXME 热点]

**下一步：**
- 开始工作后使用 /record 创建记录
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

- **不修改用户原有文件**：只创建新的 ADR/ 目录
- **已有代码时扫描但不自动创建记录**：输出建议，由用户决定
- **幂等安全**：重复执行不会破坏已有记录
