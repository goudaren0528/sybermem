#!/bin/bash

# SyberMem - 更新脚本
# 同步最新 skills 到 Claude Code 和 OpenCode 用户级目录

ADR_PATH="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_SOURCE="$ADR_PATH/packages/claude-skills"
CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"
LEGACY_LOCAL_SKILLS="$ADR_PATH/.claude/skills"

echo "=== SyberMem 更新 ==="

sync_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    rm -rf "$target/init-project" "$target/record" "$target/summary"
    for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-update; do
        if [ -d "$SKILL_SOURCE/$skill" ]; then
            rm -rf "$target/$skill"
            cp -r "$SKILL_SOURCE/$skill" "$target/"
            echo "  [$label] 已更新: /$skill"
        fi
    done
}

sync_skills "$CLAUDE_SKILLS" "Claude Code"
sync_skills "$OPENCODE_SKILLS" "OpenCode"

echo ""
echo "=== 更新完成 ==="
echo ""
echo "可用 Skills："
echo "  /sybermem-init-project  — 初始化或刷新当前项目的 SyberMem 配置"
echo "  /sybermem-record        — 创建记录（自动判断类型）"
echo "  /sybermem-summary       — 生成周报/月报"
echo "  /sybermem-digest        — Create a durable phase digest from existing records"
echo "  /sybermem-update        — 更新全局 Skills 并重新检查当前项目"
echo ""
echo "下一步：进入你的项目目录后执行 /sybermem-update"
echo "如果你只想检查项目本地文档是否需要刷新，可执行 /sybermem-init-project"
echo ""
echo "注意：更新全局 Skills 不会自动刷新项目里的 AGENTS.md / CLAUDE.md；请在项目内运行 /sybermem-update 或 /sybermem-init-project"

if [ -d "$LEGACY_LOCAL_SKILLS/sybermem-init-project" ] || [ -d "$LEGACY_LOCAL_SKILLS/sybermem-record" ] || [ -d "$LEGACY_LOCAL_SKILLS/sybermem-summary" ] || [ -d "$LEGACY_LOCAL_SKILLS/sybermem-update" ]; then
    echo ""
    echo "迁移提示：当前仓库仍存在旧的项目级 SyberMem skills 副本 (.claude/skills/sybermem-*)。"
    echo "这些副本会和全局 skills 重复显示；确认已切换到全局安装模式后，可以安全删除它们。"
fi
