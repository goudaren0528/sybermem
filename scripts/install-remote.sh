#!/bin/bash
# ADR Record System - Remote Install (no clone needed)
# Usage: curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

set -e

REPO="goudaren0528/sybermem"
BRANCH="main"
TARBALL_URL="https://github.com/$REPO/archive/$BRANCH.tar.gz"
ARCHIVE_PREFIX="sybermem-$BRANCH"

CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"

echo "=== ADR Record System - Remote Install ==="
echo ""

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Downloading from GitHub..."
curl -sL "$TARBALL_URL" | tar xz -C "$TMPDIR"

SKILLS_SRC="$TMPDIR/$ARCHIVE_PREFIX/.claude/skills"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "Error: skills not found in archive"
    exit 1
fi

install_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    for skill in init-project record summary; do
        if [ -d "$SKILLS_SRC/$skill" ]; then
            cp -r "$SKILLS_SRC/$skill" "$target/"
            echo "  [$label] installed: /$skill"
        fi
    done
}

install_skills "$CLAUDE_SKILLS" "Claude Code"
install_skills "$OPENCODE_SKILLS" "OpenCode"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Available Skills:"
echo "  /init-project  — Initialize ADR system"
echo "  /record        — Create a record (auto-detects type)"
echo "  /summary       — Generate weekly/monthly report"
echo ""
echo "Next: run /init-project in your project directory"
