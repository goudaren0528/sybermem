**中文** | [English](README.en.md)

# SyberMem

SyberMem 是面向 AI 编程工作流的项目工程记忆系统。它把一次工作的背景、决策、原因和阶段结论沉淀为本地 Markdown，让下一次会话不必从零重建上下文。

## 为什么需要它

AI agent 很擅长在当前窗口里推进工作，但跨会话后容易丢掉三个关键信号：

- 之前为什么这么设计
- 哪些问题已经踩过或修过
- 当前项目最安全的下一步是什么

SyberMem 用结构化 records、可派生索引、阶段 / 主题 digest 和只读续接视图保存这些信号。数据保存在项目本地的 `.sybermem/` 目录中，人和 AI 都能直接审阅，不是黑盒服务。

## 架构总览

```mermaid
flowchart TD
    subgraph Hosts["AI 宿主"]
        C[Claude Code]
        O["OpenCode（集成最完整）"]
        X[Codex]
    end
    Hosts -->|hooks / plugin| Core["sybermem CLI / Core<br/>召回 · digest · norm 治理"]
    Core -->|读写| Proj["项目记忆 .sybermem/<br/>records · digests · norms · INDEX"]
    Core -->|读写| Habit["用户习惯 ~/.sybermem/<br/>跨项目个人偏好"]
    Core -->|只读汇总| Hub["Hub registry<br/>portfolio 跨项目视图"]
    Proj -.->|Git 共享| Team["团队<br/>clone/pull 即得完整记忆"]
```

记忆是项目本地的 Markdown，随 Git 共享；宿主通过各自的 hook/plugin 把相关记忆在会话内注入模型，全部经由同一个 CLI/Core，避免第二套黑盒存储。

## 快速开始

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex

# Windows OpenCode / cmd.exe (PowerShell-free)
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.py').read())"
```

安装后进入目标项目，按任务选择入口：

| 你要做什么 | 入口 |
|---|---|
| 初始化新项目 | `/sybermem-init-project` |
| 不知道下一步 | `/using-sybermem`：只读定位，通过现有 `sybermem next-step --format json` 给建议 |
| 续接已有工作 | `/sybermem-resume` |
| 收尾记录有价值的工作 | `/sybermem-record` |

**当前会话刚安装：** 新落盘的 skill 不会热加载。先确认用户授权的目标是已存在目录；若目标位于已有 SyberMem 祖先下，先询问是否要创建独立嵌套项目，不能从 cwd 静默推定授权。验证下文[固定 launcher](#一行式安装)可用且 `project refresh --help` 支持 `--root` 后，由已授权安装流程执行 `sybermem project refresh --root "<confirmed-target>" --format json`；using 只能推荐，slash skill 留到新会话使用。CLI 缺失先恢复安装，不能运行 doctor。

PowerShell 调用为 `& $SyberMemCli project refresh --root "<confirmed-target>" --format json`；Bash 为 `"$SYBERMEM_CLI" project refresh --root "<confirmed-target>" --format json`（命令变量先按对应 shell 解析，替换引号内占位符）。显式 `--root` 精确写入该已存在目录，不向上查找、不隐式 mkdir、不 fallback。必须核对退出码 0、有效 JSON、返回 `root` 与授权目标一致且 `overall` 为 `fresh` 或 `updated`；失败可能已有部分写入，停止检查，不盲目重试。旧 CLI 不识别 `--root` 时停止并提示升级或新会话 skill，不能降级到无参数调用。

旧 `sybermem project refresh --format json` 行为不变：向上查找物理祖先的项目 markers，无 root 时退出 1，并非 cwd 初始化；修改 HOME 不会阻止祖先查找。`project init` 仅为已有可解析 root 提供身份，不是完整 fresh 初始化。

这些是按任务选择的入口，不是自动执行链。`using` 不初始化、不写记录、不执行下游动作；空项目如实显示无记录。旧入口继续可用，已有项目无需强制重新初始化或记录；legacy `sybermem project init` 不等同完整的受管项目 refresh。典型节奏是 init → 工作 → record，下次用 resume 恢复阶段、进展、风险与信息新鲜度。

### 按需查看运行证据

```text
sybermem doctor --runtime --format json
```

这是三层证据及局限的按需展示，不是自动检测当前宿主的功能，不需每轮运行。未传 `--runtime` 的 `sybermem doctor` 保留既有行为。

| 层级 | 可以说明什么 |
|---|---|
| 已安装 | 当前 CLI/core 的安装证据，不能泛称 plugin 已安装 |
| 当前宿主已加载 | 普通 CLI 没有 live host/session 身份，显示 `unknown` 并解释原因 |
| 本轮实际注入 | 普通 CLI 没有本轮关联，显示 `unknown`；文件存在或最新日志不能代证 |

`unknown` 是缺证据；“未支持”须有明确能力边界；“未匹配”须有本轮确实无匹配的证据，空结果/空 packets 不能推出未匹配。即使有宿主上下文交付证据，也不证明模型消费或采用。升级磁盘文件不代表运行中会话已加载新版本，须开新会话验证。CLI 不支持该参数时，按既有全局升级 → 项目更新 → 新会话顺序处理；CLI 缺失则先恢复安装。

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

- 结构化 records：`change` / `decision` / `requirement` / `bug` / `norm`
- UUID-backed `record_id`，并兼容旧 numeric record ID
- 从 canonical records 派生的 `.sybermem/INDEX.md`
- phase digest 与 theme digest，用于阶段和主题级压缩
- record 关系：`implements` / `fixes` / `related` / `superseded_by` / `crystallized_from`
- 只读续接：`/sybermem-resume` 与 `sybermem resume`
- 记忆统计：`sybermem project memory-stats` 打印 7 天 / 30 天终端表格（record 计数、类型分布、recall、Edit Alignment、digest / norm 覆盖、memory injection lane 分布）；`--format json` 供 `/sybermem-summary` 与自动化消费。详见[索引与检索](#索引与检索)
- 召回相关性反馈：OpenCode 在 `session.idle`、Codex 在 `SessionEnd`（best-effort）把召回注入过的记录与实际编辑文件（按 `related_files`）比对，写入有界 `.sybermem/.recall-outcomes.jsonl` / `.memory-usage.jsonl`，得出频率之外的 `low_relevance`（精准度）与 `low_measurability`（锚点不足）判定。详见 [Feature Map](docs/feature_map.md)
- 注入可观测性：OpenCode 与 Codex 会把交付至宿主上下文边界的记忆元数据写入 `.sybermem/.memory-usage.jsonl`（含 lane totals、注入 record ids 与 `session_outcome` 汇总，不保存原始 prompt / 完整注入文本，写入失败 fail-open）；这不证明模型消费或采用，也不能仅凭最新日志认定是当前轮。详见 [Feature Map](docs/feature_map.md)
- 项目内检索：`/sybermem-search` 与 `sybermem search`
- 下一步建议：`/using-sybermem` 与 `sybermem next-step`

### Digest 沉淀与反哺

- phase / theme digest 用 coverage hash 做机械陈旧检测：`sybermem digest status` 给出 current/stale/unknown 判定
- digest 积压信号：`sybermem digest status --format json` 带 `backlog`（未被任何 digest 覆盖的 record 数 + 距上次 digest 天数）。已经做过一次 digest 后仍持续记录的项目，会在 OpenCode `session.idle`、Claude/Codex `SessionStart` 得到"N 条记录尚未进入任何 digest"的 `⭐` 提醒；`next-step` 首次 digest 推荐改用 digest 专属的记录数阈值（而非发布阈值）
- digest 结果真正反哺：digest 进入搜索/召回语料（带 `related_digest` 连续性关联和 stale 冲突标注）；`sybermem digest latest` 返回最新 phase digest 的 Core Conclusions，**三宿主都会把它注入模型可见上下文**——OpenCode 在 startup / compaction、Claude Code 与 Codex 在 `SessionStart`——digest 内容对模型可见，而不仅仅是"去读"指针

### Project Norms（项目规范 / 约束）

- 一等 `norm` record 类型，存于 `.sybermem/norms/`，区别于个人 habit（用户级）和普通 decision
- 字段：`scope`（`global` / `topic:x` / `path:x` / `tool:x`）、祈使 `statement`、`authority: authoritative`，复用已有 lifecycle + supersede 机制
- 双通道反哺：**宪法**（active 全局 norm，最多 5 条，每会话开场恒注入，与 prompt 相关性无关）+ **域内召回**（非全局 norm 按 scope tag 或 ≥2 个强语句重叠命中，不降低召回门槛）
- 识别（都 confirmation-first，绝不自动固化）：显式——`/sybermem-record` 收尾把绑定规则固化为 `norm`（带 `crystallized_from` 溯源）；涌现——`sybermem norms nominate` 确定性地检测跨 ≥3 条 decision/requirement 反复出现、且未被现有 norm 覆盖的约束，在 `/sybermem-digest` / `/sybermem-theme-digest` 收尾提名
- 反哺覆盖三宿主：OpenCode（startup 宪法 + 每-prompt 域内召回 + `📏` toast + compaction 复用宪法）、Claude Code（`SessionStart` 宪法 + `UserPromptSubmit` 域内）、Codex（`SessionStart` 宪法 + `UserPromptSubmit` 域内）
- 治理：`sybermem norms doctor` 检测同 scope 内重叠的多条 active norm（疑似矛盾/重复，CI 可据非零退出码拦截，仅提示不改写）；`sybermem norms list --scope global|scoped|all --context <text> --format json` 是所有宿主共用的单一事实源

### Workspace / Hub

- project registry
- workspace SQLite FTS5 搜索索引：`sybermem index build`
- workspace search 支持项目、类型和状态过滤
- index 缺失、schema 过期或 stale 时给出恢复提示
- portfolio 视图：`sybermem portfolio`
- 跨项目组合视图：`sybermem portfolio` 基于 Hub registry 只读汇总各已注册项目的阶段、未决 bug/需求、digest 覆盖与最近记录日期（不需要单独的 Team 仓库或发布流程）

### User Habit Memory

- 用户级习惯存储：`~/.sybermem/user-habits/`，或测试/自定义环境中的 `SYBERMEM_HOME/user-habits/`
- 显式记录：`sybermem habit add --type workflow --applies-to planning "Prefer plans before implementation"`
- 查看与治理：`sybermem habit list`、`search`、`pause`、`delete`
- 可见提醒：`sybermem habit remind --context planning --format markdown` 与 `/sybermem-habit`
- 召回诊断：`sybermem habit test --context "planning"` 以 dry-run 方式解释当前 context 下 active/evaluated/selected 数量、每条 habit 的 policy/confidence/applies_to/score/floor/reason；`sybermem habit explain --id <habit-id> --context "planning"` 聚焦单条 habit。两者只读，不写 habit、不写候选、不注入模型
- 手动/compaction 注入：`sybermem habit inject --context planning --format markdown`
- 默认 prompt-time 可感知：`habit add` 默认 `injection_policy=prompt_ok_when_supported`，确认过的习惯在支持的宿主上开箱即可在逐 prompt 注入（弹 `🧠`），无需额外参数；相关性用 CJK 感知的加权匹配（命中 `applies_to` tag 为强信号，否则需 ≥2 个多字符语句重叠），中文上下文可命中，无关习惯保持静默
- 被动候选捕获（仅候选，永不自动写入）：OpenCode `chat.message` 检测到"以后都…/我习惯…"这类可复用偏好时，调用 `sybermem habit intent --prompt <text>` 把候选追加到用户级 `~/.sybermem/.habit-intent.json` 的**有界候选列表**（最近 5 条、10 天过期、按 summary 去重；绝不创建 active habit）。候选带 `candidate_id`、建议 type/scope，以及一段**有界、过密钥/注入过滤的 prompt 摘要**（不是完整原文，与 record-intent 的摘要契约一致），供确认时据此提议规范化 statement。`/sybermem-habit` 默认先展示 active + pending 状态视图，`habit intent-status` 列出候选，用户可一键确认某条转为 habit（随后 `habit intent-discard <id>` 单条清除），或 `habit intent-clear` 清空全部
- 注入可见性：同轮真正注入 recall / habit / 规范后只弹一条有界 post-injection summary（total items / chars / lane counts）；捕获候选时另弹 scope 感知的 `💡`（个人习惯→`/sybermem-habit`，项目约定→`/sybermem-record`，模糊时追问），startup context 用独立一次性提示
- 感知层：`sybermem habit awareness` 及 OpenCode 首轮 startup context 展示 active 习惯数量、类型分布与是否有待确认候选（只报数量，不暴露 habit 内容，也不与逐 prompt 提醒重复）
- 保守门槛：只注入 active、高置信、未被排除、与上下文直接相关的习惯，最多 3 条
- 默认不进入项目 `.sybermem/` records；个人偏好 → habit，绑定的项目规则 → 固化为 `norm`（见 Project Norms）

## CLI 与 Skill 的边界

SyberMem 有两类执行路径，可靠性不同：

| 路径 | 代表能力 | 说明 |
|---|---|---|
| CLI / Core | `sybermem resume`、`search`、`next-step`、`portfolio`、`index build`、`project index build/check`、`project memory-stats`、`record id`、`habit add/list/search/pause/delete/remind/inject/test/explain`、`digest status/latest`、`norms list/nominate/doctor`、`uninstall --scope project|global`、`project uninstall` | 程序执行，可脚本化，适合确定性查询 |
| Skill 编排 | `/sybermem-record`、`/sybermem-habit`、`/sybermem-digest`、`/sybermem-theme-digest`、`/sybermem-phase-analyze`、`/sybermem-uninstall` | 由 AI 按 skill 指令创建或修正 `.sybermem/` 记录及关系、调用用户级 habit CLI，或在卸载时询问/确认项目级与全局 scope，适合需要判断和整理的工作 |

`sybermem record id --type <change|decision|requirement|bug>` 只生成 canonical record ID；完整 record 创建仍通过 `/sybermem-record` 完成。

## 平台支持

三个宿主都能记录、召回、resume；**OpenCode 集成最完整**——逐-prompt 召回、习惯提醒、注入可观测性全部自动、原生。

| 平台 | 自动化程度 | 接入方式 |
|---|---|---|
| **OpenCode** | 最完整：逐-prompt 自动召回 + 习惯注入 + 注入可观测性 | 原生 TypeScript plugin（`chat.message` / `system.transform` 等 seam）+ skills |
| **Claude Code** | 完整：会话启动上下文 + 逐-prompt 提醒 | plugin metadata + `SessionStart` / `UserPromptSubmit` / `Stop` hooks + skills |
| **Codex** | 有界：启动上下文 + 逐-prompt 召回/提醒 + metadata-only 可观测性 | `~/.agents/skills` + `SessionStart` / `UserPromptSubmit` / `SessionEnd` / `Stop` / `PostCompact` hooks（无隐藏自动化） |

三平台共享同一套 records、CLI/Core 与 `.sybermem/` 数据，差异只在「注入自动化」的深度。逐宿主的 hook 细节与完整功能矩阵见 [Feature Map](docs/feature_map.md)、[`.opencode/INSTALL.md`](.opencode/INSTALL.md) 与 [`.codex/INSTALL.md`](.codex/INSTALL.md)。

## 安装与升级

### 一行式安装

安装命令见上文[快速开始](#快速开始)（提供 macOS / Linux、Windows PowerShell、Windows PowerShell-free 三种）。

这会刷新用户级 Claude Code skills、OpenCode skills、Codex skills（`~/.agents/skills`）、OpenCode plugin、Codex `SessionStart` / `UserPromptSubmit` / `SessionEnd` / `Stop` / `PostCompact` hooks，以及 CLI / Core runtime。安装器会创建固定 CLI launcher：macOS / Linux 为 `$HOME/.claude/sybermem/cli/sybermem`，Windows 为 `%USERPROFILE%\.claude\sybermem\cli\sybermem.cmd`。SyberMem 的 OpenCode plugin、Codex hooks 和 CLI 型 skills 在子进程找不到裸 `sybermem` 时会优先使用这个固定 launcher；安装脚本默认不修改持久 PATH。

### 从源码验证

各平台验证方式不同：

- **OpenCode**：重跑安装器（或 checkout 内 `python scripts/update.py`），分三阶段验收：① 检查安装器输出及已部署文件的 SHA-256 与源码构建产物一致；② 重启/重载宿主并检查 plugin loader；③ 用真实 prompt 验证召回和可见反馈。仅有文件不能证明 toast 或模型实际使用。V1 使用独立 `sybermem-v1.ts` 单文件入口；V2 是含 `package.json`、`server.js`、`tui.js` 的完整目录包，迁移不得同时加载旧入口。详见 [OpenCode 安装说明](.opencode/INSTALL.md)。
- **Claude Code**：`claude --plugin-dir .` 直接从 checkout 加载插件、hooks 与 skills。
- **Codex**：重跑安装器，确认 `~/.agents/skills` 下的 skills 与 `~/.codex/hooks/*.py`（及 `~/.codex/hooks.json` 合并项）已就位。

### 升级顺序

1. 先重新运行全局安装 / 更新命令。
2. 再进入已有项目运行 `/sybermem-update`。
3. 新项目运行 `/sybermem-init-project`。

安装器会把已安装版本写入 `~/.claude/sybermem/VERSION`；`sybermem project refresh` 会在项目 `.sybermem/project.yaml` 写入 `sybermem_version`。当某个项目落后于已安装版本时，会话启动会给出一条节流、fail-open 的 `⭐ 运行 /sybermem-update` 提醒（OpenCode `session.created` toast；Claude/Codex `SessionStart` 上下文）。随时可用 `sybermem doctor` 查看已安装版本与当前项目版本。

全局刷新更新用户级 runtime、skills、按宿主版本选定的 OpenCode plugin 和 Codex hooks。项目内文件需 `/sybermem-update`：先确认作用域，再使用显式 `project refresh --root "<confirmed-target>" --format json` 并按上文核对结果。失败时停止检查可能的部分写入，再另行授权恢复；必要时推荐新会话 `/sybermem-init-project`。Codex 健康检查也识别已安装项目模板。先更新全局组件，再逐项目更新；project refresh 不创建 runtime logs。V2 尚未恢复 V1 的远程版本后台刷新，不能把本地版本提醒当成远程刷新。

## 初始化项目

先将用户确认的目标规范化为绝对路径并展示；若与预期作用域不同，重新确认。以同一规范化目标核对返回 `root`，并保留祖先嵌套授权检查。Git 探测的固定 locale 为 `C`。本次仅批准 `doctor --runtime` 与 `project refresh --root` 两处接口扩展；这些检查不证明模型消费。

显式分支拒绝非空 `GIT_*` 环境覆盖；Git 探测固定 locale，严格识别非仓库结果，Git 不可用或边界未知即拒绝。目标自有独立 repo 可用，祖先 worktree 子目录拒绝；拒绝后停止，不回退无参数调用。`--root` 是静态精确目标检查，不是 OS 沙箱，不保证竞态安全或全链路脱敏。真实 refresh 仍需 VM/OS 隔离验证，目前未验。

显式 `--root` 会拒绝目标或祖先中的 symlink/reparse point、处于祖先 Git 工作树内但没有自有独立仓库的目标，以及无法确认 Git 边界的情况：Core 的 `git rm --cached` 可能影响祖先 index。用户确认嵌套项目不绕过这些检查；拒绝后停止，不回退无参数 refresh，不能保证任意嵌套目录均可初始化。

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
- `.claude/settings.json`

如果项目已有自定义 `.claude/settings.json`，SyberMem 只会补丁可识别的受管项，不覆盖无关 hooks、env 或说明。SyberMem 不再向 `CLAUDE.md` / `AGENTS.md` 注入内容；init/update 会移除旧版本遗留的 SyberMem 协议块（若文件仅含该块则删除整个文件，否则只移除块并保留用户内容）。

## 日常使用

先用 Core entrypoints 这一小组命令；advanced / lifecycle 一层仍然可以直接调用，
只是使用频率更低，并不代表被弃用。规范分类以 `docs/feature_map.md` 为准。

### Core entrypoints

- `using-sybermem`: 只读定位入口——解析项目根、报告精简的安装/项目状态，并给出唯一一条规范的下一步命令；不执行任何下游动作。
- `sybermem-init-project`: 初始化或重新脚手架项目内的 SyberMem 目录、模板与受管配置。
- `sybermem-record`: 记录一轮有价值的工作为 canonical record；收尾时可把绑定的项目规则固化为 `norm`（带 `crystallized_from` 溯源），也可补充或修正既有 record 之间的关系。
- `sybermem-resume`: 只读续接视图——当前阶段、最近进展、风险、建议下一步、置信度与信息新鲜度。
- `sybermem-search`: 在项目内查找历史 records、decisions 与 digest。
- `sybermem-digest`: 把已稳定的阶段压缩为持久的阶段级结论。
- `sybermem-habit`: 记录、查看、暂停、删除用户级习惯与待确认候选，或触发可见提醒。

### Advanced / lifecycle

- `sybermem-install`: 首次在一台机器上安装整套 SyberMem 系统。
- `sybermem-update`: 全局升级后刷新某个既有项目内的受管 SyberMem 文件。
- `sybermem-uninstall`: 自然语言卸载入口；scope 不明确时会先询问项目级还是全局，且全局卸载必须显式确认，项目级卸载保留 `.sybermem/` 历史。
- `sybermem-summary`: 查看当前项目状态与记忆/召回健康面板，适合周期性复盘。
- `sybermem-phase-analyze`: 依据完整 record 历史构建或刷新结构化阶段索引。
- `sybermem-theme-digest`: 把相关 records 与多个阶段综合为跨阶段的主题级结论。

相关 CLI（不是 Skill）：`sybermem norms list/nominate/doctor` 查看项目规范宪法、
提名重复约束、检测同 scope 冲突。

### 跨项目视图

- `sybermem portfolio`：只读汇总各已注册项目（阶段、未决 bug/需求、digest 覆盖、最近记录日期）

### 不确定下一步时

- `/sybermem-resume`（slash skill）：先恢复当前上下文
- `/using-sybermem`（slash skill）：检查当前状态并获得推荐命令
- `sybermem next-step`（终端 CLI 命令，**不是** slash 命令，没有 `/sybermem-next-step`）：用 CLI 直接获取下一步建议；`/using-sybermem` 内部也调用它，两者与 `/sybermem-resume` 使用同一个路由，结论一致

## 索引与检索

- `.sybermem/INDEX.md` 是项目内本机派生导航文件，被 Git 忽略，由 `sybermem project index build` 重建、由 `sybermem project index check` 校验；不提交或评审它。Canonical records 才是共享源。
- `sybermem project phase analyze` 会确定性地对记录分组并原子写回 `.sybermem/analysis/phase-index.md`（confirmed phases + coverage map + `status: analyzed`），使阶段分析结果不会因为手写 Markdown 而静默丢失。阶段分组是 agent 判断：agent 读取完整 record 历史产出语义分组，用 `sybermem project phase analyze --from-json <file>`（`{ "phases": [ { "title": "...", "covered_records": [...] } ] }`）校验覆盖后确定性落盘；机械分组（不带 `--from-json`，按月份+主题分桶）仅在 agent 无法产出语义分组时兜底。`/sybermem-phase-analyze` 优先走该 CLI，仅在 CLI 缺失、执行失败或输出非 JSON 时回退 agent 编排。
- `sybermem project coverage-hash --phase-id phase-NNN --format json` 把某阶段的 covered record 解析为真实文件路径（依据各记录 frontmatter `record_id:`，而非文件名）并返回 `source_records` 与确定性的 `coverage_hash`，供 `/sybermem-digest` 填充 digest 的 `coverage_hash` 字段；也可用 `--source-records <relpaths>` 直接对指定源计算哈希。
- `sybermem project memory-stats` 以表格展示最近 7 天 / 30 天的 record 数量、类型分布、recall events、injected/abstained、recall rate、Edit Alignment，以及 Memory injection 的 turns/items/chars、avg chars/turn、p95 chars/turn 和 30d lane distribution；`--format json` 给 skill 和自动化消费。召回频率指标来自 `.sybermem/.recall-debug.jsonl`，Edit Alignment 与 memory injection observability 来自 OpenCode/Codex 写入的 `.sybermem/.recall-outcomes.jsonl` 和 `.sybermem/.memory-usage.jsonl`；没有对应日志表示统计不可用，不代表召回活动为 0。Edit Alignment 只是按 `related_files` 锚点计算的编辑对齐代理，不代表语义准确率；它会同时暴露 hit、measurable、unmeasurable 和 evidence availability。Codex 的 Edit Alignment 来自 `SessionEnd` 时的 git diff 近似，不具备 OpenCode per-event 编辑遥测精度。`recall_health` 的 `low_relevance` 判定在注入样本足够且该代理值低于阈值时才触发，与频率型 `low_signal` 区分；当召回在触发但太多记录缺少可验证 `related_files` 锚点时，会给出独立的 `low_measurability` 建议。
- `sybermem project record-files --ids <a,b> --format json` 把记录 id 映射到其 `related_files`，供 OpenCode 召回相关性判定复用 Core 的 Markdown 解析。
- `sybermem index build` 构建 workspace 级 SQLite FTS5 索引，服务于跨项目搜索。
- 项目内检索默认基于已解析 Markdown records 的词法匹配和打分；`title` / `topics` / relation / body 之外，`key_conclusion` 作为一等高权重信号参与排序，`related_files` 提供有上限的路径/模块 boost 与 tie-break。显式项目检索还能做一跳 typed relation expansion：当查询直接命中 `record_id`，或先命中 typed relation 时，结果可补入关联 record，并在 JSON / 机器可读结果中带 `match: relation-expanded`、`expanded_from`、`expansion_relation` 溯源字段。`sybermem context recall --format json` 会暴露机器可读的匹配字段、分数拆解与这类 expansion provenance；prompt-time Markdown 包保持短小，不注入解释细节。需要跨项目搜索时使用 workspace index。
- prompt-time recall 继续走更保守的 shared `context recall` gate：只会在高信号 seed 已经成立后，最多为每个 seed 追加 1 条非 evidence 的一跳 relation expansion，全包最多追加 2 条；弱 keyword-only、topic-only、semantic-only 匹配不会触发 expansion，也不会自动注入每轮提示。
- 可选的 `SYBERMEM_SEMANTIC_RECALL=1` 会启用本地 char n-gram 召回补充，用于显式检索；它不会触发弱 expansion，也不会自动注入每轮提示。

## 跨项目协作

团队协作直接通过 Git 共享每个仓库的 `.sybermem/`：任何人 clone/pull 后即获得完整的项目工程记忆，agent hooks/plugin 在本地开发时自动应用。需要跨多个仓库的只读组合视图时，用 `sybermem portfolio`（基于 Hub registry，无需单独的 Team 仓库或发布流程）。

> 注：早期版本的独立 "Team memory" 发布子系统（`sybermem team`/`publish`、`/sybermem-team-*`）已移除——对"单团队共享单仓库 + Git"的工作流它是冗余的（见 CHANGELOG）。现有的外部 Team 仓库和 `.sybermem/` 历史不受影响。

## 仓库结构

```text
.claude-plugin/                      # Claude Code 插件元数据与 marketplace 清单
hooks/                               # Claude Code hook 声明与 delegator
skills/                              # Plugin-facing skills tree
packages/claude-skills/              # Skills 分发源
packages/core/                       # Core memory / norm & digest governance logic
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
sybermem uninstall --scope project
```

它会停用项目内 SyberMem runtime 接管，但保留 `.sybermem/` 历史内容，并尽量只移除受管 hook / env / instruction block。

### 全局卸载

```text
sybermem uninstall --scope global --yes
```

```bash
# Windows (PowerShell)
.\scripts\uninstall.ps1

# macOS / Linux
./scripts/uninstall.sh
```

全局卸载会移除用户级 skills、CLI、launcher 和 OpenCode plugin，不删除任何项目里的 `.sybermem/` 历史。自然语言卸载可使用 `/sybermem-uninstall`；如果没有明确说明项目级或全局，它会先询问，全局卸载必须显式确认。

## 兼容说明

- `.sybermem/` 是规范项目数据目录，可随 Git 共享。
- 各宿主的 prompt-time 召回与注入行为差异见[平台支持](#平台支持)；实现细节见各平台 INSTALL。
- 更多安装、升级和兼容细节见 [INSTALL.md](INSTALL.md)。

## License

MIT
