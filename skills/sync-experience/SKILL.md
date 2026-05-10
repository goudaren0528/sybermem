---
name: sync-experience
description: 同步高价值经验到团队层
---

# sync-experience Skill

将高价值经验从项目层同步到团队层,供团队共享。

## 使用方式

- 用户执行 `/sync-experience`
- record-experience 时提示(impact=high)
- 用户主动分享经验

## 流程

### Step 1: 筛选高价值经验

筛选条件:
- impact=high
- 适用于多项目
- 非项目特异

扫描项目层 EXPERIENCES:
```bash
find .sybermem/EXPERIENCES -name "*.md" -exec grep "impact: high" {} \;
```

### Step 2: 展示候选经验列表

展示候选经验:
```markdown
# 可同步到团队层的经验

| 经验标题 | 类别 | 适用范围 | 文件 |
|----------|------|----------|------|
| payment-timeout | pitfalls | 多项目 | EXPERIENCES/pitfalls/payment-timeout.md |
| git-commit-best-practice | best-practices | 所有项目 | EXPERIENCES/best-practices/git-commit.md |
```

### Step 3: 用户确认要同步的内容

用户选择:
- 全部同步
- 选择性同步(指定某几条)
- 不同步

### Step 4: 复制经验到团队层

复制选中的经验到 `sybermem/team/shared-experiences/`:

对应目录:
- pitfalls → team/shared-experiences/pitfalls/
- best-practices → team/shared-experiences/best-practices/
- debug → team/shared-experiences/debug/
- tools → team/shared-experiences/tools/

### Step 5: 创建 PR 等待团队审核

创建 Git 分支和 PR:

```bash
cd /path/to/sybermem
git checkout -b sync-experience-YYYY-MM-DD
git add team/shared-experiences/
git commit -m "feat: 同步高价值经验到团队层

- EXPERIENCES/pitfalls/payment-timeout.md → shared-experiences/pitfalls/
- EXPERIENCES/best-practices/git-commit.md → shared-experiences/best-practices/"
git push origin sync-experience-YYYY-MM-DD
# 创建 PR
```

### Step 6: 团队审核

团队成员审核 PR:
- 确认经验价值
- 确认适用范围
- 合并 PR

### Step 7: 更新 sybermem

PR 合并后:
- 拉取更新:`git pull upstream main`
- 运行更新脚本:`./scripts/update.sh`

团队层经验自动注入到所有项目。

## 同步判断标准

| 同步 | 不同步 |
|------|--------|
| impact=high | impact=low/medium |
| 通用经验(适用多项目) | 项目特异经验 |
| 团队受益 | 仅个人受益 |

## 经验修改建议

同步前可修改:
- 移除项目特定内容
- 调整适用范围描述
- 增加团队适用说明

## 团队层与项目层的关系

- 团队层:团队共享,所有项目可用
- 项目层:项目私有,仅当前项目使用

团队层经验通过用户级 CLAUDE.md 注入,所有项目启动时自动加载。