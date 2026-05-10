---
name: record-requirement
description: 创建需求讨论记录
---

# record-requirement Skill

创建需求讨论记录，记录需求来源、讨论过程、最终结论。

## 使用方式
- 用户执行 `/record-requirement`
- 收到需求时主动调用

## 流程

### Step 1: 收集需求信息
- 需求来源：用户反馈/客户需求/内部讨论
- 需求内容
- 优先级：high/medium/low

### Step 2: 记录讨论过程
- 关键观点
- 疑问和限制条件
- 不同方案

### Step 3: 获取下一个编号
检查 .sybermem/REQUIREMENTS/ 目录

### Step 4: 使用模板生成文件
templates/requirement-template.md

### Step 5: 创建文件
.sybermem/REQUIREMENTS/YYYY-MM-DD-NNN-title.md

### Step 6: 更新 REQUIREMENTS INDEX

### Step 7: 链接相关决策/变更
需求完成后链接到 ADR 或 CHANGELOG

## 状态追踪
| 状态 | 说明 |
|------|------|
| pending | 待处理 |
| in-progress | 进行中 |
| completed | 已完成 |
| cancelled | 已取消 |

## 与其他记录的关系
需求 → 讨论 → 决策（ADR） → 实施（CHANGELOG）