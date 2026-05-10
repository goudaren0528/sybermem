---
name: optimize-memory
description: 执行记忆优化，精简和整理记忆内容
---

# optimize-memory Skill

精简优化记忆内容，保持记忆系统质量。

## 使用方式

- 用户执行 `/optimize-memory`
- 定期触发（记录数量超过阈值）
- review-project 后执行

## 触发条件

| 条件 | 说明 |
|------|------|
| 记录数量超过阈值 | 如 ADR > 50 条 |
| 定期触发 | 每月执行一次 |
| review-project 后 | 评审发现需要优化 |
| 用户手动触发 | 用户主动请求 |

## 流程

### Step 1: 检查各目录记录数量

统计各目录记录数量：
- ADR/decisions/
- CHANGELOG/
- EXPERIENCES/
- SPECIAL-CASES/
- REQUIREMENTS/

```bash
find .sybermem/ADR/decisions -name "*.md" | wc -l
find .sybermem/CHANGELOG -name "*.md" | wc -l
...
```

### Step 2: 检查记录质量和价值

检查内容：
- **重复记录**：相同内容的记录
- **过时记录**：status=deprecated 或 superseded
- **低价值记录**：impact=low 且长时间未引用
- **已完成记录**：REQUIREMENTS 中 status=completed

### Step 3: 生成优化建议

生成优化建议列表：

| 操作类型 | 条件 | 示例 |
|----------|------|------|
| 合并 | 重复/相似内容 | ADR-005 和 ADR-008 内容相似 |
| 删除 | 低价值 + 未引用 | EXPERIENCES/tools/xxx 无引用 |
| 归档 | 已完成/废弃 | REQUIREMENTS-xxx 已 completed |
| 更新 INDEX | 删除记录后 | 更新 INDEX 文件 |

### Step 4: 用户确认优化方案

展示优化建议，用户确认：
- 同意合并 → 执行合并
- 同意删除 → 执行删除
- 同意归档 → 执行归档
- 暂不执行 → 保留现状

### Step 5: 执行优化操作

执行用户确认的操作：

**合并操作：**
- 选择主记录，保留
- 其他记录内容合并到主记录
- 删除其他记录文件
- 更新 INDEX

**删除操作：**
- 删除记录文件
- 更新 INDEX
- 可选：备份删除内容到归档目录

**归档操作：**
- 移动到 archive/ 目录（可选创建）
- 更新原 INDEX 标记为已归档

### Step 6: 更新 OVERVIEW 摘要

更新 OVERVIEW.md 的关键决策索引和特殊处理提醒部分。

### Step 7: 生成优化记录

生成优化执行记录：
```markdown
# 记忆优化记录（YYYY-MM-DD）

## 合并记录
- ADR-005 + ADR-008 → ADR-005（合并原因）

## 删除记录
- EXPERIENCES/tools/xxx（低价值）

## 归档记录
- REQUIREMENTS-xxx → archive/（已完成）

## 优化效果
- 记录数量：ADR 50 → 48
- 总记录数：xxx → xxx
```

## 保留原则

不删除的内容：
- 高影响级别记录（impact=high）
- 近期创建记录（最近 1 个月）
- 状态为 accepted 的 ADR
- 状态为 active 的 SPECIAL-CASES

## 安全策略

- 删除前备份（可选）
- 提示用户确认每项操作
- 可回滚（git 可恢复）

## 定期触发建议

建议每月执行一次 optimize-memory，保持记忆系统精简高效。