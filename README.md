**中文** | [English](README.en.md)

# SyberMem

一套 Claude Code / OpenCode 的 Skills 插件，用于追踪项目开发历史。将变更、决策、需求、Bug 记录为结构化文件，让 AI 在不同会话之间保持项目上下文记忆。

## 工作流程

安装 Skills → 在项目中运行 `/sybermem-init-project` → 完成有意义的工作后运行 `/sybermem-record` → 使用 `/sybermem-summary` 查看动态周报/月报 → 在一个有意义的阶段结束时使用 `/sybermem-digest`，将持久化阶段总结写入 `.sybermem/digests/`。每次会话开始时，AI 读取 `.sybermem/INDEX.md` 中的关键结论，回忆历史工作上下文。

## 推荐升级方式

对于已有项目，推荐直接运行 `/sybermem-update`：

1. 刷新全局安装的 SyberMem skills
2. 在当前项目继续执行 `/sybermem-init-project`
3. 检查是否需要迁移旧 `ADR/`
4. 检查项目里的 `AGENTS.md` / `CLAUDE.md` 是否还是旧版并提示刷新

## 老用户升级说明

如果你的项目以前使用 `ADR/`，不需要手动改名。首次运行 `/sybermem-init-project`、`/sybermem-record`、`/sybermem-summary` 或 `/sybermem-digest` 时，会自动把旧的 `ADR/` 迁移为 `.sybermem/`。

如果 `.sybermem/` 和 `ADR/` 同时存在，系统会优先使用 `.sybermem/`，并警告 `ADR/` 已被忽略。

仅更新全局 skills 不会自动刷新项目里的 `AGENTS.md` / `CLAUDE.md`，所以升级后建议在目标项目里执行 `/sybermem-update`。

仅更新全局 skills 并不会自动为每个项目启用 digest 支持。若要在某个项目中使用 `/sybermem-digest`，请先在该项目里运行 `/sybermem-update`。这一步只会创建缺失的 digest 相关结构，不会悄悄覆盖项目自有文件。

如果老项目里仍保留 `.claude/skills/sybermem-*` 这类项目级副本，Claude 可能会同时加载项目级和全局级 skills，导致 `/` 列表重复显示。若你已经采用全局安装模式，可以删除这些旧副本。

## 安装

### 一行命令安装（需仓库为 public）

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

### 克隆安装

```bash
# macOS / Linux
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem && ./scripts/install.sh

# Windows (PowerShell)
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem; .\scripts\install.ps1
```

### 项目初始化

全局安装完成后，进入你的项目并执行：

```text
/sybermem-init-project
```

这一步会在项目内创建或刷新：
- `.sybermem/`
- `.sybermem/digests/`（阶段 digest 目录）
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
| `/sybermem-summary` | 基于 `.sybermem/` 中已有记录和 git 历史生成周报或月报；旧 `ADR/` 会在首次使用时自动迁移 |
| `/sybermem-digest` | 从已有记录创建可持久保存的阶段摘要，将其写入 `.sybermem/digests/`，并阻止对同一批源记录重复压缩 |
| `/sybermem-update` | 刷新全局安装的 SyberMem skills，然后在当前项目继续执行 `/sybermem-init-project` |

## 在你的项目中会创建什么

```
.sybermem/
├── INDEX.md          # 主索引 — AI 在会话开始时读取关键结论
├── changes/          # 功能变更
├── decisions/        # 技术决策
├── requirements/     # 需求讨论
├── bugs/             # Bug 修复
├── digests/          # 阶段 digest
├── hooks/
│   └── record_change_on_stop.py   # 默认自动 change hook helper
└── templates/        # 记录模板（含 digest 模板）

CLAUDE.md             # Claude Code 项目指令（工作流规则）
AGENTS.md             # OpenCode 项目指令（内容相同）
.claude/settings.json # 项目级 hook 模式和 Stop hook
```

## 目录解析规则

- `.sybermem/` 是规范目录。
- 如果 `.sybermem/` 已存在，直接使用。
- 如果只有 `ADR/`，首次运行 `/sybermem-init-project`、`/sybermem-record`、`/sybermem-summary` 或 `/sybermem-digest` 时自动重命名为 `.sybermem/`。
- 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，并提示 `ADR/` 被忽略。

## 支持平台

| 平台 | 全局 Skills 位置 | 项目级文件 |
|------|------------------|-----------|
| Claude Code | `~/.claude/skills/` | `CLAUDE.md`、`.claude/settings.json`、`.sybermem/` |
| OpenCode | `~/.config/opencode/skills/` | `AGENTS.md`、`.claude/settings.json`、`.sybermem/` |

## 仓库结构

```
packages/claude-skills/               # Skills 源码（仓库内分发源，不参与项目自动加载）
├── sybermem-digest/
├── sybermem-init-project/
├── sybermem-record/
├── sybermem-summary/
└── sybermem-update/

scripts/                              # 安装和更新脚本
├── install-remote.sh / .ps1          # 一行命令远程安装
├── install.sh / .ps1                 # 本地安装
└── update.sh / .ps1                  # 更新已有安装

docs/zh/                              # 中文文档备份
```

## License

MIT
