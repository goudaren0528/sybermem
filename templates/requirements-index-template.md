---
type: index
category: requirements
auto_update: true
last_updated: <!-- {{last_updated}} -->
---

# 需求记录索引

> 本文件由系统自动维护，记录所有需求的索引信息。

---

## 统计概览

| 状态 | 数量 |
|------|------|
| Draft | <!-- {{count_draft}} --> |
| Discussing | <!-- {{count_discussing}} --> |
| Confirmed | <!-- {{count_confirmed}} --> |
| Implemented | <!-- {{count_implemented}} --> |
| Closed | <!-- {{count_closed}} --> |
| **总计** | <!-- {{total_count}} --> |

**最后更新**: <!-- {{last_updated}} -->

---

## 时间排序索引

### 最近一周

| 编号 | 日期 | 标题 | 优先级 | 状态 | 文件 |
|------|------|------|--------|------|------|
<!-- {{recent_week_table}} -->

### 最近一月

| 编号 | 日期 | 标题 | 优先级 | 状态 | 文件 |
|------|------|------|--------|------|------|
<!-- {{recent_month_table}} -->

### 全部记录

| 编号 | 日期 | 标题 | 优先级 | 状态 | 文件 |
|------|------|------|--------|------|------|
<!-- {{all_requirements_table}} -->
| R-001 | 2024-01-15 | 示例需求 | high | confirmed | [R-001-example.md](requirements/R-001-example.md) |

---

## 按状态分类

### Draft (草稿)

> 需求初步提出，尚未进入讨论

| 编号 | 标题 | 来源 | 提出日期 | 文件 |
|------|------|------|----------|------|
<!-- {{status_draft_table}} -->

### Discussing (讨论中)

> 需求正在讨论，方案待确定

| 编号 | 标题 | 来源 | 讨论次数 | 文件 |
|------|------|------|----------|------|
<!-- {{status_discussing_table}} -->

### Confirmed (已确认)

> 需求已确认，等待实施

| 编号 | 标题 | 优先级 | 确认日期 | 文件 |
|------|------|--------|----------|------|
<!-- {{status_confirmed_table}} -->

### Implemented (已实现)

> 需求已实现，相关变更已完成

| 编号 | 标题 | 实现日期 | 相关变更 | 文件 |
|------|------|----------|----------|------|
<!-- {{status_implemented_table}} -->

### Closed (已关闭)

> 需求已关闭（取消或无效）

| 编号 | 标题 | 关闭原因 | 关闭日期 | 文件 |
|------|------|----------|----------|------|
<!-- {{status_closed_table}} -->

---

## 按优先级分类

### High (高优先级)

> 需要优先处理的需求

| 编号 | 标题 | 状态 | 来源 | 文件 |
|------|------|------|------|------|
<!-- {{priority_high_table}} -->

### Medium (中优先级)

> 正常优先级的需求

| 编号 | 标题 | 状态 | 来源 | 文件 |
|------|------|------|------|------|
<!-- {{priority_medium_table}} -->

### Low (低优先级)

> 低优先级的需求

| 编号 | 标题 | 状态 | 来源 | 文件 |
|------|------|------|------|------|
<!-- {{priority_low_table}} -->

---

## 按来源分类

### 用户反馈

| 编号 | 标题 | 提出人 | 状态 | 文件 |
|------|------|--------|------|------|
<!-- {{source_user_feedback_table}} -->

### 业务需求

| 编号 | 标题 | 提出人 | 状态 | 文件 |
|------|------|--------|------|------|
<!-- {{source_business_table}} -->

### 技术改进

| 编号 | 标题 | 提出人 | 状态 | 文件 |
|------|------|--------|------|------|
<!-- {{source_tech_improvement_table}} -->

### 合规要求

| 编号 | 标题 | 提出人 | 状态 | 文件 |
|------|------|--------|------|------|
<!-- {{source_compliance_table}} -->

### 其他

| 编号 | 标题 | 提出人 | 状态 | 文件 |
|------|------|--------|------|------|
<!-- {{source_other_table}} -->

---

## 高优先级待处理

> 优先级为 high 且状态为 draft/confirmed 的需求

| 编号 | 标题 | 状态 | 来源 | 确认日期 |
|------|------|------|------|----------|
<!-- {{high_priority_pending_table}} -->

---

## 最近更新

| 编号 | 标题 | 状态变更 | 更新日期 | 文件 |
|------|------|----------|----------|------|
<!-- {{recent_updates_table}} -->

---

## 需求生命周期

```
Draft → Discussing → Confirmed → Implemented → Closed
                 ↘ Cancelled → Closed
```

### 状态说明

| 状态 | 说明 | 下一步 |
|------|------|--------|
| Draft | 需求草稿，初步提出 | 进入讨论或直接确认 |
| Discussing | 正在讨论中 | 确认或取消 |
| Confirmed | 已确认，等待实施 | 开始实施 |
| Implemented | 已实现完成 | 验收并关闭 |
| Closed | 已关闭（完成或取消） | - |

---

## 相关记录链接

### 关联决策

| 需求编号 | 需求标题 | 相关决策 | 决策标题 |
|----------|----------|----------|----------|
<!-- {{related_decisions_table}} -->

### 关联变更

| 需求编号 | 需求标题 | 相关变更 | 变更标题 |
|----------|----------|----------|----------|
<!-- {{related_changes_table}} -->

---

## 需求统计

### 按月统计

| 月份 | Draft | Discussing | Confirmed | Implemented | Closed | 总计 |
|------|-------|------------|-----------|-------------|--------|------|
<!-- {{monthly_stats_table}} -->

### 按来源统计

| 来源 | Draft | Discussing | Confirmed | Implemented | Closed | 总计 |
|------|-------|------------|-----------|-------------|--------|------|
<!-- {{source_stats_table}} -->

---

## 索引维护说明

### 自动更新规则
- 新增需求记录时自动添加索引
- 状态变更时自动更新
- 每次会话结束时同步

### 分类规则
- **状态分类**: 根据需求记录 YAML 头部的 `status` 字段
- **优先级分类**: 根据需求记录 YAML 头部的 `priority` 字段
- **来源分类**: 根据需求记录 YAML 头部的 `source` 字段

### 手动触发
- 执行 `/update-requirement-index` 手动更新
- 执行 `/record-requirement` 创建新需求时自动更新

---

## 快速查找

### 按状态筛选
- [Draft](?status=draft) - 草稿
- [Discussing](?status=discussing) - 讨论中
- [Confirmed](?status=confirmed) - 已确认
- [Implemented](?status=implemented) - 已实现
- [Closed](?status=closed) - 已关闭

### 按优先级筛选
- [High](?priority=high) - 高优先级
- [Medium](?priority=medium) - 中优先级
- [Low](?priority=low) - 低优先级

### 按来源筛选
- [用户反馈](?source=user_feedback)
- [业务需求](?source=business)
- [技术改进](?source=tech_improvement)
- [合规要求](?source=compliance)
- [其他](?source=other)

### 按时间筛选
- [最近一周](?days=7)
- [最近一月](?days=30)
- [最近三月](?days=90)
- [全部](?days=all)