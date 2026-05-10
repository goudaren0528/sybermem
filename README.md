# Sybermem 记忆系统

一个可注入的记忆系统，为 Claude Code 和 OpenCode 提供项目认知能力。

## 核心功能

- **理解项目全貌** - 项目定位、架构、技术栈
- **追溯决策脉络** - 为什么做这个决定、考虑了哪些方案
- **追踪项目进展** - 当前状态、日/周/月进展
- **积累开发经验** - 踩坑经验、最佳实践、调试方法
- **记住特殊处理** - 因业务或历史原因的特殊逻辑
- **了解开发者偏好** - 个人编码风格、工具偏好、价值观
- **全局视角** - 了解参与的所有项目历史和沉淀

## 三层架构

```
sybermem/
├── developer/                   # 开发者层（用户私有）
│   ├── preferences.md           # 个人偏好
│   ├── values.md                # 开发价值观
│   └── experiences/             # 个人经验积累
│
├── PROJECTS/                    # 项目注册中心（用户私有）
│   ├── INDEX.md                 # 所有项目总览
│   └── registered/              # 注册的项目信息
│
├── team/                        # 团队层（团队共享）
│   ├── conventions.md           # 团队约定
│   ├── team-values.md           # 团队价值观
│   └── shared-experiences/      # 共享经验
│
├── templates/                   # 模板文件
├── skills/                      # Skills 脚本
├── hooks/                       # Hooks 配置
└── scripts/                     # 安装/更新脚本
```

## 快速开始

1. Fork 本仓库
2. Clone 到本地
3. 运行安装脚本：`./scripts/install.sh`
4. 配置开发者层：编辑 `developer/preferences.md` 和 `developer/values.md`
5. 在项目中执行 `/init-project` 或 `/adapt-project`

## 目录说明

| 目录 | 用途 | 提交到上游 |
|------|------|-----------|
| `developer/` | 个人偏好、价值观、经验积累 | 否（用户私有） |
| `PROJECTS/` | 注册的项目信息、状态快照 | 否（用户私有） |
| `team/` | 团队约定、共享经验 | 是（团队共享） |
| `templates/` | 各类记录模板 | 是 |
| `skills/` | Skills 脚本 | 是 |
| `hooks/` | Hooks 配置 | 是 |
| `scripts/` | 安装/更新脚本 | 是 |

## 可用 Skills

| Skill | 用途 | 触发方式 |
|-------|------|----------|
| `/init-project` | 新项目注入记忆系统 | 手动调用 |
| `/adapt-project` | 旧项目适配记忆系统 | 手动调用 |
| `/record-adr` | 创建架构决策记录 | 手动/Hook触发 |
| `/record-change` | 创建功能变更记录 | 手动/Hook触发 |
| `/record-experience` | 创建经验记录 | 手动/Hook触发 |
| `/record-special` | 创建特殊处理记录 | 手动/Hook触发 |
| `/record-requirement` | 创建需求讨论记录 | 手动调用 |
| `/update-progress` | 更新项目进展 | 手动/SessionEnd自动 |
| `/update-overview` | 更新项目全貌 | 手动/AI检测触发 |
| `/weekly-summary` | 生成周报 | 手动调用 |
| `/monthly-summary` | 生成月报 | 手动调用 |
| `/optimize-memory` | 执行记忆优化 | 手动/定期触发 |
| `/sync-experience` | 同步经验到团队层 | 手动确认 |

## Hooks

| Hook | 触发时机 | 用途 |
|------|----------|------|
| PostToolUse | Edit/Write/Bash 后 | AI 内部判断是否需要加载记忆 |
| SessionEnd | 会话结束时 | 更新 PROGRESS + 自动生成日报摘要 |
| PreCommit | Git commit 前 | 检查是否有对应 ADR/CHANGELOG 记录 |

## 项目层结构

在各项目中创建 `.sybermem/` 目录：

```
.sybermem/
├── OVERVIEW.md                 # 项目全貌 + 开发约定
├── PROGRESS.md                 # 当前进展追踪
├── ADR/                        # 架构决策记录
│   ├── INDEX.md
│   └── decisions/
├── REQUIREMENTS/               # 需求讨论
├── CHANGELOG/                   # 功能变更
├── EXPERIENCES/                # 经验积累
└── SPECIAL-CASES/              # 项目特异处理
```

## 设计文档

详细设计请参阅 [docs/superpowers/specs/](docs/superpowers/specs/2026-05-09-sybermem-design.md)。

## 贡献

团队层内容（`team/` 目录）通过 PR 同步到上游仓库。

## License

MIT