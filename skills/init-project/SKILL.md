---
name: init-project
description: 为项目注入 Sybermem 记忆系统（自动判断新项目或已有代码项目）
---

# init-project Skill

为项目创建 `.sybermem/` 目录结构，自动判断是新项目还是已有代码项目。

## 使用方式

用户执行 `/init-project` 或 Claude 主动调用。

## 核心设计

**智能判断：**
- 新项目（空目录）→ 创建基础结构，提示用户填写
- 已有代码 → 自动扫描、分析、生成完整内容（类似 adapt-project）

用户只需要一个入口，不需要判断用哪个 skill。

## 流程

### Step 1: 检查项目状态

检查是否已有 `.sybermem/` 目录：
- 如果已存在，提示用户并询问是否重新初始化
- 如果不存在，继续

### Step 2: 判断项目类型

扫描项目目录，判断是否为新项目：

**判断标准：**
```bash
# 检查是否有代码文件（排除 .sybermem/ 和常见配置目录）
find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.java" -o -name "*.go" -o -name "*.rs" -o -name "*.jsx" -o -name "*.tsx" -o -name "*.vue" -o -name "*.svelte" \) ! -path "./.sybermem/*" ! -path "./node_modules/*" ! -path "./.git/*" | head -5
```

| 项目类型 | 判断条件 | 处理方式 |
|----------|----------|----------|
| 新项目 | 无代码文件（或只有配置文件） | 创建基础结构 → 提示用户填写 |
| 已有代码 | 存在代码文件 | 自动扫描分析 → 生成完整内容 |

### Step 3a: 新项目流程（空目录）

如果是新项目：

1. 创建目录结构（见下方）
2. 使用模板生成初始 OVERVIEW.md（项目名称、基本结构）
3. 使用模板生成初始 PROGRESS.md（初始化阶段）
4. 生成各模块 INDEX.md
5. 注册项目到 sybermem
6. 提示用户补充内容

### Step 3b: 已有代码流程

如果已有代码，自动执行 adapt-project 逻辑：

1. **扫描项目结构**
   - 目录层级、关键目录（src/, lib/, app/, tests/）
   - 配置文件（package.json, requirements.txt, pom.xml 等）
   - 文件类型分布

2. **分析技术栈**
   - 根据配置文件识别：Node.js, Python, Java, Go, Rust 等
   - 提取依赖信息

3. **生成完整 OVERVIEW.md**
   - 项目定位：根据目录名和配置推断
   - 技术架构：根据技术栈和目录结构
   - 目录结构说明：根据扫描结果
   - 开发约定：推断或提示用户补充

4. **分析 Git 历史**
   - 追溯重要决策点
   - 提取功能添加、技术选型记录

5. **创建历史 ADR 记录**
   - 为重要决策创建 ADR 记录

6. **检测特殊处理代码**
   - 扫描关键词：hack, TODO, FIXME, workaround, temporary, legacy, special
   - 创建 SPECIAL-CASES 记录

7. **生成 PROGRESS.md**
   - 当前状态：根据 Git 历史
   - 活跃模块：最近修改的文件

8. 注册项目到 sybermem

### Step 4: 创建目录结构

创建完整的项目层目录结构：

```
.sybermem/
├── OVERVIEW.md
├── PROGRESS.md
├── ADR/
│   ├── INDEX.md
│   └── decisions/
├── REQUIREMENTS/
│   ├── INDEX.md
├── CHANGELOG/
│   ├── INDEX.md
├── EXPERIENCES/
│   ├── INDEX.md
│   ├── pitfalls/
│   ├── debug/
│   ├── best-practices/
│   ├── tools/
│   ├── performance/
│   └── refactor/
├── SPECIAL-CASES/
│   ├── INDEX.md
│   ├── legacy/
│   ├── business/
│   ├── temporary/
│   ├── environment/
│   └── custom/
```

### Step 5: 注册项目到 sybermem

在 sybermem 的 PROJECTS 中注册该项目：
1. 在 `PROJECTS/INDEX.md` 添加项目条目
2. 创建 `PROJECTS/registered/{project-name}/INFO.md`
3. 创建 `PROJECTS/registered/{project-name}/LINK.md`

## 输出总结

完成后，输出：

```markdown
## Sybermem 初始化完成

**项目类型：** [新项目 / 已有代码项目]

**已创建：**
- `.sybermem/` 目录结构
- OVERVIEW.md（[自动生成 / 待补充]）
- PROGRESS.md
- 各模块 INDEX.md
- [如有代码：ADR 记录、SPECIAL-CASES 记录]

**项目注册：**
- 已注册到 ~/.claude/sybermem/PROJECTS/

**下一步：**
- [新项目] 补充 OVERVIEW.md 内容
- [已有代码] 确认生成的 ADR 和 SPECIAL-CASES 记录
- 配置 developer/preferences.md 和 developer/values.md
```

## 关键原则

- **智能判断**：自动识别新项目或已有代码
- **一键入口**：用户不需要判断用哪个 skill
- **不修改用户原有文件**：只创建新的 `.sybermem/` 目录
- **已有代码时自动生成**：扫描、分析、生成完整内容

## 模板引用

模板文件位置：`sybermem/templates/`

## 技术栈识别表

| 配置文件 | 技术栈 |
|----------|--------|
| package.json | Node.js / JavaScript / TypeScript |
| requirements.txt / pyproject.toml | Python |
| pom.xml / build.gradle | Java |
| go.mod | Go |
| Cargo.toml | Rust |
| composer.json | PHP |

## 项目类型推断

| 目录特征 | 项目类型 |
|----------|----------|
| src/api/ 或 app/api/ | Web API Service |
| src/pages/ 或 app/pages/ | Web Application |
| src/components/ | UI Library / Component |
| tests/ 或 test/ | 测试项目 |
| docs/ 为主 | 文档项目 |