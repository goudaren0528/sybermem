---
name: monthly-summary
description: 生成月报
---

# monthly-summary Skill

生成本月进展月报，汇总本月工作和里程碑。

## 使用方式
- 用户执行 `/monthly-summary`
- 定时触发（每月结束）

## 流程

### Step 1: 读取 PROGRESS.md
获取本月进展信息

### Step 2: 读取本月创建的记录
扫描本月所有记录

### Step 3: 汇总本月成果
- 功能交付情况
- 重要里程碑
- 经验沉淀
- 数据统计

### Step 4: 生成月报内容
动态生成月报（不持久存储）

### Step 5: 输出月报

### Step 6: 更新 PROGRESS 本月摘要

## 月报格式
```markdown
# 本月进展月报（YYYY-MM）

## 功能交付情况
- 新增功能：xxx

## 重要里程碑
- 完成架构重构

## 经验沉淀
- 踩坑经验：xx条

## 数据统计
- 新增 ADR：xx条
- 新增 CHANGELOG：xx条

## 下月计划
```