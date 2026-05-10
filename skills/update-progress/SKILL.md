---
name: update-progress
description: 更新项目进展（PROGRESS.md）
---

# update-progress Skill

更新项目进展记录，记录今日任务和进展。

## 使用方式
- 用户执行 `/update-progress`
- SessionEnd Hook 自动触发

## 流程

### Step 1: 收集本次进展
- 完成的任务列表
- 创建的记录（ADR、CHANGELOG等）
- 遇到的问题
- 遗留事项

### Step 2: 读取现有 PROGRESS.md

### Step 3: 更新今日进展
追加今日任务和记录。

### Step 4: 检查本周/本月摘要
周一：重置本周摘要
月初：重置本月摘要

### Step 5: 更新当前状态
- 当前阶段
- 正在进行的任务
- 阻塞事项

### Step 6: 写入 PROGRESS.md

### Step 7: 更新 sybermem PROJECTS 状态
更新 PROJECTS/registered/{project-name}/STATUS.md

## 今日进展格式
```markdown
## 今日进展（YYYY-MM-DD）
- 完成任务：
  - xxx
  - xxx
- 创建记录：
  - ADR/xxx
  - CHANGELOG/xxx
- 遗留问题：xxx
```