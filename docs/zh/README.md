# 中文版备份

以下是所有注入用户项目文件的中文原版，供参考。

这些文档与主文档保持一致：SyberMem skills 通过全局安装提供；项目内会创建或刷新 `.sybermem/`、`.sybermem/hooks/record_change_on_stop.py`、`CLAUDE.md`、`AGENTS.md`、`.claude/settings.json`。默认的项目级 settings 会启用 SyberMem `auto` / `remind` 模式，其中自动模式只自动写入基于工作区文件变更的 `change` 记录，其他类型仍通过 `/sybermem-record` 创建。旧项目中的 `ADR/` 会在首次运行 `/sybermem-init-project`、`/sybermem-record` 或 `/sybermem-summary` 时自动迁移；如果 `.sybermem/` 与 `ADR/` 同时存在，则优先使用 `.sybermem/` 并提示 `ADR/` 已被忽略。升级全局 skills 后，建议在目标项目里运行 `/sybermem-update` 检查并刷新本地 `AGENTS.md` / `CLAUDE.md`。如果老项目里仍保留 `.claude/skills/sybermem-*` 这类项目级副本，Claude 可能会同时加载项目级和全局级 skills，导致 `/` 列表重复显示；确认已切换到全局安装模式后，可以删除这些旧副本。

## 文件列表

- [CLAUDE.md](CLAUDE.zh.md)
- [AGENTS.md](AGENTS.zh.md)
- [sybermem-init-project SKILL.md](skills/init-project.zh.md)
- [sybermem-record SKILL.md](skills/record.zh.md)
- [sybermem-summary SKILL.md](skills/summary.zh.md)
- [record templates](templates/)
- [category templates](adr-templates/)
