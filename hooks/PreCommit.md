---
name: PreCommit
trigger: Git commit 前
---

# PreCommit Hook

Git commit 前，自动分析变更并创建对应记录。

## 核心原则

**自动执行：** 分析 commit 内容，自动判断并创建记录，用户无需手动调用。

## 触发时机

Git commit 执行前。

## 执行逻辑

### Step 1: 分析 commit 内容

分析即将 commit 的变更：
```bash
git diff --cached --name-only
git diff --cached --stat
git log -1 --pretty=format:"%s"  # 获取 commit message
```

### Step 2: 自动判断变更类型

| 变更类型 | 自动创建记录 |
|----------|--------------|
| 架构调整、技术选型 | ADR/decisions/ |
| 功能新增、修改、删除 | CHANGELOG/ |
| Bug 修复 | EXPERIENCES/pitfalls/ |
| 性能优化 | EXPERIENCES/performance/ |
| 重构 | EXPERIENCES/refactor/ |
| 配置调整、格式修改 | 无需记录 |

判断方法：
- 新增配置文件（package.json, tsconfig.json, pyproject.toml）→ ADR（技术选型）
- 新增模块目录 → ADR 或 CHANGELOG
- 新增功能文件 → CHANGELOG
- 修改功能实现 → CHANGELOG
- 修复 Bug（commit message 含 fix）→ EXPERIENCES/pitfalls/
- 性能相关（commit message 含 perf/optimize）→ EXPERIENCES/performance/

### Step 3: 自动创建记录

根据变更类型，自动调用对应 Skill：

```
if (架构变更):
  自动调用 record-adr skill
  生成 ADR 记录文件

if (功能变更):
  自动调用 record-change skill
  生成 CHANGELOG 记录文件

if (Bug修复):
  自动调用 record-experience skill (pitfalls)
  生成踩坑经验记录

if (性能优化):
  自动调用 record-experience skill (performance)
  生成性能优化经验
```

**自动生成内容：**
- 从 commit message 提取标题
- 从 diff 内容提取变更详情
- 自动填充 frontmatter
- 更新对应 INDEX.md

### Step 4: 继续 commit

记录创建完成后，继续执行 commit。

用户完全无感知，只看到 commit 成功。

## 避免过度记录

不触发的情况：
- 简单格式调整
- 注释修改
- 配置微调（无功能影响）
- .sybermem/ 目录本身的变更
- WIP commit（message 含 WIP/draft）

## 实现方式

Hook 通过 Claude Code Hook 机制实现，在 commit 前自动执行。

## 示例

用户执行：
```bash
git add src/payment/order-service.ts
git commit -m "feat: 添加订单支付功能"
```

Hook 自动执行：
```
PreCommit Hook:
├── 分析 diff → 新增功能文件
├── 判断类型 → 功能新增 → CHANGELOG
├── 自动调用 record-change
├── 生成 CHANGELOG/2026-05-10-001-添加订单支付功能.md
├── 更新 CHANGELOG/INDEX.md
└── 继续 commit
```

用户看到：
```
commit 成功
（记录已自动创建）
```