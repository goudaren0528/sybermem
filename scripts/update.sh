#!/bin/bash

# Sybermem 更新脚本
# 更新用户级配置中的 sybermem 区域

SYBERMEM_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_CONFIG="$HOME/.claude"
CLAUDE_MD="$CLAUDE_CONFIG/CLAUDE.md"
SETTINGS_JSON="$CLAUDE_CONFIG/settings.json"
SKILLS_DIR="$CLAUDE_CONFIG/skills"

echo "=== Sybermem 更新脚本 ==="

# Step 1: 更新 CLAUDE.md 中的 sybermem 区域
if [ -f "$CLAUDE_MD" ]; then
    if grep -q "Sybermem 记忆系统注入" "$CLAUDE_MD"; then
        echo "更新 CLAUDE.md 中的 sybermem 区域..."

        # 提取用户原有内容（sybermem 标记之前）
        USER_CONTENT=$(sed -n '1,/^---$/p' "$CLAUDE_MD" | sed '$d')

        # 生成新的 sybermem 内容
        SYBERMEM_CONTENT="
---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 \`sybermem update\` 可更新      ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统

## 开发者偏好
$(cat "$SYBERMEM_PATH/developer/preferences.md" 2>/dev/null || echo "请填写")

## 开发价值观
$(cat "$SYBERMEM_PATH/developer/values.md" 2>/dev/null || echo "请填写")

## 团队约定
$(cat "$SYBERMEM_PATH/team/conventions.md" 2>/dev/null || echo "参考文件")

## 团队价值观
$(cat "$SYBERMEM_PATH/team/team-values.md" 2>/dev/null || echo "参考文件")

## 可用 Skills
以下 Skills 在所有项目可用：
- /init-project - 新项目注入记忆系统
- /adapt-project - 旧项目适配记忆系统
- /record-adr - 创建架构决策记录
- /record-change - 创建功能变更记录
- /record-experience - 创建经验记录
- /record-special - 创建特殊处理记录
- /record-requirement - 创建需求讨论记录
- /update-progress - 更新项目进展
- /update-overview - 更新项目全貌
- /weekly-summary - 生成周报
- /monthly-summary - 生成月报
- /optimize-memory - 执行记忆优化
- /sync-experience - 同步经验到团队层
"

        # 合并写入
        echo "$USER_CONTENT$SYBERMEM_CONTENT" > "$CLAUDE_MD"
        echo "CLAUDE.md 已更新"
    else
        echo "CLAUDE.md 中未找到 sybermem 标记，请先运行 install.sh"
    fi
else
    echo "~/.claude/CLAUDE.md 不存在，请先运行 install.sh"
fi

# Step 2: 更新 settings.json
if [ -f "$SETTINGS_JSON" ]; then
    if command -v jq &> /dev/null; then
        jq '.sybermem.path = "'"$SYBERMEM_PATH"'"' "$SETTINGS_JSON" > "$SETTINGS_JSON.tmp"
        mv "$SETTINGS_JSON.tmp" "$SETTINGS_JSON"
        echo "settings.json 已更新 sybermem 路径"
    fi
fi

# Step 3: 同步 Skills
echo "同步 Skills 到 ~/.claude/skills/..."
rm -rf "$SKILLS_DIR/"* 2>/dev/null || true
cp -r "$SYBERMEM_PATH/skills/"* "$SKILLS_DIR/" 2>/dev/null || true

echo ""
echo "=== 更新完成 ==="