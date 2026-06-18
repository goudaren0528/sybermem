# SyberMem Lifecycle Layer 设计

> 把 SyberMem 嵌入 Claude Code / OpenCode 的使用生命周期：开始时给相关历史，工作中少量提示，结束时补记录，压缩时保记忆。

**Date:** 2026-06-18  
**Status:** Draft  
**Scope:** A（会话开始更聪明） + B（工作结束更无感） + C（双平台协同）  
**Notification level:** 关键节点提示

---

## 1. Background & Problem

SyberMem 已有 8 个 skills、Stop hook auto-trail、OpenCode plugin (session.created / session.idle / session.compacting)、以及 `/using-sybermem` 可见诊断入口。

但实际体验还有几个断层：

1. **启动时不像 Superpower 那样自然触发。** `/using-sybermem` 是 skill 不是 hook，不能确定性地在项目对话开始时注入记忆上下文。依赖 `CLAUDE.md` 里的行为指令，但模型不一定每次都主动执行。
2. **结束时 auto trail 足够轻量，但"该不该补 manual record / digest / phase-analyze"的提示信号还不完整。** 缺少 commit-gap 检测和跨平台 nudge 去重。
3. **Claude Code 和 OpenCode 各自实现相似逻辑，nudge state 不共享。** 交替使用两个工具时可能重复提示。

---

## 2. Design Goal

把触发点统一抽象为 4 个生命周期事件，形成闭环：

| 事件 | 目的 |
|---|---|
| Session Start | 注入项目记忆上下文，让 AI 启动即知晓历史 |
| Work Signal | 工作中命中 topic 时低噪声关联历史 |
| Session Idle / Stop | 判断是否需要 record / digest / phase-analyze |
| Compaction | 压缩前保留关键结论和阶段上下文 |

---

## 3. Architecture

```text
SyberMem Lifecycle Layer
├── Memory Reader
│   ├── parse Key Conclusions
│   ├── parse Topic Index
│   ├── parse phase-index (status, active phase, boundaries)
│   └── detect freshness / boundary gap
│
├── Signal / Nudge Policy
│   ├── startup relevance policy
│   ├── record nudge policy (high-signal, commit-gap)
│   ├── digest nudge policy (theme cluster, phase stability)
│   ├── phase-analyze stale policy (git boundary gap)
│   └── cross-platform nudge dedup
│
├── Claude Code Adapter
│   ├── SessionStart hook → startup context injection
│   └── Stop hook → auto trail + record/digest/analyze nudges
│
├── OpenCode Adapter
│   ├── session.created → toast + context
│   ├── session.idle → change detection + nudge
│   └── session.compacting → memory injection
│
└── Visible Skill Layer
    └── /using-sybermem → diagnostic report (unchanged role)
```

### Key Principles

- **启动 hook 只注入事实，不发号施令。** 避免 prompt-injection 风险。
- **Skill 做诊断，不承担自动生命周期触发。** `/using-sybermem` 是可见面板，不是 startup 机制。
- **Claude Code 和 OpenCode 共享语义策略，但不强求触发点一致。** 各用各平台最擅长的 hook/plugin 特性。
- **默认关键节点提示。** 不做高频 toast。
- **有 stale 检测。** phase-index 落后 git boundary、commit gap、digest 覆盖落后都会在合适时机提示。

---

## 4. Session Start — 确定性启动层

### 4.1 Claude Code SessionStart Hook

新增脚本：`.sybermem/hooks/session_start_context.py`

匹配器：`startup`、`resume`、`clear`、`compact`

> **实现时验证：** Claude Code SessionStart hook 是否支持 matchers 字段以及 `compact` matcher。如果不支持 matchers 细分，hook 默认在所有 session start 场景触发即可满足 startup / resume / clear；compact 恢复记忆则降级为 CLAUDE.md 协议。

行为：

1. Resolve project root（复用已有 `resolve_sybermem_root()` 逻辑）
2. 读取 `.sybermem/INDEX.md` 的 `## Key Conclusions`
3. 读取 `## Topic Index`
4. 读取 `.sybermem/analysis/phase-index.md` 的 status、last_git_boundary、最近 confirmed phase
5. 比较 `last_git_boundary` 与当前 `git rev-parse HEAD`，计算 commits ahead
6. 输出结构化 JSON `hookSpecificOutput.additionalContext`

示例输出（注入到 Claude 上下文）：

```text
SyberMem startup context:
Loaded 8 key conclusions from SyberMem.
Relevant topics: hooks, automation, digest, compression, skills, framework, init, distribution, install.
Phase index: analyzed. 6 confirmed phases.
Active phase: Phase analysis and digest automation.
Stale signal: phase-index last git boundary is 8a8ecde, current HEAD is 7e55768 (3 commits ahead).
```

对用户可见部分保持短（Claude 模型根据 context 决定在第一条回复里展示摘要）：

```text
Loaded 8 key conclusions from SyberMem.
```

如有 stale signal，补一句：

```text
Phase index is 3 commits behind HEAD — consider /sybermem-phase-analyze.
```

### 4.2 settings.json 变更

```json
{
  "env": {
    "SYBERMEM_RECORD_MODE": "auto"
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/69046/.claude/sybermem/launch_session_start_context.py",
            "timeout": 15,
            "statusMessage": "SyberMem loading project memory..."
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/69046/.claude/sybermem/launch_record_change_on_stop.py",
            "timeout": 60,
            "statusMessage": "SyberMem checking whether to record a change..."
          }
        ]
      }
    ]
  }
}
```

### 4.3 OpenCode session.created

已有 toast 展示 conclusions 数量。增强为：

- 同样检测 phase-index stale signal
- 如果 stale，toast 多显示一行

### 4.4 `/using-sybermem` 定位不变

| 场景 | 机制 |
|---|---|
| 启动自动加载项目记忆 | `SessionStart` hook |
| 用户想看完整状态 | `/using-sybermem` |
| 模型发现 SyberMem 异常 | 主动调用 `/using-sybermem` |

---

## 5. Work Signal — Topic-Aware Recall

当用户的问题命中 Topic Index 中的关键词时，模型可利用 startup context 中注入的 Topic Index 做关联。

例如用户问："OpenCode plugin 怎么触发？"

模型在 context 中已有：

```text
hooks: change-003, change-005, bug-001
```

可直接引用相关历史，无需重新读全库。

这不是新的触发机制，而是 SessionStart 注入 Topic Index 后的自然结果。模型按需读取具体 record 文件。

---

## 6. Session Idle / Stop — 结束记录层

### 6.1 记录完整性信号

在 nudge policy 判断时即时计算，不存储为单独文件：

| 信号 | 含义 |
|---|---|
| `has_auto_trail` | Stop hook 已写轻量 change trail |
| `has_manual_record` | 有 `/sybermem-record` 产物 |
| `has_reason` | manual record 包含原因/影响 |
| `has_phase_coverage` | phase-index 已覆盖此工作 |
| `has_digest` | 对应 phase 已有 digest |
| `is_high_signal` | 命中 high-signal patterns（README, SKILL.md, hook, script, spec） |

判断逻辑：

```text
if has_auto_trail && is_high_signal && !has_manual_record:
    → "this change looks important enough for /sybermem-record"

if has_manual_record && has_phase_coverage && phase_is_stable && !has_digest:
    → "this phase may be ready for /sybermem-digest"

if !has_phase_coverage && git_ahead_of_boundary:
    → "consider /sybermem-phase-analyze to index recent work"
```

### 6.2 Stop Hook 增强

在现有 `record_change_on_stop.py` 中增加：

1. **Commit-gap 检测：** 读取最近 record date，计算 `git log --oneline --since=<date>` 的行数。如果 ≥10，附加提示。
2. **Auto trail 去重增强：** 写入前检查最近 3 条 auto trail 的 `related_files`，如果与当前有 >80% 重叠则 skip。

### 6.3 OpenCode session.idle

已有变更检测和 toast。增强：

1. 对齐 commit-gap 检测逻辑（已有 `countCommitsSinceLastRecord`）
2. 读写统一的 `.nudge-state.json`（见 §7）

### 6.4 提示级别

| 级别 | 条件 | 行为 |
|---|---|---|
| 静默 | 无变更 / soft-skip only / 低信号 | 不提示 |
| 短提示 | 多文件变更 / 高信号 / commit gap ≥10 | 一句话建议 |
| 阶段提示 | theme cluster + phase stable / phase-index stale ≥5 commits | 建议 digest 或 analyze |

---

## 7. Cross-Platform Nudge Dedup

### 7.1 统一 nudge state 文件

合并 `.auto-nudge-state.json` 和 `.opencode-nudge-state.json` 为：

```text
.sybermem/.nudge-state.json
```

字段结构：

```json
{
  "theme_recent_stops": {
    "docs-scripts": ["2026-06-16", "2026-06-17"]
  },
  "digest_nudged_at_window_len": {
    "docs-scripts": 2
  },
  "last_nudge": {
    "platform": "claude-code",
    "type": "record",
    "theme": "docs-scripts",
    "date": "2026-06-17"
  }
}
```

### 7.2 向后兼容

- 如果 `.auto-nudge-state.json` 存在但 `.nudge-state.json` 不存在，首次写入时迁移旧数据到新文件。
- 如果 `.opencode-nudge-state.json` 存在，同理迁移。
- 旧文件迁移后不删除，但不再更新。后续手动或 `/sybermem-update` 时清理。

### 7.3 共享 cooldown 规则

- 同一个 theme 在同一 nudge window 里最多提示一次，不分平台。
- `platform` 字段仅用于追踪来源，不参与 cooldown 判断。

---

## 8. Compaction — 压缩前记忆注入

### 8.1 OpenCode session.compacting（已有，增强）

当前注入：

- Key Conclusions
- Active Phase
- Topic Index
- SyberMem Commands

增强为也注入：

- Stale signal（phase-index boundary gap）
- 限制总长度 ≤ 3000 字符，避免 compaction 噪音

### 8.2 Claude Code compact 降级

Claude Code 没有 `session.compacting` plugin API。降级策略：

1. `SessionStart` hook 的 `compact` matcher（**需验证是否支持**）：compact 后重新注入 startup context，等价于 compaction 后恢复记忆。如果 SessionStart hook 不区分 compact 场景，默认行为已经覆盖——每次 session resume 都会重新注入。
2. `CLAUDE.md` 协议继续要求摘要后优先读取 Key Conclusions。

两者叠加，在 compact 场景下也能恢复项目记忆。

---

## 9. Platform Capability Matrix

| 生命周期 | Claude Code | OpenCode | 共享 |
|---|---|---|---|
| 会话开始 | `SessionStart` hook 注入 context | `session.created` toast + context | Memory Reader |
| 工作中 | 模型 + Topic Index context | 模型 + Topic Index context | Topic Index |
| 压缩前 | `SessionStart` compact matcher 重新注入 | `session.compacting` 注入 memory | Memory Reader |
| 会话结束 | `Stop` hook auto trail + nudge | `session.idle` toast + nudge | Nudge Policy, `.nudge-state.json` |
| 诊断 | `/using-sybermem` skill | `/using-sybermem` skill | Skill 定义 |

---

## 10. Implementation File Manifest

| 操作 | 文件 | 说明 |
|---|---|---|
| **新增** | `.sybermem/hooks/session_start_context.py` | SessionStart hook 脚本：读取 conclusions + phase + topics + stale |
| **新增** | `scripts/global-session-start-launcher.py` | 全局 launcher，resolve root 后调用项目内脚本 |
| **修改** | `.claude/settings.json` | 增加 SessionStart hook entry |
| **修改** | `.sybermem/hooks/record_change_on_stop.py` | 加 commit-gap 检测、auto trail 去重增强、读写 `.nudge-state.json` |
| **修改** | `packages/opencode-plugin/sybermem.ts` | nudge state 合并为 `.nudge-state.json`、stale 检测对齐、compaction 增强 |
| **新增** | `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py` | init-project 模板里带 startup 脚本 |
| **修改** | `packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json` | 模板加 SessionStart hook |
| **修改** | `packages/claude-skills/sybermem-init-project/SKILL.md` | init-project 时安装 SessionStart hook |
| **修改** | `scripts/install.sh` / `scripts/install.ps1` | 安装 session start launcher |
| **修改** | `scripts/install-remote.sh` / `scripts/install-remote.ps1` | 同步 session start launcher |
| **修改** | `scripts/update.sh` / `scripts/update.ps1` | 同步 session start launcher |
| **修改** | `README.md` | 更新架构描述，说明 lifecycle layer |
| **不动** | `packages/claude-skills/using-sybermem/SKILL.md` | 继续作为可见诊断入口，定位不变 |

---

## 11. Out of Scope

以下不在本次设计范围内：

- 自动生成 manual record / digest（方案 3 激进版）
- 记录完整性评分面板 / UI
- 新的 slash command
- 修改 `/using-sybermem` skill 行为

---

## 12. Success Criteria

1. Claude Code 启动项目对话时，自动注入 SyberMem 上下文，无需手动 `/using-sybermem`。
2. OpenCode 启动时已有的 toast 继续工作，并增加 stale 检测。
3. Claude Code Stop hook 新增 commit-gap 检测，auto trail 去重减少噪音记录。
4. 两个平台共享 `.nudge-state.json`，交替使用不重复提示。
5. compact 后（两个平台）项目记忆能恢复。
6. 用户不需要记住何时该 record / digest / analyze — 系统在关键节点提示。
