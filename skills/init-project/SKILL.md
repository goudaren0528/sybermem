---
name: init-project
description: 为新项目注入 Sybermem 记忆系统
---

# init-project Skill

为新项目创建 `.sybermem/` 目录结构，注入记忆系统。

## 使用方式

用户执行 `/init-project` 或 Claude 主动调用。

## 流程

### Step 1: 检查项目状态

检查当前项目是否已有 `.sybermem/` 目录：
- 如果已存在，提示用户并询问是否重新初始化
- 如果不存在，继续创建

### Step 2: 创建目录结构

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

### Step 3: 生成初始 OVERVIEW.md

使用模板 `templates/overview-template.md`：
- 项目定位：根据项目名称推断
- 技术架构：根据目录结构分析
- 其他部分：提示用户补充

### Step 4: 生成 PROGRESS.md

使用模板 `templates/progress-template.md`：
- 当前状态：初始化阶段
- 其他部分：待填充

### Step 5: 生成各模块 INDEX.md

使用对应的 INDEX 模板创建各模块 INDEX 文件。

### Step 6: 注册项目到 sybermem

在 sybermem 的 PROJECTS 中注册该项目：
1. 在 `PROJECTS/INDEX.md` 添加项目条目
2. 创建 `PROJECTS/registered/{project-name}/INFO.md`
3. 创建 `PROJECTS/registered/{project-name}/LINK.md`

### Step 7: 提示用户补充

提示用户：
- 补充 OVERVIEW.md 中的项目定位、技术架构等内容
- 补充 developer/preferences.md 和 developer/values.md

## 关键原则

- **不修改用户原有文件**：只创建新的 `.sybermem/` 目录
- **不修改项目根目录 CLAUDE.md**：项目层独立

## 模板引用

模板文件位置：`sybermem/templates/`

## 项目命名规范

项目名称使用目录名或用户指定的名称，格式：
- 小写字母
- 连字符分隔单词
- 例：`my-project`, `payment-service`