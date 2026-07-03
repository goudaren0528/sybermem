**中文** | [English](README.en.md)

# SyberMem

一套 Claude Code / OpenCode 的 Skills 插件，用于追踪项目开发历史。将变更、决策、需求、Bug 记录为结构化文件，让 AI 在不同会话之间保持项目上下文记忆。

## 安装方式

| 模式 | 适用平台 | 推荐度 | 说明 |
|---|---|---|---|
| 插件安装 | Claude Code | 推荐 | 通过插件加载 hooks 和 skills |
| 脚本安装 | Claude Code / OpenCode | 兼容保留 | 复制 skills 到用户目录 |
| OpenCode 插件 | OpenCode | 推荐 | 提供 session.created / idle / compacting 生命周期 |

SyberMem 后续会优先以 Claude Code 插件安装作为首选路径；脚本安装会继续保留，作为兼容模式与跨平台兜底方式。

## 工作流程

安装 SyberMem → 在项目中运行 `/sybermem-init-project` → 完成有意义的工作后运行 `/sybermem-record` → 使用 `/sybermem-phase-analyze` 从项目历史构建或刷新 `.sybermem/analysis/phase-index.md` → 使用 `/sybermem-phase-confirm` 确认或调整候选阶段 → 使用 `/sybermem-summary` 查看最近活跃 confirmed phase 的当前状态面板（若 analysis layer 不存在，则回退到 weekly/monthly 动态报表）→ 在一个有意义的阶段结束时使用 `/sybermem-digest`，将持久化阶段总结写入 `.sybermem/digests/`。`phase-index.md` 是持久化的项目分析产物，不是最终 digest。每次会话开始时，AI 读取 `.sybermem/INDEX.md` 中的关键结论，回忆历史工作上下文。在 `auto` 模式下，stop hook 仍会自动写入轻量 `change` trail，但在检测到高价值变化模式时，也可能非阻塞地提示你补 `/sybermem-record` 或后续 `/sybermem-digest`。

`/sybermem-summary` 看”现在这个阶段状态如何”，而 `/sybermem-digest` 记录”这个阶段最终沉淀了什么”。

## 生命周期层（Lifecycle Layer）

SyberMem 嵌入 Claude Code / OpenCode 的会话生命周期，让项目记忆无感地跟随工作流：

| 生命周期 | Claude Code | OpenCode |
|---|---|---|
| 会话开始 | `SessionStart` hook 自动注入 Key Conclusions、Topic Index、phase 状态 | `session.created` toast 通知 |
| 工作中 | 模型根据 Topic Index 关联历史记录 | 同上 |
| 压缩前 | `SessionStart` compact 后重新注入 | `session.compacting` 注入 Key Conclusions + phase |
| 会话结束 | `Stop` hook 写轻量 change trail + nudge | `session.idle` 检测变更 + toast |

两个平台共享 `.sybermem/.nudge-state.json`，交替使用时不重复提示。

## 推荐升级方式

对于已有项目，推荐直接运行 `/sybermem-update`：

1. 刷新全局安装的 SyberMem skills
2. 在当前项目继续执行 `/sybermem-init-project`
3. 检查是否需要迁移旧 `ADR/`
4. 检查项目里的 `AGENTS.md` / `CLAUDE.md` 是否还是旧版并提示刷新

## 老用户升级说明

如果你的项目以前使用 `ADR/`，不需要手动改名。首次运行 `/sybermem-init-project`、`/sybermem-record`、`/sybermem-summary`、`/sybermem-digest`、`/sybermem-phase-analyze` 或 `/sybermem-phase-confirm` 时，会自动把旧的 `ADR/` 迁移为 `.sybermem/`。

如果 `.sybermem/` 和 `ADR/` 同时存在，系统会优先使用 `.sybermem/`，并警告 `ADR/` 已被忽略。

仅更新全局 skills 不会自动刷新项目里的 `AGENTS.md` / `CLAUDE.md`，所以升级后建议在目标项目里执行 `/sybermem-update`。

仅更新全局 skills 并不会自动为每个项目启用 digest 支持。若要在某个项目中使用 `/sybermem-digest`，请先在该项目里运行 `/sybermem-update`。这一步只会创建缺失的 digest 相关结构，不会悄悄覆盖项目自有文件。

已有项目也会通过 `/sybermem-update` 按项目拿到 `.sybermem/analysis/phase-index.md`。

如果老项目里仍保留 `.claude/skills/sybermem-*` 这类项目级副本，Claude 可能会同时加载项目级和全局级 skills，导致 `/` 列表重复显示。若你已经采用全局安装模式，可以删除这些旧副本。

如果你希望已有项目也拿到新的 stop hook 提示行为，仍然需要进入那个项目再运行一次 `/sybermem-update`。全局 skills 更新一次即可，但项目本地的 hook/template/说明刷新仍然是按项目生效。

如果你之前在子目录中遇到 stop hook 报错（文件找不到），运行 `/sybermem-update` 后该问题会自动修复。更新后的 hook 会自动向上查找包含 `.sybermem/` 和 `.claude/settings.json` 的最近祖先目录作为项目根。

现在 stop hook 的子目录修复通过全局 launcher 实现。更新后的项目会把 Stop hook command 自动迁移为全局绝对路径 `python C:/Users/69046/.claude/sybermem/launch_record_change_on_stop.py`。这样即使 Claude 的当前工作目录在项目子目录中，launcher 也能先找到真正项目根，再调用项目内的 `record_change_on_stop.py`。

已有项目运行 `/sybermem-update` 后，应自动完成这次 command 迁移；即使 `.claude/settings.json` 是 custom，只要里面仍然是可识别的旧 SyberMem Stop hook command，也会只替换这一行。

SyberMem 的很多行为变化并不只存在于全局 skill 本身，还依赖项目内的 managed files（例如 `CLAUDE.md`、`AGENTS.md`、`.claude/settings.json`、hook 模板等）。因此，已有项目在升级后通常还需要运行一次 `/sybermem-update`，才能真正拿到新的本地行为。

`/sybermem-update` 会补齐缺失的 managed files、刷新 stale 的 SyberMem-managed 文件，并保留 custom 本地文件不被悄悄覆盖。

SyberMem 现在会通过 `CLAUDE.md` / `AGENTS.md` 顶部的 `using-sybermem` 协议块来建立会话入口规则。已有项目运行 `/sybermem-update` 时，如果这些文件仍然属于 SyberMem-managed 范围，就会自动插入或刷新这个协议块；若文件已经是 custom，则默认不会整体覆盖。

`using-sybermem` 现在是双入口：顶部协议块会自动在会话开始时生效，而 `/using-sybermem` 则是用户可见的诊断入口。手动运行它时，系统会显示当前项目的 SyberMem 状态、summary/digest/analyze/record 的路由结果，以及建议下一步执行的命令。

## 安装

### Claude Code 插件安装（推荐）

适用于希望通过插件统一加载 hooks 与 skills 的 Claude Code 用户。这是 SyberMem 面向未来的首选安装路径。

#### 本地开发 / 测试

```bash
claude --plugin-dir .
```

这会从当前仓库目录加载 `.claude-plugin/`，适合本地联调 marketplace 元数据、hooks 与 skills 打包内容。

#### 未来的正式安装路径

未来会优先通过 Claude Code marketplace / 插件安装路径分发。当前仓库已经包含 `.claude-plugin/marketplace.json` 与 `.claude-plugin/plugin.json`，便于本地验证和后续接入。

### Claude Code / OpenCode 脚本安装（兼容保留）

以下命令保留为 direct/script install 方式，适合兼容旧环境、无插件场景，或需要将 skills 直接复制到用户目录时使用。

#### 一行命令安装（需仓库为 public）

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

#### 克隆安装

```bash
# macOS / Linux
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem && ./scripts/install.sh

# Windows (PowerShell)
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem; .\scripts\install.ps1
```

### OpenCode 安装

OpenCode 推荐使用其插件路径来获得 `session.created` / `session.idle` / `experimental.session.compacting` 生命周期能力。安装说明见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md)。

### 项目初始化

完成全局安装或插件接入后，进入你的项目并执行：

```text
/sybermem-init-project
```

这一步会在项目内创建或刷新：
- `.sybermem/`
- `.sybermem/digests/`（阶段 digest 目录）
- `.sybermem/analysis/phase-index.md`（持久化阶段分析产物）
- `.sybermem/hooks/record_change_on_stop.py`（默认自动 change hook helper）
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json`（默认启用 SyberMem `auto` / `remind` 模式）

不会在项目里再安装一份 skills。

详见 [INSTALL.md](INSTALL.md)。

## Skills

| Skill | 功能 |
|-------|------|
| `/sybermem-init-project` | 在项目中创建或刷新 `.sybermem/` 目录结构，扫描现有代码库，生成或刷新 `CLAUDE.md` / `AGENTS.md`，并在首次运行时自动迁移旧 `ADR/` |
| `/sybermem-record` | 从当前会话上下文创建记录，AI 自动判断类型：变更、决策、需求或 Bug，并写入 `.sybermem/` |
| `/sybermem-summary` | 动态查看最近活跃 confirmed phase 的当前状态面板；若 analysis layer 不存在，则回退到周报/月报 |
| `/sybermem-digest` | 从已有记录创建可持久保存的阶段摘要，将其写入 `.sybermem/digests/`，并阻止对同一批源记录重复压缩 |
| `/sybermem-theme-digest` | 为单个 topic 创建跨多个 phase 的持久化高阶摘要（Theme Digest） |
| `/sybermem-phase-analyze` | 从完整项目历史构建或刷新 `.sybermem/analysis/phase-index.md`，生成可持续维护的阶段分析索引 |
| `/sybermem-phase-confirm` | 确认、重命名或调整 `phase-index.md` 中的候选阶段，使阶段结构变为明确的项目分析结果 |
| `/using-sybermem` | 显示当前 SyberMem 状态、可用命令以及建议的下一步操作 |
| `/sybermem-update` | 刷新全局安装的 SyberMem skills，然后在当前项目继续执行 `/sybermem-init-project` |
| `/sybermem-search` | 按关键词、topic、phase 范围、日期范围或记录 ID 检索记录，并显示所属 phase、关系与替代提示 |
| `/sybermem-link` | 在两条已有记录间建立正向关系（implements / fixes / related / superseded-by） |

## Theme Digest Layer

除了 phase digest (`/sybermem-digest`), SyberMem 现在还支持 theme digest (`/sybermem-theme-digest`)：

- phase digest = 某个阶段最终沉淀了什么
- theme digest = 某个主题跨多个阶段最终沉淀了什么

Theme digest 目录为 `.sybermem/theme-digests/`。第一版按单个 topic 聚合,优先使用已有 phase digests,再用 raw records 补缺。

安装或更新后，可直接运行：

```bash
sybermem project init --register
sybermem index build
sybermem search hooks --scope workspace
```

## 记录关系与检索

记录可以在 frontmatter 中声明可选的正向关系字段：

- `implements: [requirement-NNN]` — 实现某需求/决策
- `fixes: [bug-NNN]` — 修复某 bug
- `related: [type-NNN]` — 弱关联

关系只存正向。`/sybermem-search <record-id>` 在查询时实时扫描，反向列出所有引用该记录的记录（`Referenced by`）。`/sybermem-record` 创建记录时会尝试推断并提议关系；`/sybermem-link` 用于事后补充。

## Topic 治理与替代关系

Topic Index 现在支持可选状态后缀：

- `[active]` — 当前活跃 topic（默认；无标记视为 active）
- `[low]` — 低活跃度 topic，仍可查询
- `[deprecated → <new-topic>]` — 已被新 topic 替代，search 会提示使用新 topic

记录 frontmatter 还支持可选的 `superseded_by: <record-id>` 字段，用于表示旧记录已被新记录替代。`/sybermem-link old superseded-by new` 会：

1. 在旧记录 frontmatter 写入 `superseded_by: <new-id>`
2. 将旧记录的 Key Conclusion 从 `## Key Conclusions` 移到 `## Archived Conclusions`
3. 在归档行尾追加 `[superseded by <new-id>]`

## 日常工作流

推荐把 SyberMem 当作“项目记忆的日常工具链”来用：

```text
查历史                → /sybermem-search <keyword|topic|record-id>
看现状                → /sybermem-summary
完成有价值工作        → /sybermem-record
phase-index stale     → /sybermem-phase-analyze
阶段收束              → /sybermem-digest
主题跨 phase 收束     → /sybermem-theme-digest <topic>
不确定当前状态/下一步 → /using-sybermem
```

## 在你的项目中会创建什么

```
.sybermem/
├── INDEX.md                        # 主索引 — Active/Archived Conclusions、Digests、Topic Index
├── changes/                        # 功能变更
├── decisions/                      # 技术决策
├── requirements/                   # 需求讨论
├── bugs/                           # Bug 修复
├── digests/                        # 阶段 digest
├── theme-digests/                  # 主题 digest（跨多个 phase）
├── analysis/
│   └── phase-index.md              # 持久化项目分析产物（含 lifecycle 字段）
├── hooks/
│   ├── record_change_on_stop.py    # 默认自动 change hook helper
│   ├── session_start_context.py    # SessionStart 上下文注入脚本
│   ├── check_project_health.py     # update fast-path 健康检查脚本
│   └── launch_record_change_on_stop.py # root-resolving stop-hook launcher helper
└── templates/
    ├── change-template.md
    ├── decision-template.md
    ├── requirement-template.md
    ├── bug-template.md
    ├── digest-template.md
    └── theme-digest-template.md

CLAUDE.md                           # Claude Code 项目指令（工作流规则）
AGENTS.md                           # OpenCode 项目指令（内容相同）
.claude/settings.json               # 项目级 hook 模式（SessionStart / Stop）
```

`INDEX.md` 当前包含这些核心区段：
- `Key Conclusions` — Active conclusions，会在 SessionStart 注入
- `Archived Conclusions` — 归档结论，不在启动时注入，但仍可搜索
- `Stage Digests` — phase digest 索引
- `Theme Digests` — topic-level digest 索引
- `Topic Index` — topic → record IDs（支持 `[active]` / `[low]` / `[deprecated → ...]` 后缀）

## 目录解析规则

- `.sybermem/` 是规范目录。
- 如果 `.sybermem/` 已存在，直接使用。
- 如果只有 `ADR/`，首次运行 `/sybermem-init-project`、`/sybermem-record`、`/sybermem-summary`、`/sybermem-digest`、`/sybermem-phase-analyze` 或 `/sybermem-phase-confirm` 时自动重命名为 `.sybermem/`。
- 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，并提示 `ADR/` 被忽略。

## 支持平台

| 平台 | 当前状态 | 说明 |
|------|----------|------|
| Claude Code | fully supported | 插件安装（推荐）或脚本安装（兼容）均已完整 dogfood |
| OpenCode | fully supported | TypeScript plugin 已实现 `session.created` / `session.idle` / `experimental.session.compacting` |
| Gemini CLI | entry files present | `GEMINI.md` 与扩展元数据已提供，但未像 Claude/OpenCode 一样完整 dogfood |
| Cursor | metadata present | `.cursor-plugin/plugin.json` 已存在，运行时行为尚未同等强度验证 |
| Codex | metadata present | `.codex-plugin/plugin.json` 已存在，运行时行为尚未同等强度验证 |
| Kimi | metadata present | `.kimi-plugin/plugin.json` 已存在，运行时行为尚未同等强度验证 |

## 仓库结构

```
.claude-plugin/                       # Claude Code 插件元数据与 marketplace 清单
hooks/                                # Claude Code 插件 hook 声明与 delegator
skills/                               # Plugin-facing skills tree
packages/claude-skills/               # Skills 源码（仓库内分发源，不参与项目自动加载）
├── sybermem-digest/
├── sybermem-init-project/
├── sybermem-link/
├── sybermem-phase-analyze/
├── sybermem-phase-confirm/
├── sybermem-record/
├── sybermem-search/
├── sybermem-summary/
├── sybermem-theme-digest/
├── sybermem-update/
└── using-sybermem/

scripts/                              # 安装、更新与打包校验脚本
├── install-remote.sh / .ps1          # 一行命令远程安装
├── install.sh / .ps1                 # 本地脚本安装
├── update.sh / .ps1                  # 更新已有安装
└── check-plugin-package.py           # 插件分发内容与真实 CLI validate 校验

docs/zh/                              # 中文文档备份
```

## Team MVP（进行中）

SyberMem 正在进入 Team MVP 路线：

- **Phase A**：`sybermem team init` —— 创建 team repo 骨架、写 `team.yaml`、绑定远程 Git
- **Phase B**：`sybermem publish status` —— 必要时先利用现有 digest（或在材料足够时先补 phase digest），再将 `project.md` + Team Project Summary 风格的 `current-status.md` + `meta.json` 发布到 Team repo
- **Phase C**：每次 `publish status` 后自动重建 `dashboards/current-overview.md`，作为团队统一总览入口
- **Phase D**：`publish status` 自动记住团队关联，无需每次传 `--team-path`；`team init` 自动首次提交并推送
- **Phase E**：`sybermem team summary` —— 基于 Team repo 已发布内容生成低成本管理摘要（markdown + json），服务管理 agent 的日常消费
- **Phase F**：发布时同步完整的 phase/theme digest 历史到 Team repo，形成“概括看 status、详细看 digest”的团队工程记忆层
- **Team Skills**：`/sybermem-team-publish` 与 `/sybermem-team-summary` 提供与项目级 slash workflow 一致的 Team 入口

> `sybermem publish status` 是 Team 发布的唯一入口。不要再记多个 team push / bootstrap 命令；系统会在 publish 流程中自动补齐低风险前置条件，并在高影响动作前提示你确认。

后续 `team sync`、`team review`、digest/lesson 发布会在此基础上叠加。

## License

MIT
