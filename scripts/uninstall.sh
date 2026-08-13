#!/bin/bash
set -e

CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"
CLAUDE_SYBERMEM="$HOME/.claude/sybermem"
OPENCODE_PLUGIN="$HOME/.config/opencode/plugins/sybermem.ts"

for name in \
  sybermem-init-project sybermem-record sybermem-summary sybermem-digest \
  sybermem-resume sybermem-phase-analyze sybermem-phase-confirm using-sybermem \
  sybermem-update sybermem-search sybermem-link sybermem-theme-digest \
  sybermem-team-publish sybermem-team-summary sybermem-habit; do
  rm -rf "$CLAUDE_SKILLS/$name" || true
  rm -rf "$OPENCODE_SKILLS/$name" || true
done

rm -rf "$CLAUDE_SYBERMEM" || true
rm -f "$OPENCODE_PLUGIN" || true

# Remove the ~/.local/bin/sybermem symlink if it points at our (now removed) wrapper.
LOCAL_BIN_LINK="$HOME/.local/bin/sybermem"
if [ -L "$LOCAL_BIN_LINK" ]; then
  target="$(readlink "$LOCAL_BIN_LINK" 2>/dev/null || true)"
  case "$target" in
    *"/.claude/sybermem/cli/sybermem") rm -f "$LOCAL_BIN_LINK" || true ;;
  esac
fi

echo "SyberMem global uninstall complete."
echo "Project histories under .sybermem/ were not removed."
