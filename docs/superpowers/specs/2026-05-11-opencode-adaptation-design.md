# OpenCode 适配设计

## 背景

ADR 记录系统当前只支持 Claude Code。用户需要在 OpenCode 中也使用同样的 3 个 skill（`/init-project`、`/record`、`/summary`）。

## 关键发现

OpenCode 原生兼容 Claude Code 的 skill 体系：

| 层级 | OpenCode 搜索路径 |
|------|-------------------|
| 项目级 | `.opencode/skills/`、`.claude/skills/`、`.agents/skills/` |
| 用户级 | `~/.config/opencode/skills/`、`~/.claude/skills/`、`~/.agents/skills/` |

- SKILL.md 格式完全相同
- 项目指令文件为 `AGENTS.md`，不存在时回退到 `CLAUDE.md`

## 设计决策

**不做 `core/` 抽象层，不做双份 skill 文件。**

因为 OpenCode 直接读取 `.claude/skills/`，两个平台共用同一份 skill 定义即可。

## 变更清单

### 新建文件

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | OpenCode 项目指令，内容与 CLAUDE.md 一致 |
| `scripts/install.ps1` | Windows PowerShell 安装脚本 |
| `scripts/update.ps1` | Windows PowerShell 更新脚本 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `scripts/install.sh` | 增加复制到 `~/.config/opencode/skills/` |
| `scripts/update.sh` | 增加同步到 `~/.config/opencode/skills/` |
| `README.md` | 加 OpenCode 说明，双平台结构 |
| `INSTALL.md` | 加 OpenCode 安装步骤 |

### 不变文件

| 文件 | 原因 |
|------|------|
| `.claude/skills/*/SKILL.md` | OpenCode 直接读取，无需改动 |
| `.claude/settings.local.json` | Claude 专属 hook，OpenCode 不需要 |
| `ADR/` | 平台无关，不动 |
| `CLAUDE.md` | Claude Code 继续使用 |

## AGENTS.md 内容

与 CLAUDE.md 相同，仅标题调整：

```markdown
# ADR 记录系统

## 核心规则
每次有意义的工作完成后，执行 /record 创建记录。AI 自动判断类型。

## 目录
- ADR/changes/ — 功能变更
- ADR/decisions/ — 技术决策
- ADR/requirements/ — 需求/讨论
- ADR/bugs/ — Bug 修复
- ADR/INDEX.md — 总索引

## 工作流
1. 开始前：读 ADR/INDEX.md
2. 工作后：执行 /record
3. 文件命名：YYYY-MM-DD-NNN-标题.md

## 可用 Skills
- /record — 创建记录（自动判断类型）
- /init-project — 初始化 ADR 系统
- /summary — 生成周报/月报

## 无需记录
格式调整、注释修改、无功能影响的配置微调。
```

## 安装脚本逻辑

### install.sh / install.ps1

```
1. 检测 ~/.claude/skills/ → 复制 3 个 skill
2. 检测 ~/.config/opencode/skills/ → 复制 3 个 skill
3. 输出安装结果
```

### update.sh / update.ps1

```
1. 同步 ~/.claude/skills/ 中的 3 个 skill
2. 同步 ~/.config/opencode/skills/ 中的 3 个 skill
3. 输出更新结果
```

## 最终仓库结构

```
adr-project/
├── .claude/
│   ├── skills/
│   │   ├── init-project/SKILL.md
│   │   ├── record/
│   │   │   ├── SKILL.md
│   │   │   └── templates/ (4 files)
│   │   └── summary/SKILL.md
│   └── settings.local.json
├── ADR/
│   ├── INDEX.md
│   ├── changes/ decisions/ requirements/ bugs/
│   └── templates/ (4 files)
├── scripts/
│   ├── install.sh
│   ├── install.ps1
│   ├── update.sh
│   └── update.ps1
├── docs/superpowers/specs/
├── CLAUDE.md
├── AGENTS.md
├── README.md
└── INSTALL.md
```
