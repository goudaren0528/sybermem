# SyberMem 体验改进方案：术语统一与安装文档纠正（批次 E）

**Date:** 2026-08-05
**Status:** Proposed
**Scope:** 术语一致性（Stage Digest vs phase digest）/ 安装顺序文档 / Key Conclusions 治理原则
**Source:** docs/audit/2026-08-05-sybermem-comprehensive-audit.md §3（复核属实）

## 1. 背景与问题

审计 §3 复核确认：

1. **术语不一致**：INDEX.md 用 `## Stage Digests`，README 用 "phase digest"，同一概念两种命名，增加认知负担。
2. **安装顺序反直觉**：README 把 `claude --plugin-dir .`（开发者本地路径）标为「推荐」，把一行式 remote install 标为「兼容模式」，而后者才是普通用户最直观的路径。
3. **Key Conclusions 偏实现史**：session-start 注入的 Key Conclusions 混着分发/插件/框架的内部升级史，不全是「当前要紧的事」。

## 2. 设计目标

用最小、安全的文档/措辞改动降低认知摩擦，不改代码行为、不碰 AI 契约。

1. 统一 digest 术语：全项目对「阶段摘要」统一用 **phase digest / Phase Digests**（INDEX 标题、health-check 提示文案、README 一致）。
2. 纠正安装文档：把一行式 remote install 定位为**面向普通用户的推荐**，`claude --plugin-dir .` 定位为**开发者/本地验证**。
3. 为 Key Conclusions 建立**治理原则**（写进 CONTRIBUTING/记录 skill 说明）：只保留当前操作真相与活跃约束，release/实现史交给 archived/digest。

## 3. 设计边界与安全性

### 已验证安全
- **改 INDEX 的 `## Stage Digests` → `## Phase Digests` 是安全的**：`check_project_health.py` 用 HTML 注释锚点（`<!-- add new digest records here -->`）检测 digest section，**不依赖标题字面**（已核验 line 198）。
- 术语改动只触及 markdown 标题/文案，不改任何解析逻辑。

### 保留 / 不引入
- 不改 skill 的 HARD-GATE 机器契约措辞（AI 依赖它，激进改写风险高 → 不在本方案）。
- 不改 record/digest 的 anchor 注释（health check 依赖它们）。
- 不改代码行为、不改 CLI、不改 hook。
- 不动既有 digest 记录内容。

## 4. 方案

### 4.1 digest 术语统一

- INDEX.md：`## Stage Digests` → `## Phase Digests`（模板 3 副本同步）。
- `check_project_health.py`（3 副本）：action 文案 "insert Stage Digests section" → "insert Phase Digests section"。
- README.md / README.en.md：确认统一用 "phase digest"（已一致，补齐任何残留）。
- 术语表：在 README 加一句 glossary 说明 phase digest = 阶段摘要。

> 注意：INDEX 里既有的历史 digest 表格内容不动，只改 section 标题。

### 4.2 安装文档纠正

README.md / README.en.md 安装章节调整定位（不删任何安装方式）：
- 一行式 remote install（curl/irm）→ 标为**「推荐（普通用户）」**。
- `claude --plugin-dir .` → 标为**「开发者 / 本地验证」**。
- 升级顺序说明保留，但用一句话规则收敛：「新项目 → init；已有项目升级后 → update」。

### 4.3 Key Conclusions 治理原则

在 CONTRIBUTING.md 加一节「Key Conclusions 写什么」：
- Key Conclusions 只保留**当前操作真相 + 活跃约束**。
- release/实现史属 archived 或 digest，不进 Key Conclusions 的活跃区。
- 这是**书面原则**，不改现有已写入的 conclusions（避免重排历史）。

## 5. 验收标准

1. INDEX.md 用 `## Phase Digests`；health check 仍通过（锚点未变）；3 副本一致。
2. `check_project_health.py` 文案统一为 "Phase Digests"；3 副本一致。
3. README/README.en 安装章节：remote install 标推荐给用户、plugin-dir 标开发者；术语统一用 phase digest。
4. CONTRIBUTING 有 Key Conclusions 治理原则一节。
5. `pytest packages/core packages/cli` 全绿；`check-plugin-package.py` `OK`；skill 镜像无 drift。

## 6. 明确不做（本方案外）

- skill 瘦身（init-project 236 行拆「人类速览 + 机器契约」）：涉及 AI 行为契约与主观取舍，风险高，作为独立、更谨慎的工作，不在本批次。
- 不改已写入的 Key Conclusions 内容（只立原则）。
