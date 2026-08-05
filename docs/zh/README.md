# 中文版备份

> 这是面向参考的中文备份文档，不是主入口。主入口请看仓库根目录的 [README.md](../../README.md)。以下内容已对齐 SyberMem v2 当前能力。

## 概览

SyberMem skills 可通过 Claude Code 插件安装（推荐）或脚本安装（兼容）使用；OpenCode 提供独立插件运行时。项目内会创建或刷新 `.sybermem/`、`CLAUDE.md`、`AGENTS.md`、`.claude/settings.json`，默认启用 SyberMem `auto` / `remind` 模式（自动模式只写基于工作区变更的 `change` 记录，其他类型仍用 `/sybermem-record`）。

当前共有 11 个 skill，覆盖记录、检索、关系、阶段分析、digest、theme digest 与诊断：`/sybermem-init-project`、`/sybermem-record`、`/sybermem-summary`、`/sybermem-digest`、`/sybermem-theme-digest`、`/sybermem-phase-analyze`、`/sybermem-phase-confirm`、`/using-sybermem`、`/sybermem-update`、`/sybermem-search`、`/sybermem-link`。

v2 当前已具备的治理能力：

- **Active / Archived Conclusions** — `INDEX.md` 分层，只有 active 结论会在 SessionStart 注入，archived 仍可被 `/sybermem-search` 找到
- **phase lifecycle** — phase-index 的 phase 带 `active` / `completed` / `archived` 状态
- **Topic Index 状态后缀** — `[active]` / `[low]` / `[deprecated → <new-topic>]`
- **`superseded_by`** — 记录可声明被哪条新记录替代；`/sybermem-link old superseded-by new` 会写入字段并把旧结论移到 Archived Conclusions
- **Search / Link / Theme Digest** — 检索、关系治理与跨 phase 主题压缩

旧项目中的 `ADR/` 会在首次运行 `/sybermem-init-project`、`/sybermem-record`、`/sybermem-summary`、`/sybermem-digest`、`/sybermem-phase-analyze` 或 `/sybermem-phase-confirm` 时自动迁移；如果 `.sybermem/` 与 `ADR/` 同时存在，则优先使用 `.sybermem/` 并提示 `ADR/` 已被忽略。仅更新全局 skills 并不会自动为每个项目启用新结构；如需在目标项目中启用，请先在该项目里运行 `/sybermem-update`。

平台支持：Claude Code 与 OpenCode 为 fully supported；Gemini / Cursor / Codex / Kimi 目前是入口文件或 metadata 已提供，运行时尚未同等强度验证。

安装或更新后，可直接运行：

```bash
sybermem project init --register
sybermem index build
sybermem search hooks --scope workspace
```

## 日常工作流

```text
查历史                → /sybermem-search
看现状                → /sybermem-summary
完成有价值工作        → /sybermem-record
phase-index stale     → /sybermem-phase-analyze
阶段收束              → /sybermem-digest
主题跨 phase 收束     → /sybermem-theme-digest <topic>
不确定下一步          → /using-sybermem
```

## 当前项目目录

`/sybermem-init-project` / `/sybermem-update` 会在项目中创建或刷新（节选）：

- `.sybermem/digests/` — 阶段 digest
- `.sybermem/theme-digests/` — 主题 digest（跨多个 phase）
- `.sybermem/analysis/phase-index.md` — 持久化阶段分析（含 lifecycle 字段）
- `.sybermem/hooks/record_change_on_stop.py` — 默认自动 change hook helper
- `.sybermem/hooks/session_start_context.py` — SessionStart 上下文注入脚本
- `.sybermem/hooks/check_project_health.py` — update fast-path 健康检查脚本
- `.sybermem/hooks/launch_record_change_on_stop.py` — root-resolving stop-hook launcher helper
- `.sybermem/templates/theme-digest-template.md` — theme digest 模板
- `INDEX.md` 含 `Key Conclusions` / `Archived Conclusions` / `Phase Digests` / `Theme Digests` / `Topic Index`

## 文件列表

- [CLAUDE.md](CLAUDE.zh.md)
- [AGENTS.md](AGENTS.zh.md)
- [sybermem-init-project SKILL.md](skills/init-project.zh.md)
- [sybermem-record SKILL.md](skills/record.zh.md)
- [sybermem-summary SKILL.md](skills/summary.zh.md)
- [record templates](templates/)
- [category templates](adr-templates/)
