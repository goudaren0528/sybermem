---
name: SessionEnd
trigger: 会话结束时
---

# SessionEnd Hook

会话结束时，更新项目进展并生成日报摘要。

## 触发时机

会话结束：
- 用户退出
- 长时间无活动
- 用户主动触发结束

## 执行逻辑

### Step 1: 收集本次会话操作摘要

收集本次会话的操作：
- 完成的任务（Edit/Write 操作摘要）
- 创建的记录（扫描 .sybermem/ 目录变化）
- 遇到的问题

### Step 2: 检查是否有未记录的重要内容

判断是否需要创建记录：
- 功能变更 → 提示创建 CHANGELOG
- 技术决策 → 提示创建 ADR
- 踩坑经验 → 提示创建 EXPERIENCE
- 特殊处理 → 提示创建 SPECIAL-CASE

### Step 3: 更新 PROGRESS.md 今日进展

调用 update-progress Skill：
- 追加今日进展
- 更新当前状态

### Step 4: 生成日报摘要

动态生成日报（不持久存储）：
```markdown
# 今日进展摘要（YYYY-MM-DD）

## 完成任务
- xxx
- xxx

## 创建记录
- ADR/xxx
- CHANGELOG/xxx

## 遗留问题
- xxx

## 明日计划建议
- xxx
```

### Step 5: 更新 sybermem PROJECTS 状态

更新 `PROJECTS/registered/{project-name}/STATUS.md`：
- 最后活动时间
- 活跃模块
- 当前状态

### Step 6: 提示用户确认

提示用户：
- 显示日报摘要
- 确认是否需要创建遗漏记录
- 稳定明日计划

## 自动执行流程

```
SessionEnd Hook:
├── collect_session_summary()
├── check_unrecorded_content()
│   └── if (功能变更): suggest("/record-change")
│   └── if (技术决策): suggest("/record-adr")
│   └── if (踩坑): suggest("/record-experience")
├── call(update-progress)
├── generate_daily_summary()
├── update_projects_status()
└── prompt_user_confirm()
```

## 日报用途

- 个人回顾
- 项目追踪
- 团队协作参考

日报为动态生成，不持久存储到 `.sybermem/` 目录。