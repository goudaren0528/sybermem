---
name: adapt-project
description: 为已有代码的项目适配 Sybermem 记忆系统
---

# adapt-project Skill

为已有代码的项目创建记忆系统，并分析现有代码生成初始记录。

## 使用方式
用户执行 `/adapt-project` 或 Claude 主动调用。

## 流程

### Step 1: 检查项目状态
检查当前项目是否已有 `.sybermem/` 目录。

### Step 2: 扫描项目结构
使用 Glob 分析目录结构：
- 关键目录（src/, lib/, app/, tests/）
- 配置文件（package.json, requirements.txt, pom.xml, go.mod, Cargo.toml）
- 文件类型分布

### Step 3: 分析技术栈
根据配置文件推断：
- package.json → Node.js/JS/TS
- requirements.txt/pyproject.toml → Python
- pom.xml/build.gradle → Java
- go.mod → Go
- Cargo.toml → Rust

### Step 4: 生成 OVERVIEW.md
基于扫描和分析结果生成：
- 项目定位（根据目录名和配置推断）
- 技术架构（技术栈 + 目录结构）
- 开发约定（推断或提示用户补充）

### Step 5: 分析 Git 历史
分析 git log 追溯关键决策点：
- 重要功能添加
- 技术选型记录
- 架构变更记录

### Step 6: 创建历史 ADR 记录
根据 Git 历史为重要决策创建 ADR。

### Step 7: 检测特殊处理代码
Grep 搜索关键词：hack, TODO, FIXME, workaround, temporary, legacy
为发现的特殊处理创建 SPECIAL-CASES 记录。

### Step 8: 创建目录结构和 INDEX

### Step 9: 注册项目到 sybermem

## 关键原则
- 不修改用户原有文件
- 追溯历史决策帮助理解项目演进
- 检测特殊处理避免误删重要逻辑