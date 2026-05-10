---
name: record-adr
description: 创建架构决策记录（ADR）
---

# record-adr Skill

创建架构决策记录，记录技术选型、架构设计等重要决策。

## 判断标准
ADR 只记录架构层面决策：
- 技术选型（框架、库、工具） ✓
- 架构设计（模块划分、数据流） ✓
- 接口设计（API 规范） ✓
- 长期影响决策 ✓
- 多方案权衡 ✓

普通功能开发、Bug修复、配置修改 → 使用其他 Skill

## 流程

### Step 1: 确认决策类型
询问是否属于架构决策。

### Step 2: 收集决策信息
- 背景：决策的背景和问题
- 考虑的方案：方案A/B/C 及优缺点
- 最终决策：选择方案和理由
- 影响与后果：决策影响

### Step 3: 获取下一个编号
检查 .sybermem/ADR/decisions/ 目录。

### Step 4: 使用模板生成文件
使用 templates/decision-template.md

### Step 5: 创建文件
.sybermem/ADR/decisions/YYYY-MM-DD-NNN-title.md

### Step 6: 更新 ADR INDEX

### Step 7: 更新 OVERVIEW 关键决策索引

## 标题命名建议
- 选择 xxx 作为 xx 框架
- 采用 xxx 架构模式
- 将 xx 模块迁移到 xxx