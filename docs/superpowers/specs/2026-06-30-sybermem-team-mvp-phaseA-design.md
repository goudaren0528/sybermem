# SyberMem Team MVP Phase A 设计

> 构建团队统一存储的第一刀：一个带远程 Git 绑定的 Team 仓库骨架，为后续 `publish status` / `team sync` 铺路。

**Date:** 2026-06-30
**Status:** Draft
**Scope:** Requirement-003 / Team MVP Phase A。只做 `team.yaml`、`sybermem team init`、Team Git 仓库目录结构。不做 publish / sync / review / lessons 行为。
**Parent spec:** `docs/superpowers/specs/2026-06-29-sybermem-cross-project-and-team-memory-spec.md`

---

## 1. Background & Problem

当前 Requirement-003 的执行顺序已经被正式调整：

```text
Hub MVP
  → Team MVP
  → Promote / Personal Lesson / richer Hub polish
```

也就是说，下一步最有价值的事情不是继续打磨个人 Hub，而是让**多个项目的工程化记忆能够汇总到一个团队存储里统一管理**。

要实现这一点，第一步不是上来就做发布、审核、搜索，而是先建立一个**稳定、可复用、带远程 Git 绑定的 Team 仓库骨架**。

Phase A 的作用是：
- 生成 Team identity
- 生成 Team Git repo 目录结构
- 把 Team 与远程仓库绑定
- 为后续 `publish status` / `team sync` 留好路径

---

## 2. Design Goal

让用户能运行：

```bash
sybermem team init \
  --path D:/team-memory \
  --team-id team_rental_platform \
  --name "Rental Platform" \
  --remote https://github.com/example/sybermem-team.git
```

并得到一个**可作为团队统一存储根目录**的本地 Git 仓库骨架。

---

## 3. Design Choice

采用：**本地目录骨架 + 远程 Git 绑定**。

### 不选择的方案

#### 方案 1：只建本地目录，不管 remote
缺点：还不是“真正的团队统一存储”，团队协作价值太弱。

#### 方案 2：自动 clone 远程仓库
缺点：需要处理空仓库/非空仓库/已有目录冲突，Phase A scope 过大。

### 选择的方案

#### 方案 3：新建本地骨架 + 配置 remote（推荐）

- `--remote` 必填
- 新目录时执行 `git init` + `git remote add origin`
- 已有 git repo 时校验 origin
- 不自动 clone，不自动 push，不自动创建远程仓库

这样：
- 第一步就是真正的 Team 存储
- 但复杂度仍可控

---

## 4. Command Design

### CLI 形态

```bash
sybermem team init \
  --path D:/team-memory \
  --team-id team_rental_platform \
  --name "Rental Platform" \
  --remote https://github.com/example/sybermem-team.git
```

### 参数

| 参数 | 含义 | 必填 |
|------|------|------|
| `--path` | 本地 team repo 目录 | 是 |
| `--team-id` | 稳定 team identity | 是 |
| `--name` | 显示名称 | 是 |
| `--remote` | 远程 Git URL | 是 |
| `--format` | `text` / `json` | 否 |

---

## 5. Team Repo 结构

初始化完成后：

```text
D:/team-memory/
├── .git/
├── team.yaml
├── projects/
├── lessons/
│   ├── candidates/
│   ├── accepted/
│   ├── rejected/
│   └── deprecated/
├── standards/
├── architecture/
├── publications/
└── dashboards/
```

### 目录意义

| 目录 | 作用 |
|------|------|
| `projects/` | 未来 `publish status` / `project.md` / `current-status.md` 的存储位置 |
| `lessons/` | 未来 Team Lesson 生命周期目录（先建骨架） |
| `standards/` | 未来团队正式规范 |
| `architecture/` | 未来团队级架构决策 |
| `publications/` | 未来 publish manifest |
| `dashboards/` | 未来团队聚合视图 |

### 为什么现在就建这些目录

因为目录骨架一旦稳定，后续 `publish` / `review` / `sync` 就不需要再改 Team 仓库根结构。Phase A 的目标就是把这个根结构定下来。

---

## 6. `team.yaml`

### 文件位置

```text
<team-repo>/team.yaml
```

### 内容

```yaml
schema_version: 1
team_id: team_rental_platform
name: Rental Platform
repository:
  remote: https://github.com/example/sybermem-team.git
created_at: 2026-06-30T10:00:00+08:00
```

### 规则

- `team_id` 一旦指定后不可变
- `remote` 必填
- `created_at` 由 CLI 写入
- 不自动写入成员列表（后续 Phase B/C 再考虑）

---

## 7. Git Behavior

### 7.1 路径不存在

如果 `--path` 不存在：
1. 创建目录
2. `git init`
3. `git remote add origin <remote>`
4. 写 `team.yaml`
5. 创建目录骨架

### 7.2 路径存在但不是 Git 仓库

- 报错并停止
- 原因：不能假设用户希望把现有普通目录变成 Team repo

### 7.3 路径存在且是 Git 仓库

- 如果没有 `origin` → `git remote add origin <remote>`
- 如果已有 `origin` 且一致 → 继续
- 如果已有 `origin` 且不一致 → 报错并提示冲突

### 7.4 Phase A 明确不做

- 不自动 `git clone`
- 不自动 `git pull`
- 不自动 `git push`
- 不自动创建初始 commit
- 不自动创建远程 Git 仓库

理由：保持最小可用，把 Git 远程的创建和推送权交给用户。

---

## 8. Output Design

### Text

```text
Initialized team repo:
- team_id: team_rental_platform
- name: Rental Platform
- path: D:/team-memory
- remote: https://github.com/example/sybermem-team.git
```

### JSON

```json
{
  "status": "created",
  "team_id": "team_rental_platform",
  "name": "Rental Platform",
  "path": "D:/team-memory",
  "remote": "https://github.com/example/sybermem-team.git"
}
```

### 幂等情况

如果 team repo 已存在且 remote 一致：

```json
{
  "status": "existing",
  "team_id": "team_rental_platform",
  "name": "Rental Platform",
  "path": "D:/team-memory",
  "remote": "https://github.com/example/sybermem-team.git"
}
```

---

## 9. File Manifest

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `packages/core/sybermem_core/team.py` | Team repo init 逻辑 |
| 修改 | `packages/cli/sybermem_cli/main.py` | 增加 `team init` 命令 |
| 新增 | `schemas/team.yaml.example` | Team schema 示例 |

---

## 10. Backward Compatibility

- 当前所有 Project / Hub 能力不受影响
- 不修改 `projects.yaml`
- 不修改现有 `.sybermem/` 项目结构
- 不影响 `sybermem search` / `project status` / `portfolio`

---

## 11. Out of Scope

Phase A 明确不做：
- `publish status`
- `team sync`
- `team review`
- Team search
- Lessons/Standards/Architecture 的写入逻辑
- 成员权限 / RBAC
- 自动 clone / push / PR

---

## 12. Success Criteria

1. `sybermem team init ...` 能创建一个可用的 Team Git 仓库骨架
2. `team.yaml` 正确生成
3. `origin` remote 正确绑定
4. 已有 repo + 正确 remote 时可幂等运行
5. 已有 repo + 错误 remote 时会报错而不是静默覆盖
6. 这一步完成后，后续 `publish status` 只需要往 `projects/<slug>/` 写文件即可
