# SyberMem CLI/Skill 双轨对齐方案

**Date:** 2026-08-05
**Status:** Proposed
**Scope:** Project 作用域的 CLI 命令面 / Skill 执行路径 / 检索静默失败
**Source:** docs/audit/2026-08-05-sybermem-comprehensive-audit.md §1（已复核属实）

## 1. 背景与问题

审计 §1 已复核确认三个真实问题：

1. **`resume` 悬空**：`packages/core/sybermem_core/resume.py` 的 `build_resume_checkpoint(project_root, mode)` 已完整实现 fast/standard/deep 三档，但唯一调用方是 `tests/test_resume.py`。CLI、hooks、OpenCode 插件、`sybermem-resume` skill 均不调用它。用户拿不到程序化 resume。
2. **双轨制不透明**：`search / status / portfolio / team-* / publish` 走 CLI + core（程序校验）；`record / link / digest / theme-digest / resume / phase-*` 是纯 Skill-driven（LLM 编辑 markdown，无程序保障）。README 把两者都呈现为「命令」，用户无法区分可靠性等级。
3. **检索静默失败**：`search_project()` 在 `resolve_project_root()` 返回 `None` 时直接 `return []`（search.py:169/209/215），无任何用户可见提示，与「无匹配结果」不可区分。

## 2. 设计目标

- 让已实现的 `resume` 能力通过 CLI 被真实调用，消除悬空浪费。
- 让 record/link/digest 的「skill-driven」本质在文档中透明，用户能判断可靠性。
- 让检索的「找不到项目根」从静默 `[]` 变成显式、可诊断的结果。

## 3. 设计边界

### 保留
- `.sybermem/` Markdown 作为 Project canonical source。
- record/link/digest/theme-digest/phase-* 继续是 Skill-driven（本方案**不**把它们下沉为 core 写入器 —— 那是更大范围的独立决策，见 §6）。
- 现有全部 CLI 命令签名与 `--format text|json` 契约。
- `build_resume_checkpoint` 现有返回结构与只读语义（不新增写行为）。

### 不引入
- 新的记忆存储或 current-state 文件。
- record/link/digest 的 core 写入器（超出本方案范围）。
- 对 resume 返回结构的破坏性改动。

## 4. 方案

### 4.1 暴露 `sybermem resume` CLI 命令（核心）

新增顶层子命令，直接包装既有 `build_resume_checkpoint`：

```
sybermem resume [--mode fast|standard|deep] [--format text|json]
```

- `cmd_resume` 调 `resolve_project_root()`；`None` 时向 stderr 打印显式提示并返回 1（与其它命令一致）。
- 调 `build_resume_checkpoint(root, mode=args.mode)`。
- `--format json` 直接 `dump_json(checkpoint)`。
- `--format text` 渲染：current phase / recent progress / risks / next action / confidence / freshness / reason（复用 checkpoint 已有字段）。
- 只读，绝不写任何项目记忆 —— 与 resume.py 现有语义一致。

**选择理由**：`build_resume_checkpoint` 已实现且被测试覆盖，接 CLI 是纯 wiring，零核心逻辑风险，性价比最高。

### 4.2 检索静默失败改为显式诊断

`search_project()` 在 root 为 None 时，不再静默 `return []`，而是抛出一个可被 CLI 捕获的显式信号。为保持向后兼容与最小改动：

- 引入 `ProjectRootNotFoundError`（或复用现有异常族），在 `search_project` 入口 root 为 None 时抛出。
- `cmd_search`（project scope）捕获该异常，向 stderr 打印「No SyberMem project root found.」并返回 1，与 `cmd_project_status` 行为一致。
- `compact_project_search`（hook 热路径调用）**保留返回 `[]` 的容错**——hook 不能因无项目根而报错。通过参数区分：CLI 路径要显式错误，hook 路径要静默降级。

> 关键约束：`compact_project_search` 被 `task_recall.py` 每 prompt 调用，**绝不能**在无项目根时抛错破坏 hook。因此显式失败只作用于 CLI 的 `search_project` 直接入口，hook 用的 compact 变体维持静默降级。

### 4.3 双轨契约文档化

在 README.md（及 README.en.md）新增一节「命令 vs Skill 编排」，明确：

| 类别 | 能力 | 可靠性 |
|---|---|---|
| CLI 命令（程序校验） | search / status / portfolio / resume / team-* / publish | 确定性、可脚本化 |
| Skill 编排（LLM 执行） | record / link / digest / theme-digest / phase-* | 依赖 AI 按 skill 指令编辑 markdown |

不夸大 skill-driven 能力为「命令」，让用户知道哪些可脚本化、哪些依赖 AI 判断。

## 5. 验收标准

1. `sybermem resume --format json` 在本项目返回合法 checkpoint JSON；`--mode standard/deep` 各返回对应档位。
2. `sybermem resume`（text）打印 phase/progress/risks/next-action/confidence/freshness/reason。
3. 无项目根时 `sybermem resume` 和 `sybermem search`（project scope）返回码 1 + stderr 提示，不再静默空结果。
4. `task_recall.py` hook 在无项目根时仍静默不报错（回归保护）。
5. `pytest packages/core packages/cli` 全绿；新增 resume CLI 测试。
6. README/README.en 有「命令 vs Skill 编排」区分表。

## 6. 明确排除（留待独立决策）

- 把 record/link/digest/theme-digest 下沉为 core 写入器 + CLI —— 这是「双轨合一」的大改造，涉及记忆写入协议，风险与范围远超本方案，需单独 spec 评估。本方案只做「让 resume 可用 + 让双轨透明 + 修静默失败」这三件低风险、高确定性的事。
