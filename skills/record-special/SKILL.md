---
name: record-special
description: 创建特殊处理记录（SPECIAL-CASES）
---

# record-special Skill

创建特殊处理记录，记录因业务现状或历史原因的特殊逻辑。

## 为什么重要
- 新人/AI 不理解原因，可能"优化"导致出错
- 临时方案容易被遗忘
- 重构时需要特别注意

## 特殊处理类型
| 类别 | 目录 | 内容 |
|------|------|------|
| legacy | SPECIAL-CASES/legacy/ | 历史遗留 |
| business | SPECIAL-CASES/business/ | 业务特殊性 |
| temporary | SPECIAL-CASES/temporary/ | 临时方案（待优化） |
| environment | SPECIAL-CASES/environment/ | 环境限制 |
| custom | SPECIAL-CASES/custom/ | 客户定制 |

## 流程

### Step 1: 确定特殊处理类型

### Step 2: 收集特殊处理信息
- 特殊处理描述
- 原因分析
- 影响范围
- 相关代码（关键！文件路径）
- 影响级别
- 注意事项

如果是临时方案：
- 后续计划

### Step 3: 生成文件名

### Step 4: 使用模板生成文件
templates/special-case-template.md

### Step 5: 创建文件

### Step 6: 更新 SPECIAL-CASES INDEX（关键！）
**按文件路径关联表格**（最重要）：
```
| {{related_code}} | {{filename}} | {{impact_level}} |
```
AI 修改文件时会检查此区域自动加载相关记录。

### Step 7: 提示用户确认

## related_code 格式
- 单个文件：src/payment/order-service.ts
- 多个文件：src/payment/*.ts
- 目录：src/payment/

## 重构提醒
AI 检测到用户要重构相关代码时，自动加载 SPECIAL-CASES 记录提醒注意事项。