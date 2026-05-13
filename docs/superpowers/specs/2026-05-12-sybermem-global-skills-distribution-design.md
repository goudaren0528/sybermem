# SyberMem 全局 Skills 分发设计

## 背景

当前仓库同时存在两类 SyberMem skill 来源：

- 用户级全局安装：`~/.claude/skills/sybermem-*`
- 仓库内项目级副本：`<repo>/.claude/skills/sybermem-*`

Claude Code 会同时扫描用户级与项目级 skills。这样一来，只要打开 SyberMem 仓库本身，或打开任何包含项目级 SyberMem skill 副本的项目，就会在 `/` skill 列表中看到重复项。

用户希望采用更清晰、稳定的分层：

- skill 只保留一份全局安装
- 新项目只生成项目级 `CLAUDE.md`、`AGENTS.md` 和 `.sybermem/`
- 仓库继续作为 SyberMem 的分发源码仓库，但不再作为 Claude 自动加载的项目级 skill 容器

## 目标

1. 消除 SyberMem 仓库自身的重复 skill 显示问题。
2. 确保新项目不会因为安装或初始化流程获得项目级 skill 副本。
3. 保留当前的一键安装和更新体验。
4. 明确区分全局层、项目层、仓库源码层的职责。

## 非目标

- 不拆成多个仓库。
- 不引入新的发布系统或包管理流程。
- 不自动删除用户项目中的历史 `.claude/skills/sybermem-*` 副本。
- 不改变 `.sybermem/`、`CLAUDE.md`、`AGENTS.md` 的项目级职责。

## 设计决策

### 1. 将 skill 源码移出 `.claude/skills/`

SyberMem 仓库不再把 skill 源码放在会被 Claude 自动扫描的 `.claude/skills/` 目录下。

新的源码目录使用非自动加载路径，例如：

```text
packages/claude-skills/
```

目录结构示例：

```text
packages/claude-skills/
├── sybermem-init-project/
│   ├── SKILL.md
│   └── project-files/
│       ├── CLAUDE.md
│       └── AGENTS.md
├── sybermem-record/
│   ├── SKILL.md
│   └── templates/
├── sybermem-summary/
│   └── SKILL.md
└── sybermem-update/
    └── SKILL.md
```

这样 Claude 打开本仓库时不会再把这些源码目录当作项目级可加载 skill。

### 2. 全局层与项目层职责固定

#### 全局层

全局层只负责提供可调用的 skills：

- `~/.claude/skills/sybermem-*`
- `~/.config/opencode/skills/sybermem-*`

这些内容由安装脚本和更新脚本复制过去。

#### 项目层

项目层只负责承载项目上下文和记录：

- `<project>/.sybermem/`
- `<project>/CLAUDE.md`
- `<project>/AGENTS.md`

`/sybermem-init-project` 与 `/sybermem-update` 只能创建、刷新或迁移这些项目级内容，不能在项目里再创建 `.claude/skills/sybermem-*`。

### 3. 安装脚本改为从源码目录分发到全局目录

下列脚本统一从 `packages/claude-skills/` 读取 skill 源码：

- `scripts/install.sh`
- `scripts/install.ps1`
- `scripts/install-remote.sh`
- `scripts/install-remote.ps1`
- `scripts/update.sh`
- `scripts/update.ps1`

它们继续复制到：

- Claude Code：`~/.claude/skills`
- OpenCode：`~/.config/opencode/skills`

但不再依赖仓库内 `.claude/skills/`。

### 4. 保留项目初始化体验，但不再产生项目级 skill

标准使用路径固定为两步：

1. 全局安装或更新 SyberMem skills
2. 进入目标项目执行 `/sybermem-init-project` 或 `/sybermem-update`

效果如下：

- 第一步解决“这台机器是否具备 SyberMem 能力”
- 第二步解决“当前项目是否启用 SyberMem，以及项目规则文件是否齐全”

这样用户在任何新项目中都只会得到项目级 `.sybermem/`、`CLAUDE.md`、`AGENTS.md`，不会得到第二份项目内 skills。

### 5. 历史遗留副本只提示，不自动删除

对于已经存在的项目内旧副本：

```text
.claude/skills/sybermem-init-project
.claude/skills/sybermem-record
.claude/skills/sybermem-summary
.claude/skills/sybermem-update
```

安装或更新流程可以输出明确提示：

- 这些目录是旧的项目级 SyberMem skill 副本
- 它们会导致和全局 skill 重复显示
- 若你已采用全局安装模式，可以安全删除它们

但脚本不自动删除这些目录，避免误删用户项目中的自定义内容或非标准改造。

## 需要修改的内容

### 目录结构

- 删除仓库作为运行态来源的 `.claude/skills/sybermem-*`
- 新增 `packages/claude-skills/sybermem-*`
- 如果仓库还有其他必须保留的 `.claude` 配置，仅保留非 skill 自动加载内容

### 脚本

- `scripts/install.sh`
- `scripts/install.ps1`
- `scripts/install-remote.sh`
- `scripts/install-remote.ps1`
- `scripts/update.sh`
- `scripts/update.ps1`

统一修改为从 `packages/claude-skills/` 复制 skill。

### 文档

- `README.md`
- `README.en.md`
- `INSTALL.md`
- 相关中文文档（如需要同步）

统一说明：

- skills 是全局安装
- `.sybermem/`、`CLAUDE.md`、`AGENTS.md` 是项目级内容
- 新项目不会安装项目内 skills
- 老项目如果存在 `.claude/skills/sybermem-*`，可能导致重复显示，建议迁移到纯全局模式

## 最终结构

```text
sybermem-repo/
├── packages/
│   └── claude-skills/
│       ├── sybermem-init-project/
│       ├── sybermem-record/
│       ├── sybermem-summary/
│       └── sybermem-update/
├── scripts/
│   ├── install.sh
│   ├── install.ps1
│   ├── install-remote.sh
│   ├── install-remote.ps1
│   ├── update.sh
│   └── update.ps1
├── docs/
├── CLAUDE.md
├── AGENTS.md
└── .sybermem/
```

## 成功标准

完成后应满足以下条件：

1. 打开 SyberMem 仓库本身时，不再出现重复的 SyberMem skill。
2. 运行安装脚本后，skills 只出现在用户级全局目录中。
3. 新项目执行 `/sybermem-init-project` 后，只生成：
   - `.sybermem/`
   - `CLAUDE.md`
   - `AGENTS.md`
4. 文档中清楚区分“全局 skill 安装”和“项目级初始化”两个动作。
5. 对历史项目内 skill 副本给出迁移说明，但不做高风险自动删除。

## 推荐实施顺序

1. 新建 `packages/claude-skills/` 并迁移现有 SyberMem skills
2. 修改安装和更新脚本的复制源目录
3. 更新 README / INSTALL / 相关中文文档
4. 删除仓库中会被自动加载的 `.claude/skills/sybermem-*`
5. 手动验证：
   - 打开本仓库时 skill 列表无重复
   - 全局安装后新项目只生成项目级内容
