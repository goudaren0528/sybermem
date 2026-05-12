#!/bin/bash

# ADR 记录系统 - 安装脚本
# 将 skills 复制到 Claude Code 和 OpenCode 用户级目录

ADR_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"

echo "=== ADR 记录系统安装 ==="

install_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    for skill in init-project record summary; do
        if [ -d "$ADR_PATH/.claude/skills/$skill" ]; then
            cp -r "$ADR_PATH/.claude/skills/$skill" "$target/"
            echo "  [$label] 已安装: /$skill"
        fi
    done
}

install_skills "$CLAUDE_SKILLS" "Claude Code"
install_skills "$OPENCODE_SKILLS" "OpenCode"

echo ""
echo "=== 安装完成 ==="
echo ""
echo "可用 Skills："
echo "  /init-project  — 初始化 ADR 系统"
echo "  /record        — 创建记录（自动判断类型）"
echo "  /summary       — 生成周报/月报"
echo ""
echo "下一步：在项目目录中执行 /init-project"
echo ""
echo "注意：Windows 用户请使用 install.ps1"
