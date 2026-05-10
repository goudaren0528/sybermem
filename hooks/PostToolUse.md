---
name: PostToolUse
trigger: Edit, Write, Bash 工具调用后
---

# PostToolUse Hook

在 Edit、Write、Bash 工具调用后，AI 内部判断是否需要加载相关记忆。

## 核心原则

**用户无感知：** 所有加载都是 AI 内部执行，不打断用户。

用户只体验"AI 给出了更好的建议"，不感知加载过程。

## 触发时机

每次以下工具调用后：
- Edit：修改代码文件
- Write：创建新文件
- Bash：执行命令

## 执行逻辑

### 情况 1：Edit/Write 修改代码文件

```
if (tool == "Edit" || tool == "Write"):
  file_path = extract_file_path(operation)

  # 1. 检查 SPECIAL-CASES INDEX 的文件路径关联
  related_cases = check_special_cases_index(file_path)

  if related_cases:
    # AI 内部读取，作为上下文
    read(related_cases)
    # 不向用户提示，融入任务执行

  # 2. 检查 EXPERIENCES INDEX 的模块关联
  module = detect_module_from_path(file_path)
  related_experiences = check_experiences_index(module)

  if related_experiences:
    read(related_experiences)
```

### 情况 2：Bash 执行测试/构建失败

```
if (tool == "Bash" && result == "failure"):
  error_type = analyze_error(result)

  # 检查 EXPERIENCES/pitfalls + debug
  related_experiences = check_experiences_index(error_type)

  if related_experiences:
    read(related_experiences)
    # AI 参考历史踩坑经验调整修复策略
```

### 情况 3：读取代码发现问题

```
if (AI 分析代码发现潜在问题):
  problem_type = classify_problem(performance? logic? security?)

  # 加载对应类型 EXPERIENCES
  related_experiences = check_experiences_index(problem_type)

  if related_experiences:
    read(related_experiences)
```

### 情况 4：处理技术决策类任务

```
if (AI 判断这是"技术决策类任务"):
  # 加载 ADR + REQUIREMENTS + values/team-values
  read(".sybermem/ADR/INDEX.md")
  read(".sybermem/REQUIREMENTS/INDEX.md")
  # values/team-values 已在用户级 CLAUDE.md 中加载
```

## 检查 INDEX 文件方法

### SPECIAL-CASES INDEX 检查

```markdown
## 按文件路径关联
| 文件路径 | 特殊处理记录 | 影响级别 |
|----------|-------------|----------|
- src/payment/order-service.ts → temporary/payment-polling.md
- src/user/auth.ts → legacy/user-session-compat.md
```

匹配逻辑：
- 精确匹配：file_path == related_code
- 通配符匹配：file_path matches related_code pattern
- 目录匹配：file_path in related_code directory

### EXPERIENCES INDEX 检查

```markdown
## 按模块分类
- payment/
  - pitfalls: payment-timeout.md
  - debug: payment-log-analysis.md
```

匹配逻辑：
- 根据 file_path 推断模块名
- 查找模块对应的经验记录

## 实现方式

Hook 不直接执行读取，而是：
1. 判断是否需要加载
2. 如果需要，调用 Read 工具读取相关记录
3. 读取结果作为 AI 内部上下文
4. 继续执行任务

**关键：** 读取融入任务流程，不单独提示用户。

## 避免过度加载

控制策略：
- 每次加载量 < 3000 tokens
- 优先加载高影响级别（impact=high）记录
- 同类操作短时间内不重复加载