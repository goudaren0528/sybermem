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
- 记忆统计：`sybermem project memory-stats` 默认打印最近 7 天 / 30 天的终端表格（含召回精准度列），`--format json` 输出结构化统计供 `/sybermem-summary` 使用
- 召回相关性反馈：OpenCode 通过 `file.edited` / `todo.updated` / `tool.execute.after` 累积每轮编辑焦点、任务完成与测试/构建信号，`session.idle` 据此把召回注入过的记录与实际编辑的文件（按记录的 `related_files`）比对，写入有界 `.sybermem/.recall-outcomes.jsonl`，得出频率之外的 `low_relevance`（精准度）判定；record 提醒也据此带上语义化触发原因
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

### User Habit Memory

- 用户级习惯存储：`~/.sybermem/user-habits/`，或测试/自定义环境中的 `SYBERMEM_HOME/user-habits/`
- 显式记录：`sybermem habit add --type workflow --applies-to planning "Prefer plans before implementation"`
- 查看与治理：`sybermem habit list`、`search`、`pause`、`delete`
- 可见提醒：`sybermem habit remind --context planning --format markdown` 与 `/sybermem-habit`
- 手动/compaction 注入：`sybermem habit inject --context planning --format markdown`
- 被动候选捕获（仅候选，永不自动写入）：OpenCode `chat.message` 检测到"以后都…/我习惯…"这类可复用偏好时，调用 `sybermem habit intent --prompt <text>` 把候选写入用户级 `~/.sybermem/.habit-intent.json`（绝不创建 active habit，绝不持久化密钥/注入文本）；`/sybermem-habit` 读取 `habit intent-status` 后经用户确认一键转为 habit，再 `habit intent-clear` 清除
- 独立醒目的注入提示：OpenCode 里 recall 与 habit 各弹独立 toast——recall 用 `⭐`，应用的用户习惯用单独的 `🧠`（不再混在一条里），捕获到候选偏好时弹 `💡`
- 感知层：`sybermem habit awareness` 及 OpenCode 首轮 startup context 展示 active 习惯数量、类型分布与是否有待确认候选（只报数量，不暴露 habit 内容，也不与逐 prompt 提醒重复）
- 保守门槛：只注入 active、高置信、未被排除、与上下文直接相关的习惯，最多 3 条
- 默认不进入项目 `.sybermem/` records，也不发布到 Team memory

## CLI 与 Skill 的边界

SyberMem 有两类执行路径，可靠性不同：

| 路径 | 代表能力 | 说明 |
|---|---|---|
| CLI / Core | `sybermem resume`、`search`、`next-step`、`portfolio`、`index build`、`project index build/check`、`project memory-stats`、`record id`、`habit add/list/search/pause/delete/remind/inject`、`team init/summary`、`publish status`、`project uninstall` | 程序执行，可脚本化，适合确定性查询和发布流程 |
| Skill 编排 | `/sybermem-record`、`/sybermem-habit`、`/sybermem-link`、`/sybermem-digest`、`/sybermem-theme-digest`、`/sybermem-phase-analyze`、`/sybermem-phase-confirm` | 由 AI 按 skill 指令编辑 `.sybermem/` Markdown 或调用用户级 habit CLI，适合需要判断和整理的工作 |

`sybermem record id --type <change|decision|requirement|bug>` 只生成 canonical record ID；完整 record 创建仍通过 `/sybermem-record` 完成。

## 平台支持

详细功能矩阵见 [SyberMem Feature Map](docs/feature_map.md)；这里保留最常用的平台摘要。

| 平台 | 支持级别 | 说明 |
|---|---|---|
| Claude Code | 完整集成 | plugin metadata、skills、SessionStart / Stop / UserPromptSubmit hooks |
| OpenCode | 支持集成 | skills + TypeScript plugin；session lifecycle、prompt-time project recall、User Habit Memory 提醒、record-intent metadata 与 recall debug logging 都走受支持的 plugin/chat transform 路径 |
| Codex | Partial runtime + skills | 用户级 skills 安装到 `~/.agents/skills`，并安装 `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` hooks；支持 bounded startup context、prompt-time recall、habit reminder、record-intent capture、Stop record nudge 和 compact re-seed marker；仍无 hidden auto-resume、后台自动化或 agent runtime |

Claude Code 受管项目可通过 `UserPromptSubmit` 对明显偏好语句或 prompt-approved habits 给出有界提醒；老项目需运行 `/sybermem-update` 刷新 hook。OpenCode 通过 `chat.message` + `experimental.chat.system.transform` 提供逐 prompt 高信号项目召回，并把 User Habit Memory 提醒和 recall hints 一起注入同一轮 system prompt；`chat.message` 还会写入 bounded `.sybermem/.record-intent.json` 和 `.sybermem/.recall-debug.jsonl` metadata，不保存原始 prompt；`session.created` 现在除了 toast，还会为该会话首轮准备一份一次性 startup context（key conclusions、phase、stale/digest 提示、next-step），由首个 `experimental.chat.system.transform` 前置注入到模型可见的 system prompt；startup context 不含 habit，避免与逐 prompt habit 注入重复。`session.idle` 还会读取 `sybermem project memory-stats` 的 `recall_health`，仅在近窗召回为 `low_signal` 时给一条节流、fail-open 的提示。`⭐`/`💡` 继续用于可见化 recall，habit 提醒保持保守，只取 active、高置信、直接相关、在受支持 prompt 场景下允许注入的内容，输出有界且 fail-open。Codex 现在会安装 `~/.codex/hooks/sybermem_session_start.py`、`sybermem_user_prompt.py`、`sybermem_stop.py` 和 `sybermem_post_compact.py`，并把它们合并到 `~/.codex/hooks.json` 的 `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact`。其中 `SessionStart` / `UserPromptSubmit` 通过 `hookSpecificOutput.additionalContext` 提供 bounded startup context、prompt-time project recall 和 User Habit Memory 提醒；UserPromptSubmit 还会为显式记录请求写入 bounded `.sybermem/.record-intent.json` metadata，不保存原始 prompt；Stop 只做防循环 record nudge；PostCompact 只写 compact re-seed marker。但 Codex 仍不支持 hidden auto-resume、后台自动化、prompt 或 agent handler runtime，也不安装 `.codex/config.toml`。更多说明见 [`.codex/INSTALL.md`](.codex/INSTALL.md)。OpenCode 说明见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md)。

## 安装与升级

### 一行式安装

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

这会刷新用户级 Claude Code skills、OpenCode skills、Codex skills（`~/.agents/skills`）、OpenCode plugin、Codex `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` hooks，以及 CLI / Core runtime。安装器会创建固定 CLI launcher：macOS / Linux 为 `$HOME/.claude/sybermem/cli/sybermem`，Windows 为 `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd`。SyberMem 的 OpenCode plugin、Codex hooks 和 CLI 型 skills 在子进程找不到裸 `sybermem` 时会优先使用这个固定 launcher；安装脚本默认不修改持久 PATH。

### 本地插件验证

```bash
claude --plugin-dir .
```

适合在仓库 checkout 中直接验证 Claude Code 插件、hooks 和 skills。

### 升级顺序

1. 先重新运行全局安装 / 更新命令。
2. 再进入已有项目运行 `/sybermem-update`。
3. 新项目运行 `/sybermem-init-project`。

全局刷新只更新用户级 runtime、Claude/OpenCode/Codex skills、OpenCode plugin 和 Codex 用户级 hooks；项目内的 `.sybermem/`、hooks、模板和说明文件需要 `/sybermem-update` 才会刷新。`/sybermem-update` 会优先调用 `sybermem project refresh --format json` 做可脚本化的项目内刷新，只有 CLI 缺失、执行失败或输出非 JSON 时才回退到 agent 编排的 `/sybermem-init-project`。Codex 的健康检查会把 `~/.agents/skills/sybermem-init-project/project-files` 作为模板来源之一，因此 Codex 安装路径也能参与项目 freshness 检查。老用户要拿到 OpenCode 新的 habit reminder、record-intent metadata 或 recall debug logging 链路，先重跑全局安装/更新以刷新 `~/.config/opencode/plugins/sybermem.ts`，再进项目跑 `/sybermem-update`。若修复的是 CLI launcher、OpenCode plugin、Codex hook 或 skill 指令链路，也按这个顺序生效。

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
- `/sybermem-habit`：记录、查看、暂停、删除用户级习惯，或触发可见提醒
- `/sybermem-summary`：查看当前项目状态
- `/sybermem-digest`：沉淀稳定阶段结论
- `/sybermem-theme-digest`：沉淀跨阶段主题结论
- `/sybermem-team-publish`：preview、review 后发布到 Team memory

### 管理者 / 管理 agent

- `/sybermem-team-summary`：生成 Team 管理摘要
- 阅读 Team repo 中的 `dashboards/current-overview.md` 和 `latest-management-summary.md`

### 不确定下一步时

- `/sybermem-resume`（slash skill）：先恢复当前上下文
- `/using-sybermem`（slash skill）：检查当前状态并获得推荐命令
- `sybermem next-step`（终端 CLI 命令，**不是** slash 命令，没有 `/sybermem-next-step`）：用 CLI 直接获取下一步建议；`/using-sybermem` 内部也调用它，两者与 `/sybermem-resume` 使用同一个路由，结论一致

## 索引与检索

- `.sybermem/INDEX.md` 是项目内派生导航文件，由 `sybermem project index build` 重建，由 `sybermem project index check` 校验。
- `sybermem project phase analyze` 会确定性地对记录分组并原子写回 `.sybermem/analysis/phase-index.md`（confirmed phases + coverage map + `status: analyzed`），使阶段分析结果不会因为手写 Markdown 而静默丢失；`sybermem project phase confirm --from-json <file>` 可把 agent 产出的高质量分组在校验覆盖后确定性落盘。`/sybermem-phase-analyze` 优先走该 CLI，仅在 CLI 缺失、执行失败或输出非 JSON 时回退 agent 编排。
- `sybermem project memory-stats` 以表格展示最近 7 天 / 30 天的 record 数量、类型分布、recall events、injected/abstained、recall rate 和召回精准度；`--format json` 给 skill 和自动化消费。召回频率指标来自 `.sybermem/.recall-debug.jsonl`，召回精准度来自 `.sybermem/.recall-outcomes.jsonl`；没有对应日志表示统计不可用，不代表召回活动为 0。`recall_health` 的 `low_relevance` 判定在注入样本足够且精准度低于阈值时才触发，与频率型 `low_signal` 区分。
- `sybermem project record-files --ids <a,b> --format json` 把记录 id 映射到其 `related_files`，供 OpenCode 召回相关性判定复用 Core 的 Markdown 解析。
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
.codex-plugin/                       # Codex marketplace/entry metadata
.codex/                              # Codex install notes and bounded habit hook
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
- Claude 的 prompt-time recall 适用于受管 Claude hooks；OpenCode 使用 `chat.message` + `experimental.chat.system.transform` 提供高信号项目召回，并在同一条 transform 注入保守的 User Habit Memory 提醒，同时通过 `chat.message` 写入 prompt-free record-intent 与 recall debug metadata；Codex 通过 `SessionStart` / `UserPromptSubmit` / `Stop` / `PostCompact` 提供 bounded startup context、prompt-time recall、habit reminder、record-intent capture、loop-safe record nudge 和 compact re-seed marker，但仍不支持 hidden auto-resume、后台自动化或 direct compaction prompt injection。
- 更多安装、升级和兼容细节见 [INSTALL.md](INSTALL.md)。

## License

MIT
