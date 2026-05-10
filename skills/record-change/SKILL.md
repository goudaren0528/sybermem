---
name: record-change
description: 创建功能变更记录（CHANGELOG）
---

# record-change Skill

创建功能变更记录，记录新增、修改、删除功能。

## 判断标准
功能变更：
- 新增功能模块 ✓
- 修改已有功能行为 ✓
- 删除功能 ✓
- API 变化 ✓
- 数据结构变化 ✓

简单格式调整、注释修改、配置微调 → 无需记录

## 流程

### Step 1: 确认变更类型

### Step 2: 收集变更信息
- 变更内容
- 变更原因
- 影响范围
- 相关文件

### Step 3: 获取下一个编号

### Step 4: 使用模板生成文件
templates/change-template.md

### Step 5: 创建文件
.sybermem/CHANGELOG/YYYY-MM-DD-NNN-title.md

### Step 6: 更新 CHANGELOG INDEX