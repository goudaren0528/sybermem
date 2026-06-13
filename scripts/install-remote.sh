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

echo "=== SyberMem Remote Install ==="
echo ""

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Downloading from GitHub..."
curl -sL "$TARBALL_URL" | tar xz -C "$TMPDIR"

SKILLS_SRC="$TMPDIR/$ARCHIVE_PREFIX/packages/claude-skills"
LAUNCHER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/global-stop-hook-launcher.py"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "Error: skills not found in archive"
    exit 1
fi

install_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    rm -rf "$target/init-project" "$target/record" "$target/summary"
    for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update; do
        if [ -d "$SKILLS_SRC/$skill" ]; then
            rm -rf "$target/$skill"
            cp -r "$SKILLS_SRC/$skill" "$target/"
            echo "  [$label] installed: /$skill"
        fi
    done
}

install_skills "$CLAUDE_SKILLS" "Claude Code"
install_skills "$OPENCODE_SKILLS" "OpenCode"

mkdir -p "$LAUNCHER_DIR"
cp "$LAUNCHER_SOURCE" "$LAUNCHER_PATH"
chmod +x "$LAUNCHER_PATH"
echo "  [Global] installed stop hook launcher: $LAUNCHER_PATH"

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
echo ""
echo "Next: open your project and run /sybermem-update"
echo "If you only want the local project refresh check, run /sybermem-init-project"
echo ""
echo "Note: updating global skills does not automatically refresh project AGENTS.md / CLAUDE.md files"
echo "Stop hook subdirectory compatibility is now provided by the global launcher at ~/.claude/sybermem/launch_record_change_on_stop.py"
