**中文** | [English](README.en.md)

# SyberMem

SyberMem 是面向 AI 编程工作流的项目 / 团队工程记忆系统。它把一次工作的背景、决策、原因和阶段结论沉淀为本地 Markdown，让下一次会话不必从零重建上下文。

## 为什么需要它

AI agent 很擅长在当前窗口里推进工作，但跨会话后容易丢掉三个关键信号：

- 之前为什么这么设计
- 哪些问题已经踩过或修过
- 当前项目最安全的下一步是什么

SyberMem 用结构化 records、可派生索引、阶段 / 主题 digest 和只读续接视图保存这些信号。数据保存在项目本地的 `.sybermem/` 目录中，人和 AI 都能直接审阅，不是黑盒服务。

## 快速开始

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

安装后进入目标项目：

```text
/sybermem-init-project
/sybermem-record
/sybermem-resume
```

典型节奏是：初始化项目，完成一轮有价值的工作后记录它，下次打开项目先用 `/sybermem-resume` 获取当前阶段、最近进展、风险、建议下一步、置信度和信息新鲜度。

## 一条记忆长什么样

`/sybermem-record` 会在 `.sybermem/changes/`、`.sybermem/decisions/`、`.sybermem/requirements/` 或 `.sybermem/bugs/` 下写入 Markdown record：

```markdown
---
type: change
record_id: change-6a3ab8a0e44e4c41843b66bde8b7134a
date: 2026-08-07
title: UUID-backed record IDs and derived project index
key_conclusion: 采用 UUID record_id 和派生 INDEX，让并行记录安全合并
topics: [architecture, collaboration, quality]
implements: [requirement-002]
---

## Change Content
...

## Reason
...

## Impact Scope
...
```

`.sybermem/INDEX.md` 由 canonical records 派生重建，用作导航和会话启动的关键结论层。真正的长期压缩层是 phase digest 和 theme digest。

## 当前能力

### Project memory

- 结构化 records：`change` / `decision` / `requirement` / `bug`
- UUID-backed `record_id`，并兼容旧 numeric record ID
- 从 canonical records 派生的 `.sybermem/INDEX.md`
- phase digest 与 theme digest，用于阶段和主题级压缩
- record 关系：`implements` / `fixes` / `related` / `superseded_by`
- 只读续接：`/sybermem-resume` 与 `sybermem resume`
- 项目内检索：`/sybermem-search` 与 `sybermem search`
- 下一步建议：`/using-sybermem` 与 `sybermem next-step`

### Workspace / Hub

- project registry
- workspace SQLite FTS5 搜索索引：`sybermem index build`
- workspace search 支持项目、类型和状态过滤
- index 缺失、schema 过期或 stale 时给出恢复提示
- portfolio 视图：`sybermem portfolio`

### Team memory

- Team repo 初始化：`sybermem team init`
- 发布前只读 preview：`sybermem publish status --preview`
- 使用 preview hash 发布，避免基于过期预览写入
- Team overview 自动更新
- Team management summary：`sybermem team summary`
- phase / theme digest 历史同步到 Team repo
- 对应 skill：`/sybermem-team-publish`、`/sybermem-team-summary`

## CLI 与 Skill 的边界

SyberMem 有两类执行路径，可靠性不同：

| 路径 | 代表能力 | 说明 |
|---|---|---|
| CLI / Core | `sybermem resume`、`search`、`next-step`、`portfolio`、`index build`、`project index build/check`、`record id`、`team init/summary`、`publish status`、`project uninstall` | 程序执行，可脚本化，适合确定性查询和发布流程 |
| Skill 编排 | `/sybermem-record`、`/sybermem-link`、`/sybermem-digest`、`/sybermem-theme-digest`、`/sybermem-phase-analyze`、`/sybermem-phase-confirm` | 由 AI 按 skill 指令编辑 `.sybermem/` Markdown，适合需要判断和整理的工作 |

`sybermem record id --type <change|decision|requirement|bug>` 只生成 canonical record ID；完整 record 创建仍通过 `/sybermem-record` 完成。

## 平台支持

| 平台 | 支持级别 | 说明 |
|---|---|---|
| Claude Code | 完整集成 | plugin metadata、skills、SessionStart / Stop / UserPromptSubmit hooks |
| OpenCode | 支持集成 | skills + TypeScript plugin；session lifecycle 与 compaction 承接 |

OpenCode 目前没有已文档化的逐次用户提示词自动注入回调。SyberMem 不会在 OpenCode 上声明隐藏 auto-resume、后台执行或不受支持的 prompt-time injection；OpenCode 上的 `/sybermem-resume` 和 `/sybermem-search` 是手动入口，自动承接主要依赖受支持的 compaction 生命周期。更多说明见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md)。

## 安装与升级

### 一行式安装

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

这会刷新用户级 Claude Code skills、OpenCode skills、OpenCode plugin，以及 CLI / Core runtime。

### 本地插件验证

```bash
claude --plugin-dir .
```

适合在仓库 checkout 中直接验证 Claude Code 插件、hooks 和 skills。

### 升级顺序

1. 先重新运行全局安装 / 更新命令。
2. 再进入已有项目运行 `/sybermem-update`。
3. 新项目运行 `/sybermem-init-project`。

全局刷新只更新用户级 runtime 和 skills；项目内的 `.sybermem/`、hooks、模板和说明文件需要 `/sybermem-update` 才会刷新。

## 初始化项目

在目标项目中运行：

```text
/sybermem-init-project
```

它会创建或刷新：

- `.sybermem/`
- `.sybermem/digests/`
- `.sybermem/theme-digests/`
- `.sybermem/analysis/phase-index.md`
- `.sybermem/project.yaml`
- `.sybermem/hooks/`
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json`

如果项目已有自定义 `.claude/settings.json`，SyberMem 只会补丁可识别的受管项，不覆盖无关 hooks、env 或说明。

## 日常使用

### 项目 owner

- `/sybermem-resume`：获取只读续接视图
- `/sybermem-record`：记录一轮有价值的工作
- `/sybermem-search`：查找历史 records
- `/sybermem-summary`：查看当前项目状态
- `/sybermem-digest`：沉淀稳定阶段结论
- `/sybermem-theme-digest`：沉淀跨阶段主题结论
- `/sybermem-team-publish`：preview、review 后发布到 Team memory

### 管理者 / 管理 agent

- `/sybermem-team-summary`：生成 Team 管理摘要
- 阅读 Team repo 中的 `dashboards/current-overview.md` 和 `latest-management-summary.md`

### 不确定下一步时

- `/sybermem-resume`：先恢复当前上下文
- `/using-sybermem`：检查当前状态并获得推荐命令
- `sybermem next-step`：用 CLI 获取下一步建议

## 索引与检索

- `.sybermem/INDEX.md` 是项目内派生导航文件，由 `sybermem project index build` 重建，由 `sybermem project index check` 校验。
- `sybermem index build` 构建 workspace 级 SQLite FTS5 索引，服务于跨项目搜索。
- 项目内检索默认基于已解析 Markdown records 的词法匹配和打分；需要跨项目搜索时使用 workspace index。
- 可选的 `SYBERMEM_SEMANTIC_RECALL=1` 会启用本地 char n-gram 召回补充，用于显式检索，不会自动注入每轮提示。

## Team workflow

推荐路径：

1. 在项目内持续 record / digest
2. 用 `/sybermem-team-publish` 或 `sybermem publish status --preview --format json` 生成只读 preview
3. review source revision、source hash、freshness、conflicts 和 review-required 状态
4. 使用 preview hash 发布
5. Team overview 自动更新
6. 用 `/sybermem-team-summary` 或 `sybermem team summary` 生成管理摘要
7. 需要细节时下钻到完整 digest 历史

## 仓库结构

```text
.claude-plugin/                      # Claude Code 插件元数据与 marketplace 清单
hooks/                               # Claude Code hook 声明与 delegator
skills/                              # Plugin-facing skills tree
packages/claude-skills/              # Skills 分发源
packages/core/                       # Core memory / Team publication logic
packages/cli/                        # sybermem CLI
packages/opencode-plugin/            # OpenCode plugin
scripts/                             # 安装、更新、卸载与打包校验脚本
```

## 卸载

### 项目级卸载

```text
sybermem project uninstall
```

它会停用项目内 SyberMem runtime 接管，但保留 `.sybermem/` 历史内容，并尽量只移除受管 hook / env / instruction block。

### 全局卸载

```bash
# Windows (PowerShell)
.\scripts\uninstall.ps1

# macOS / Linux
./scripts/uninstall.sh
```

全局卸载会移除用户级 skills、CLI、launcher 和 OpenCode plugin，不删除任何项目里的 `.sybermem/` 历史。

## 兼容说明

- `.sybermem/` 是当前规范目录。
- 如果项目仍使用旧 `ADR/`，首次运行相关 SyberMem workflow 时会迁移到 `.sybermem/`。
- Claude 的 prompt-time recall 只适用于受管 Claude hooks；OpenCode 不声明同类逐次注入。
- 更多安装、升级和兼容细节见 [INSTALL.md](INSTALL.md)。

## License

MIT
