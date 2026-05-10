---
type: requirement
date: {{date}}
number: {{requirement_number}}
title: {{title}}
source: {{source}}  # 需求来源：用户反馈、业务需求、技术改进等
priority: {{priority}}  # high | medium | low
status: {{status}}  # draft | discussing | confirmed | implemented | closed
---

# {{title}}

## 需求来源

**提出人**: {{proposer}}

**提出日期**: {{proposed_date}}

**来源类型**: {{source_type}}  # 用户反馈 | 业务需求 | 技术改进 | 合规要求 | 其他

**优先级说明**:
{{priority_reason}}

---

## 需求内容

### 需求描述
{{requirement_description}}

### 功能需求
1. {{functional_requirement_1}}
2. {{functional_requirement_2}}
3. {{functional_requirement_3}}

### 非功能需求
- **性能**: {{performance_requirement}}
- **安全**: {{security_requirement}}
- **可用性**: {{usability_requirement}}
- **其他**: {{other_non_functional}}

### 验收标准
- [ ] {{acceptance_criteria_1}}
- [ ] {{acceptance_criteria_2}}
- [ ] {{acceptance_criteria_3}}

---

## 讨论过程

### 第一次讨论
**日期**: {{discussion_date_1}}
**参与人**: {{participants_1}}
**讨论内容**:
{{discussion_content_1}}

**结论**:
{{discussion_conclusion_1}}

---

### 第二次讨论
**日期**: {{discussion_date_2}}
**参与人**: {{participants_2}}
**讨论内容**:
{{discussion_content_2}}

**结论**:
{{discussion_conclusion_2}}

---

## 最终结论

**确认状态**: {{final_status}}

**确认日期**: {{confirmation_date}}

**确认人**: {{confirmer}}

**最终方案**:
{{final_solution}}

---

## 设计理念/限制

### 设计理念
{{design_philosophy}}

### 限制条件
- {{constraint_1}}
- {{constraint_2}}
- {{constraint_3}}

---

## 相关决策/变更

### 相关决策
- 决策记录: `ADR/decisions/{{related_decision_file}}`

### 相关变更
- 变更记录: `ADR/changes/{{related_change_file}}`

---

## 备注

{{additional_notes}}