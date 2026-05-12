#!/bin/bash

# ADR 记录系统 - 更新脚本
# 同步最新 skills 到 Claude Code 和 OpenCode 用户级目录

ADR_PATH="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"

echo "=== ADR 记录系统更新 ==="

sync_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    for skill in init-project record summary; do
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
