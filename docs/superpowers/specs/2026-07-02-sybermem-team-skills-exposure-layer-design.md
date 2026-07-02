# SyberMem Team Skills Exposure Layer 设计

> 把当前 Team CLI 能力暴露成用户可直接触发的 SyberMem skills，解决 `publish status` / `team summary` 与其他 slash workflow 不一致的问题。

**Date:** 2026-07-02
**Status:** Draft
**Scope:** 只为现有 Team CLI 能力增加 skill 包装层，不改变 Team 底层能力，不新增重复的 Team 业务命令。
**Parent specs:**
- `docs/superpowers/specs/2026-07-02-sybermem-team-push-bootstrap-flow-design.md`
- `docs/superpowers/specs/2026-07-02-sybermem-team-agent-consumption-layer-phaseE-design.md`

---

## 1. Background & Problem

当前 SyberMem 的使用方式存在明显不一致：

### 项目内工作流（skill 驱动）
- `/sybermem-record`
- `/sybermem-summary`
- `/sybermem-digest`
- `/sybermem-update`
- `/using-sybermem`

### Team 工作流（CLI 驱动）
- `sybermem publish status`
- `sybermem team summary`

这会造成：
- 用户日常工作流割裂
- Team 能力可发现性差
- 明明已有 Team MVP，使用方式却不像其余 SyberMem 技能那样自然

---

## 2. Design Goal

为当前已有的 Team CLI 能力增加对应的 skills：

- `/sybermem-team-publish`
- `/sybermem-team-summary`

这样：
- **CLI 保留**：给自动化、脚本、agent 调用
- **Skill 补上**：给用户日常 slash workflow

保持双入口并存，但语义一致。

---

## 3. Design Choice

### 不选：继续只保留 CLI
缺点：和现有 SyberMem 使用方式割裂，用户必须记 CLI。

### 不选：把 Team 能力塞进已有 `/sybermem-summary` / `/using-sybermem`
缺点：语义混杂，层级不清。

### 选择：双入口并存
- CLI 继续保留
- Skill 做交互包装层

并明确：
> skill 是交互层，CLI 是执行层。

---

## 4. New Skills

### 4.1 `/sybermem-team-publish`

#### 目标
用户在项目内运行：

```text
/sybermem-team-publish
```

它包装现有：

```bash
sybermem publish status
```

#### 行为
- 如果当前项目已记住 Team 关联 → 直接发布
- 如果还没 Team 关联 → 引导提供 Team path 或初始化 Team repo
- 如果项目未初始化 → 明确路由到 `/sybermem-init-project`

#### 用户输出风格
面向用户解释结果，而不是直接暴露原始 JSON：

```md
## Team Publish
- Project: sybermem
- Team: team_rental_platform
- Team path: D:/team-memory

Published:
- project.md
- current-status.md
- meta.json
- dashboards/current-overview.md

Push: success
```

---

### 4.2 `/sybermem-team-summary`

#### 目标
用户运行：

```text
/sybermem-team-summary
```

它包装现有：

```bash
sybermem team summary --team-path ...
```

#### 行为
- 优先从当前项目的 `project.yaml.team.team_path` 读取 Team 路径
- 如果没有 Team 关联 → 提示用户提供 Team repo path
- 如果 Team repo 还没有任何发布内容 → 明确提示先跑 Team publish

#### 用户输出风格

```md
## Team Summary Generated
- Team: team_rental_platform
- Team path: D:/team-memory

Generated:
- dashboards/latest-management-summary.md
- dashboards/latest-management-summary.json
- dashboards/.summary-state.json

Recommended reading:
- dashboards/latest-management-summary.md
```

---

## 5. Routing Rules with Existing Skills

### `/using-sybermem`
升级为总诊断入口，额外报告：
- 当前项目是否已关联 Team
- Team path 是否可访问
- 当前可直接运行 `/sybermem-team-publish` / `/sybermem-team-summary`

### `/sybermem-init-project`
只负责项目级初始化。
- 如果用户误跑 `/sybermem-team-publish` 且项目未初始化 → 明确路由到 `/sybermem-init-project`

### `/sybermem-update`
不直接执行 Team 动作，但 update 完成后应提示：
- 如果项目有 Team 关联 → 可运行 Team skills
- 如果没有 → 如果要进入 Team memory，可运行 `/sybermem-team-publish`

### `/sybermem-summary`
保持项目级摘要语义：
- 回答“当前项目现在怎么样？”

### `/sybermem-team-summary`
保持团队级语义：
- 回答“团队最近整体发生了什么？”

---

## 6. Command/Skill Boundary

### 保留 CLI 能力
- `sybermem publish status`
- `sybermem team summary`

### 新增 skills
- `/sybermem-team-publish`
- `/sybermem-team-summary`

### 明确不新增重复 CLI
- 不新增 `team push`
- 不新增 `team bootstrap`

原因：
- Team Push Bootstrap Flow 已经确认由现有 `publish status` 承担
- 只需要 skill 包装层，不需要再造一套平行业务语义

---

## 7. UX Principles

### 用户只需要记住的 Team 工作流
项目 owner：
- `/sybermem-record`
- `/sybermem-summary`
- `/sybermem-team-publish`

管理者 / 管理 agent：
- `/sybermem-team-summary`

不确定时：
- `/using-sybermem`

### Team skill 输出必须目标导向
不要只回显 CLI JSON。
要告诉用户：
- 发布去了哪里
- 生成了什么
- 下一步看哪里

---

## 8. Out of Scope

本轮明确不做：
- `/sybermem-team-init`
- `/sybermem-team-review`
- `/sybermem-team-search`
- `/sybermem-team-sync`

先把最常用、最核心的 Team 入口补齐即可。

---

## 9. Success Criteria

1. 用户可以通过 slash workflow 直接触发 Team publish
2. 用户可以通过 slash workflow 直接触发 Team management summary
3. 不新增和 `publish` 重复语义的新业务命令
4. Team skills 和现有 `using-sybermem` / `sybermem-summary` / `sybermem-update` 路由边界清晰
5. CLI 继续保留，skill 只做交互包装层
