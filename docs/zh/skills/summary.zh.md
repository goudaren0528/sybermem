---
name: summary
description: 生成项目进展报告（周报或月报），汇总工作成果
---

# summary Skill

生成项目进展报告。默认生成周报，传入 `monthly` 参数生成月报。

## 使用方式

- `/summary` — 生成本周周报
- `/summary monthly` — 生成本月月报

## 流程

### Step 1: 确定报告范围

- 无参数或 `weekly` → 本周（最近 7 天）
- `monthly` → 本月（最近 30 天）

### Step 2: 收集数据

扫描 ADR/ 目录中对应时间范围内的记录文件：

```
ADR/changes/     → 功能变更
ADR/decisions/   → 技术决策
ADR/requirements/ → 需求记录
ADR/bugs/        → Bug 修复
```

同时参考 Git log 获取 commit 历史。

### Step 3: 生成报告

动态输出（不持久存储），格式：

```markdown
# 项目进展报告（YYYY-MM-DD ~ YYYY-MM-DD）

## 主要成果
- ...

## 关键决策
- ADR/decisions/...

## 问题与修复
- ADR/bugs/...

## 遗留问题
- ...

## 下一步计划
- ...
```

### Step 4: 月报额外内容

月报在周报基础上增加：
- 按周分组的进展汇总
- 本月数据统计（记录数量、类型分布）
- 趋势观察

## 设计原则

- **不持久存储**：报告动态生成，避免文件膨胀
- **数据驱动**：基于实际记录文件，不凭空推测
- **精简输出**：控制在一屏内可读完
