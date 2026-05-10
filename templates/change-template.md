---
type: change
date: {{date}}
number: {{change_number}}
title: {{title}}
status: {{status}}  # planned | in_progress | completed | rolled_back
related_files:
  - {{file_path_1}}
  - {{file_path_2}}
  - {{file_path_3}}
---

# {{title}}

## 变更内容

### 变更类型
{{change_type}}  # feature | fix | refactor | enhancement | breaking_change

### 变更描述
{{change_description}}

### 具体改动
1. **{{module_or_file_1}}**
   - 改动: {{change_detail_1}}
   - 原因: {{change_reason_1}}

2. **{{module_or_file_2}}**
   - 改动: {{change_detail_2}}
   - 原因: {{change_reason_2}}

---

## 变更原因

### 问题背景
{{problem_background}}

### 触发因素
- {{trigger_1}}
- {{trigger_2}}

### 目标
{{change_goal}}

---

## 影响范围

### 受影响的模块
- {{affected_module_1}}
- {{affected_module_2}}
- {{affected_module_3}}

### 受影响的功能
- {{affected_feature_1}}
- {{affected_feature_2}}

### 兼容性影响
**向后兼容**: {{backward_compatible}}  # 是 | 否 | 部分

**兼容性说明**:
{{compatibility_notes}}

### 风险评估
- **高风险**: {{high_risk_areas}}
- **中风险**: {{medium_risk_areas}}
- **低风险**: {{low_risk_areas}}

---

## 实现方案

### 技术方案
{{technical_approach}}

### 实现步骤
1. {{implementation_step_1}}
2. {{implementation_step_2}}
3. {{implementation_step_3}}

### 关键代码变更
```{{language}}
// {{code_description}}
{{key_code_changes}}
```

---

## 测试验证

### 测试策略
{{test_strategy}}

### 测试用例
- [ ] {{test_case_1}}
- [ ] {{test_case_2}}
- [ ] {{test_case_3}}

### 验证结果
**测试日期**: {{test_date}}

**测试结果**: {{test_result}}  # 通过 | 部分通过 | 失败

**测试详情**:
{{test_details}}

---

## 相关决策

- 决策记录: `ADR/decisions/{{related_decision_file}}`
- 需求记录: `ADR/requirements/{{related_requirement_file}}`

---

## 备注

{{additional_notes}}

---

## 回滚计划

**是否需要回滚**: {{need_rollback}}  # 是 | 否

**回滚方案**:
{{rollback_plan}}

**回滚触发条件**:
{{rollback_conditions}}