#!/bin/bash

# SyberMem - 更新脚本
# 同步最新 skills 到 Claude Code 和 OpenCode 用户级目录

ADR_PATH="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_SOURCE="$ADR_PATH/packages/claude-skills"
CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"
LAUNCHER_DIR="$HOME/.claude/sybermem"
LAUNCHER_PATH="$LAUNCHER_DIR/launch_record_change_on_stop.py"
LAUNCHER_SOURCE="$ADR_PATH/scripts/global-stop-hook-launcher.py"
SESSION_LAUNCHER_SOURCE="$ADR_PATH/scripts/global-session-start-launcher.py"
SESSION_LAUNCHER_PATH="$LAUNCHER_DIR/launch_session_start_context.py"
CLI_DIR="$HOME/.claude/sybermem/cli"
CLI_VENV="$CLI_DIR/venv"
CLI_WRAPPER="$CLI_DIR/sybermem"
PLUGIN_SOURCE="$ADR_PATH/packages/opencode-plugin/sybermem.ts"
OPENCODE_PLUGIN_DIR="$HOME/.config/opencode/plugins"
LEGACY_LOCAL_SKILLS="$ADR_PATH/.claude/skills"

echo "=== SyberMem 更新 ==="

sync_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    rm -rf "$target/init-project" "$target/record" "$target/summary"
    for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-resume sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update sybermem-search sybermem-link sybermem-theme-digest sybermem-team-publish sybermem-team-summary; do
        if [ -d "$SKILL_SOURCE/$skill" ]; then
            rm -rf "$target/$skill"
            cp -r "$SKILL_SOURCE/$skill" "$target/"
            echo "  [$label] 已更新: /$skill"
        fi
    done
}

sync_skills "$CLAUDE_SKILLS" "Claude Code"
sync_skills "$OPENCODE_SKILLS" "OpenCode"

mkdir -p "$LAUNCHER_DIR"
cp "$LAUNCHER_SOURCE" "$LAUNCHER_PATH"
chmod +x "$LAUNCHER_PATH"
echo "  [Global] 已安装 stop hook launcher: $LAUNCHER_PATH"
cp "$SESSION_LAUNCHER_SOURCE" "$SESSION_LAUNCHER_PATH"
chmod +x "$SESSION_LAUNCHER_PATH"
echo "  [Global] 已安装 session start launcher: $SESSION_LAUNCHER_PATH"
mkdir -p "$CLI_DIR"
python -m venv "$CLI_VENV"
"$CLI_VENV/bin/python" -m pip install --upgrade pip
"$CLI_VENV/bin/pip" install "$ADR_PATH/packages/core" "$ADR_PATH/packages/cli"
cat > "$CLI_WRAPPER" <<'EOF'
#!/bin/bash
SYBERMEM_HOME="$HOME/.claude/sybermem/cli"
exec "$SYBERMEM_HOME/venv/bin/sybermem" "$@"
EOF
chmod +x "$CLI_WRAPPER"
echo "  [Global] 已安装 sybermem CLI: $CLI_WRAPPER"

if [ -d "$HOME/.config/opencode" ]; then
    mkdir -p "$OPENCODE_PLUGIN_DIR"
    cp "$PLUGIN_SOURCE" "$OPENCODE_PLUGIN_DIR/sybermem.ts"
    echo "  [OpenCode] 已更新 plugin: $OPENCODE_PLUGIN_DIR/sybermem.ts"
fi

echo ""
echo "=== 更新完成 ==="
echo ""
echo "可用 Skills："
echo "  /sybermem-init-project  — 初始化或刷新当前项目的 SyberMem 配置"
echo "  /sybermem-record        — 创建记录（自动判断类型）"
echo "  /sybermem-summary       — 基于现有记录生成周报/月报"
echo "  /sybermem-resume        — 基于当前项目状态生成只读续接视图"
echo "  /sybermem-digest        — 基于现有记录沉淀阶段摘要"
echo "  /sybermem-phase-analyze — 从项目历史构建或刷新持久化阶段索引"
echo "  /sybermem-phase-confirm — 确认或调整阶段索引中的候选阶段"
echo "  /using-sybermem         — 显示当前 SyberMem 状态和建议的下一步命令"
echo "  /sybermem-update        — 更新全局 Skills 并重新检查当前项目"
echo "  /sybermem-search        — 按关键词、topic、phase 范围、日期范围或记录 ID 检索记录"
echo "  /sybermem-link          — 在两条已有记录间建立正向关系（implements / fixes / related / superseded-by）"
echo "  /sybermem-theme-digest  — 为单个 topic 创建跨多个 phase 的持久化高阶摘要"
echo "  /sybermem-team-publish  — 将当前项目发布到 Team memory"
echo "  /sybermem-team-summary  — 生成 Team 管理摘要"
echo ""
echo "sybermem CLI 已安装，可直接运行：sybermem project init --register"
echo ""
echo "下一步：进入你的项目目录后执行 /sybermem-update"
echo "如果你只想检查项目本地文档是否需要刷新，可执行 /sybermem-init-project"
echo ""
echo "注意：更新全局 Skills 不会自动刷新项目里的 AGENTS.md / CLAUDE.md；请在项目内运行 /sybermem-update 或 /sybermem-init-project"
echo "注意：stop hook 的子目录兼容现在由全局 launcher 提供：~/.claude/sybermem/launch_record_change_on_stop.py"

if [ -d "$LEGACY_LOCAL_SKILLS/sybermem-init-project" ] || [ -d "$LEGACY_LOCAL_SKILLS/sybermem-record" ] || [ -d "$LEGACY_LOCAL_SKILLS/sybermem-summary" ] || [ -d "$LEGACY_LOCAL_SKILLS/sybermem-update" ]; then
    echo ""
    echo "迁移提示：当前仓库仍存在旧的项目级 SyberMem skills 副本 (.claude/skills/sybermem-*)。"
    echo "这些副本会和全局 skills 重复显示；确认已切换到全局安装模式后，可以安全删除它们。"
fi
