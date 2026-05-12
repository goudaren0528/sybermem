---
name: sybermem-record
description: 在项目中创建 SyberMem 记录（变更、决策、需求、Bug），也适用于仍然使用旧 ADR 存储的项目。
---

# sybermem-record Skill

统一的 SyberMem 记录入口。AI 根据上下文自动判断记录类型。

## 目录解析规则

在读取或写入记录之前，先解析项目数据目录：

1. 如果 `.sybermem/` 已存在，直接使用。
2. 如果只有 `ADR/`，将 `ADR/` 重命名为 `.sybermem/`，并告知用户旧目录已自动迁移。
3. 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，警告 `ADR/` 已被忽略，不自动合并。
4. 如果两者都不存在，提示用户先执行 `/sybermem-init-project`。

## 流程

### Step 1: 判断记录类型

根据当前工作上下文自动判断：

| 信号 | 类型 | 目录 |
|------|------|------|
| 新增/修改/删除功能代码 | change | `.sybermem/changes/` |
| 技术选型、架构设计、多方案权衡 | decision | `.sybermem/decisions/` |
| 用户提出需求、讨论功能方向 | requirement | `.sybermem/requirements/` |
| 修复 Bug、排查问题 | bug | `.sybermem/bugs/` |

判断不确定时，让用户选择。

### Step 2: 获取下一个编号

```
检查 .sybermem/{type}/ 目录 → 找最大编号 → +1
空目录 → 001
格式：001, 002, 003...
```

### Step 3: 收集信息

从当前会话上下文中提取，缺少关键信息时才询问用户。

### Step 4: 创建文件

路径：`.sybermem/{type}/{YYYY-MM-DD}-{NNN}-{标题}.md`

内容模板使用 `.claude/skills/sybermem-record/templates/{type}.md`。

### Step 5: 更新 INDEX.md 表格

在 `.sybermem/INDEX.md` 对应表格的 `<!-- add new records here -->` 注释上方插入新行。

### Step 6: 回写关键结论

在 `.sybermem/INDEX.md` 的 `## Key Conclusions` 区域插入一行一句话核心结论，必须同时包含“做了什么”和“为什么”。

## 错误处理

- 目录解析后仍不存在 `.sybermem/INDEX.md` → 提示先执行 `/sybermem-init-project`
- 编号冲突 → 自动递增
- 必填字段缺失 → 询问用户补充

## 不记录的情况

- 简单格式调整、注释修改
- 配置文件微调（无功能影响）
- WIP / draft 类工作
