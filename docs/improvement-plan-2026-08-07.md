# SyberMem 能力评审与改进计划

> 状态（2026-08-10）：全部 14 项举措 + 3 个衍生缺陷（P0 UUID、B1 fixed 状态、B2 merged-hook 绕过召回门）已完成。core 测试 138 passed。
> 最终链路评审（2026-08-10）：发现并修复 B2——E1/E6 只写进了独立 task_recall.main，而实际 wired 的是 merged user_prompt.py，导致高信号门与观测日志在生产路径上失效。已改为同源复用并加回归测试。
> 创建日期：2026-08-07
> 范围：记忆（Memory）/ 治理（Governance）/ 召回（Recall）三大能力的有效性与经济性评审，及按优先级排序的改进举措。
> 约束（不可动摇的产品意图）：
> 1. **Markdown 是唯一真源**，人和 AI 都能直读；不引入第二套黑盒 store（decision-002）。
> 2. **确定性归 CLI/core，非确定性归 AI skill**；召回是「辅助证据」不是「指令」。
> 3. **降低重启摩擦，但不假装能力**（诚实标注边界）。

---

## 0. 状态看板

| 编号 | 举措 | 维度 | 优先级 | 状态 |
|------|------|------|--------|------|
| P0 | UUID successor 引导正则修复 | 效果/正确性 | 立即 | ✅ 已完成（bug-2ffd869f） |
| E1 | 召回从「每轮低质注入」→「高信号精准注入」 | 效果 | 立即 | ✅ 已完成 |
| E3 | digest 陈旧机械检测（coverage_hash） | 效果 | 立即 | ✅ 已完成（含 skill 侧收尾） |
| D1 | 分发链路完整性检查（改进能传播到分发包/存量项目） | 治理/分发 | 立即 | ✅ 已完成（本轮缺陷已修 + 回归护栏；通用护栏 2/3 待后续） |
| A1 | 收敛到单一入口 `/using-sybermem` 智能分诊 | 可用性 | 短期 | ✅ 已完成 |
| A3 | 记录时机主动提醒（commit gap 挂生命周期） | 可用性 | 短期 | ✅ 已完成 |
| E4 | 信任元数据从「推断」→「声明」（可选 frontmatter） | 效果 | 短期 | ✅ 已完成 |
| A2 | record 一步到位，砍掉中间确认 | 可用性 | 中期 | ✅ 已完成 |
| E5 | 召回排序纳入「相关性具体度」 | 效果 | 中期 | ✅ 已完成 |
| E6 | 召回命中率可度量（本地日志基线） | 效果 | 中期 | ✅ 已完成 |
| A4 | resume 输出「简报」而非字段转储 | 可用性 | 中期 | ✅ 已完成 |
| B1 | 修复 `fixed` 状态 bug 被误判为 open（A4 暴露） | 效果/正确性 | 中期 | ✅ 已完成 |
| B2 | 修复 merged user_prompt.py 绕过 E1 高信号门 + E6 日志（最终评审暴露） | 效果/正确性 | 评审 | ✅ 已完成 |
| A5 | 首次体验样板 record | 可用性 | 增强 | ✅ 已完成 |
| G4 | publish hash 正名（用户文案 + 范围说明，不改持久化字段名） | 治理/诚实 | 增强 | ✅ 已完成 |
| G5 | archived 真源归位到 frontmatter | 治理 | 增强 | ✅ 已完成（机制由 E4 提供，本轮补测试+文档） |
| E2 | 轻量语义召回（本地 char n-gram 向量，opt-in） | 效果 | 增强 | ✅ 已完成 |

图例：✅ 完成 / 🔵 进行中 / ⬜ 待处理

---

## 1. 评审结论（有效且经济吗？）

**总评：方向正确，但目前只是部分有效、部分经济。** 最扎实的是确定性的 record 解析 + 派生 INDEX + publish hash 门禁；最薄弱的是 AI 重编排的仪式、字符串推断的治理、以及被过度包装成「召回」的词法检索。

### 1.1 记忆（Memory）— 部分有效 / 经济性偏低
- **有效**：record→INDEX 确定性可靠；digest 是真正的压缩层（digest-006 把 9 条压成 6 条）。
- **问题**：
  - INDEX 仍随 record 线性增长，它不是压缩层却常被当压缩层用。
  - auto-record-on-stop 已被证明是**净负**——语料里 20+ 条自动记录后来全被归档/压缩，污染搜索和 digest。项目已在 change-047 停掉（正确纠偏，无需再动）。
- **经济性**：record + link + digest + phase-analyze + phase-confirm + theme-digest 六个非确定性 AI skill，对以 Markdown 为源的系统仪式过重。

### 1.2 治理（Governance）— 部分有效
- **有效**：authority/lifecycle/freshness 模型概念自洽（集中在 `derive_continuity_metadata`）；publish hash 门禁是真的（`project_source_snapshot` 对每源文件 SHA-256，mismatch 拒绝发布），不是花架子。
- **P0 缺陷（已修）**：`retrieval.RECORD_ID_RE` 只匹配 3 位 numeric id，UUID record 的 `superseded_by`/`fixes` 无法解析成 successor 引导 → record 被标 superseded 却不告诉用户「该用哪条」。已通过共享 `RECORD_ID_SUFFIX` 修复。
- **脆弱点**：治理元数据大量靠路径子串、marker 文本、INDEX 段落推断，易与 canonical 漂移。
- **边界**：publish hash 只覆盖 project records + identity，是「stale-preview 防护」而非「完整发布安全证明」，命名应更诚实。

### 1.3 召回（Recall）— 部分有效偏弱
- **实情**：项目内 `compact_project_search` 是**词法扫描 + 阈值**（title×4 / topic×3 / relation×3 / body≤3，score≥5 且 matched_fields≥2），**不是 FTS 也不是语义**。真正的 FTS5 只在 workspace 层。
- **问题**：
  - 漏召回同义/改写查询；偶尔注入貌似相关但错误的提示。
  - 排序只看 authority→freshness→score→date，导致新泛泛 record 压过老而精准 record。
  - hook 在**每条**合格 prompt 上跑一次子进程 + 词法扫描 + 注入 token；每次新进程，缓存跨进程失效——隐性持续开销。
  - abstention 设计在 core 有意义（`no_reliable_recall`），但 hook 未开 `include_abstention`，热路径对 agent 不可见。

---

## 2. 改进举措（按维度）

### 2.1 可用性提高

#### A1. 收敛到单一入口 `/using-sybermem` 智能分诊【短期】✅
- **痛点**：owner 要在 resume/record/summary/digest/team-publish 间自选，靠人记住 6 个命令；`using-sybermem` 原来用 AI 解读的 DOT 决策图re-derive 推荐，与 resume 用的 core 路由存在漂移风险。
- **方案**：把确定性路由暴露成 CLI，让 skill 调用它作为权威推荐，而不是 AI 重推。
- **实现**：新增 `sybermem next-step`（text/json），薄封装 `next_step_router.recommend_next_step`；`using-sybermem` Step 3 改为「运行 `sybermem next-step --format json`，其 action+reason 即权威推荐」，DOT 图降级为 CLI 不可用时的手工兜底说明。resume 与 using-sybermem 从此同源。
- **落地点**：`packages/cli/sybermem_cli/main.py`（`cmd_next_step` + argparse）、`using-sybermem/SKILL.md`（+镜像）。
- **验证**：`sybermem next-step` 对本项目返回确定性推荐（text+json）；skill 两份拷贝同步。

#### A2. record 一步到位，砍掉中间确认【中期】✅
- **痛点**：record skill 11 步 flow + HARD-GATE + relation 逐条确认，小改动劝退。
- **方案**：默认「快速记录」——AI 从上下文直接填 type/key_conclusion/topics/relation，一次成文，只在歧义时问；逐条确认降级为「记完给你看，要改再说」。仪式保留给大型 decision。
- **实现**：SKILL 新增「Choose a path: fast vs full」——fast path 一次跑完 4-11 步、跳过 2-3 的交互确认与 step 7 的逐条 relation 询问（仍推断并写关系），只在结尾汇报一次；full path 保留给歧义/高风险/decision。**两条路径同守 HARD-GATE + Verification**（文件+frontmatter+index build/check），fast 只去掉确认摩擦不去掉完成保证。
- **落地点**：`sybermem-record/SKILL.md`（+镜像）。

#### A3. 记录时机主动提醒【短期】✅
- **痛点**：记录靠人自觉，容易漏记，而记录及时性是记忆系统命根子。
- **方案**：SessionStart 注入一条「距上次记录 N 个 commit」的轻提醒（提醒非动作）。
- **实现**：`session_start_context.py` 新增 `latest_record_date` + `detect_record_gap`（自 shell git，与既有 hook 风格一致，零 core 依赖），gap ≥ 3 时追加一行 record 提醒；实测本项目今天有记录→gap=0→不误报。
- **落地点**：`.sybermem/hooks/session_start_context.py`（+2 分发拷贝，已同步）。

#### A4. resume 输出「简报」而非字段转储【中期】✅
- **方案**：checkpoint 增 `brief` 字段——3-4 行自然语言简报（phase+置信度+新鲜度、最近工作、待关注 open items、建议下一步），CLI text 模式先打简报再打结构化字段。
- **实现**：`resume._brief()` 从既有字段确定性合成，只读；结构化字段仍是权威源。
- **落地点**：`resume.py`（`_brief`）、`cli/main.py:cmd_resume`（先打 brief）。
- **验证**：实测 resume 先输出 4 行人类简报；顺带发现并修复 B1（fixed bug 误判 open）。

#### A5. 首次体验样板【增强】✅
- **方案**：`/sybermem-init-project` 在**全新项目**上**征询后**（opt-in）生成 1 条示例 change record，让新用户立刻看到记忆格式并能试 `/sybermem-resume`。
- **实现**：init SKILL 新增 Step 7.5——仅限 fresh 新项目、必须显式同意、走 record fast path、走 index build/check；**existing-codebase 扫描与 refresh 一律不生成**，严守「scan but don't auto-create records」不变式。summary 的 Next steps 增一句引导。
- **落地点**：`sybermem-init-project/SKILL.md`（+镜像）。

### 2.2 效果提高

#### E1. 召回「高信号精准注入」【立即】✅
- **痛点**：每条合格 prompt 都词法扫描 + 注入，既漏召回又偶尔注入噪音。
- **方案**：
  - 提高触发门槛：只在命中 record-id / relation / 显著高分（score ≥ 12）时注入，否则静默。**宁缺毋滥**——错误召回比不召回更伤信任。
  - abstention 原因写本地 debug 日志（hook 当前未开 `include_abstention`，agent 看不到为何不召回）。
- **落地点**：`search.py:high_signal_recall_hints`（新增 core 契约，含高信号门 + abstention 原因）、`.sybermem/hooks/task_recall.py`（调用 + 写 `.recall-debug.jsonl` 有界日志）。
- **实现**：`HIGH_SIGNAL_SCORE_FLOOR=12.0`；hook 只 import `high_signal_recall_hints`，两份分发模板已同步；debug 日志滚动上限 200 行、不存 prompt payload、已 gitignore。
- **验证**：core 全量 123 passed（含 3 个新 E1 测试）；对本项目实测——`change-047`（record-id 命中）注入成功，泛泛「project change history」保持静默并写入 abstention 日志。

#### E2. 轻量语义召回（opt-in）【增强】✅
- **决策**：用**纯本地 char n-gram + hashing trick + 余弦**（零依赖），不引入 torch/onnx/模型下载——契合「无第三方重依赖、离线、Markdown 为真源」。它不是 transformer embedding，捕捉的是词法/形态重叠（共享子串、词序无关、抗小改动/CJK），能补回相当一部分同义/改写/拼写变体的漏召回。
- **实现**：新增 `semantic_recall.py`（`build_vector`/`cosine`/`semantic_scores`，FNV 确定性哈希、L2 归一化稀疏向量）。`compact_project_search` 在 **opt-in 开关** `SYBERMEM_SEMANTIC_RECALL=1` 下，对词法漏召回的 record 追加语义候选，tag `match="semantic"`，相似度映射到 [5,10) 的 bounded score。
- **经济性与安全**：**默认关**（热路径 token/compute 经济性不变）；语义命中**永远低于高信号门（12）**，只在显式 search 出现、绝不自动注入 hook；E5 排序里 semantic 具体度最低，不会盖过精准词法命中。
- **落地点**：`semantic_recall.py`、`search.py`（`_add_semantic_supplement` + 开关）。
- **验证**：4 个新测试（cosine 性质、形态相关排序、默认关无补充、开启后补回 authenticating→authentication 这类词法漏召回且 score<12）；core 全量 137 passed。

#### E3. digest 陈旧机械检测【立即】✅
- **痛点**：digest 是 AI 写的，源 record 变了不失效（theme-digest hooks 那条已被 change-047 推翻却仍显权威）。
- **方案**：给 digest 加 `coverage_hash`（对 `source_records` 当前内容的确定性哈希）；search 比对源文件，不符标 `stale`。**纯确定性、归 core**。
- **落地点**：新增 `digest_coverage.py`（`compute_coverage_hash` / `digest_coverage_verdict`）；`search.py:_annotate_digest_coverage` 在 search 结果中机械降级 stale digest。
- **契约**：只有声明 `coverage_hash` 的 digest 可校验；旧 digest 无此字段返回 `unknown`（绝不误报 stale），向后兼容零改动。缺失源文件参与哈希为显式 `<missing>` 标记。
- **待接**：digest 生成 skill 需在写 digest 时输出 `coverage_hash`（下一步 skill 侧改动；core 侧机制已就绪）。
- **验证**：core 全量 123 passed（含 5 个新 E3 测试，覆盖 unknown/current→stale/search 降级）。

#### E4. 信任元数据「声明」优先，推断兜底【短期】✅
- **痛点**：source_kind 靠路径子串、authority 靠 marker、archived 靠 INDEX 段落，易漂移。
- **方案**：可选显式 `source_kind`/`authority`/`lifecycle` frontmatter，core 优先读显式值，字符串推断降级为 legacy 兜底。旧 record 零改动。
- **实现**：`classify_source_kind/authority/lifecycle` 增 `declared` 参数（**仅识别合法值**，typo/未知值忽略→回退推断，防止坏 record 污染分类）；`records.parse_record_file` 解析可选 `authority:`/`lifecycle:`；`derive_continuity_metadata` 与 resume 两处 authoritative 过滤都改为声明优先。record SKILL 记录了可选字段用法。
- **落地点**：`retrieval.py`、`records.py`、`resume.py`、`sybermem-record/SKILL.md`（+镜像）。
- **验证**：3 个新测试（声明覆盖、非法值回退、evidence 降级）；core 全量 129 passed。

#### E5. 召回排序纳入「相关性具体度」【中期】✅
- **痛点**：排序 authority→freshness→score→date，新泛泛 record 压过老精准 record（Oracle 举的 change-048 压 change-037）。
- **方案**：把 match 具体度提到排序前列。
- **实现**：新排序键 `(authority, specificity, freshness, score, created)`，`specificity` = record-id(0)>relation(1)>topic(2)>keyword(3)。authority 仍领先（不让 evidence 盖过 authoritative），但同信任层内精准匹配不再被更新的泛匹配埋没，recency 仅作最终 tiebreak。
- **落地点**：`search.py:_compact_sort_key`。
- **验证**：新测试——老的 topic 精准匹配排在更新的 keyword 泛匹配之前；core 全量 130+ passed。

#### B1. `fixed` 状态 bug 被误判为 open【中期】✅（A4 暴露的既有缺陷）
- **痛点**：`status.py` 只把 `status == "resolved"` 视为关闭，但 bug 记录普遍用 `status: fixed`，导致所有 fixed bug 被当成 open——A4 简报把「open items」摆到最显眼处后立刻暴露。`retrieval.classify_lifecycle` 也只认 `resolved/completed/done`，同源不一致。
- **方案**：单一真源 `TERMINAL_STATUSES = {resolved, fixed, completed, done, closed}` + `is_open_status()`；status 开放判定与 lifecycle 分类都复用。无 status 字段的 record 保守视为 open。
- **落地点**：`retrieval.py`（常量 + helper）、`status.py`（open_bugs/open_requirements）。
- **验证**：新测试（fixed/resolved 关闭、无 status 保持 open）；实测本项目 3 个 fixed bug 从 open 列表消失。

#### E6. 召回命中率可度量【中期】✅
- **方案**：记录「注入了哪条 + match 类型」与「为何 abstain」到本地日志，建立召回质量基线，数据驱动阈值调优（支撑 E1）。
- **实现**：把 E1 的 `log_abstention` 泛化为 `log_recall_event(root, event, **fields)`，同时记 `inject`（record_id + match）与 `abstain`（reason）事件到 `.recall-debug.jsonl`（有界 200 行、不存 prompt、不落 stdout）。
- **落地点**：`.sybermem/hooks/task_recall.py`（+2 分发拷贝，已同步）。
- **验证**：实测 record-id 命中 prompt 写出 `inject` 事件含 `change-047 / record-id`。

### 2.3 分发链路完整性

#### D1. 改进必须能传播到分发包与存量项目【立即】✅（本轮缺陷已修）
- **痛点（核心风险）**：SyberMem 的受管文件（hooks / templates / instruction blocks）存在多份拷贝——项目本地 `.sybermem/`、分发源 `packages/claude-skills/.../project-files/`、镜像 `skills/.../project-files/`。一个改进如果只改了其中一份，就会出现「新装用户拿不到」或「存量项目 `/sybermem-update` 拿不到」的静默断链。历史上 bug-001 / bug-004 都是这类断链。
- **本轮暴露的具体缺陷**：`check_project_health.py` 对 `digest-template.md` 只做 `check_file_exists`（存在即 fresh），从不比对内容。因此 E3 给模板加 `coverage_hash` 后，**存量项目跑 `/sybermem-update` 不会被替换**——改进传不下去。
- **本轮修复**：
  - `digest-template.md` 改为内容感知的 `check_digest_template`（缺 `coverage_hash:` → stale → replace），`generate_actions` 增加对应 replace 动作。
  - E3 / E1 的所有受管文件拷贝已全部同步（digest 模板 3 份、digest SKILL 2 份、task_recall hook 3 份、health-check 3 份）。
- **待补的通用护栏（后续）**：
  1. **分发一致性测试**：对每一类受管文件断言「所有分发拷贝 byte-identical」（task_recall 已有此测试；应扩展到 digest 模板、health-check、其余 hooks）。
  2. **受管文件清单单一真源**：把「哪些是受管文件 + 用哪种 check（存在/内容/协议块）」收敛到一处声明，避免 `main()` 文件映射与 `generate_actions` 两处各写一遍导致漏项（如本次 `digest-template` 就是漏项）。
  3. **能力→传播 检查项**：任何新增「能力字段」（如 `coverage_hash`）都必须同时提供 health-check 的 stale 判据，否则视为分发未完成。
- **落地点**：`.sybermem/hooks/check_project_health.py`（+2 分发拷贝）、`packages/core/tests/test_init_project_distribution.py`（一致性/传播回归）。

### 2.4 治理/诚实

#### G4. publish hash 正名【增强】✅
- **权衡**：`source_hash` 是跨 payload / 持久化 meta.json / CLI flag / Team summary 消费方的稳定契约键，直接改键名会破坏已发布 meta.json 与 flag 契约（违反最小改动+向后兼容）。
- **方案**：**不改持久化字段键**，改**用户可见文案**——preview 文本改为「memory source hash」并附一行范围说明「project_records_digests_identity — 一个 stale-preview 防护，而非完整发布安全证明」；stale_preview 拒绝文案也说明「项目记忆自 review 后已变」。诚实标注能力边界，零契约破坏。
- **落地点**：`cli/publish_render.py`。实测渲染正确。

#### G5. archived 真源归位【增强】✅（机制由 E4 提供）
- **方案**：archived 状态落 record frontmatter（`lifecycle: archived`），INDEX 派生只作 fallback。
- **实现**：E4 已让 `classify_lifecycle` 声明优先——`lifecycle: archived` frontmatter 直接胜出，无需 INDEX 段落。本轮补一个测试锁定「声明 archived 无需 INDEX 条目即生效」，record SKILL 已在 E4 记录该字段用法。派生产物（INDEX）不再是 archived 的唯一真源。
- **落地点**：`retrieval.py`（E4 已改）、`test_retrieval.py`（本轮新测试）。

#### E2. 轻量语义召回（opt-in）【增强】⬜ 待评估
- 见 2.2 E2。工作量最大（本地 embedding + 混合检索），建议单独立项，不与小项混做。

---

## 3. 执行顺序

| 阶段 | 举措 | 理由 |
|------|------|------|
| **立即** | E1、E3 | 直接堵信任漏洞 + 省 token，工作量小 |
| **短期** | A1、A3、E4 | 可用性和效果最大杠杆，复用现有逻辑 |
| **中期** | A2、E5、E6、A4 | 打磨体验、建立度量 |
| **增强** | E2、A5、G4、G5 | opt-in / 锦上添花 |

每完成一项：更新第 0 节看板状态，并按 `/sybermem-record` 约定写 canonical record。

---

## 4. 参考（相关记录）
- P0 修复：`bug-2ffd869fce244c4c8d7e1305e674c60d`
- UUID 迁移：`change-6a3ab8a0e44e4c41843b66bde8b7134a`
- 连续性/信任层设计决策：`decision-002`
- 压缩需求源头：`requirement-002`
