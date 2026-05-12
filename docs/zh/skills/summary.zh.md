---
name: summary
description: 生成 SyberMem 项目周报或月报，也适用于仍然使用旧 ADR/ 存储的项目。
---

# summary Skill

生成 SyberMem 项目进展报告。默认生成周报，传入 `monthly` 参数生成月报。

## 使用方式

- `/summary` — 生成本周周报
- `/summary monthly` — 生成本月月报

## 目录解析规则

在收集报告数据前，先解析项目数据目录：

1. 如果 `.sybermem/` 已存在，直接使用。
2. 如果只有 `ADR/`，将 `ADR/` 重命名为 `.sybermem/`，并告知用户旧目录已自动迁移。
3. 如果 `.sybermem/` 和 `ADR/` 同时存在，使用 `.sybermem/`，警告 `ADR/` 已被忽略，不自动合并。
4. 如果两者都不存在，提示用户先执行 `/init-project`。

## 流程

### Step 1: 确定报告范围

- 无参数或 `weekly` → 本周（最近 7 天）
- `monthly` → 本月（最近 30 天）

### Step 2: 收集数据

扫描 `.sybermem/` 中对应时间范围内的记录文件：

```
.sybermem/changes/      → 功能变更
.sybermem/decisions/    → 技术决策
.sybermem/requirements/ → 需求记录
.sybermem/bugs/         → Bug 修复
```

同时参考 Git log 获取 commit 历史。

### Step 3: 生成报告

动态输出（不持久存储），格式：

```markdown
# 项目进展报告（YYYY-MM-DD ~ YYYY-MM-DD）

## 主要成果
- ...

## 关键决策
- .sybermem/decisions/...

## 问题与修复
- .sybermem/bugs/...

## 遗留问题
- ...

## 下一步计划
- ...
```

### Step 4: 月报额外内容

月报在周报基础上增加：
- 按周分组的进展汇总
- 本月数据统计（记录数量、类型分布）
- 趋势观察

## 设计原则

- **`.sybermem/` 是规范目录**：报告始终基于规范项目数据目录中的记录生成
- **兼容旧项目**：升级 Skills 即可，旧 `ADR/` 会在首次使用时自动迁移
- **不持久存储**：报告动态生成，避免文件膨胀
- **数据驱动**：基于实际记录文件，不凭空推测
- **精简输出**：控制在一屏内可读完
