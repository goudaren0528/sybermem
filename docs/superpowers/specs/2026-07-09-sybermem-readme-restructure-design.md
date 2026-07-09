# SyberMem README 重构设计

> 将 README 中英版从“演进历史说明”重构为“当前能力与使用方式说明”，减少 ADR/阶段历程叙述，突出当前可用能力、日常工作流与 Team workflow。

**Date:** 2026-07-09
**Status:** Draft
**Scope:** 只重构 `README.md` 与 `README.en.md` 的信息架构和文案重心；不改变代码，不删除详细 specs/docs，只调整 README 作为产品入口文档的角色。

---

## 1. Background & Problem

当前 README 的主要问题不是信息缺失，而是**信息重心错位**：

- 过多聚焦在 ADR / 历史迁移 / 阶段演进
- 用户第一次阅读时，很难快速知道 **现在的 SyberMem 到底能做什么**
- 项目 owner、管理者、管理 agent 的日常使用路径不够清楚
- Team 能力虽然已经发展很多，但 README 仍带有较强的“阶段进度播报”感

结果就是：
- 新用户不容易快速理解当前产品能力
- 老用户也不容易一眼找到当前最重要的动作
- README 更像“项目演进记录”，而不是“当前产品说明”

---

## 2. Design Goal

README 中英版应重构为：

> **“当前 SyberMem 是什么、现在能做什么、你今天该怎么用”**

而不是：

> **“它曾经如何从 ADR / v1 / 多个阶段一步步演进到现在”**

README 的角色应明确为：
- 产品入口说明
- 安装入口
- 工作流入口
- Team workflow 入口

更细的背景、设计史、迁移细节保留在：
- `INSTALL.md`
- `docs/superpowers/specs/`
- digests / theme digests / records

---

## 3. Core Content Principles

### 3.1 以当前能力为中心
README 必须先回答：
- SyberMem 是什么
- 当前支持哪些能力
- 当前支持哪些平台
- 当前 Team workflow 怎么用

### 3.2 以使用路径为中心
README 必须让用户知道：
- 初始化项目
- 做完工作后记录
- 阶段稳定后 digest
- 发布到 Team memory
- 生成 Team summary

### 3.3 中英文结构尽量一致
不是只翻译句子一致，而是：
- 信息层级一致
- 段落结构一致
- 未来维护成本最低

### 3.4 历史细节降级
这些内容不再作为 README 主叙事：
- 详细 ADR 迁移史
- stop hook 修复史
- 分阶段实现史（Phase A/B/C/...）的过细描述
- 某次 update 做了什么

这些内容保留在 docs/specs/changelog 层。

---

## 4. Recommended README Structure

### 1. What is SyberMem?
一句话定义当前产品：
- 面向 AI 工作流的项目/团队工程记忆系统
- 记录项目进展、阶段沉淀、团队摘要，并支持管理 agent 消费

### 2. Core Capabilities
按当前能力而不是历史阶段来组织：

#### Project
- structured records
- phase index
- digest / theme digest
- search / link

#### Hub
- project registry
- workspace search
- portfolio / status

#### Team
- team init
- team publish
- team overview
- team summary
- digest history layer

### 3. Install
保留当前推荐安装路径：
- Claude Code plugin install
- script install（兼容）
- OpenCode path

不在这里展开过多迁移历史。

### 4. Daily Workflow
按用户角色提供最小动作路径：

#### 项目 owner
- `/sybermem-record`
- `/sybermem-summary`
- `/sybermem-digest`
- `/sybermem-team-publish`

#### 管理者 / 管理 agent
- `/sybermem-team-summary`

#### 不确定时
- `/using-sybermem`

### 5. Team Workflow
明确讲清当前 Team 能力：
- team init
- publish status
- current overview
- team summary
- digest history

并强调：

```text
概括看 status
详细看 digest
```

### 6. Modes / Reminder Behavior
简洁说明：
- `auto` = 轻量 `change` trail + reminders
- `remind` = reminders only, no automatic `change` trail

### 7. Repo Structure
只讲当前结构，不讲过多设计史。

### 8. More Docs
最后引导到：
- `INSTALL.md`
- `docs/superpowers/specs/`
- 中文 docs 目录

---

## 5. Content to Reduce or Move Out of README Main Flow

这些内容不一定删除，但不再作为 README 主体重点：
- ADR 迁移的长篇解释
- 子目录 stop hook 修复细节
- “为什么以前是这样”的长段解释
- Team Phase A/B/C/D/E/F 的详细里程碑播报语气

尤其 Team 部分应从“阶段汇报”改成“当前怎么用”。

---

## 6. Team Section Reframing

README 中的 Team 内容不应主要写成：
- 现在到了哪个 Phase
- 之前做了什么里程碑

而应主要写成：

### Team workflow today
1. 项目内记录 / digest
2. `/sybermem-team-publish` 同步到 Team repo
3. 自动更新 `current-overview.md`
4. `/sybermem-team-summary` 生成管理摘要
5. 需要时下钻 digest 历史

这样更贴近真实使用，而不是开发进度。

---

## 7. Success Criteria

1. 新用户打开 README 能快速理解当前 SyberMem 是什么
2. 用户能一眼看到最重要的工作流命令
3. Team workflow 比现在更清楚、可执行
4. README 不再主要围绕 ADR / 演进历史叙事
5. 中英文 README 结构一致，便于长期维护
