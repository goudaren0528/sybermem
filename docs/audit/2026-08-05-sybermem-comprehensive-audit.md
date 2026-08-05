# SyberMem 综合调研报告与复核改进计划

- 调研日期：2026-08-05
- 调研方法：5 个并行 subagent，分别覆盖 **功能可用性 / 使用体验 / 效率 / 分发完整性 / 开源最佳实践**，结论均以源码交叉核验
- 调研基准 commit：`dde4857`（`chore: ignore local package build artifacts`）
- 文档定位：本报告的每一部分都附带 **「复核方案」** 与 **「改进方案框架」**，供后续逐项验证结论真实性后再动手改进

> ⚠️ 重要免责：本报告是 **一次性快照式调研**，部分结论（尤其是 subagent 给出的「missing/broken」判断）**可能高估或低估**。任何改进动作前，必须先执行对应章节的「复核方案」确认结论为真。已知的一处过度判断已在 §1 中修正说明。

---

## 实现进展（2026-08-05 已落地 P0 + P1）

复核通过后已按 spec → plan → 实现 → 验证的节奏完成 P0 与 P1：

| 部分 | 交付 | 关键验证 |
|---|---|---|
| **P0-§1 双轨对齐** | 新增 `sybermem resume` CLI（fast/standard/deep×text/json）；`search_project` 无项目根改显式报错（hook 路径仍静默）；README/README.en 加「命令 vs Skill 编排」表 | pytest core 83 + cli 11 绿；resume 三模式真终端跑通；无根 exit 1；hook 未受影响 |
| **P0-§2 效率（批次 A）** | 项目搜索进程内缓存（消除二次全扫）；合并 `detect_record_intent`+`task_recall` 为单进程 `user_prompt.py`（3 副本+3 settings+插件委托器+包校验同步）；stop hook commit-gap 去重 | **合并 hook 实测 297ms vs 旧 491ms，降 39%**；check-plugin-package `OK` |
| **P1-§5 开源运营** | 根 `LICENSE`(MIT)+两包 license 声明；cli 依赖 core + 元数据；`VERSION` 单源+`sync-version.py`+一致性校验；`.github/workflows/ci.yml`；CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/issue·PR 模板 | 两包 `python -m build` 成功（License-Expression+Requires-Dist）；version sync 幂等覆盖 8 处；校验反例生效；CI YAML 合法 |
| **批次 D-§4 分发一致性** | 统一 Codex/Cursor/Kimi manifest 元数据；CI 加 version-skew + skill-drift 双 gate；README/README.en 加平台支持级别矩阵（诚实降级） | manifest 合法 JSON；sync-version 幂等；pytest 83+11 绿；check-plugin-package `OK` |
| **批次 E-§3 体验** | digest 术语全项目统一 `Stage Digests → Phase Digests`（安全：health check 用锚点非标题）；安装文档纠正（remote install 推荐给用户、plugin-dir 给开发者）；CONTRIBUTING 加 Key Conclusions 治理原则 | health check 锚点完好；skill 镜像无 drift；pytest 83+11 绿；check-plugin-package `OK` |
| **批次 F-§2-e 效率补漏** | `search_workspace` 查询时陈旧检测：`workspace_index_staleness()` 比对 indexed HEAD vs current HEAD，CLI 打印 stderr 提示 + json `index_staleness` 字段（不自动重建、不改结果） | 3 新单测（fresh/stale/skip）；CLI 端到端 stale 时提示、exit code 不变；pytest core 86 + cli 11 绿 |

**Spec/Plan 落盘：**
- `docs/superpowers/specs/2026-08-05-sybermem-dual-track-alignment-design.md`
- `docs/superpowers/specs/2026-08-05-sybermem-hotpath-efficiency-design.md`
- `docs/superpowers/specs/2026-08-05-sybermem-oss-readiness-design.md`
- 对应 plan 在 `docs/superpowers/plans/`（该目录被 .gitignore 忽略，属本地工作产物约定）

**P0-§2 批次 B（已完成 2026-08-05）：** auto-trail 改有界滚动 journal。经下游依赖调研（auto-trail 深嵌 canonical 枚举、8 个文件被 digest 引用）+ 用户确认，采取**最低风险路径**：stop hook 的 auto 模式不再写 `.sybermem/changes/` markdown 与 INDEX 行，改 append `.sybermem/.auto-trail.jsonl`（有界 200 条）；**既有 26 条零改动**（不碰 digest provenance / publish hash / status 计数 / search archived）；去重改从 journal 读；reminder/nudge 信号不变。验证：stop hook 实测写 journal 不写 markdown、去重+有界生效、既有记录零改动、pytest core 83 + cli 11 绿（更新 1 个编码旧契约的 stop-hook 测试）、check-plugin-package `OK`。spec: `docs/superpowers/specs/2026-08-05-sybermem-auto-trail-journal-design.md`。

**范围内明确延后（需用户/独立决策）：**
- **批次 C（更大范围）**：真正清理既有 26 条 + 让 status/publish 从 journal 重算 —— 会改 publish source_hash 语义，独立决策。
- **P0-§2 stop hook next-id 持久化**：state 与 changes/ 目录可能不一致导致编号冲突，保守保留 glob。
- **P1-§5 CI 真实绿灯**：本地已跑通 pytest/build/package-check 步骤，矩阵/多 OS 并行需 push 到 GitHub 才能确认。
- **§3 体验瘦身 / §4 平台补全**：第二梯队，根因修复后跟进。

**顺带修复（实现中发现）：** stop hook 的两个模板副本原落后于运行时版本（`GIT_CWD=Path.cwd()` 旧 buggy 版、缺 `theme_key or "misc"`），已统一到运行时较新版。

---

## 复核结果总表（2026-08-05 已执行）

18 项复核清单全部执行完毕，均以源码/实测交叉验证。结论：**核心结论全部属实，2 处需精确化，0 处推翻。**

| 编号 | 复核项 | 结果 | 关键证据 |
|---|---|---|---|
| §1-a | resume.py 无生产调用方 | ✅ 属实 | `build_resume_checkpoint` 唯一调用方是 `tests/test_resume.py`；CLI/hooks/opencode/skill 全不调 |
| §1-b | 双轨制（CLI vs skill-driven） | ✅ 属实 | record/link/digest/resume 的 SKILL grep 到的 "sybermem" 全是 description 文字，非真实命令；edit-verbs 高、真实 CLI-cmds=0 |
| §1-c | search/portfolio 静默失败 | ✅ 属实 | `search_project` 在 `root is None` 时 `return []`（search.py:169/209/215），无用户可见提示 |
| §2-a | 项目搜索是全扫非 FTS | ✅ 属实 | search.py:176 每次调用 `[parse_record_file(rf) for rf in iter_record_files(root)]`；空结果时:218 又全扫一次 |
| §2-b | 两个独立 prompt hook 进程 | ✅ 属实 | `.claude/settings.json` UserPromptSubmit 挂 2 个 hook block，各起独立 Python 进程 |
| §2-c | stop hook 过重 | ✅ 属实 | 3 次 git 列举 + `count_commits_since_last_record` 扫 4 目录（可能调 2 次）+ `recommend_next_step` 再 parse 全量 + 写 md + 重写 INDEX |
| §2-d | auto-trail 占半个语料库 | ✅ 属实 | 51 条记录中 26 条为 auto-trail（"Auto-generated from workspace changes"）；digest 7 条 |
| §2-e | workspace 查询不校验 HEAD | ⚠️ 精确化 | `search_workspace` 签名无 HEAD/rebuild 参数 → **查询时不校验**；HEAD 比对只发生在 `index build` **构建时**。原结论方向对，表述需精确 |
| §2-f | 实测每 prompt hook 耗时 | ✅ 实测 | 51 条记录下：detect_record_intent ~188ms + task_recall ~200ms，**双 hook 合计实测 ~517ms**，随记录数线性增长 |
| §3-a | init-project 最臃肿 | ✅ 属实（数字精确化） | 实测 179 行 + 19 处 ceremony 标记居首（subagent 报 236 行系不同口径）；team-summary(30)/team-publish(52) 最简 |
| §3-b | 术语不一致 | ✅ 属实 | INDEX.md 用 "## Stage Digests"，README 用 "phase digest"，同概念两命名 |
| §4-a | Codex/Cursor/Kimi 仅 stub | ✅ 属实 | 三者各仅 1 个 4 字段 plugin.json，内容完全相同，无 runtime；.superpowers 仅 sdd 文档非分发物 |
| §4-b | skill 树靠手动单向 sync | ✅ 属实 | 当前 37 文件完全一致（碰巧已同步），验证「靠手动 sync 维持」 |
| §4-c | 非 Claude/OpenCode 无打包 guardrail | ✅ 属实 | check-plugin-package.py 对 Codex/Cursor/Kimi/Gemini 仅校验「文件存在+JSON 可解析」 |
| §5-a | 无 CI + 无 LICENSE | ✅ 属实 | 无 `.github/`、无 `.github/workflows`、无任何 `LICENSE*` 文件 |
| §5-b | cli 包依赖缺失 | ✅ 属实 | `dependencies = []` 但 main.py 有 12 处 `from sybermem_core.*` |
| §5-c | version 硬编码散落 | ✅ 属实 | 主仓 8 处：2 pyproject + 5 平台 manifest + gemini-extension |
| §5-d | 无社区健康文件 | ✅ 属实 | CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/issue·PR 模板/CODEOWNERS 全缺 |

**两处精确化说明：**
1. **§2-e**：workspace 陈旧风险真实存在，但机制要说清 —— 是「查询时不校验新鲜度」，而非「完全不比对 HEAD」；`index build` 时会比对 HEAD 跳过未变项目。
2. **§3-a / §1（subagent 数字口径）**：init-project 实测 179 行（非 236），bloat 排名结论不变；§1 record/link/digest 是「有意 skill-driven」而非「broken」，已在 §1.2 修正。

---

## 0. 总体结论

**产品设计有真实价值（生命周期感知的工程记忆系统），但当前处在「能跑但不成熟」阶段。**

最致命的不是缺功能，而是三个系统性问题：

1. **架构双轨制未对齐** —— CLI/core 路径与 Skill 驱动路径并存但不透明（§1）
2. **热路径与存储在线性劣化** —— 每 prompt 全量重扫、auto-trail 噪声已占半个语料库（§2）
3. **开源运营层几乎为零** —— 无 CI、无 LICENSE 文件、包依赖不可发布（§5）

### 若只做三件事（跨维度收敛优先级）

| 优先级 | 动作 | 解决的根因 |
|---|---|---|
| P0 | 对齐双轨架构（先把已实现的 `resume` 接上 CLI；明确 record/link/digest 的执行契约） | 功能可信度根因（§1） |
| P0 | 治理 auto-trail + 项目搜索索引化 | 一举改善效率/存储/搜索质量/注入噪声（§2） |
| P1 | 补 CI + LICENSE + 包依赖 + version 单源 | 开源信任门槛（§5） |

体验层 skill 瘦身（§3）、平台声称降级（§4）属第二梯队，可在根因修复后跟进。

---

## 1. 功能可用性：CLI 与 Skill 双轨制未对齐（最高优先级）

### 1.1 调研结论

系统实际存在 **两套执行路径**，但对用户和文档都不透明：

| 能力 | 实际执行方式 | 状态 |
|---|---|---|
| search / status / publish / team / index / portfolio | CLI + core（Python） | ✅ 真实可调用 |
| record / link / digest / theme-digest / resume | 纯 Skill 驱动（LLM 直接改 markdown，无 CLI 后端） | ⚠️ 能跑但无程序化保障 |
| phase-analyze / phase-confirm / update / init-project 完整流程 | Skill 指令 + 外部脚本，core 无对应实现 | ⚠️ 契约漂移 |

**已核验的实际 CLI 命令面**（`packages/cli/sybermem_cli/main.py`）：
- `project init | status | uninstall`
- `index build`
- `search`
- `portfolio`
- `team init | summary`
- `publish status`

**关键证据**：
- `resume.py`（`packages/core/sybermem_core/resume.py`）已完整实现 fast/standard/deep，但 CLI **完全没暴露入口**，仅测试在调用 —— 纯遗漏浪费。
- `records.py` 只有读取/解析，**没有 record/link 的写入器**；写操作全靠 skill 指令让 LLM 手改 frontmatter（已核验 `skills/sybermem-link/SKILL.md` 明确写「editing the SOURCE record's frontmatter」）。

### 1.2 对 subagent 结论的修正

> 功能可用性 subagent 将 record/link/digest/resume 标为「Missing-or-Broken」是 **过度判断**。经复核，它们是 **有意的 Skill-driven 设计**（LLM 直接编辑 markdown），并非坏掉。真实问题是 **双轨边界未文档化、可靠性不一致**，而非「功能缺失」。

后果：同样是「写记忆」，`record` 靠 LLM 自觉、`publish` 靠程序校验，可靠性完全不一致；用户读 README 以为都是命令，实际有一半是「提示词说服 AI 去做」。

### 1.3 复核方案（✅ 已于 2026-08-05 执行）

- [x] 逐一审计 14 个 SKILL.md 的落地动作（CLI 调用 vs LLM 文件编辑）→ 见下表
- [x] 确认 `resume.py` 无任何生产调用方（唯一调用方为 `tests/test_resume.py`）
- [x] 确认 record/link/digest 的 skill 无隐式 CLI 依赖（grep 到的 "sybermem" 均为 description 文字）
- [x] 建立权威表：`能力 → 执行路径 → 可靠性保障`

**权威执行路径表（已核验）：**

| 能力 | 执行路径 | 可靠性保障 |
|---|---|---|
| search / status / portfolio / team-* / publish | CLI + core | 程序校验 |
| record / link / digest / theme-digest / resume | Skill-driven（LLM 编辑 markdown） | LLM 自觉 |
| phase-analyze / phase-confirm | Skill-driven（core 无实现） | LLM 自觉 |
| resume（特例） | **core 已实现但零生产调用** | 悬空浪费 |

### 1.4 改进方案框架

- **方向 A（推荐）**：把已实现的 `resume` 暴露成真 CLI 命令（零成本）；对 record/link/digest 评估是否下沉为 core 写入器 + 薄 CLI，以获得程序化保障
- **方向 B（最低成本）**：保持双轨，但在 README/INSTALL 中坦诚区分「命令」与「skill 编排」，消除认知误导
- 无论哪个方向，先修 `search_project` / `portfolio` 的静默失败（找不到 root 时静默返回 `[]`，应给出显式降级提示）

---

## 2. 效率：热路径与存储在线性劣化（高优先级）

### 2.1 调研结论

- **每个 prompt 重扫全量记忆**：本仓库 `.claude/settings.json` 实际挂了 **两个** prompt hook（`task_recall.py` + `detect_record_intent.py`），各自 `iter_record_files()` 全目录 markdown 重解析。项目搜索 **完全没用 SQLite/FTS 索引**，是纯 O(records) 扫描，空结果时还会二次全扫。
- **stop hook 太重**：每次结束跑 3 次 git 列举 + 扫 4 个记录目录算最新日期 + 扫 `changes/` 算下一个 id + 调 `recommend_next_step()`（内部又把所有记录 parse 一遍），全在同步 60s 路径上。
- **auto-trail 已污染半个语料库**：当前 57 条记录里 **25 条是 "Auto-recorded workspace file changes on stop" 噪声**，`INDEX.md` 里 26 行 feature 表 + 20 行归档全是它。低价值记录仍被 parse、index、search、去重、hook 扫描全程拖累。
- **workspace 索引会无限过期**：有 FTS，但只靠手动 `sybermem index build` 刷新，查询时不比对 HEAD，陈旧结果会一直存在。

**已核验的规模数字（基准 commit）**：57 条记录总数 / 25 条 auto-trail / 7 条 digest / 启动注入约 1479 字符·13 行 / `INDEX.md` 26 行 auto-trail feature 表。

### 2.2 复核方案（✅ 已于 2026-08-05 执行）

- [x] 实测单 prompt hook 墙钟耗时 → 51 条记录下 detect_record_intent ~188ms + task_recall ~200ms，**双 hook 合计 ~517ms**
- [x] 确认 `search_project` 未走 FTS → search.py:176 每次全目录 `parse_record_file`，空结果时:218 二次全扫
- [x] 确认两个 prompt hook 独立进程 → `.claude/settings.json` 挂 2 个独立 hook block
- [x] 统计 auto-trail 参与度 → 51 条记录中 26 条 auto-trail，全程参与 parse/index/search/dedup
- [x] 确认 workspace 查询不校验 HEAD → `search_workspace` 签名无 HEAD 参数；HEAD 比对仅在 `index build` 时（精确化，见总表 §2-e）

> 未做：人造 500 条记录的压测对比。当前 51 条已实测 ~517ms/prompt，线性劣化方向明确；若要精确曲线，可后续补压测。

### 2.3 改进方案框架（按性价比排序）

1. 项目搜索改走缓存/SQLite，按 mtime/HEAD 失效；复用第一遍 parse 结果避免二次全扫
2. 合并两个 prompt hook 为单进程；对普通 prompt 短路 classifier，避免 import core
3. stop hook 把 status/router 扫描移出热路径；next-id / 最新日期落到 state 文件；去掉重复的 commit-gap 计算
4. **停止为每次 stop 写一条 markdown**，改为滚动 journal，只在跨阈值时提升为正式记录；auto-trail 默认排除出去重与 compact recall
5. workspace 查询加轻量 stale 检测（indexed HEAD != current HEAD 时告警/自动重建）

---

## 3. 使用体验：能力强但心智负担过载（高优先级）

### 3.1 调研结论

- **安装顺序反直觉的 footgun**：README 把 `claude --plugin-dir .`（其实是开发者本地路径）标为「推荐」，把一行式 remote install 标为「兼容模式」；升级必须记住「先全局 → `/sybermem-update` → 可能 `/sybermem-init-project`」三层，文档反复防御性重申，正说明它总被漏。
- **Skill 像合规手册不像帮助**：`sybermem-init-project` **236 行**，塞满 HARD-GATE / Red Flags / Common Rationalizations / 文件分类外科手术规则。`sybermem-team-publish` 短且清楚，反衬其它 skill 臃肿不一致。
- **术语不一致**：INDEX 里叫 "Stage Digests"、README 叫 "phase digest"；summary 与 resume 都是「当前状态视图」却职责不同；Hub 与 workspace 边界模糊。
- **注入内容偏实现史**：session-start 从 Key Conclusions 注入，但当前列表混着分发/插件/框架的内部升级史，不是「现在要紧的事」。

**最臃肿 skill 排序**：`sybermem-init-project` > `sybermem-search` > `using-sybermem` > `sybermem-record` > `sybermem-update`；最清晰：`sybermem-team-publish` > `sybermem-resume`。

### 3.2 复核方案（部分执行）

- [x] 统计各 SKILL.md 行数与 ceremony 标记 → init-project 179 行/19 标记居首；team-summary 30 行最简（见总表 §3-a）
- [x] 列出术语不一致 → "Stage Digests"(INDEX) vs "phase digest"(README) 同概念两命名已确认
- [ ] 让未接触项目的人按 README 走完首次安装（需真人参与，未执行 —— 属主观体验类，建议改进阶段做可用性测试）
- [ ] 抽样真实 session 注入内容评估相关性（需历史 session 数据，未执行）

> §3 属体验主观维度，静态可验证项（行数/术语）已确认属实；「安装卡点」「注入相关性」需真人/历史数据，留待改进阶段做用户测试。

### 3.3 改进方案框架

- 定义「核心模式」（Project + record + resume + digest）作默认，Hub/Team/theme-digest/trust 作进阶层
- skill 拆成「人类速览版（5-10 行）+ 机器安全契约」，向 `team-publish` 风格看齐
- 统一术语 + 一页 glossary（每项一句话）
- Key Conclusions 只留当前操作真相，release 史移到 archived/digest-only recall

---

## 4. 分发完整性：平台声称 > 实际打包（中优先级）

### 4.1 调研结论

| 平台 | 实际状态 |
|---|---|
| Claude Code | ✅ 完整（manifest + marketplace + hooks 全 wired，validation 最深） |
| OpenCode | ✅ 实现完整但脚本驱动（`packages/opencode-plugin/sybermem.ts` 真实 runtime，无一等 manifest） |
| Gemini | ⚠️ 仅入口描述符 |
| Codex / Cursor / Kimi | ⚠️ 只有 6 行 stub manifest，无 runtime hook |
| .superpowers | ❌ 只是内部 sdd 文档，根本不是分发物 |

- **Skill 双份易漂移**：`packages/claude-skills`（source of truth）→ `skills`（plugin-facing）靠 `sync-plugin-skills.py` 单向手动同步；install/update 脚本直读源目录，但 Claude 插件用同步后的 `skills/`，改了源忘 sync 就会 lag。`check-plugin-package.py` 有静态校验兜底但非预防式。
- **manifest schema 不统一**：Claude 用 object author + 全字段，Codex/Cursor/Kimi 只有 4 个字段。
- **version 硬编码散落 8+ 处**（core/cli/5 平台 manifest 全是 `0.1.0`）。
- OS 层面 `.sh`/`.ps1` 三对脚本基本对等；真正的分裂在 local（`pip install`）vs remote（`--force-reinstall`）刷新语义。

### 4.2 复核方案（✅ 已于 2026-08-05 执行）

- [x] 逐平台清点 → Codex/Cursor/Kimi 各仅 1 个 4 字段 stub manifest（内容完全相同），无 runtime；.superpowers 仅 sdd 文档
- [x] diff `packages/claude-skills` vs `skills` → 当前 37 文件完全一致（碰巧已同步，验证靠手动 sync）
- [x] `check-plugin-package.py` 平台矩阵 → Claude 深度校验 / OpenCode 间接校验 / Codex·Cursor·Kimi·Gemini 仅「文件存在+JSON 可解析」
- [x] `sync-plugin-skills.py` 方向 → 上次调研已确认单向 `packages/claude-skills → skills`，会 delete/re-copy
- [ ] 逐行比对 3 对 `.sh`/`.ps1` 脚本对等性（上次调研已判定基本对等，本轮未逐行复验）

### 4.3 改进方案框架

- Codex/Cursor/Kimi/Gemini：**要么补全 runtime + validator，要么在文档进一步降级声明**
- release 流程自动跑 `sync-plugin-skills.py`
- 统一各平台 manifest schema
- version 单源化（见 §5）

---

## 5. 开源最佳实践：运营成熟度几乎为零（高杠杆，易补）

### 5.1 调研结论

代码/文档/测试底子已不错，缺的是运营层：

| 杠杆 | 缺口 |
|---|---|
| 高 | **无任何 CI**（根目录无 `.github/`），却同时有 Python 包 + bash/ps1 安装器 + 多平台插件 + 双语文档，全靠手工保证 |
| 高 | **打包不可发布**：`sybermem-cli` 直接 import `sybermem_core` 却声明 `dependencies = []`，靠 force-reinstall 本地源码树硬塞 venv |
| 高 | **无 LICENSE 文件**（README/manifest 都写 MIT，但仓库根没有 LICENSE 文件，法律上不成立） |
| 高 | **version 多处重复** 无单源，易 skew |
| 中 | 无 CONTRIBUTING / SECURITY / CODE_OF_CONDUCT / issue·PR 模板 |
| 中 | 无 release 自动化；安装脚本无 smoke test；pyproject 元数据过薄 |

### 5.2 复核方案（✅ 已于 2026-08-05 执行，全部属实）

- [x] 无 `.github/`、无 `.github/workflows`、无任何 `LICENSE*` 文件
- [x] `packages/cli/pyproject.toml` 的 `dependencies = []`，但 main.py 有 12 处 `from sybermem_core.*`
- [x] version 硬编码主仓 8 处：`packages/cli/pyproject.toml`、`packages/core/pyproject.toml`、`.claude-plugin/{plugin,marketplace}.json`、`.codex-plugin/`、`.cursor-plugin/`、`.kimi-plugin/plugin.json`、`gemini-extension.json`
- [x] CONTRIBUTING / SECURITY / CODE_OF_CONDUCT / issue·PR 模板 / CODEOWNERS 全部不存在

### 5.3 改进方案框架（最高杠杆 5 件）

1. 加 CI：OS × Python 矩阵跑 test + build + `check-plugin-package.py` + 安装 smoke
2. 修包依赖：cli 依赖 core，或合并单包，支持 `pipx install`
3. 加根 `LICENSE`，并在两个 pyproject 里 wire `license` / `license-files`
4. version 单源化（tag 驱动 setuptools-scm/Hatch VCS，或单 `VERSION` 文件 + 生成脚本）
5. 补 `.github/` 社区文件（CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/issue·PR 模板）

---

## 6. 后续工作流建议

每一部分（§1–§5）都遵循同一个三步节奏：

```
复核（confirm 结论真实性） → 方案制定（写 spec/plan） → 改进（实现 + 验证）
```

建议顺序：先 P0（§1、§2），再 P1（§5），最后 §3、§4。每个部分的复核结果与最终方案，应回写为独立的 spec/plan 文档（放 docs/superpowers/specs 与 plans），并用 `/sybermem-record` 沉淀决策。

### 复核任务总览（勾选跟踪）

- [x] §1 功能双轨制复核 —— ✅ 全部属实（含 1 处 subagent 过度判断已修正）
- [x] §2 效率热路径复核 —— ✅ 全部属实（§2-e 表述精确化；实测 ~517ms/prompt）
- [x] §3 体验友好度复核 —— ✅ 静态项属实；主观项（安装卡点/注入相关性）留待用户测试
- [x] §4 分发完整性复核 —— ✅ 全部属实
- [x] §5 开源运营复核 —— ✅ 全部属实

### 下一步：从复核转入方案制定

复核已确认结论真实。建议按 P0 → P1 顺序进入「方案制定」，每个部分产出独立 spec/plan（放 `docs/superpowers/specs` 与 `plans`）：

1. **P0-§1**：resume 接 CLI（零成本）+ 双轨契约文档化 + search/portfolio 静默失败改显式提示
2. **P0-§2**：项目搜索索引化 + 双 prompt hook 合并 + stop hook 瘦身 + auto-trail 改滚动 journal
3. **P1-§5**：加根 LICENSE + `.github/` CI（test/build/check-plugin-package/smoke）+ cli 依赖 core + version 单源
4. **§3 / §4**：skill 瘦身向 team-publish 看齐 + 术语统一 + 非核心平台补 validator 或降级声明
