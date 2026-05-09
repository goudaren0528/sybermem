---
name: record-adr
description: 创建 ADR 记录文件并更新索引，用于记录功能性变更、技术决策、讨论需求和Bug修复
---

# record-adr Skill

用于创建符合 ADR 规范的记录文件并自动更新索引。

## 使用方式

- 用户执行 `/record-adr`
- Claude 在完成工作后主动调用

## 流程

### Step 1: 确定记录类型

询问用户或根据上下文判断记录类型：
- `change` - 功能性变更
- `decision` - 技术决策
- `requirement` - 讨论/需求记录
- `bug` - Bug修复记录

### Step 2: 获取下一个编号

检查 `ADR/{type}/` 目录，找到下一个可用编号：
- 查看已有文件，确定最大编号
- 新编号 = 最大编号 + 1（格式：001, 002, ...）
- 如果目录为空，编号为 001

### Step 3: 收集必要信息

根据类型收集必填字段：

**change 类型**:
- 标题
- 变更内容
- 变更原因
- 影响范围
- 状态（implemented | planned | reverted）
- 作者（可选）
- 关联文件（可选）

**decision 类型**:
- 标题
- 背景
- 考虑的方案
- 最终决策
- 状态（accepted | deprecated | superseded）

**requirement 类型**:
- 标题
- 需求来源
- 需求内容
- 讨论过程（可选）
- 最终结论
- 优先级（high | medium | low）

**bug 类型**:
- 标题
- Bug描述
- 问题原因
- 解决方案
- 严重程度（critical | high | medium | low）

### Step 4: 生成记录文件

使用模板生成文件内容，创建文件：
```
ADR/{type}/{YYYY-MM-DD}-{number}-{title}.md
```

示例：`ADR/changes/2026-05-08-001-添加用户登录功能.md`

### Step 5: 更新 INDEX.md

在 `ADR/INDEX.md` 对应表格中添加新条目：

```markdown
| {number} | {date} | {title} | {status} | [链接](changes/{filename}.md) |
```

插入到对应表格的注释占位符下方。

## 必填字段检查

每种类型必须包含以下字段，否则拒绝创建：

| 类型 | 必填字段 |
|------|----------|
| change | 变更内容、变更原因、影响范围 |
| decision | 背景、考虑的方案、最终决策 |
| requirement | 需求来源、需求内容、最终结论 |
| bug | Bug描述、问题原因、解决方案 |

## 错误处理

- 如果 INDEX.md 不存在，提示用户先运行初始化
- 如果编号冲突，自动递增直到找到可用编号
- 如果必填字段缺失，提示用户补充

## 模板位置

模板文件位于 `.claude/skills/record-adr/templates/` 目录：
- `change.md`
- `decision.md`
- `requirement.md`
- `bug.md`