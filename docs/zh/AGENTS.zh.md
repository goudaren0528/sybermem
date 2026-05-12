# SyberMem 项目记录系统

## 核心规则

每次有意义的工作完成后，执行 `/record` 创建记录。AI 自动判断类型。

## 目录

- `.sybermem/changes/` — 功能变更
- `.sybermem/decisions/` — 技术决策
- `.sybermem/requirements/` — 需求/讨论
- `.sybermem/bugs/` — Bug 修复
- `.sybermem/INDEX.md` — 总索引

## 目录解析

- `.sybermem/` 是规范项目数据目录。
- 如果 `.sybermem/` 已存在，直接使用。
- 如果只有 `ADR/`，首次运行 `/init-project`、`/record` 或 `/summary` 时会自动重命名为 `.sybermem/`。
- 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，并警告 `ADR/` 已被忽略。
- 用户不需要手动重命名旧的 `ADR/` 目录。

## 工作流

1. **会话启动（强制）**：在回应用户第一条消息之前，必须先读取 `.sybermem/INDEX.md` 的关键结论区，获取项目上下文。不要跳过这一步。
2. **工作中（主动关联）**：修改代码前，检查关键结论中是否有与当前工作相关的记录。如有，主动告知用户相关的历史决策或背景，再开始工作。遇到架构、选型、历史原因相关问题时，先检索 `.sybermem/` 目录中的详细记录再回答。
3. **工作后（主动提醒）**：完成功能开发、Bug 修复、技术决策、需求讨论等有意义的工作后，主动询问用户："要创建一条记录吗？我可以执行 /record。"不要等用户记得。
4. 文件命名：`YYYY-MM-DD-NNN-标题.md`

## 可用 Skills

- `/record` — 创建记录（自动判断类型）
- `/init-project` — 初始化 SyberMem 系统
- `/summary` — 生成周报/月报

## 无需记录

格式调整、注释修改、无功能影响的配置微调。
