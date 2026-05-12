---
name: record
description: 创建项目记录（变更/决策/需求/Bug），自动判断类型，一个入口完成所有记录
---

# record Skill

统一的记录入口。AI 根据上下文自动判断记录类型，用户无需选择。

## 流程

### Step 1: 判断记录类型

根据当前工作上下文自动判断，无需询问用户：

| 信号 | 类型 | 目录 |
|------|------|------|
| 新增/修改/删除功能代码 | change | ADR/changes/ |
| 技术选型、架构设计、多方案权衡 | decision | ADR/decisions/ |
| 用户提出需求、讨论功能方向 | requirement | ADR/requirements/ |
| 修复 Bug、排查问题 | bug | ADR/bugs/ |

**判断不确定时**，用 AskUserQuestion 让用户选择。

### Step 2: 获取下一个编号

```
检查 ADR/{type}/ 目录 → 找最大编号 → +1
空目录 → 001
格式：001, 002, 003...
```

### Step 3: 收集信息

从当前会话上下文中提取，缺少关键信息时才询问用户。

**change**（必填：变更内容、变更原因、影响范围）：

```yaml
frontmatter:
  type: change
  date: YYYY-MM-DD
  number: NNN
  title: 简要标题
  status: implemented | planned | reverted
sections:
  - 变更内容
  - 变更原因
  - 影响范围
```

**decision**（必填：背景、考虑的方案、最终决策）：

```yaml
frontmatter:
  type: decision
  date: YYYY-MM-DD
  number: NNN
  title: 简要标题
  status: accepted | deprecated | superseded
sections:
  - 背景
  - 考虑的方案
  - 最终决策
  - 影响与后果
```

**requirement**（必填：需求来源、需求内容、最终结论）：

```yaml
frontmatter:
  type: requirement
  date: YYYY-MM-DD
  number: NNN
  title: 简要标题
  source: 来源
  priority: high | medium | low
sections:
  - 需求来源
  - 需求内容
  - 最终结论
```

**bug**（必填：Bug描述、问题原因、解决方案）：

```yaml
frontmatter:
  type: bug
  date: YYYY-MM-DD
  number: NNN
  title: 简要标题
  severity: critical | high | medium | low
sections:
  - Bug描述
  - 问题原因
  - 解决方案
  - 预防措施
```

### Step 4: 创建文件

路径：`ADR/{type}/{YYYY-MM-DD}-{NNN}-{标题}.md`

使用 `.claude/skills/record/templates/{type}.md` 模板。

### Step 5: 更新 INDEX.md 表格

在 `ADR/INDEX.md` 对应表格的 `<!-- 新记录在此添加 -->` 注释上方插入新行。

### Step 6: 回写关键结论

在 `ADR/INDEX.md` 的 `## 关键结论` 区域，`<!-- 新结论在此添加 -->` 注释上方插入一行：

```
- [类型-编号] 一句话核心结论 (日期)
```

示例：
```
- [决策-003] 选择 JWT 鉴权而非 Session，支持多端场景 (2026-05-11)
- [变更-007] 登录流程改为手机号+验证码，去掉密码 (2026-05-11)
- [Bug-002] 修复并发写入导致的数据丢失，加了行锁 (2026-05-11)
```

要求：结论必须包含**做了什么**和**为什么**，一句话内完成。

## 错误处理

- INDEX.md 不存在 → 提示先初始化项目
- 编号冲突 → 自动递增
- 必填字段缺失 → 询问用户补充

## 不记录的情况

- 简单格式调整、注释修改
- 配置文件微调（无功能影响）
- WIP/draft 类工作
