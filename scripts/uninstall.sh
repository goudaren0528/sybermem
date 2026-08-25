#!/bin/bash
set -e

CLAUDE_SYBERMEM="$HOME/.claude/sybermem"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MANIFEST="$CLAUDE_SYBERMEM/managed-install.json"
REMOVER="$CLAUDE_SYBERMEM/safe-managed-remove.py"
[ -f "$MANIFEST" ] || MANIFEST="$SCRIPT_DIR/managed-install.json"
[ -f "$REMOVER" ] || REMOVER="$SCRIPT_DIR/safe-managed-remove.py"
python "$REMOVER" uninstall --home "$HOME" --manifest "$MANIFEST"

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
