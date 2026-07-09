# SyberMem Two-Layer Uninstall Model 设计

> 将“卸载 SyberMem”明确拆成两层：项目级停用（保留历史，停用运行时接管）与全局级卸载（删除全局 skills/CLI/launcher，不碰项目历史）。

**Date:** 2026-07-09
**Status:** Draft
**Scope:** 只定义卸载模型、边界和目标行为；不实现具体命令。覆盖项目级停用与全局级卸载两层。

---

## 1. Background & Problem

用户对“卸载 SyberMem”的真实需求并不单一，而是两种完全不同的场景：

1. **当前项目不再由 SyberMem 接管，但历史内容要保留**
2. **当前机器不再安装 SyberMem 全局能力，但已有项目历史不要被删**

如果把这两类需求混在同一个模糊的“uninstall”动作里，会带来：
- 容易误删历史
- 容易混淆作用范围（当前项目 vs 当前机器）
- 难以解释执行后的真实结果

因此需要一个明确的两层卸载模型。

---

## 2. Design Goal

把“卸载 SyberMem”拆成两层：

### Layer 1: 项目级卸载
目标：
> 保留 `.sybermem/` 历史内容，但停用当前项目中的 SyberMem 运行时接管。

### Layer 2: 全局级卸载
目标：
> 删除当前用户机器上的 SyberMem 全局安装，但不碰任何项目中的历史内容。

---

## 3. Layer 1 — Project Uninstall

### 保留
- `.sybermem/`
- records / digests / theme-digests / analysis
- `.sybermem/project.yaml`
- Team repo 中已经发布的内容（间接保留）

### 停用
- `.claude/settings.json` 中的 SyberMem hooks
- `SYBERMEM_RECORD_MODE`
- `CLAUDE.md` / `AGENTS.md` 中 SyberMem 工作流主导内容
- Team publish / Team summary 的运行时触发入口

### 预期结果
进入该项目时：
- 不再自动加载 SyberMem 工作流
- 不再自动记录 / 自动提醒
- 不再自动 Team publish / Team summary 路由
- 但历史仍然完整可回看，未来也可重新接回

---

## 4. Layer 2 — Global Uninstall

### 删除
- `~/.claude/skills/sybermem-*`
- `~/.config/opencode/skills/sybermem-*`
- `~/.claude/sybermem/cli/`
- `~/.claude/sybermem/launch_record_change_on_stop.py`
- `~/.claude/sybermem/launch_session_start_context.py`
- OpenCode plugin 副本（若存在）

### 不动
- 任意项目中的 `.sybermem/`
- 任意项目中的 `project.yaml`
- 任意 Team repo
- 已有 records / digests / phase-index / summaries

### 预期结果
当前机器上不再有：
- SyberMem slash skills
- SyberMem CLI
- SyberMem launchers / plugin

但项目历史完全保留。

---

## 5. Recommended Command Model

### 项目级卸载
建议作为独立入口：

```text
/sybermem-project-uninstall
```

### 全局级卸载
建议作为独立入口：

```text
/sybermem-uninstall
```

### 为什么不合并成一个命令
如果只做一个命令，再靠参数区分：
- `--project-only`
- `--global`
- `--preserve-history`

会让用户很容易误解和误操作。分成两个入口更安全，语义也更清晰。

---

## 6. Project Uninstall Behavior Details

### `.claude/settings.json`
应移除或停用：
- `SessionStart`
- `Stop`
- `UserPromptSubmit`
- `env.SYBERMEM_RECORD_MODE`

### `CLAUDE.md` / `AGENTS.md`
分两种情况：

#### A. 纯 SyberMem-managed 文件
- 可以整体替换为极简停用说明，或删除 SyberMem 主协议内容

#### B. 用户自定义文件
- 只移除 SyberMem 的 bounded protocol block
- 保留用户自定义内容

### 关键原则
> **保留历史，不保留运行时接管。**

---

## 7. Global Uninstall Behavior Details

### 清理对象
- 全局 slash skills
- 全局 CLI
- 全局 launcher
- OpenCode plugin 副本

### 输出说明
全局卸载完成后，系统应明确告诉用户：
- 全局能力已移除
- 现有项目中的 `.sybermem/` 历史内容未删除
- 若未来重新安装，可继续基于现有历史恢复

---

## 8. Reversibility

### Project Uninstall
可逆：
- 之后再次运行 `/sybermem-update` 或 `/sybermem-init-project`
- 即可重新启用 hooks / protocol / runtime integration

### Global Uninstall
可逆：
- 重新执行 install / update
- 即可恢复全局 skills / CLI / launcher

---

## 9. Safety Principles

1. **Never delete `.sybermem/` automatically**
2. **Always distinguish project scope from global scope**
3. **Only remove runtime integration, not historical content**
4. **Project-level uninstall must preserve user custom files outside SyberMem-managed sections**
5. **Uninstall should be reversible**

---

## 10. Out of Scope

本轮不做：
- 真正实现命令
- Team repo 清理 / archive
- selective uninstall（只卸载 Team 但保留 Project runtime）

---

## 11. Success Criteria

1. 项目级卸载和全局级卸载语义明确分离
2. 项目级卸载保留 `.sybermem/` 历史但停用运行时接管
3. 全局级卸载只清当前机器上的全局能力，不碰项目历史
4. 两层卸载都具备明确、可逆、低误操作风险的行为模型
