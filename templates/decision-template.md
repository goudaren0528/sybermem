---
type: decision
date: {{date}}
number: {{decision_number}}
title: {{title}}
status: {{status}}  # proposed | accepted | deprecated | superseded
supersedes: {{supersedes_decision_number}}  # 如果该决策替代了之前的决策，填写被替代的决策编号
---

# {{title}}

## 背景

{{background}}

描述为什么需要做出这个决策，当前面临的问题或挑战是什么。

---

## 考虑的方案

### 方案 A: {{option_a_name}}

**描述**:
{{option_a_description}}

**优点**:
- {{option_a_pro_1}}
- {{option_a_pro_2}}

**缺点**:
- {{option_a_con_1}}
- {{option_a_con_2}}

---

### 方案 B: {{option_b_name}}

**描述**:
{{option_b_description}}

**优点**:
- {{option_b_pro_1}}
- {{option_b_pro_2}}

**缺点**:
- {{option_b_con_1}}
- {{option_b_con_2}}

---

### 方案 C: {{option_c_name}}

**描述**:
{{option_c_description}}

**优点**:
- {{option_c_pro_1}}
- {{option_c_pro_2}}

**缺点**:
- {{option_c_con_1}}
- {{option_c_con_2}}

---

## 最终决策

**选择方案**: {{chosen_option}}

**决策理由**:
{{decision_reason}}

---

## 影响与后果

### 正面影响
- {{positive_impact_1}}
- {{positive_impact_2}}

### 负面影响/风险
- {{negative_impact_1}}
- {{negative_impact_2}}

### 需要注意的事项
- {{attention_point_1}}
- {{attention_point_2}}

---

## 相关变更

- 变更记录: `ADR/changes/{{related_change_file}}`
- 需求记录: `ADR/requirements/{{related_requirement_file}}`

---

## 备注

{{additional_notes}}

---

## 参考资源

- {{reference_1}}
- {{reference_2}}