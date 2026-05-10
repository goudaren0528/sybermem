---
name: weekly-summary
description: 生成周报
---

# weekly-summary Skill

生成本周进展周报，汇总本周工作和成果。

## 使用方式
- 用户执行 `/weekly-summary`
- 定时触发（每周结束）

## 流程

### Step 1: 读取 PROGRESS.md
获取本周进展信息

### Step 2: 读取本周创建的记录
扫描本周创建的记录文件

### Step 3: 汇总本周成果
- 主要成果
- 关键决策
- 遇到的问题
- 经验总结

### Step 4: 生成周报内容
动态生成周报（不持久存储）

### Step 5: 输出周报
显示给用户确认

### Step 6: 更新 PROGRESS 本周摘要

## 周报格式
```markdown
# 本周进展周报（YYYY-WXX）

## 主要成果
- xxx

## 关键决策
- ADR/xxx

## 遇到的问题
- EXPERIENCES/pitfalls/xxx

## 经验总结
- EXPERIENCES/best-practices/xxx

## 下周计划
- 待办事项
```