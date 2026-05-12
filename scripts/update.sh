#!/bin/bash

# SyberMem - 更新脚本
# 同步最新 skills 到 Claude Code 和 OpenCode 用户级目录

ADR_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"

echo "=== SyberMem 更新 ==="

sync_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    rm -rf "$target/init-project" "$target/record" "$target/summary"
    for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-update; do
        if [ -d "$ADR_PATH/.claude/skills/$skill" ]; then
            rm -rf "$target/$skill"
            cp -r "$ADR_PATH/.claude/skills/$skill" "$target/"
            echo "  [$label] 已更新: /$skill"
        fi
    done
}

sync_skills "$CLAUDE_SKILLS" "Claude Code"
sync_skills "$OPENCODE_SKILLS" "OpenCode"

echo ""
echo "=== 更新完成 ==="
echo ""
echo "下一步：进入你的项目目录后执行 /sybermem-update"
echo "如果你只想检查项目本地文档是否需要刷新，可执行 /sybermem-init-project"
echo ""
echo "注意：更新全局 Skills 不会自动刷新项目里的 AGENTS.md / CLAUDE.md；请在项目内运行 /sybermem-update 或 /sybermem-init-project"
