# SyberMem Team MVP Phase B 设计

> 在 Team Phase A 的仓库骨架之上，先发布最小可用的团队项目状态：`project.md` + `current-status.md`。

**Date:** 2026-07-01
**Status:** Draft
**Scope:** Requirement-003 / Team MVP Phase B。只做 `publish status`，不做 digest/lesson/review/search/sync/history。
**Parent spec:** `docs/superpowers/specs/2026-06-30-sybermem-team-mvp-phaseA-design.md`

---

## 1. Background & Problem

Phase A 已经交付了 Team repo 的基础：
- `team.yaml`
- Team Git 仓库目录骨架
- `sybermem team init`
- 远程 Git 绑定

但此时 Team repo 还只是一个空壳。它虽然已经是“团队统一存储”的容器，但没有任何实际内容，因此还不能让团队成员回答：

- 这个项目是什么？
- 它现在进行到哪里？
- 最近有什么变化？
- 有什么待处理事项？

如果 Phase B 一上来就发布 raw records / digests / lessons，就会立即引入隐私、审核、重复和共享边界问题。对 MVP 而言，这太重。

因此，Phase B 的目标必须收敛为：

> **先把每个项目的“身份卡片 + 当前状态快照”发布到 Team repo。**

---

## 2. Design Goal

新增一个最小命令：

```bash
sybermem publish status --team-path D:/team-memory
```

它把当前项目的最小状态发布到：

```text
<team-repo>/projects/<slug>/
├── project.md
└── current-status.md
```

这一步完成后，多个项目就能第一次真正汇总到 Team repo 中统一管理。

---

## 3. Design Choice

### 为什么发布 `project.md` + `current-status.md`

#### 不选：只发布 `current-status.md`
缺点：只有状态，没有项目身份卡片；以后团队仓库里目录一多，缺少稳定的项目入口页。

#### 不选：再加 digest 摘要
缺点：立刻碰到“哪些 digest 能共享”“要不要脱敏”“是否需要审核”等问题，会把 Phase B scope 拉大。

#### 选择：`project.md` + `current-status.md`
优点：
- `project.md` 负责“这个项目是谁”
- `current-status.md` 负责“它现在怎么样”
- 两个文件就能形成 Team repo 的最小项目入口

---

## 4. Command Design

### 命令

```bash
sybermem publish status --team-path D:/team-memory
sybermem publish status --team-path D:/team-memory --format json
```

### 行为流程

1. 解析当前 project root
2. 读取 `.sybermem/project.yaml`
3. 调用现有 `sybermem project status --format json`
4. 读取 Team repo 的 `team.yaml`
5. 校验 Team repo 结构存在
6. 在 `projects/<slug>/` 下写入/更新：
   - `project.md`
   - `current-status.md`
7. 输出结果

### Phase B 明确不做

- 不自动 commit
- 不自动 push
- 不生成 `status-history/`
- 不批量发布多个项目
- 不发布 digests / lessons / decisions / records

---

## 5. Published Artifacts

### 5.1 `project.md`

稳定、低频变化的项目身份卡片。

```markdown
# sybermem

- Project ID: prj_01J6SYBERMEM0001
- Slug: sybermem
- Name: sybermem
- Repository: https://github.com/goudaren0528/sybermem
- Team: team_rental_platform
- Registered at: 2026-06-29T18:00:00+08:00
```

### 5.2 `current-status.md`

高频覆盖更新的状态快照。

```markdown
# sybermem — Current Status

- Updated at: 2026-07-01T10:00:00+08:00
- Source commit: 20d1cc4

## Active Phase
- phase-010 — Search, relations, and theme digest

## Recent Records
- change-010
- decision-001

## Open Bugs
- none

## Open Requirements
- requirement-003

## Next
- continue Team MVP Phase B
```

### 为什么不带更多内容

第一版的目标是“统一管理项目状态”，不是“团队知识全量发布”。所以：
- 只带当前最重要的可共享状态信息
- 不带完整 record 正文
- 不带 digest 正文
- 不带私人推测或 lesson 提炼

---

## 6. Team Repo Structure After Phase B

Phase A 结束时：

```text
team.yaml
projects/
lessons/
standards/
architecture/
publications/
dashboards/
```

Phase B 之后，第一个真实业务内容出现：

```text
projects/
└── sybermem/
    ├── project.md
    └── current-status.md
```

当第二个项目（如 teamspark）发布状态后：

```text
projects/
├── sybermem/
│   ├── project.md
│   └── current-status.md
└── teamspark/
    ├── project.md
    └── current-status.md
```

这时 Team repo 已经具备统一管理多个项目状态的最小可用形态。

---

## 7. Output Design

### JSON 输出

```json
{
  "status": "published",
  "team_id": "team_rental_platform",
  "project_id": "prj_01J6SYBERMEM0001",
  "slug": "sybermem",
  "team_path": "D:/team-memory",
  "files": [
    "D:/team-memory/projects/sybermem/project.md",
    "D:/team-memory/projects/sybermem/current-status.md"
  ]
}
```

### Text 输出

```text
Published project status to Team repo:
- team: team_rental_platform
- project: sybermem
- files:
  - projects/sybermem/project.md
  - projects/sybermem/current-status.md
```

---

## 8. File Manifest

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `packages/core/sybermem_core/publish.py` | status publication core logic |
| 修改 | `packages/cli/sybermem_cli/main.py` | 新增 `publish status` 命令 |
| 可选修改 | `packages/core/sybermem_core/team.py` | 如果需要复用 team repo 读取逻辑 |

---

## 9. Backward Compatibility

- 不影响 Project / Hub 现有命令
- 不修改项目 `.sybermem/` 内容
- Team repo 仍然不需要自动 push
- 没有 Team repo 的用户不会受影响

---

## 10. Out of Scope

Phase B 明确不做：
- `status-history/`
- `sybermem team sync`
- `sybermem team review`
- `publish digest`
- `publish lesson`
- Team search
- 审核状态流
- 访问控制

这些留到后续 Team Phase C / D。

---

## 11. Success Criteria

1. `sybermem publish status --team-path <path>` 可以运行
2. Team repo 中创建 `projects/<slug>/project.md`
3. Team repo 中创建 `projects/<slug>/current-status.md`
4. 同一个项目重复发布是幂等的（覆盖更新，不重复创建）
5. 多个项目发布后，`projects/` 目录成为真正的团队统一状态入口
