# SyberMem Injection Slimming & Update Efficiency 设计

> 精简 CLAUDE.md/AGENTS.md 注入、限制 session_start_context 输出、确保 update 非破坏性修正已有用户、提升安装/更新效率。

**Date:** 2026-07-10
**Status:** Draft
**Scope:** 只优化注入内容和更新效率，不新增功能。

---

## 1. CLAUDE.md / AGENTS.md 精简

### 当前问题
76 行，大量内容与 skill 定义重复（Available Skills 列表、Workflow 11 条、Session Protocol 7 条）。

### 目标
精简到 ~15 行，只保留：
- 极简 Session Protocol（3 条）
- Core Rule（1 句）
- Directories（5 行快速参考）
- No Record Needed（2 行边界）

### 移除
- Available Skills 列表（harness 自己显示）
- Workflow 11 条详细规则（每个 skill 自己定义）
- Directory Resolution 详细规则（hook/core 自己处理）
- auto/remind 模式详细说明（hook + skill 已处理）

### 非破坏性保证
- 如果 CLAUDE.md / AGENTS.md 有用户自定义内容，只替换 protocol block
- 不覆盖 protocol block 以外的任何内容
- 如果文件是纯 SyberMem-managed，替换整个文件为新精简模板

---

## 2. session_start_context.py 输出限制

### 当前问题
- 全量注入所有 Key Conclusions（无上限）
- 全量注入整个 Topic Index
- 还注入了 skill 列表（三重重复）

### 目标
限制到 ~10 行高信号输出：
- 项目身份（1 行）
- Key Conclusions 数量（1 行）
- 最近 5 条 Key Conclusions（而不是全量）
- Active phase（1-2 行）
- Stale signal（1 行）

### 移除
- 完整 Topic Index（lookup index，不需要每次注入）
- Skill 列表（harness 已提供）
- 全量 Key Conclusions 改为最近 5 条

---

## 3. update 非破坏性修正已有用户

### 当前问题
已有项目的 CLAUDE.md 可能包含旧版过重的 protocol block。  
update 需要能识别并替换成新版精简版。

### 方法
在 `check_project_health.py` 的 `check_instruction_file` 中：
- 如果 protocol block 存在但内容与新模板不一致
- 标记为 `stale`
- update 时只替换 protocol block，不动 block 以外的用户内容

### 非破坏性保证
- 只操作 `<!-- SYBERMEM_SESSION_PROTOCOL:START -->` 到 `END -->` 之间的内容
- block 以外的内容完全保留
- 如果文件没有 protocol block，按现有逻辑处理（insert 或 skip）

---

## 4. 安装/更新效率

### 当前问题
每次 install/update 都要：
1. 复制 13 个 skill 目录
2. 创建/重建 Python venv
3. pip install core + cli 包

其中 venv + pip install 是最耗时的部分。

### 优化方向
- 如果 venv 已存在且 packages 已安装，跳过 pip install
- 只在版本变化或 venv 缺失时才重建
- 可以通过检测 `sybermem_core` 是否已安装来决定

### 具体策略
在 install/update 脚本中：
1. 检查 venv 是否存在
2. 检查 `sybermem_core` 是否已安装（`pip show sybermem_core`）
3. 如果两者都满足 → 跳过 pip install，只更新 skill 文件
4. 如果任一缺失 → 执行完整 pip install

---

## 5. 暂时停用 SyberMem

### 已有能力
`sybermem project uninstall` 已经做到：
- 保留 `.sybermem/`
- 停用 hooks / settings / protocol block
- 可逆

### 需要补充的
- 在 README 里明确说明这个能力
- 在 `/using-sybermem` 输出里提到停用选项

---

## 6. using-sybermem SKILL.md 精简

### 当前问题
146 行，含重复的 Integration 列表、20 行 graphviz 图、6 个 examples。

### 目标
精简到 ~70 行：
- 移除 Integration 列表
- 用 3 行优先级列表替代 graphviz 图
- 压缩 examples 到 2 个

---

## 7. Success Criteria

1. CLAUDE.md/AGENTS.md 从 ~76 行降到 ~15 行
2. session_start_context 从无上限降到 ~10 行
3. update 能非破坏性地将旧版过重 protocol block 替换为精简版
4. install/update 在 venv+packages 已存在时跳过 pip install
5. 用户可通过 `sybermem project uninstall` 暂时停用
6. 所有变更对用户自定义内容非破坏性