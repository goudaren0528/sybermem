#!/bin/bash

# SyberMem - 安装脚本
# 将 skills 复制到 Claude Code 和 OpenCode 用户级目录

ADR_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"

echo "=== SyberMem 安装 ==="

install_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    rm -rf "$target/init-project" "$target/record" "$target/summary"
    for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-update; do
        if [ -d "$ADR_PATH/.claude/skills/$skill" ]; then
            rm -rf "$target/$skill"
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
echo "  /sybermem-init-project  — 初始化或刷新当前项目的 SyberMem 配置"
echo "  /sybermem-record        — 创建记录（自动判断类型）"
echo "  /sybermem-summary       — 生成周报/月报"
echo "  /sybermem-update        — 更新全局 Skills 并重新检查当前项目"
echo ""
echo "下一步：进入你的项目目录后执行 /sybermem-update"
echo "如果你只想初始化或刷新当前项目，可执行 /sybermem-init-project"
echo ""
echo "注意：更新全局 Skills 不会自动刷新项目里的 AGENTS.md / CLAUDE.md；请在项目内运行 /sybermem-update 或 /sybermem-init-project"
echo ""
echo "注意：Windows 用户请使用 install.ps1"
