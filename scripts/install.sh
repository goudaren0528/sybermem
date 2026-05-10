#!/bin/bash

# Sybermem 安装脚本
# 合入用户级配置，不破坏用户原有内容

SYBERMEM_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_CONFIG="$HOME/.claude"
CLAUDE_MD="$CLAUDE_CONFIG/CLAUDE.md"
SETTINGS_JSON="$CLAUDE_CONFIG/settings.json"
SKILLS_DIR="$CLAUDE_CONFIG/skills"

echo "=== Sybermem 安装脚本 ==="
echo "sybermem 路径: $SYBERMEM_PATH"

# Step 1: 检查并创建 ~/.claude/ 目录
if [ ! -d "$CLAUDE_CONFIG" ]; then
    echo "创建 ~/.claude/ 目录..."
    mkdir -p "$CLAUDE_CONFIG"
fi

# Step 2: 创建 skills 目录
if [ ! -d "$SKILLS_DIR" ]; then
    echo "创建 ~/.claude/skills/ 目录..."
    mkdir -p "$SKILLS_DIR"
fi

# Step 3: 合入 CLAUDE.md（追加 + 分隔标记）
if [ -f "$CLAUDE_MD" ]; then
    echo "检测到已有 ~/.claude/CLAUDE.md，追加 sybermem 内容..."

    # 检查是否已存在 sybermem 标记
    if grep -q "Sybermem 记忆系统注入" "$CLAUDE_MD"; then
        echo "sybermem 已注入，跳过"
    else
        # 追加分隔标记和内容
        cat >> "$CLAUDE_MD" << 'EOF'

---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 `sybermem update` 可更新        ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统

## 开发者偏好
请填写 sybermem/developer/preferences.md

## 开发价值观
请填写 sybermem/developer/values.md

## 团队约定
参考 sybermem/team/conventions.md

## 团队价值观
参考 sybermem/team/team-values.md

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

EOF
        echo "CLAUDE.md 已追加 sybermem 内容"
    fi
else
    echo "创建 ~/.claude/CLAUDE.md..."
    cat > "$CLAUDE_MD" << 'EOF'
# Claude Code 用户配置

---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 `sybermem update` 可更新        ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统

## 开发者偏好
请填写 sybermem/developer/preferences.md

## 开发价值观
请填写 sybermem/developer/values.md

## 团队约定
参考 sybermem/team/conventions.md

## 团队价值观
参考 sybermem/team/team-values.md

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

EOF
fi

# Step 4: 合入 settings.json
if [ -f "$SETTINGS_JSON" ]; then
    echo "检测到已有 ~/.claude/settings.json..."

    # 检查是否已存在 sybermem 配置
    if grep -q '"sybermem"' "$SETTINGS_JSON"; then
        echo "settings.json 已包含 sybermem 配置，跳过"
    else
        # 使用 jq 合入配置（如果 jq 可用）
        if command -v jq &> /dev/null; then
            jq '. + {"sybermem": {"path": "'"$SYBERMEM_PATH"'", "version": "2.0.0"}}' "$SETTINGS_JSON" > "$SETTINGS_JSON.tmp"
            mv "$SETTINGS_JSON.tmp" "$SETTINGS_JSON"
            echo "settings.json 已合入 sybermem 配置"
        else
            echo "提示：请手动在 settings.json 中添加以下配置："
            echo '  "sybermem": {"path": "'"$SYBERMEM_PATH"'", "version": "2.0.0"}'
        fi
    fi
else
    echo "创建 ~/.claude/settings.json..."
    cat > "$SETTINGS_JSON" << EOF
{
  "sybermem": {
    "path": "$SYBERMEM_PATH",
    "version": "2.0.0"
  }
}
EOF
fi

# Step 5: 复制 Skills 到用户级目录
echo "复制 Skills 到 ~/.claude/skills/..."
cp -r "$SYBERMEM_PATH/skills/"* "$SKILLS_DIR/" 2>/dev/null || true

echo ""
echo "=== 安装完成 ==="
echo ""
echo "下一步："
echo "1. 编辑 sybermem/developer/preferences.md 和 values.md"
echo "2. 在项目中执行 /init-project 或 /adapt-project"
echo ""
echo "非侵入性说明："
echo "- 已有 CLAUDE.md：追加在末尾 + 分隔标记"
echo "- 已有 settings.json：合入 sybermem 配置"
echo "- 用户原有内容完整保留"