**中文** | [English](README.en.md)

# SyberMem

一套 Claude Code / OpenCode 的 Skills 插件，用于追踪项目开发历史。将变更、决策、需求、Bug 记录为结构化文件，让 AI 在不同会话之间保持项目上下文记忆。

## 工作流程

安装 Skills → 在项目中运行 `/init-project` → 完成有意义的工作后运行 `/record`。AI 自动判断记录类型并写入 `.sybermem/` 目录。每次会话开始时，AI 读取 `.sybermem/INDEX.md` 中的关键结论，回忆历史工作上下文。

## 老用户升级说明

如果你的项目以前使用 `ADR/`，只需要升级 Skills，不需要手动改名。首次运行 `/init-project`、`/record` 或 `/summary` 时，会自动把旧的 `ADR/` 迁移为 `.sybermem/`。

如果 `.sybermem/` 和 `ADR/` 同时存在，系统会优先使用 `.sybermem/`，并警告 `ADR/` 已被忽略。

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

### 直接复制到项目

将 `.claude/skills/` 和 `CLAUDE.md`（或 `AGENTS.md`）复制到项目根目录。

详见 [INSTALL.md](INSTALL.md)。

## Skills

| Skill | 功能 |
|-------|------|
| `/init-project` | 在项目中创建 `.sybermem/` 目录结构，扫描现有代码库，生成 `CLAUDE.md` / `AGENTS.md`，并在首次运行时自动迁移旧 `ADR/` |
| `/record` | 从当前会话上下文创建记录，AI 自动判断类型：变更、决策、需求或 Bug，并写入 `.sybermem/` |
| `/summary` | 基于 `.sybermem/` 中已有记录和 git 历史生成周报或月报；旧 `ADR/` 会在首次使用时自动迁移 |

## 在你的项目中会创建什么

```
.sybermem/
├── INDEX.md          # 主索引 — AI 在会话开始时读取关键结论
├── changes/          # 功能变更
├── decisions/        # 技术决策
├── requirements/     # 需求讨论
├── bugs/             # Bug 修复
└── templates/        # 记录模板

CLAUDE.md             # Claude Code 项目指令（工作流规则）
AGENTS.md             # OpenCode 项目指令（内容相同）
```

## 目录解析规则

- `.sybermem/` 是规范目录。
- 如果 `.sybermem/` 已存在，直接使用。
- 如果只有 `ADR/`，首次运行 `/init-project`、`/record` 或 `/summary` 时自动重命名为 `.sybermem/`。
- 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，并提示 `ADR/` 被忽略。

## 支持平台

| 平台 | Skills 位置 | 项目指令文件 |
|------|------------|-------------|
| Claude Code | `~/.claude/skills/` 或 `.claude/skills/` | `CLAUDE.md` |
| OpenCode | `~/.config/opencode/skills/` 或 `.claude/skills/` | `AGENTS.md` |

## 仓库结构

```
.claude/skills/               # Skills（安装的内容）
├── init-project/SKILL.md
├── record/
│   ├── SKILL.md
│   └── templates/
└── summary/SKILL.md

scripts/                       # 安装和更新脚本
├── install-remote.sh / .ps1   # 一行命令远程安装
├── install.sh / .ps1          # 本地安装
└── update.sh / .ps1           # 更新已有安装

docs/zh/                       # 中文文档备份
```

## License

MIT
