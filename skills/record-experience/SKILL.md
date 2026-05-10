---
name: record-experience
description: 创建开发经验记录
---

# record-experience Skill

创建开发经验记录，积累踩坑、最佳实践、调试方法等。

## 经验类型
| 类别 | 目录 | 内容 |
|------|------|------|
| pitfalls | EXPERIENCES/pitfalls/ | 踩坑经验 |
| debug | EXPERIENCES/debug/ | 调试方法 |
| best-practices | EXPERIENCES/best-practices/ | 最佳实践 |
| tools | EXPERIENCES/tools/ | 工具技巧 |
| performance | EXPERIENCES/performance/ | 性能优化 |
| refactor | EXPERIENCES/refactor/ | 重构经验 |

## 流程

### Step 1: 确定经验类型

### Step 2: 收集经验信息
- 场景描述
- 问题/内容
- 解决方案
- 关键要点
- 相关代码
- 影响级别（high/medium/low）

### Step 3: 生成文件名
YYYY-MM-DD-title.md（不使用编号）

### Step 4: 使用模板生成文件
templates/experience-template.md

### Step 5: 创建文件
.sybermem/EXPERIENCES/{category}/YYYY-MM-DD-title.md

### Step 6: 更新 EXPERIENCES INDEX

### Step 7: 判断是否同步团队层
如果 impact=high，提示用户执行 `/sync-experience`