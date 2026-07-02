# SyberMem Team MVP Phase D — Onboarding Polish 设计

> 让 Team 初始化和发布流程更顺滑：引导远程仓库、自动首次提交/推送、项目持久记住 Team 关联、init-project 感知 Team。

**Date:** 2026-07-02
**Status:** Draft
**Scope:** Requirement-003 / Team MVP Phase D。修复 team init 首次推送、project.yaml 增加 team 字段、publish 自动读默认 team、init-project/health-check 感知 Team。
**Parent spec:** `docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseC-design.md`

---

## 1. Background & Problem

Phase A/B/C 已经让 Team MVP 的核心链路跑通：

```text
team init → publish status → auto-overview → auto-commit → auto-push
```

但在实际使用中暴露了 5 个摩擦点：

1. `team init` 后默认分支是 `master`，首次 push 到 GitHub 会失败
2. `team init` 没有做 initial commit，导致首次 push 需要额外手动操作
3. `project.yaml` 不记得项目属于哪个 Team，每次 `publish status` 都要手动传 `--team-path`
4. `sybermem-init-project` skill 和 `check_project_health.py` 对 Team 完全无感知，初始化完项目后不知道还有 Team 功能
5. `publish status` 不能自动从项目配置读取默认 Team 路径

---

## 2. Design Goals

### D.1 `team init` 改进
- `git init` 后立刻 `git branch -M main`
- 创建完骨架后做一次 initial commit
- 尝试 `git push -u origin main`（失败则提示检查远程仓库）

### D.2 `project.yaml` 增加 `team` 字段
新增可选的 `team` 区块：

```yaml
schema_version: 1
project_id: prj_01J6SYBERMEM0001
slug: sybermem
team:
  team_id: team_rental_platform
  team_path: D:/team-memory
```

写入时机：
- `publish status` 第一次成功发布后，自动回写 `project.yaml` 的 `team` 字段
- 不在 `team init` 时写入（因为 team init 在 Team repo 目录操作，不在项目目录）

### D.3 `publish status` 支持从 `project.yaml` 读默认 team
- 如果 `--team-path` 未指定，尝试从当前项目 `project.yaml` 的 `team.team_path` 读取
- 如果 `--team-path` 显式指定，使用它（并更新 `project.yaml` 的 `team` 字段）
- 如果两者都没有，报错并提示用户

### D.4 `sybermem-init-project` 在 "Next steps" 中感知 Team
- 如果项目 `project.yaml` 有 `team` 字段 → 提示可以 `sybermem publish status`
- 如果没有 → 提示可以用 `sybermem team init` 创建团队仓库，或在首次 publish 时关联

### D.5 `check_project_health.py` 增加 Team 状态
新增 `team` 区块：

```json
"team": {
  "has_team_link": true,
  "team_path": "D:/team-memory",
  "team_path_accessible": true
}
```

不影响 `overall` 判定（Team 关联不是项目健康的硬性前提），只作为信息区块。

---

## 3. Backward Compatibility

- `project.yaml` 的 `team` 字段是可选的，不影响现有项目
- `publish status --team-path` 仍然可用，显式参数优先
- `check_project_health.py` 新增 `team` 区块不影响 `overall` 判定
- 不修改 Team repo 的结构

---

## 4. File Manifest

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `packages/core/sybermem_core/team.py` | team init 加 branch -M main + initial commit + push |
| 修改 | `packages/core/sybermem_core/publish.py` | publish 支持从 project.yaml 读默认 team；成功后回写 team 字段 |
| 修改 | `packages/core/sybermem_core/identity.py` | render_project_yaml 支持可选 team 字段 |
| 修改 | `packages/core/sybermem_core/project.py` | parse project.yaml team 字段 |
| 修改 | `packages/cli/sybermem_cli/main.py` | publish status 的 --team-path 变为可选 |
| 修改 | `.sybermem/hooks/check_project_health.py` | 增加 team 检查区块 |

---

## 5. Out of Scope

- Team join / clone 流程（后续再考虑）
- sybermem-init-project skill 的完整 Team 引导交互（本轮只改 "Next steps" 文本建议）
- project.yaml team 字段的自动清理（如果 Team repo 被删除）

---

## 6. Success Criteria

1. `sybermem team init` 创建后可以直接 `git push -u origin main` 成功（远程仓库可达时）
2. `sybermem publish status` 第一次成功后，`project.yaml` 自动记住 team 关联
3. 第二次及以后 `sybermem publish status` 不再需要 `--team-path`
4. `check_project_health.py` 输出包含 `team` 区块
5. 已有项目的 `project.yaml` 不受影响（team 字段可选）
