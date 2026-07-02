# SyberMem Team Digest History Publication Layer 设计

> 让 Team repo 不只是当前状态和摘要入口，还保留完整的 phase/theme digest 历史：概括看 status，详细看 digest。

**Date:** 2026-07-02
**Status:** Draft
**Scope:** 为 Team repo 增加完整的 phase digest / theme digest 历史同步层；不同步 raw records，不同步 decision/requirement 全历史。
**Parent specs:**
- `docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseB-design.md`
- `docs/superpowers/specs/2026-07-02-sybermem-team-project-summary-refactor-design.md`
- `docs/superpowers/specs/2026-07-02-sybermem-team-agent-consumption-layer-phaseE-design.md`

---

## 1. Background & Problem

当前 Team repo 已经有：
- `project.md`
- `current-status.md`
- `meta.json`
- `dashboards/current-overview.md`
- `dashboards/latest-management-summary.*`

这已经足够提供：
- 当前状态总览
- 管理 agent 的低成本消费层

但仍有一个核心不足：

> 当 `current-status.md` / `latest-management-summary.*` 信息不够时，Team repo 里没有完整的高质量原文可下钻。

如果不把 digest 原文同步到 Team repo，就会出现：
- 只靠 status 看不够细
- 需要再回到各项目 repo 去找 digest 或 raw records
- Team repo 失去“统一工程记忆入口”的意义

因此，Team repo 需要从“当前状态入口”升级为：

> **当前状态 + 完整摘要历史** 的团队工程记忆库。

---

## 2. Design Goal

让 Team repo 同时具备两层能力：

### 当前视图层
- `project.md`
- `current-status.md`
- `meta.json`
- `dashboards/current-overview.md`
- `dashboards/latest-management-summary.*`

### 历史摘要层
- 完整 **phase digest** 历史
- 完整 **theme digest** 历史

使用方式：

```text
概括看 overview / management summary / current-status
详细看 phase-digests / theme-digests
```

---

## 3. Design Choice

### 不选：只同步 latest digest
优点：目录简单，默认更轻。
缺点：只能看到最后结果，缺少阶段演化和历史沉淀，难以支撑深层经验提取与规范总结。

### 不选：同步 raw records / decisions / requirements 全历史
优点：信息最完整。
缺点：Team repo 会迅速膨胀成各项目原始记录镜像，噪音和治理复杂度太高。

### 选择：同步完整 phase digest + theme digest 历史
优点：
- 保留足够的高质量沉淀原文
- 仍然保持 Team repo 以“摘要层”为主，不引入 raw record 镜像
- 非常适合管理 agent 的深读升级路径

---

## 4. Team Repo Structure Upgrade

每个项目目录升级为：

```text
projects/<slug>/
├── project.md
├── current-status.md
├── meta.json
├── phase-digests/
│   ├── 2026-06-29-003-platform-ecosystem-and-plugin-packaging-phase.md
│   └── ...
└── theme-digests/
    ├── 2026-06-22-001-hooks.md
    └── ...
```

### 映射关系

本地项目：

```text
.sybermem/digests/
.sybermem/theme-digests/
```

映射到 Team repo：

```text
projects/<slug>/phase-digests/
projects/<slug>/theme-digests/
```

一对一复制，保留原文件名。

---

## 5. Synchronization Strategy

### 关键原则

> **全量集合、增量同步、幂等覆盖、第一版不自动删除**

### 5.1 对 phase digests
- Team 目标文件不存在 → 复制
- Team 目标文件存在但内容不同 → 覆盖更新
- Team 目标文件存在且内容相同 → 跳过

### 5.2 对 theme digests
- 规则同上

### 5.3 为什么不用全量重写
- 成本更高
- git diff 噪音更大
- 每次 publish 变慢

所以正确策略不是“每次把所有历史重写一遍”，而是：
- Team repo 最终拥有完整 digest 历史
- 每次 publish 只同步新增或变化的 digest 文件

---

## 6. Deletion Policy

### 第一版：**不自动删除**

即：
- 本地新增 digest → 同步过去
- 本地同名 digest 修改 → 覆盖更新
- Team repo 里已有但本地删除了 → 暂不自动删除

### 为什么
- digest 是沉淀物，不是构建产物
- 自动删除团队知识风险过高
- 先保守保留，再考虑后续 prune/archive 机制

---

## 7. `meta.json` Upgrade

当前 `meta.json` 只有：
- `source_phase_digest`
- `source_theme_digest`

升级后建议增加：

```json
{
  "project_id": "prj_01J6SYBERMEM0001",
  "slug": "sybermem",
  "published_at": "2026-07-02T10:00:00+08:00",
  "source_commit": "20d1cc4",
  "latest_phase_digest": "projects/sybermem/phase-digests/2026-06-29-003-platform-ecosystem-and-plugin-packaging-phase.md",
  "latest_theme_digest": "projects/sybermem/theme-digests/2026-06-22-001-hooks.md",
  "phase_digest_count": 3,
  "theme_digest_count": 1
}
```

### 作用
- 让 agent 不读完整目录也能知道摘要历史是否丰富
- 给 management summary / worth deeper review 更低成本的信号来源

---

## 8. Publish Pipeline Integration

Digest 历史同步不是单独命令，而是并入现有 `publish status`：

```text
publish status
  → 检查/补 digest
  → 生成 project.md / current-status.md / meta.json
  → 同步 phase-digests / theme-digests（增量）
  → rebuild current-overview
  → commit + push
```

### 为什么
用户前面已经确认：
- 希望只记住一个入口：`publish`

所以 digest 历史同步应属于统一的 Team publication pipeline，而不是另起一个新动作。

---

## 9. Consumption Impact

加入完整 digest 历史后，Team repo 消费方式变成 4 层：

### Layer 0: Team 总览入口
- `dashboards/current-overview.md`

### Layer 1: 管理消费层
- `dashboards/latest-management-summary.*`

### Layer 2: 单项目摘要
- `projects/<slug>/current-status.md`
- `projects/<slug>/meta.json`

### Layer 3: 完整 digest 历史
- `projects/<slug>/phase-digests/`
- `projects/<slug>/theme-digests/`

这正好满足：

```text
概括看 status
详细看 digest
```

---

## 10. Experience / Efficiency / Economy

### 体验
- 打开 Team repo 时先看 overview 和 summary
- 不够时直接在同一个 Team repo 下钻 digest 原文
- 不需要再回各项目 repo 深读

### 效率
- 默认消费仍然轻（overview / summary / current-status）
- 只有在 Worth Deeper Review 或主动点名项目时才读 digest 原文

### 经济性
- 比“没有 digest，只能回源读 raw records”更便宜
- 因为 Team repo 已经持有高质量摘要原文
- 但默认读取路径仍然不会每次全量读所有 digest

---

## 11. Out of Scope

本轮明确不做：
- raw records 全量同步
- decisions/requirements 全历史同步
- digest 自动删除 / archive
- digest review workflow
- team search 重构

---

## 12. Success Criteria

1. Team repo 中每个项目目录新增：
   - `phase-digests/`
   - `theme-digests/`
2. `publish status` 能增量同步完整 phase/theme digest 历史
3. 已同步文件内容相同则跳过，不制造无意义 diff
4. `meta.json` 能表达最新 digest 路径与历史计数
5. 管理视角可以：
   - 概括看 overview / summary / current-status
   - 详细看 digest 原文
