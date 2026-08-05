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
- 用户手动触发的 `/sybermem-resume` 有界只读续接
- phase digest / theme digest
- 关系与替代（implements / fixes / related / superseded_by）
- 带 source-aware trust 字段的项目内 summary / search / link

### Hub
- project registry
- workspace search
- workspace index 缺失 / 过期时的安全恢复提示
- project status
- portfolio 视图

### Team
- team init
- Team publish preview，review，publish with hash
- team overview
- team management summary
- Team Project Summary
- 完整 phase / theme digest 历史同步

## 平台支持级别

不同平台的集成完整度不同，请按实际支持级别选择：

| 平台 | 支持级别 | 说明 |
|---|---|---|
| **Claude Code** | 完整 | plugin manifest + marketplace + hooks 全 wired，`claude plugins validate` 校验 |
| **OpenCode** | 完整 | 真实 TypeScript runtime（`packages/opencode-plugin/sybermem.ts`），脚本安装 |
| **Gemini** | 入口集成 | `gemini-extension.json` + `GEMINI.md` 入口，未做深度 runtime 验证 |
| **Codex / Cursor / Kimi** | 元数据占位 | 仅有统一 manifest 元数据，暂无平台 runtime hook |

> Codex / Cursor / Kimi 目前是元数据占位，尚未提供各自平台的运行时集成。

## 安装

### 一行式安装（推荐，普通用户）

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

最直观的安装方式，无需 clone 仓库，一条命令刷新 Claude Code / OpenCode skills、OpenCode 插件与 CLI / Core runtime。

### Claude Code 插件安装（开发者 / 本地验证）

```bash
claude --plugin-dir .
```

适合在本地仓库内直接以插件形式加载 hooks 与 skills 做开发或验证。

### OpenCode

OpenCode 也可以通过其插件路径使用。安装说明见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md)。

当前文档化限制仍然成立，OpenCode 没有已文档化的逐次用户提示词自动注入回调，因此不会注册不受支持的 `UserPromptSubmit` 自动注入。OpenCode 侧的显式历史检索以手动 `/sybermem-search` 为主，自动记忆承接只依赖受支持的 compaction 生命周期。

`/sybermem-resume` 在 OpenCode 上同样可手动使用，但它仍是只读续接视图，不会自动执行建议动作，也不会声称存在隐藏 auto-resume、后台执行或不受支持的逐次注入。

### 安装 / 升级顺序

1. 先做全局安装或全局刷新。
   - 脚本安装会刷新 Claude Code skills、OpenCode skills、OpenCode plugin，以及 CLI / Core runtime。
   - 重新运行远程安装命令，就是受支持的全局 runtime 刷新路径。
2. 再进入目标项目执行 `/sybermem-update`。
   - 这一步才会刷新项目本地的 hooks、模板、说明文件和受管设置补丁。
3. 如果项目还没初始化，再运行 `/sybermem-init-project`。

也就是说：先全局，再项目内。旧项目想拿到新行为，只做全局更新不够。

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
- `.sybermem/hooks/task_recall.py`
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json`

其中：
- `auto` = 轻量 `change` trail + 提醒
- `remind` = 只提醒，不自动写 `change` trail
- Claude 的默认 `UserPromptSubmit` hook 同时负责自然语言记录意图捕获与只读 task recall
- 如果项目已有自定义 `.claude/settings.json`，只会对可识别的 SyberMem 管理项做外科式补丁，不会覆盖无关的自定义 hooks、env 或说明

## 日常使用

### 项目 owner
- `/sybermem-resume` — 用自然语言拿到有边界的只读续接视图，返回当前状态、风险和建议下一步
- `/sybermem-record` — 完成一轮有价值工作后记录
- `/sybermem-summary` — 查看当前项目状态
- `/sybermem-digest` — 在阶段稳定后沉淀阶段摘要
- `/sybermem-theme-digest` — 在主题跨阶段稳定后沉淀主题摘要
- `/sybermem-team-publish` — 先预览，再审核，再用 preview hash 发布到 Team memory

### 管理者 / 管理 agent
- `/sybermem-team-summary` — 生成 Team 管理摘要
- 直接阅读 `dashboards/current-overview.md` / `latest-management-summary.md`

### 不确定下一步时
- `/sybermem-resume` — 先拿到只读续接视图，再决定是否继续执行下一步
- `/using-sybermem` — 检查当前项目状态，并获得推荐命令

## 命令 vs Skill 编排

SyberMem 的能力分两类执行路径，可靠性不同，使用时请区分：

| 类别 | 能力 | 执行方式 | 特性 |
|---|---|---|---|
| **CLI 命令**（程序校验） | `sybermem resume` / `search` / `project status` / `portfolio` / `team init` / `team summary` / `publish status` | 由 `sybermem` CLI + core 直接执行 | 确定性、可脚本化、结果稳定 |
| **Skill 编排**（AI 执行） | `/sybermem-record` / `/sybermem-link` / `/sybermem-digest` / `/sybermem-theme-digest` / `/sybermem-phase-analyze` / `/sybermem-phase-confirm` | 由 AI 按 skill 指令编辑 `.sybermem/` markdown | 依赖 AI 判断，非确定性命令 |

- `sybermem resume` 现在提供**程序化**续接（`--mode fast|standard|deep`、`--format text|json`），与自然语言的 `/sybermem-resume` skill 并存。
- record / link / digest 等属于 Skill 编排：它们没有对应的 CLI 命令，是让 AI 依据 skill 指令直接编辑 markdown 记录，因此可靠性取决于 AI 是否正确遵循 skill。


## Resume 与信任说明

`/sybermem-resume` 是自然语言优先的续接入口，适合“继续这个项目”、“我刚刚做到哪了”、“下一步最安全是什么”这类请求。

- `fast`：给短版续接，只显示当前 phase、最近进展、主要风险、建议下一步和原因
- `standard`：默认续接，补充当前 digest 覆盖或最关键未决问题这类信任信息
- `deep`：仍然是有边界的续接，只额外指出应该继续读哪些 records 或 digests，不会自动展开整段历史

续接结果应明确展示：current phase、recent progress、risks、next action、confidence、freshness、reason。

`/sybermem-resume` 只读，不会自动执行建议动作，也不会写 record、digest 或设置。信任字段会尽量说明信息来自当前 authoritative record、digest，还是仅作为辅助证据的历史材料。它使用现有的 resume / status / search / next-step 路径，不会创建第二套 memory store。

当你需要显式历史证据时，运行 `/sybermem-search`。项目内搜索和 workspace search 都会尽量标明 authority、lifecycle、freshness、successor guidance。workspace search 依赖 `sybermem index build` 生成的索引；如果索引缺失、schema 过期或 FTS 不可用，系统会给出安全恢复提示或降级路径，而不是伪造结果。

## Team workflow

当前 Team workflow 的推荐使用路径是：

1. 项目内记录 / digest
2. `/sybermem-team-publish` 先生成只读 preview
3. review preview 的 source revision、source hash、freshness、conflicts、review-required
4. 使用 preview hash 发布到 Team repo
5. 自动更新 `dashboards/current-overview.md`
6. `/sybermem-team-summary` 生成管理摘要
7. 需要时下钻到完整 digest 历史

也就是：

```text
概括看 status
详细看 digest
```

### Team 当前支持
- **Phase A**：`sybermem team init` —— 创建 Team repo 骨架、写 `team.yaml`、绑定远程 Git
- **Phase B**：`sybermem publish status --preview --format json` —— 生成只读 preview，供发布前 review
- **Phase C**：`sybermem publish status --preview-source-hash <source_hash> --format json` —— 使用刚审核过的 preview hash 执行真实发布
- **Phase D**：每次 `publish status` 后自动重建 `dashboards/current-overview.md`
- **Phase E**：`publish status` 自动记住 Team 关联，无需每次传 `--team-path`
- **Phase F**：`sybermem team summary` —— 生成低成本管理摘要（markdown + json）
- **Phase G**：同步完整 phase / theme digest 历史到 Team repo
- **Team Skills**：`/sybermem-team-publish` 与 `/sybermem-team-summary`

> Team publish 的安全路径是 preview → review → publish with hash。preview 是只读视图，不会写 Team repo；真正发布时如果返回 `stale_preview`，必须先重新预览，不能重用旧 hash。

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

## 卸载

SyberMem 的卸载分为两层：

### 项目级卸载（保留历史，停用运行时接管）

```text
sybermem project uninstall
```

- 保留 `.sybermem/` 历史内容
- 只移除 `.claude/settings.json` 中的 SyberMem hooks / env
- 只移除 `CLAUDE.md` / `AGENTS.md` 中的 SyberMem 协议块
- 用户原有内容不受破坏
- 之后可重新运行 `/sybermem-update` 恢复

### 全局卸载（删除全局能力，不碰项目历史）

```bash
# Windows (PowerShell)
.\scripts\uninstall.ps1

# macOS / Linux
./scripts/uninstall.sh
```

- 删除全局 skills / CLI / launcher / OpenCode plugin
- 不删除任何项目里的 `.sybermem/` 历史

## 兼容说明

- `.sybermem/` 是规范目录
- 如果项目里仍是旧的 `ADR/`，首次运行相关命令时会自动迁移为 `.sybermem/`
- Claude 项目里的 `UserPromptSubmit` 修复只适用于受管 Claude hooks，OpenCode 不支持也不会声称支持同类逐次注入
- 更多升级与兼容细节见 `INSTALL.md`

## License

MIT
