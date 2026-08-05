# SyberMem 开源运营成熟度方案

**Date:** 2026-08-05
**Status:** Proposed
**Scope:** LICENSE / CI / Python 包依赖与元数据 / 版本单源 / 社区健康文件
**Source:** docs/audit/2026-08-05-sybermem-comprehensive-audit.md §5（已复核属实）

## 1. 背景与问题

审计 §5 已复核确认（全部属实）：

1. **无 LICENSE 文件**：README/manifest 都写 MIT，但仓库根无 `LICENSE` 文件，法律上不成立。
2. **cli 包依赖缺失**：`packages/cli/pyproject.toml` 的 `dependencies = []`，但 `main.py` 有 12 处 `from sybermem_core.*`。脱离 curl|bash 场景无法独立安装。
3. **version 硬编码散落 8 处**：2 个 pyproject + `.claude-plugin/{plugin,marketplace}.json` + `.codex-plugin` + `.cursor-plugin` + `.kimi-plugin` + `gemini-extension.json`，易 skew。
4. **无任何 CI**：无 `.github/`，Python 包 + bash/ps1 安装器 + 多平台插件 + 双语文档全靠手工保证。
5. **无社区健康文件**：CONTRIBUTING / SECURITY / CODE_OF_CONDUCT / issue·PR 模板全缺。

## 2. 设计目标

用最小、确定性的改动把仓库拉到「可信任、可贡献、可发布」的开源基线。

1. 加根 `LICENSE`（MIT），并让两个 Python 包声明 license。
2. `sybermem-cli` 声明对 `sybermem-core` 的依赖；补齐 PyPA 期望的元数据。
3. 版本单源：一个 `VERSION` 文件 + 一个同步脚本覆盖全部 8 处，并加一致性校验。
4. 加 `.github/workflows` CI：pytest + build + `check-plugin-package.py` + 安装 smoke。
5. 加社区健康文件。

## 3. 设计边界

### 保留
- setuptools 构建后端与现有包结构（不引入 poetry/hatch 迁移）。
- curl|bash 远程安装作为主分发路径（CI/PyPI 是补充，不替换）。
- 现有 `check-plugin-package.py` 校验，扩展而非重写。
- MIT 许可（README 与全部 manifest 已声明 MIT）。

### 不引入
- setuptools-scm / tag 驱动版本：因为 5 个平台 manifest 是纯 JSON，Python-only 的 scm 方案覆盖不了它们。改用 `VERSION` 文件 + 同步脚本，一次覆盖 Python + JSON。
- PyPI 实际发布动作（本轮加 build/CI 骨架，真正 publish 留作维护者手动/后续）。
- 破坏现有安装脚本行为。

## 4. 方案

### 4.1 LICENSE（低风险）

- 新增根 `LICENSE`（MIT 标准全文，author/year 用现有 manifest 的 `goudaren0528`）。
- 两个 `pyproject.toml` 加 `license = "MIT"` 与 `license-files = ["LICENSE"]`（SPDX 表达式形式，setuptools>=68 支持）。

> 注意：Python 包在 `packages/core` 与 `packages/cli` 子目录，`license-files` 需指向能解析到的 LICENSE。若子包构建时找不到根 LICENSE，则在每个包目录放一份 LICENSE 或用相对路径 —— 实现时验证 `python -m build` 能否打进许可。

### 4.2 cli 依赖 core + 元数据（低-中风险）

- `sybermem-cli` 加 `dependencies = ["sybermem-core"]`（本地开发时用可编辑安装满足，PyPI 发布时按版本约束）。
- 两个包补：`readme`、`authors`、`keywords`、`classifiers`、`[project.urls]`（Homepage / Repository / Issues / Changelog 指向 `github.com/goudaren0528/sybermem`）。

> 约束：加 `dependencies=["sybermem-core"]` 后，现有 curl|bash 安装（`--force-reinstall` 本地两个源码树）必须仍能工作。实现时验证安装脚本顺序：先装 core，再装 cli，pip 能就地满足依赖。

### 4.3 版本单源（中风险，需正确性验证）

- 新增根 `VERSION` 文件（内容如 `0.1.0`）。
- 新增 `scripts/sync-version.py`：读取 `VERSION`，写入全部 8 处（2 pyproject 的 `version =`，5 个 JSON manifest 的 `"version"`，gemini-extension 的 `"version"`）。
- 扩展 `check-plugin-package.py`：校验 8 处版本与 `VERSION` 一致，不一致则 fail。
- 发布流程：改 `VERSION` → 跑 `sync-version.py` → 校验。

### 4.4 CI（中风险）

- 新增 `.github/workflows/ci.yml`：
  - matrix：`ubuntu-latest` / `windows-latest` / `macos-latest` × Python `3.10`–`3.13`（至少 3.10 与 3.12）。
  - 步骤：安装 → `pytest packages/core packages/cli` → `python -m build`（两个包）→ `python scripts/check-plugin-package.py`。
  - 单独 job：安装 smoke（在临时 HOME 跑 install → 验证 `sybermem` 可执行 + skill/plugin 文件 → uninstall），至少 ubuntu + windows。
- CI 只跑校验，不发布。

### 4.5 社区健康文件（低风险）

- `CONTRIBUTING.md`：支持平台矩阵、skill sync 规则（`packages/claude-skills → skills`，跑 `sync-plugin-skills.py`）、如何跑 `check-plugin-package.py`、version 单源流程、双语文档同步。
- `SECURITY.md`：报告渠道与响应预期。
- `CODE_OF_CONDUCT.md`：标准 Contributor Covenant。
- `.github/ISSUE_TEMPLATE/bug.yml`、`feature.yml`、`.github/pull_request_template.md`。

## 5. 验收标准

1. 根 `LICENSE` 存在（MIT）；两个 pyproject 声明 license；`python -m build` 两个包成功且许可被打包。
2. `sybermem-cli` 声明依赖 `sybermem-core`；现有 curl|bash 安装路径仍工作（验证安装顺序满足依赖）。
3. `VERSION` 存在；`sync-version.py` 能把版本写入 8 处；`check-plugin-package.py` 校验版本一致。
4. `.github/workflows/ci.yml` 存在且 YAML 合法；本地手动跑通其核心步骤（pytest + build + check-plugin-package）。
5. CONTRIBUTING / SECURITY / CODE_OF_CONDUCT / issue·PR 模板齐全。
6. `check-plugin-package.py` 仍 `OK`（含新版本一致性校验）。
7. 现有 pytest（core 83 + cli 11）全绿。

## 6. 分批建议

- **批次 1（本轮，低风险确定性）**：LICENSE + 社区文件 + VERSION 单源 + cli 依赖/元数据。全是新增或元数据，可本地验证。
- **批次 2（本轮，需真实 CI 环境验证）**：`.github/workflows/ci.yml`。本地只能验证 YAML 合法性与单步骤可跑；矩阵/OS 并行需 push 到 GitHub 才能真正跑绿。因此本轮交付 CI 文件 + 本地跑通其步骤，真实 CI 绿灯在 push 后确认。
