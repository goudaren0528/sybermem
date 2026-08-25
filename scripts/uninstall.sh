#!/bin/bash
set -e

CLAUDE_SKILLS="$HOME/.claude/skills"
OPENCODE_SKILLS="$HOME/.config/opencode/skills"
CODEX_SKILLS="$HOME/.agents/skills"
CLAUDE_SYBERMEM="$HOME/.claude/sybermem"
OPENCODE_PLUGIN="$HOME/.config/opencode/plugins/sybermem.ts"

safe_remove_managed_dir() {
  local root="$1" target="$2"
  [ -e "$target" ] || [ -L "$target" ] || return 0
  [ ! -L "$root" ] || { echo "Refusing linked managed root: $root" >&2; return 1; }
  local root_real parent_real
  root_real="$(cd "$root" && pwd -P)" || return 1
  parent_real="$(cd "$(dirname "$target")" && pwd -P)" || return 1
  [ "$parent_real" = "$root_real" ] || { echo "Refusing to remove path outside managed root: $target" >&2; return 1; }
  if [ -L "$target" ]; then rm -f -- "$target"; else rm -rf -- "$target"; fi
}

for name in \
  sybermem-init-project sybermem-record sybermem-summary sybermem-digest \
  sybermem-resume sybermem-phase-analyze using-sybermem \
  sybermem-update sybermem-search sybermem-link sybermem-theme-digest \
  sybermem-team-publish sybermem-team-summary sybermem-habit \
  sybermem-phase-confirm; do
  safe_remove_managed_dir "$CLAUDE_SKILLS" "$CLAUDE_SKILLS/$name" || true
  safe_remove_managed_dir "$OPENCODE_SKILLS" "$OPENCODE_SKILLS/$name" || true
  safe_remove_managed_dir "$CODEX_SKILLS" "$CODEX_SKILLS/$name" || true
done

# Remove only SyberMem-owned launcher/runtime paths. Preserve unknown user files.
safe_remove_managed_dir "$CLAUDE_SYBERMEM" "$CLAUDE_SYBERMEM/cli" || true
rm -f -- "$CLAUDE_SYBERMEM/launch_record_change_on_stop.py" || true
rm -f -- "$CLAUDE_SYBERMEM/launch_session_start_context.py" || true
rm -f -- "$CLAUDE_SYBERMEM/VERSION" || true
rmdir "$CLAUDE_SYBERMEM" 2>/dev/null || true
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
