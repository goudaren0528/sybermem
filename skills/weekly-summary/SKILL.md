---
name: weekly-summary
description: 生成周报，并自动提炼开发者偏好和价值观
---

# weekly-summary Skill

生成本周进展周报，汇总本周工作和成果，**自动提炼开发者偏好和价值观**。

## 使用方式
- 用户执行 `/weekly-summary`
- 定时触发（每周结束）

## 核心设计

**自动提炼偏好：** 分析本周开发行为，自动更新 developer/preferences.md 和 developer/values.md。

## 流程

### Step 1: 读取 PROGRESS.md
获取本周进展信息

### Step 2: 读取本周创建的记录
扫描本周创建的记录文件：
- ADR/decisions/
- CHANGELOG/
- EXPERIENCES/
- SPECIAL-CASES/

### Step 3: 汇总本周成果
- 主要成果
- 关键决策
- 遇到的问题
- 经验总结

### Step 4: 分析并提炼开发者偏好（新增）

分析本周开发行为，提炼偏好：

| 分析维度 | 提取内容 |
|----------|----------|
| 技术选型（ADR） | 倾向的技术栈、框架偏好 |
| 编码模式 | 常用的设计模式、代码风格 |
| 问题处理 | 对 Bug 的处理方式、调试习惯 |
| 工具使用 | 常用的工具、命令 |
| 时间分配 | 模块开发时间分布 |

**提炼逻辑：**
```
if (本周多次使用 TypeScript):
  preferences.技术栈偏好 += "倾向 TypeScript"

if (本周 ADR 选择方案 A 多次):
  preferences.决策风格 += "偏向保守/稳妥方案"

if (本周多次使用 TDD):
  preferences.开发习惯 += "倾向测试驱动开发"

if (遇到性能问题优先优化而非重构):
  values.效率观 += "优先解决实际问题"
```

### Step 5: 自动更新 developer/preferences.md 和 developer/values.md（新增）

**更新策略：**
- 增量追加新发现的偏好
- 不删除已有内容
- 标记更新时间和来源

```markdown
## 开发偏好（自动提炼于 2026-05-10）

### 技术栈偏好
- 倾向使用 TypeScript（本周 80% 新代码使用 TS）
- 倾向函数式编程风格

### 开发习惯
- 测试驱动开发（本周 3 次 TDD 实践）
- 小步提交（平均 commit 粒度较小）

### 工具偏好
- 倾向使用 VSCode + Claude Code

---
## 开发价值观（自动提炼于 2026-05-10）

### 代码质量观
- 倾向可读性优先

### 效率观
- 优先解决实际问题

### 决策风格
- 倾向稳妥方案（本周 ADR 多选择保守方案）
```

### Step 6: 生成周报内容
动态生成周报（不持久存储）

### Step 7: 输出周报和偏好更新
显示给用户：
- 本周周报
- 新提炼的偏好和价值观（供用户确认）

## 周报格式
```markdown
# 本周进展周报（YYYY-WXX）

## 主要成果
- xxx

## 关键决策
- ADR/xxx

## 遇到的问题
- EXPERIENCES/pitfalls/xxx

## 经验总结
- EXPERIENCES/best-practices/xxx

## 新发现的偏好
- 技术栈：倾向 TypeScript
- 开发习惯：测试驱动开发

## 下周计划
- 待办事项
```

## 偏好提炼来源

| 来源 | 提取内容 |
|------|----------|
| ADR 决策 | 技术选型偏好、决策风格 |
| CHANGELOG | 功能开发模式、编码习惯 |
| EXPERIENCES | 问题处理方式、调试习惯 |
| Git commit | 提交粒度、时间分布 |
| 对话记录 | 价值观表达 |

## 用户可手动修改

自动提炼的内容用户可以：
- 确认保留
- 手动修改
- 删除不准确的内容

developer/preferences.md 和 developer/values.md 采用**自动提炼 + 手动补充**的双向机制。