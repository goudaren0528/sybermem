# SyberMem 检索与关系能力设计

> 把 SyberMem 从"记录+分组+压缩"系统,扩展为也能"检索+串联"的项目记忆系统。

**Date:** 2026-06-19
**Status:** Draft
**Scope:** A(检索/查询)+ B(知识关系)。不含 C(规模化压缩)和 D(记录生命周期)。

---

## 1. Background & Problem

能力评估发现:SyberMem 当前是优秀的"记录 + 分组 + 压缩"系统,但检索和关系能力弱。

具体痛点:
1. **找回知识只能手动 grep 或逐条读。** 没有检索 skill。Topic Index 是手动维护的,随规模失效。
2. **记录之间是孤立的。** 无法表达"change-008 实现了 requirement-002"或"bug-001 是 change-003 引入的"。phase 分析只能靠时间/路径/topic 邻近,拿不到用户标注的因果意图。
3. **没有范围查询。** 无法"总结 phase-002 到 phase-004"或"列出某日期段的决策"。

目标:在不破坏 SyberMem 零依赖、纯 markdown、AI 原生理解哲学的前提下,补上检索和关系能力。

---

## 2. Design Decisions

| 决策点 | 选择 | 理由 |
|---|---|---|
| A 检索实现 | AI-驱动 skill | 零依赖,纯 markdown,符合现有哲学 |
| B 关系写入 | 创建时推断 + 专用 link skill | 新记录自然带关系,历史记录可补 |
| B 双向导航 | 只存正向,查询时实时反向扫描 | 零冗余,永不漂移 |

---

## 3. 知识关系数据模型

记录 frontmatter 增加三个可选关系字段:

```yaml
---
type: change
date: 2026-06-18
number: 008
title: Add Claude Code plugin skeleton
status: implemented
related_files: ...
implements: [requirement-002]
fixes: [bug-001]
related: [change-005, decision-003]
---
```

| 字段 | 含义 | 典型方向 |
|---|---|---|
| `implements` | 这条记录实现了某需求/决策 | change → requirement / decision |
| `fixes` | 这条记录修复了某 bug | change / bug → bug |
| `related` | 弱关联,无明确因果 | 任意 → 任意 |

规则:
- 值是记录 ID 数组(如 `requirement-002`、`change-005`)。
- **只存正向**:记录声明自己依赖谁,被依赖者不反向记录。
- 三个字段都可选;没有关系的记录不写这些字段。
- ID 必须是已存在的记录(写入时验证)。

---

## 4. `/sybermem-search` 检索 skill

新增 AI-驱动检索 skill。零依赖,模型用 file-system 工具(Grep/Read)完成。

### 调用语法

```text
/sybermem-search auth                  # 关键词
/sybermem-search #hooks                 # 按 topic
/sybermem-search phase-002..phase-004   # phase 范围
/sybermem-search 2026-05-01..2026-06-15 # 日期范围
/sybermem-search requirement-002        # 按记录 ID(含反向引用)
```

### 检索流程(先廉价后精确)

1. **解析 query 类型**:`#topic` / `phaseN..phaseM` / `date..date` / `type-NNN` ID / 自由关键词。
2. **分层检索**:
   - topic → 查 INDEX.md `## Topic Index`,取记录 ID 列表
   - phase 范围 → 查 phase-index.md coverage map,取覆盖记录
   - 日期范围 → 按记录文件名日期前缀过滤
   - 关键词 → 先 Grep `## Key Conclusions`,再 Grep 记录正文
   - 记录 ID → 定位该记录,并反向扫描所有记录的关系字段找引用者
3. **富化结果**:为每条命中记录附加所属 phase(查 coverage map)和关系字段。
4. **排序输出**:相关度高的在前(关键词命中 Key Conclusions > 命中正文;日期新的优先)。

### 输出格式

```markdown
## SyberMem Search: "auth"

Found N records:

1. **[decision-003]** #auth #security — 一句话结论 (2026-05-20)
   - Phase: phase-002 (Foundation and distribution)
   - File: .sybermem/decisions/2026-05-20-003-...md
   - Relations: implements requirement-002
   - Referenced by: change-008 (implements)

2. ...
```

### 关键设计

- 检索结果**带 phase 归属 + 正向关系 + 反向引用**——这是 A 与 B 互补处。
- 纯 AI 执行,无脚本,无索引文件。
- 当 query 是记录 ID 时,自动计算反向引用(见 §6)。

---

## 5. `/sybermem-link` 关系补充 skill

轻量 skill,事后在两条已有记录间建立/修改正向关系。

### 调用语法

```text
/sybermem-link <source-id> <relation> <target-id>
/sybermem-link change-008 implements requirement-002
/sybermem-link bug-001 related change-003
```

`<relation>` ∈ {`implements`, `fixes`, `related`}。

### 流程

1. 解析 `<source-id> <relation> <target-id>`。
2. 用 file-system 工具验证两条记录都存在;任一不存在则报错停止。
3. 读取 source 记录,在 frontmatter 对应字段追加 target-id(已存在则去重跳过)。
4. **不动 target 记录**(只存正向)。
5. 报告:更新了哪条记录的哪个字段。

### 边界

- 只建立/追加关系,不删除(删除可手动编辑 frontmatter,本次不做 unlink)。
- 不创建记录;两条记录都必须已存在。

---

## 6. 双向导航(查询时实时反向扫描)

因为只存正向,反向关系在查询时算出来,不持久化。

触发:
- `/sybermem-search <record-id>` —— 找出所有指向该 ID 的记录。
- search 输出中,被检索到的记录附带 `Referenced by:` 行。

实现:AI 用 Grep 扫描 `.sybermem/{changes,decisions,requirements,bugs}/` 所有记录的 frontmatter,匹配 `implements`/`fixes`/`related` 字段中包含目标 ID 的记录。零冗余,永不漂移。

---

## 7. record skill 增强(创建时推断关系)

`/sybermem-record` 在创建记录时,AI 从当前会话上下文推断可能的关系,提议给用户确认:

```text
检测到这个 change 可能实现了 requirement-002("阶段总结与压缩需求")。
是否添加 implements: [requirement-002]?
```

- 推断来源:当前会话讨论的需求/bug/决策、改动涉及的功能领域。
- 用户确认后写入 frontmatter 关系字段。
- 用户拒绝或无明显关系则不写。
- 这是**提议**,不是强制;record skill 的核心三步(文件/INDEX 行/Key Conclusion)不受影响。

---

## 8. File Manifest

| 操作 | 文件 | 说明 |
|---|---|---|
| 新增 | `packages/claude-skills/sybermem-search/SKILL.md` | 检索 skill |
| 新增 | `packages/claude-skills/sybermem-link/SKILL.md` | 关系补充 skill |
| 修改 | `packages/claude-skills/sybermem-record/SKILL.md` | 加创建时关系推断步骤 |
| 修改 | `packages/claude-skills/sybermem-record/templates/{change,decision,requirement,bug}.md` | frontmatter 注释说明关系字段 |
| 修改 | `packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md` 和 `AGENTS.md` | skill 列表加 search/link |
| 修改 | 项目根 `CLAUDE.md` / `AGENTS.md` | 同上(保持同步) |
| 修改 | `README.md` | 文档化检索和关系能力 |
| 修改 | `scripts/sync-plugin-skills.py` 触发后的 `skills/` | 同步新 skill 到 plugin 树 |

---

## 9. Backward Compatibility

- 关系字段全部可选;现有记录没有这些字段,照常工作。
- 检索 skill 不依赖任何新文件,可在任何已初始化 SyberMem 项目直接用。
- Topic Index、phase-index、digest 格式不变。
- 不引入任何数据库、索引服务或外部依赖。

---

## 10. Out of Scope

明确不做:
- 全文搜索引擎 / 索引服务(用 AI Grep)
- 持久化反向索引文件(查询时实时扫描)
- phase 层级 / meta-digest(C 组)
- 记录状态工作流 / topic 衰减(D 组)
- 查询语言 DSL(自然语言 + 简单语法即可)
- 关系删除 / unlink(可手动编辑 frontmatter)

---

## 11. Success Criteria

1. `/sybermem-search auth` 返回相关记录,带 phase 归属和关系信息。
2. `/sybermem-search #hooks` 按 topic 检索。
3. `/sybermem-search phase-002..phase-004` 按 phase 范围检索。
4. `/sybermem-search requirement-002` 返回该记录 + 所有引用它的记录(反向)。
5. `/sybermem-link change-008 implements requirement-002` 正确写入 source frontmatter,不动 target。
6. `/sybermem-record` 创建记录时能提议合理的关系关联。
7. 所有现有记录(无关系字段)继续正常工作。
8. 零新依赖。
