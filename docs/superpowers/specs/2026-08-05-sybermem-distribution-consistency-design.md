# SyberMem 分发一致性方案（批次 D）

**Date:** 2026-08-05
**Status:** Proposed
**Scope:** 平台 manifest schema 统一 / skill 漂移预防 / 非核心平台声明降级
**Source:** docs/audit/2026-08-05-sybermem-comprehensive-audit.md §4（复核属实）

## 1. 背景与问题

审计 §4 复核确认：

1. **manifest schema 不统一**：Claude 用 object author + 全字段（homepage/repository/license/keywords）；Gemini 用 string author + 部分字段 + nested metadata；Codex/Cursor/Kimi 仅 4 个字段（name/description/version/author-string），缺 homepage/repository/license/keywords。
2. **skill 双份易漂移**：`packages/claude-skills`（source of truth）→ `skills`（plugin-facing）靠 `sync-plugin-skills.py` 单向手动同步；`check-plugin-package.py` 有静态 parity 校验兜底，但 release/CI 未自动跑 sync，改源忘 sync 是 footgun。
3. **非核心平台声明偏高**：Codex/Cursor/Kimi 只有 stub manifest 无 runtime，Gemini 仅入口描述符，但文档未足够清晰地标注它们的支持级别。

## 2. 设计目标

用最小、确定性的改动统一元数据、预防漂移、诚实声明支持级别，不破坏任何平台的既有校验。

1. 统一 Codex/Cursor/Kimi 的 manifest 元数据字段，与 Claude/Gemini 对齐（description/author 结构/homepage/repository/license/keywords）。
2. 在 CI 的 package job 里加入 skill sync 校验（drift 即失败），并让 `check-plugin-package.py` 的 parity 校验成为 CI gate。
3. 在 README/README.en 明确各平台支持级别（Claude/OpenCode 完整；Gemini 入口；Codex/Cursor/Kimi 元数据占位）。

## 3. 设计边界

### 保留
- **Claude plugin.json / marketplace.json 不动**：它们通过 `claude plugins validate`，schema 有官方约束，改动有破坏风险。
- Gemini extension 的 nested metadata（其官方规范需要）。
- `sync-plugin-skills.py` 的单向方向（`packages/claude-skills → skills`）。
- version 字段由 `sync-version.py` 单源管理（不在本方案手改）。

### 不引入
- 为 Codex/Cursor/Kimi 补真实 runtime hook（那是「补全平台」的大范围工作，非本方案；本方案只统一元数据 + 诚实声明）。
- 破坏任何平台 manifest schema 的字段。
- 改变 skill 源与镜像的方向或结构。

## 4. 方案

### 4.1 统一 Codex/Cursor/Kimi manifest 元数据

把三者从 4 字段 stub 补齐到与 Claude 一致的元数据形态：
- `description`：统一为与 Claude 一致的完整描述。
- `author`：改为 object 形式 `{"name": "goudaren0528"}`（与 Claude 一致）。
- 新增 `homepage` / `repository` / `license` / `keywords`。
- `version` 保持 `0.1.0`（由 sync-version 管理）。

> 风险控制：这三个平台的 manifest 目前无对应 runtime、无平台侧 schema 校验（check-plugin-package 只验「文件存在 + JSON 可解析」），补充标准元数据字段是纯增量，不会破坏任何东西。

### 4.2 skill 漂移预防（CI gate）

- CI 的 `package` job 已跑 `check-plugin-package.py`，其中 `check_skill_tree_parity` 会在 `packages/claude-skills` 与 `skills` 不一致时 fail。
- 增强：在 package job 里，先跑 `python scripts/sync-plugin-skills.py`，再跑 `git diff --exit-code -- skills/`（若 sync 产生了改动说明源与镜像漂移了 → CI 失败提示先 sync）。这把「忘记 sync」从运行时 footgun 变成 CI 硬门。
- 本地：CONTRIBUTING 已写 sync 规则，无需改。

### 4.3 非核心平台声明降级

在 README.md / README.en.md 的安装/平台章节，明确标注支持级别矩阵：
- **完整支持**（runtime + validation）：Claude Code、OpenCode
- **入口集成**：Gemini（`gemini-extension.json` + `GEMINI.md` 入口）
- **元数据占位**（manifest only，暂无 runtime）：Codex、Cursor、Kimi

不夸大后三者为「已支持平台」。

## 5. 验收标准

1. Codex/Cursor/Kimi 三个 manifest 有统一的完整元数据字段，且都是合法 JSON。
2. `check-plugin-package.py` 仍 `OK`（含 version 一致性 + skill parity + claude validate）。
3. `sync-version.py` 对新字段的 manifest 仍幂等（version 行仍被正确识别）。
4. CI 的 package job 含 skill-sync drift gate（sync 后 `git diff --exit-code skills/` 干净）。
5. README/README.en 有清晰的平台支持级别矩阵。
6. `pytest packages/core packages/cli` 全绿（分发改动不应影响测试）。

## 6. 明确不做

- 不为 Codex/Cursor/Kimi 补 runtime hook（独立的「平台补全」工作）。
- 不动 Claude/Gemini manifest 的 schema 结构。
