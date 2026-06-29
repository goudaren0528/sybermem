# SyberMem Install/Update Script Skill List Catch-up 设计

> 让脚本安装/更新路径分发 `sybermem-search`、`sybermem-link`、`sybermem-theme-digest`，补齐当前 8→11 skill 的落差。

**Date:** 2026-06-29
**Status:** Draft
**Scope:** 最小修复。只补 6 个脚本中的硬编码 skill 列表和 help 文案，不做脚本去硬编码化。

---

## 1. Background & Problem

SyberMem 后续新增了 3 个 skill：
- `sybermem-search`
- `sybermem-link`
- `sybermem-theme-digest`

但 6 个安装/更新脚本仍然只分发旧的 8 个 skill：
- `install.sh`
- `install.ps1`
- `install-remote.sh`
- `install-remote.ps1`
- `update.sh`
- `update.ps1`

结果：
- repo 里有这 3 个新 skill ✅
- plugin `skills/` 树里有这 3 个新 skill ✅
- 但用户走脚本安装/更新路径时，可能拿不到这 3 个新 skill ❌

这是一个分发层遗漏，不是功能层问题。

---

## 2. Design

### 2.1 修复原则

采用**最小修复**：
- 不改变安装路径
- 不改变脚本结构
- 不引入共享配置文件
- 不自动从 `packages/claude-skills/` 动态发现 skill
- 只把 6 个脚本中的硬编码 skill 列表从 8 个补到 11 个
- 同时更新安装完成后的“可用 Skills”帮助文案

### 2.2 新的 11 个 skill 列表

```text
sybermem-init-project
sybermem-record
sybermem-summary
sybermem-digest
sybermem-phase-analyze
sybermem-phase-confirm
using-sybermem
sybermem-update
sybermem-search
sybermem-link
sybermem-theme-digest
```

### 2.3 受影响脚本

| 文件 | 改动 |
|---|---|
| `scripts/install.sh` | skill copy loop + help 文案 |
| `scripts/install.ps1` | skill copy loop + help 文案 |
| `scripts/install-remote.sh` | skill copy loop + help 文案 |
| `scripts/install-remote.ps1` | skill copy loop + help 文案 |
| `scripts/update.sh` | skill copy loop + help 文案 |
| `scripts/update.ps1` | skill copy loop + help 文案 |

### 2.4 Help 文案新增的 3 行

```text
/sybermem-search       — Search/query records by keyword, topic, phase range, date range, or record ID
/sybermem-link         — Add a forward relation between two existing records
/sybermem-theme-digest — Create a durable topic-level digest that compresses one theme across multiple related phases or records
```

### 2.5 不做的事

本次明确不做：
- skill 列表去硬编码化
- 从 `packages/claude-skills/` 自动发现目录
- 把脚本安装路径降级为 legacy / 迁移到 plugin-only
- 重构 install/update 脚本共享逻辑

这些属于后续的“脚本可维护性优化”，不是当前最小修复目标。

---

## 3. Verification

### 3.1 本地脚本 smoke test

运行：
- `scripts/update.ps1`
- 或 `scripts/install.ps1`

预期：输出里显示 11 个 skill 全部“已更新”/“已安装”。

### 3.2 目录验证

检查以下目录存在：

```text
~/.claude/skills/sybermem-search/
~/.claude/skills/sybermem-link/
~/.claude/skills/sybermem-theme-digest/
~/.config/opencode/skills/sybermem-search/
~/.config/opencode/skills/sybermem-link/
~/.config/opencode/skills/sybermem-theme-digest/
```

### 3.3 文案验证

脚本结尾的“可用 Skills”列表包含上述 3 个新条目。

---

## 4. Success Criteria

1. 6 个 install/update 脚本都复制 11 个 skill，而不是旧 8 个
2. Claude Code 用户目录获得 `sybermem-search` / `sybermem-link` / `sybermem-theme-digest`
3. OpenCode 用户目录同样获得这 3 个新 skill
4. 脚本输出的 help 文案同步显示 11 个 skill
5. 不改变其他安装行为
