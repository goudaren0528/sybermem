**中文** | [English](README.en.md)

# SyberMem

SyberMem 是一个面向 AI 工作流的项目 / 团队工程记忆系统。

它帮助你把：
- 项目进展
- 技术决策
- 阶段性沉淀
- 团队摘要

保存成结构化记忆，让项目 owner、管理者与管理 agent 可以在不同会话中持续消费这些内容。

## 当前能力

### Project
- 结构化 records（change / decision / requirement / bug）
- 持久化 phase index
- phase digest / theme digest
- 关系与替代（implements / fixes / related / superseded_by）
- 项目内 summary / search / link

### Hub
- project registry
- workspace search
- project status
- portfolio 视图

### Team
- team init
- team publish
- team overview
- team management summary
- Team Project Summary
- 完整 phase / theme digest 历史同步

## 安装

### Claude Code 插件安装（推荐）

```bash
claude --plugin-dir .
```

适合希望通过插件统一加载 hooks 与 skills 的 Claude Code 用户。

### Claude Code / OpenCode 脚本安装（兼容模式）

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

### OpenCode

OpenCode 也可以通过其插件路径使用。安装说明见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md)。

## 初始化项目

进入项目目录后，运行：

```text
/sybermem-init-project
```

这一步会创建或刷新：
- `.sybermem/`
- `.sybermem/digests/`
- `.sybermem/theme-digests/`
- `.sybermem/analysis/phase-index.md`
- `.sybermem/project.yaml`
- `.sybermem/hooks/record_change_on_stop.py`
- `.sybermem/hooks/detect_record_intent.py`
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json`

其中：
- `auto` = 轻量 `change` trail + 提醒
- `remind` = 只提醒，不自动写 `change` trail

## 日常使用

### 项目 owner
- `/sybermem-record` — 完成一轮有价值工作后记录
- `/sybermem-summary` — 查看当前项目状态
- `/sybermem-digest` — 在阶段稳定后沉淀阶段摘要
- `/sybermem-theme-digest` — 在主题跨阶段稳定后沉淀主题摘要
- `/sybermem-team-publish` — 将当前项目同步到 Team memory

### 管理者 / 管理 agent
- `/sybermem-team-summary` — 生成 Team 管理摘要
- 直接阅读 `dashboards/current-overview.md` / `latest-management-summary.md`

### 不确定下一步时
- `/using-sybermem` — 检查当前项目状态，并获得推荐命令

## Team workflow

当前 Team workflow 的推荐使用路径是：

1. 项目内记录 / digest
2. `/sybermem-team-publish` 同步到 Team repo
3. 自动更新 `dashboards/current-overview.md`
4. `/sybermem-team-summary` 生成管理摘要
5. 需要时下钻到完整 digest 历史

也就是：

```text
概括看 status
详细看 digest
```

### Team 当前支持
- **Phase A**：`sybermem team init` —— 创建 Team repo 骨架、写 `team.yaml`、绑定远程 Git
- **Phase B**：`sybermem publish status` —— 发布 `project.md` + Team Project Summary 风格的 `current-status.md` + `meta.json`
- **Phase C**：每次 `publish status` 后自动重建 `dashboards/current-overview.md`
- **Phase D**：`publish status` 自动记住 Team 关联，无需每次传 `--team-path`
- **Phase E**：`sybermem team summary` —— 生成低成本管理摘要（markdown + json）
- **Phase F**：同步完整 phase / theme digest 历史到 Team repo
- **Team Skills**：`/sybermem-team-publish` 与 `/sybermem-team-summary`

> `sybermem publish status` 是 Team 发布的唯一入口。不要再记多个 team push / bootstrap 命令；系统会在 publish 流程中自动补齐低风险前置条件，并在高影响动作前提示你确认。

## 模式与提醒

- `auto` = 自动轻量 `change` trail + 提醒
- `remind` = 只提醒，不自动写 `change` trail
- 如果你明确说“这轮结束提醒我记录”，系统会记录这一轮的记录意图，并在合适时机提醒你运行 `/sybermem-record`

## 工作流路由

SyberMem 现在会优先按下面的顺序推荐下一步动作：

```text
record > digest > team-publish
```

这样可以减少你在一轮工作完成后犹豫“先 record、digest 还是 publish”的摩擦。

## 仓库结构

```text
.claude-plugin/                      # Claude Code 插件元数据与 marketplace 清单
hooks/                               # Claude Code 插件 hook 声明与 delegator
skills/                              # Plugin-facing skills tree
packages/claude-skills/              # Skills 源码（仓库内分发源）
packages/core/                       # Core memory / Team publication logic
packages/cli/                        # sybermem CLI
scripts/                             # 安装、更新与打包校验脚本
```

## 兼容说明

- `.sybermem/` 是规范目录
- 如果项目里仍是旧的 `ADR/`，首次运行相关命令时会自动迁移为 `.sybermem/`
- 更多升级与兼容细节见 `INSTALL.md`

## 更多文档

- [INSTALL.md](INSTALL.md)
- [`docs/superpowers/specs/`](docs/superpowers/specs/)
- [`docs/zh/`](docs/zh/)

## License

MIT
