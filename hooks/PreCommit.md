---
name: PreCommit
trigger: Git commit 前
---

# PreCommit Hook

Git commit 前，检查是否有对应的 ADR 或 CHANGELOG 记录。

## 触发时机

Git commit 执行前。

## 检查逻辑

### Step 1: 分析 commit 内容

分析即将 commit 的变更：
- 查看变更文件列表
- 分析变更类型

```bash
git diff --cached --name-only
git diff --cached --stat
```

### Step 2: 判断变更类型

根据变更内容判断：

| 变更类型 | 应有记录 |
|----------|----------|
| 架构调整、技术选型 | ADR/decisions/ |
| 功能新增、修改、删除 | CHANGELOG/ |
| 配置调整、格式修改 | 无需记录 |
| Bug 修复 | EXPERIENCES/pitfalls/（可选） |

判断方法：
- 新增配置文件（package.json, tsconfig.json）→ ADR
- 新增模块目录 → ADR 或 CHANGELOG
- 新增功能文件 → CHANGELOG
- 修改功能实现 → CHANGELOG
- 删除功能 → CHANGELOG

### Step 3: 检查是否有对应记录

检查对应目录是否有相关记录：
```bash
ls .sybermem/ADR/decisions/ | grep "{{date}}"
ls .sybermem/CHANGELOG/ | grep "{{date}}"
```

### Step 4: 提示用户

如果缺失记录，提示：
> "本次 commit 涉及 xxx 变更，是否需要创建记录？
> - 架构变更 → 执行 `/record-adr`
> - 功能变更 → 执行 `/record-change`"

如果已有记录或无需记录，继续 commit。

### Step 5: 用户选择

用户选择：
- 创建记录 → 调用对应 Skill
- 不创建 → 继续 commit（标记为日常小修改）
- 取消 commit → 返回处理

## 避免过度提示

不触发的情况：
- 简单格式调整
- 注释修改
- 配置微调（无功能影响）
- .sybermem/ 目录本身的变更

## 例外情况

以下情况允许跳过记录：
- 用户明确表示"日常小修改"
- WIP commit（标记为 work-in-progress）
- 配置调整

## 实现方式

Hook 通过 Git pre-commit 钩子或 Claude Code Hook 机制实现。

```bash
# Git pre-commit 钩子示例
#!/bin/bash
# 检查是否有对应的 ADR 或 CHANGELOG
# 如缺失，提示用户
```