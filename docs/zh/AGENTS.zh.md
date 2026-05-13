# SyberMem 项目记录系统

## 核心规则

每次有意义的工作完成后，执行 `/sybermem-record` 创建记录。AI 自动判断类型。

## 目录

- `.sybermem/changes/` — 功能变更
- `.sybermem/decisions/` — 技术决策
- `.sybermem/requirements/` — 需求/讨论
- `.sybermem/bugs/` — Bug 修复
- `.sybermem/INDEX.md` — 总索引

## 目录解析

- `.sybermem/` 是规范项目数据目录。
- 如果 `.sybermem/` 已存在，直接使用。
- 如果只有 `ADR/`，首次运行 `/sybermem-init-project`、`/sybermem-record` 或 `/sybermem-summary` 时会自动重命名为 `.sybermem/`。
- 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，并警告 `ADR/` 已被忽略。
- 用户不需要手动重命名旧的 `ADR/` 目录。

## 工作流

1. **会话启动（强制）**：在回应用户第一条消息之前，必须先读取 `.sybermem/INDEX.md` 的关键结论区，获取项目上下文。不要跳过这一步。
2. **工作中（主动关联）**：修改代码前，检查关键结论中是否有与当前工作相关的记录。如有，主动告知用户相关的历史决策或背景，再开始工作。遇到架构、选型、历史原因相关问题时，先检索 `.sybermem/` 目录中的详细记录再回答。
3. **工作后（auto/remind 模式）**：项目可以在有意义的工作完成后，基于当前工作区文件变更自动创建一条基础的 SyberMem `change` 记录，或者提醒用户进行记录。模式由 `.claude/settings.json` 中的 `SYBERMEM_RECORD_MODE` 控制。
4. **记录类型范围**：自动模式只会基于工作区文件变更写入 `change` 记录。`decision`、`requirement`、`bug` 仍请使用 `/sybermem-record`。
5. **模式切换**：支持 `auto` 和 `remind` 两种模式。可通过 `/hooks` 或直接编辑 `.claude/settings.json` 修改。默认 hook helper 位于 `.sybermem/hooks/record_change_on_stop.py`。
6. 文件命名：`YYYY-MM-DD-NNN-标题.md`

## 可用 Skills

- `/sybermem-record` — 创建记录（自动判断类型）
- `/sybermem-init-project` — 初始化或刷新当前项目的 SyberMem 配置
- `/sybermem-summary` — 生成周报/月报
- `/sybermem-update` — 更新全局 Skills 并重新检查当前项目

## 无需记录

格式调整、注释修改、无功能影响的配置微调。
