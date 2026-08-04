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
  sybermem-team-publish sybermem-team-summary; do
  rm -rf "$CLAUDE_SKILLS/$name" || true
  rm -rf "$OPENCODE_SKILLS/$name" || true
done

rm -rf "$CLAUDE_SYBERMEM" || true
rm -f "$OPENCODE_PLUGIN" || true

echo "SyberMem global uninstall complete."
echo "Project histories under .sybermem/ were not removed."
