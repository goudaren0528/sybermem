---
type: index
category: special-cases
auto_update: true
last_updated: <!-- {{last_updated}} -->
---

# 特殊处理索引

> 本文件由系统自动维护，记录所有特殊处理情况的索引信息。
>
> **重要**: AI 在修改文件前必须检查此索引，确认是否有相关的特殊处理需要遵循！

---

## 统计概览

| 状态 | 数量 |
|------|------|
| Active | <!-- {{count_active}} --> |
| To Be Resolved | <!-- {{count_to_be_resolved}} --> |
| Resolved | <!-- {{count_resolved}} --> |
| Monitoring | <!-- {{count_monitoring}} --> |
| **总计** | <!-- {{total_count}} --> |

**最后更新**: <!-- {{last_updated}} -->

---

## 文件路径关联表 (关键)

> **AI 必读**: 修改以下文件时，必须先阅读对应的特殊处理记录！

| 文件路径 | 特殊处理记录 | 影响级别 | 状态 | 关键说明 |
|----------|--------------|----------|------|----------|
<!-- {{file_path_table}} -->
| `src/core/memory.c` | [SP-001-内存对齐处理](special-cases/SP-001-memory-alignment.md) | high | active | 内存分配需要特殊对齐 |
| `src/data/parser.rs` | [SP-002-遗留解析器兼容](special-cases/SP-002-legacy-parser.md) | medium | monitoring | 保留向后兼容代码 |

---

## 按类别分类

### Legacy (遗留代码)

> 历史遗留的特殊处理，需要谨慎对待

| 编号 | 标题 | 影响级别 | 状态 | 文件 |
|------|------|----------|------|------|
<!-- {{category_legacy_table}} -->

### Business (业务逻辑)

> 业务相关的特殊处理，理解业务背景很重要

| 编号 | 标题 | 影响级别 | 状态 | 文件 |
|------|------|----------|------|------|
<!-- {{category_business_table}} -->

### Temporary (临时方案)

> 临时性的特殊处理，需要关注后续优化

| 编号 | 标题 | 影响级别 | 状态 | 文件 |
|------|------|----------|------|------|
<!-- {{category_temporary_table}} -->

### Environment (环境相关)

> 特定环境下的特殊处理

| 编号 | 标题 | 影响级别 | 状态 | 文件 |
|------|------|----------|------|------|
<!-- {{category_environment_table}} -->

### Performance (性能优化)

> 为性能考虑的特殊处理

| 编号 | 标题 | 影响级别 | 状态 | 文件 |
|------|------|----------|------|------|
<!-- {{category_performance_table}} -->

### Security (安全相关)

> 安全相关的特殊处理

| 编号 | 标题 | 影响级别 | 状态 | 文件 |
|------|------|----------|------|------|
<!-- {{category_security_table}} -->

### Compatibility (兼容性)

> 兼容性相关的特殊处理

| 编号 | 标题 | 影响级别 | 状态 | 文件 |
|------|------|----------|------|------|
<!-- {{category_compatibility_table}} -->

### Custom (自定义)

> 其他自定义的特殊处理

| 编号 | 标题 | 影响级别 | 状态 | 文件 |
|------|------|----------|------|------|
<!-- {{category_custom_table}} -->

---

## 按模块分类

### 核心模块

| 编号 | 标题 | 类别 | 影响级别 | 文件路径 |
|------|------|------|----------|----------|
<!-- {{module_core_table}} -->

### 数据层

| 编号 | 标题 | 类别 | 影响级别 | 文件路径 |
|------|------|------|----------|----------|
<!-- {{module_data_table}} -->

### 接口层

| 编号 | 标题 | 类别 | 影响级别 | 文件路径 |
|------|------|------|----------|----------|
<!-- {{module_interface_table}} -->

### 业务逻辑

| 编号 | 标题 | 类别 | 影响级别 | 文件路径 |
|------|------|------|----------|----------|
<!-- {{module_business_table}} -->

### 基础设施

| 编号 | 标题 | 类别 | 影响级别 | 文件路径 |
|------|------|------|----------|----------|
<!-- {{module_infrastructure_table}} -->

---

## 高风险区域

> **警告**: 以下特殊处理影响级别为 high 且状态为 active，修改相关代码时务必谨慎！

| 编号 | 标题 | 文件路径 | 特殊处理说明 | 风险描述 |
|------|------|----------|--------------|----------|
<!-- {{high_risk_table}} -->

---

## 活跃特殊处理

> 状态为 active 或 monitoring 的特殊处理，需要特别关注

| 编号 | 标题 | 类别 | 影响级别 | 文件 |
|------|------|------|----------|------|
<!-- {{active_special_cases_table}} -->

---

## 待解决项

> 状态为 to_be_resolved 的特殊处理，需要后续优化

| 编号 | 标题 | 影响级别 | 预计完成日期 | 文件 |
|------|------|----------|--------------|------|
<!-- {{to_be_resolved_table}} -->

---

## 最近更新

| 编号 | 标题 | 状态变更 | 更新日期 | 文件 |
|------|------|----------|----------|------|
<!-- {{recent_updates_table}} -->

---

## AI 修改检查清单

> AI 在修改代码前应执行以下检查：

### 步骤 1: 检查文件路径
- [ ] 在文件路径关联表中查找目标文件
- [ ] 如有匹配，阅读对应的特殊处理记录

### 步骤 2: 理解特殊处理
- [ ] 理解特殊处理的原因
- [ ] 了解代码中的特殊标记 (TODO, FIXME, HACK)
- [ ] 确认修改不会破坏特殊处理的逻辑

### 步骤 3: 评估影响
- [ ] 检查影响级别 (high/medium/low)
- [ ] 如果是 high 级别，建议先与用户确认
- [ ] 考虑是否需要更新特殊处理记录

### 步骤 4: 执行修改
- [ ] 遵循特殊处理记录中的注意事项
- [ ] 如修改涉及特殊处理逻辑，更新记录
- [ ] 完成后更新索引

---

## 索引维护说明

### 自动更新规则
- 新增特殊处理记录时自动添加索引
- 状态变更时自动更新
- **文件路径关联表自动同步**
- 每次会话结束时同步

### 文件路径关联维护
- 从特殊处理记录的 `related_code` 字段自动提取
- 支持通配符匹配 (如 `src/core/*.c`)
- 多个文件路径自动展开

### 分类规则
- **类别分类**: 根据特殊处理记录 YAML 头部的 `category` 字段
- **模块分类**: 根据特殊处理记录 YAML 头部的 `related_code` 字段
- **风险标记**: `impact_level=high` 且 `status=active`

### 手动触发
- 执行 `/update-special-case-index` 手动更新
- 执行 `/record-special` 创建新记录时自动更新

---

## 快速查找

### 按状态筛选
- [Active](?status=active) - 活跃的特殊处理
- [To Be Resolved](?status=to_be_resolved) - 待解决项
- [Resolved](?status=resolved) - 已解决项
- [Monitoring](?status=monitoring) - 监控中

### 按影响级别筛选
- [高风险](?impact=high) - 高影响级别
- [中风险](?impact=medium) - 中等影响
- [低风险](?impact=low) - 低影响

### 按类别筛选
- [Legacy](?category=legacy) - 遗留代码
- [Business](?category=business) - 业务逻辑
- [Temporary](?category=temporary) - 临时方案
- [Environment](?category=environment) - 环境相关
- [Performance](?category=performance) - 性能优化
- [Security](?category=security) - 安全相关
- [Compatibility](?category=compatibility) - 兼容性
- [Custom](?category=custom) - 自定义