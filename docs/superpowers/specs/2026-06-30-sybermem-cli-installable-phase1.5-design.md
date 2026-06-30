# SyberMem CLI 可安装化 / 调用体验完善（Phase 1.5）设计

> 在 Core Phase 1 的基础上，去掉 `PYTHONPATH=... python -m ...` 的粗糙调用方式，为用户提供可安装的 `sybermem` 命令与统一调用体验。

**Date:** 2026-06-30
**Status:** Draft
**Scope:** Phase 1.5。CLI 可安装化、wrapper、install/update 脚本支持、文档与 Skill 迁移到 `sybermem ...`。不迁移 hooks 到 CLI。
**Parent spec:** `docs/superpowers/specs/2026-06-30-sybermem-core-phase1-design.md`

---

## 1. Background & Problem

Phase 1 已经交付了最小可用 Core / CLI：
- `sybermem project init --register`
- `sybermem index build`
- `sybermem search --scope project|workspace`

但当前调用方式仍然很粗糙：

```bash
PYTHONPATH=packages/core;packages/cli python -m sybermem_cli.main ...
```

这有几个问题：
- 普通用户无法接受这种命令形态
- README / Skill 文档不适合长期展示这种实现细节
- CLI 无法作为一个稳定的工具路径被其他脚本和未来 Skill 调用
- 与现有 `~/.claude/sybermem/launch_record_change_on_stop.py` / `launch_session_start_context.py` 的固定分发模式不一致

Phase 1.5 的目标是把 CLI 变成一个真正可安装、可调用的工具，同时不打断现有 hooks 和 Skill 的工作方式。

---

## 2. Design Goal

用户在安装 / 更新 SyberMem 后，应该能直接运行：

```bash
sybermem project init --register
sybermem index build
sybermem search hooks --scope workspace
```

不再需要看到：

```bash
PYTHONPATH=packages/core;packages/cli python -m sybermem_cli.main ...
```

---

## 3. Design Choice

采用 **脚本安装 + 固定运行时目录**。

### 安装位置

```text
~/.claude/sybermem/cli/
├── venv/
├── sybermem      # Unix wrapper
└── sybermem.cmd  # Windows wrapper
```

### 原则

- 不污染系统 Python
- 不依赖用户 PATH 状态
- 继续沿用现有 `~/.claude/sybermem/` 固定目录模式
- install/update 脚本负责创建和刷新 CLI
- 文档和 Skill 统一改用 `sybermem ...`

---

## 4. Install / Update Script Changes

现有脚本已经负责：
- 分发 skills 到 `~/.claude/skills/`
- 安装全局 launchers 到 `~/.claude/sybermem/`

Phase 1.5 新增职责：

1. 创建 CLI 目录：
   - `~/.claude/sybermem/cli/`
2. 创建虚拟环境：
   - `python -m venv ~/.claude/sybermem/cli/venv`
3. 安装 `packages/core` 和 `packages/cli`
4. 创建 wrapper：
   - Windows: `sybermem.cmd`
   - Unix: `sybermem`
5. 输出提示：
   - CLI 已安装
   - 示例命令：`sybermem project init --register`

### 支持的脚本

| 文件 | 需要改动 |
|---|---|
| `scripts/install.sh` | 安装 CLI + Unix wrapper |
| `scripts/install.ps1` | 安装 CLI + Windows wrapper |
| `scripts/install-remote.sh` | 从远程归档安装 CLI |
| `scripts/install-remote.ps1` | 从远程归档安装 CLI |
| `scripts/update.sh` | 更新 CLI |
| `scripts/update.ps1` | 更新 CLI |

---

## 5. Wrapper Design

### 5.1 Windows

文件：`~/.claude/sybermem/cli/sybermem.cmd`

```cmd
@echo off
set "SYBERMEM_HOME=%USERPROFILE%\.claude\sybermem\cli"
"%SYBERMEM_HOME%\venv\Scripts\sybermem.exe" %*
```

### 5.2 Unix

文件：`~/.claude/sybermem/cli/sybermem`

```bash
#!/bin/bash
SYBERMEM_HOME="$HOME/.claude/sybermem/cli"
exec "$SYBERMEM_HOME/venv/bin/sybermem" "$@"
```

### 5.3 为什么不用系统 PATH 直接安装

- 不污染全局 Python 环境
- 不依赖用户 PATH / shell profile
- 与现有 launcher 分发模式一致
- hook 和脚本调用都可以走稳定的固定路径

---

## 6. 现有 launcher 的策略

现有：
- `~/.claude/sybermem/launch_record_change_on_stop.py`
- `~/.claude/sybermem/launch_session_start_context.py`

### Phase 1.5 选择

**保留，不迁移到 CLI。**

理由：
- 这两个 launcher 已经稳定工作
- Phase 1.5 只改善“用户调用 CLI”的体验
- hook 迁到 CLI 是更大的变更，应该在后续单独设计和验证

因此：
- CLI 安装化 ≠ hook runtime 重写
- 现有 hooks 保持 Python launcher 路线不变

---

## 7. Skill / Doc 迁移规则

### 7.1 Skill

第一个接入 CLI 的 Skill 继续是：
- `/sybermem-search --scope workspace`

其文档和提示改成：

```text
sybermem search <query> --scope workspace --format json
```

而不是：

```text
PYTHONPATH=... python -m sybermem_cli.main search ...
```

### 7.2 文档

以下文档中涉及 CLI 的地方统一切换到 `sybermem ...`：
- `README.md`
- `README.en.md`
- `docs/zh/README.md`
- Core Phase 1 spec / plan（引用时同步更新）
- 未来所有提到 CLI 的文档

### 7.3 兼容期

对开发者来说，仓库里仍然可以直接：

```bash
PYTHONPATH=packages/core;packages/cli python -m sybermem_cli.main ...
```

但这不再出现在用户文档和用户-facing Skill 中。

---

## 8. Backward Compatibility

- 旧安装用户：跑一次 install/update 脚本即可获得 CLI wrapper
- 现有 hooks：不受影响
- 现有 Skills：不需要一次性全改，只是文档和未来调用路径切换
- CLI 没安装时，workspace search 仍可暂时 fallback 到旧的 AI 遍历模式（直到 Skill 完全切换）

---

## 9. Verification

### 核心成功标准

1. 运行 install/update 脚本后，存在：
   - `~/.claude/sybermem/cli/venv/`
   - `~/.claude/sybermem/cli/sybermem.cmd`（Windows）
   - `~/.claude/sybermem/cli/sybermem`（Unix）
2. 直接运行成功：
   - `sybermem project init --register --format json`
   - `sybermem index build --format json`
   - `sybermem search hooks --scope workspace --format json`
3. 现有 launchers 仍正常工作
4. README / Skill 不再暴露 `PYTHONPATH=... python -m ...`

### 推荐 smoke chain

```text
scripts/update.ps1
→ sybermem project init --register
→ sybermem index build
→ sybermem search hooks --scope workspace
```

如果这条链完整跑通，Phase 1.5 成功。

---

## 10. Out of Scope

本阶段明确不做：
- hooks 全面迁移到 CLI
- Team / Lesson / Portfolio
- pipx / uv tool 作为默认安装方式
- 修改用户 shell profile / PATH
- Windows MSI / installer
- Core 功能扩展（仅安装与 UX）

---

## 11. Success Criteria

1. `sybermem` 成为可调用命令（无需 `PYTHONPATH`）
2. install/update 脚本都能安装和刷新 CLI
3. 文档和 Skill 用 `sybermem ...` 作为标准调用形式
4. hooks 不回归
5. 未来 Skill 调用 CLI 有稳定路径可依赖
