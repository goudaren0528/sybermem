# SyberMem Team Push Bootstrap Flow 设计

> 不新增 `team push` 之类的重复能力，而是直接升级现有 `sybermem publish status`，让它成为 Team memory 的高层发布入口：缺什么前置就补什么。

**Date:** 2026-07-02
**Status:** Draft
**Scope:** 只设计 `publish status` 的 bootstrap orchestration；不新增并行命令，不改变 Team repo 数据模型。
**Parent specs:**
- `docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseB-design.md`
- `docs/superpowers/specs/2026-07-02-sybermem-team-mvp-phaseD-design.md`

---

## 1. Background & Problem

当前 SyberMem 已经具备 Team publication 的底层能力：
- 项目初始化 / project identity
- Team repo 初始化
- `publish status`
- auto-overview
- management summary
- Team digest history

但用户体验上仍有一个明显问题：

> 如果用户的真实心智模型是“我要把这个项目推到 Team memory”，那么系统现在还要求用户自己记住很多前置步骤。

例如：
- 项目还没初始化要先 `/sybermem-init-project`
- 没 `project.yaml` 要先 `project init`
- 没 Team 关联要先指定 `--team-path`
- Team repo 不存在要先 `team init`
- 没 digest 时 publish 的行为也要用户自己理解

这导致能力虽已齐全，但“目标导向体验”不够强。

---

## 2. Design Goal

**不新增 `team push` 之类的重复入口。**

而是把现有：

```bash
sybermem publish status
```

升级成：

> **Team Push Bootstrap Flow 的唯一入口**

即：
- 用户只表达目标：把项目发布到 Team memory
- 系统自动检查并补齐必要路径
- 只有在高影响或有歧义时才停下来确认

---

## 3. Design Choice

### 不选：继续保持当前严格前置模式
缺点：用户必须记住大量前置步骤，体验差。

### 不选：新增 `sybermem team push`
缺点：和 `publish status` 重复，造成心智分裂与内部逻辑重复。

### 选择：升级 `sybermem publish status`
让它成为：
- 当前唯一的 Team 发布入口
- 内部具备 bootstrap orchestration

这最符合用户希望的：

```text
我只要记住 publish
```

---

## 4. Core UX Principle

### 用户只需要记住

```bash
sybermem publish status
```

### 系统内部负责

```text
publish status
  → 检查项目是否初始化
  → 检查 project identity
  → 检查 Team 关联
  → 检查 Team repo
  → 检查 digest / readiness
  → 执行 publish
```

### 提示方式

所有提示都应该围绕“完成 publish”来组织，而不是把用户拉进实现细节：

不要说：
- 你缺 `project.yaml`
- 你缺 `team_path`
- 你缺 `team init`

要说：
- 为了完成 publish，我需要先初始化项目身份
- 为了完成 publish，我需要你确认 Team repo
- 为了完成 publish，我会先补一个 digest

---

## 5. Check Order and Decision Tree

### Step 1: 项目初始化检查

#### 情况 A：项目已初始化
- 已有 `.sybermem/` → 继续

#### 情况 B：项目未初始化
- 不直接报错
- 提示：

```text
This project is not initialized for SyberMem yet.
Initialize project memory first so it can be published to Team memory? [yes/no]
```

如果用户确认：
- 触发等价于 `/sybermem-init-project`

### Step 2: project identity 检查

#### 情况 A：已有 `project.yaml`
- 继续

#### 情况 B：缺少 `project.yaml`
- 自动补齐，无需单独确认
- 因为这属于低风险前置

### Step 3: Team 关联检查

#### 情况 A：`project.yaml.team.team_path` 已存在
- 继续

#### 情况 B：没有 Team 关联

##### B1. 用户显式提供了 `--team-path`
- 使用该路径
- 成功 publish 后自动写回 `project.yaml`

##### B2. 用户未提供
- 提示：

```text
No Team association found for this project.
Choose an existing Team repo path or initialize a new Team repo.
```

### Step 4: Team repo 可用性检查

#### 情况 A：路径存在且是有效 Team repo
- 继续

#### 情况 B：路径不存在
- 不直接失败
- 提示：

```text
Team repo path does not exist.
Initialize a new Team repo here? [yes/no]
```

如果用户确认：
- 触发等价于 `sybermem team init`

#### 情况 C：路径存在但不是有效 Team repo
- 停止并提示路径冲突
- 不自动覆盖

### Step 5: digest / readiness 检查

沿用已确认的规则：
- 至少 2 条 record
- 或 1 条 decision
- 或 1 个 completed phase

#### 有 digest
- 直接用

#### 无 digest 但内容足够
- 自动补 phase digest

#### 内容不足
- 停止 publish，并提示原因

---

## 6. Automatic vs Confirmed Actions

### 自动补齐（低风险）
- `project.yaml`
- Hub registry entry
- Team association write-back
- digest / status 这类可重建内容前置

### 需要确认（高影响）
- 创建新的 Team repo
- 首次推送到远程 Git
- 覆盖或替换错误 Team 关联 / remote

---

## 7. Command Shape

### 保留的唯一命令

```bash
sybermem publish status
sybermem publish status --team-path D:/team-memory
sybermem publish status --format json
```

### 不新增
- `sybermem team push`
- `sybermem publish bootstrap`
- `sybermem publish ensure`

原因：避免重复能力和心智分裂。

---

## 8. Why This Matters

这样做之后：
- 用户只需要记住一个目标导向动作：`publish`
- 系统负责吸收步骤复杂度
- Team 能力仍然保持可控，不会过度自动化到不可理解

这意味着 SyberMem 会从：

```text
一组功能能力
```

变成：

```text
一个真正的目标导向工作流入口
```

---

## 9. Out of Scope

本轮明确不做：
- 新增 `team push` 命令
- 完整交互式 Team onboarding wizard
- 自动选择多个 Team 仓库
- lesson/review/search 新能力

---

## 10. Success Criteria

1. 用户只需要记住 `sybermem publish status`
2. 缺失的低风险前置能自动补齐
3. 高影响动作会在执行前要求确认
4. publish 的提示围绕“完成 Team 发布”这个目标来组织
5. 不新增和 `publish` 重复语义的新命令
