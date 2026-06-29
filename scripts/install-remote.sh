#!/bin/bash
# SyberMem - Remote Install (no clone needed)
# Usage: curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

set -e

REPO="goudaren0528/sybermem"
BRANCH="main"
TARBALL_URL="https://github.com/$REPO/archive/$BRANCH.tar.gz"
ARCHIVE_PREFIX="sybermem-$BRANCH"

CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"
LAUNCHER_DIR="$HOME/.claude/sybermem"
LAUNCHER_PATH="$LAUNCHER_DIR/launch_record_change_on_stop.py"
SESSION_LAUNCHER_PATH="$LAUNCHER_DIR/launch_session_start_context.py"
OPENCODE_PLUGIN_DIR="$HOME/.config/opencode/plugins"

echo "=== SyberMem Remote Install ==="
echo ""

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Downloading from GitHub..."
curl -sL "$TARBALL_URL" | tar xz -C "$TMPDIR"

SKILLS_SRC="$TMPDIR/$ARCHIVE_PREFIX/packages/claude-skills"
LAUNCHER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/global-stop-hook-launcher.py"
SESSION_LAUNCHER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/global-session-start-launcher.py"
PLUGIN_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/packages/opencode-plugin/sybermem.ts"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "Error: skills not found in archive"
    exit 1
fi

install_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    rm -rf "$target/init-project" "$target/record" "$target/summary"
    for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update sybermem-search sybermem-link sybermem-theme-digest; do
        if [ -d "$SKILLS_SRC/$skill" ]; then
            rm -rf "$target/$skill"
            cp -r "$SKILLS_SRC/$skill" "$target/"
            echo "  [$label] installed: /$skill"
        fi
    done
}

install_skills "$CLAUDE_SKILLS" "Claude Code"
install_skills "$OPENCODE_SKILLS" "OpenCode"

# Claude Code: install global stop hook launcher
if [ -d "$HOME/.claude" ]; then
    mkdir -p "$LAUNCHER_DIR"
    cp "$LAUNCHER_SOURCE" "$LAUNCHER_PATH"
    chmod +x "$LAUNCHER_PATH"
    echo "  [Claude Code] installed stop hook launcher: $LAUNCHER_PATH"
    if [ -f "$SESSION_LAUNCHER_SOURCE" ]; then
        cp "$SESSION_LAUNCHER_SOURCE" "$SESSION_LAUNCHER_PATH"
        chmod +x "$SESSION_LAUNCHER_PATH"
        echo "  [Claude Code] installed session start launcher: $SESSION_LAUNCHER_PATH"
    fi
fi

# OpenCode: install plugin
if [ -d "$HOME/.config/opencode" ]; then
    mkdir -p "$OPENCODE_PLUGIN_DIR"
    if [ -f "$PLUGIN_SOURCE" ]; then
        cp "$PLUGIN_SOURCE" "$OPENCODE_PLUGIN_DIR/sybermem.ts"
        echo "  [OpenCode] installed plugin: $OPENCODE_PLUGIN_DIR/sybermem.ts"
    fi
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Available Skills:"
echo "  /sybermem-init-project  — Initialize or refresh SyberMem in the current project"
echo "  /sybermem-record        — Create a record (auto-detects type)"
echo "  /sybermem-summary       — Generate weekly/monthly reports"
echo "  /sybermem-digest        — Create a durable phase digest from existing records"
echo "  /sybermem-phase-analyze — Build or refresh the persistent phase index from project history"
echo "  /sybermem-phase-confirm — Confirm or adjust candidate phases in the phase index"
echo "  /using-sybermem         — Show current SyberMem status and the recommended next command"
echo "  /sybermem-update        — Refresh global skills, then re-check the current project"
echo "  /sybermem-search        — Search/query records by keyword, topic, phase range, date range, or record ID"
echo "  /sybermem-link          — Add a forward relation between two existing records (implements / fixes / related / superseded-by)"
echo "  /sybermem-theme-digest  — Create a durable topic-level digest that compresses one theme across multiple related phases or records"
echo ""
echo "Next: open your project and run /sybermem-update"
echo "If you only want the local project refresh check, run /sybermem-init-project"
echo ""
echo "Note: updating global skills does not automatically refresh project AGENTS.md / CLAUDE.md files"
echo "Stop hook subdirectory compatibility is now provided by the global launcher at ~/.claude/sybermem/launch_record_change_on_stop.py"
