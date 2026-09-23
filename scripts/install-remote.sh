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
CODEX_SKILLS="$HOME/.agents/skills"
CODEX_HOOK_DIR="$HOME/.codex/hooks"
CODEX_HOOK_PATH="$CODEX_HOOK_DIR/sybermem_user_prompt.py"
CODEX_SESSION_HOOK_PATH="$CODEX_HOOK_DIR/sybermem_session_start.py"
CODEX_SESSION_END_HOOK_PATH="$CODEX_HOOK_DIR/sybermem_session_end.py"
CODEX_STOP_HOOK_PATH="$CODEX_HOOK_DIR/sybermem_stop.py"
CODEX_POST_COMPACT_HOOK_PATH="$CODEX_HOOK_DIR/sybermem_post_compact.py"
CODEX_OBSERVABILITY_PATH="$CODEX_HOOK_DIR/_codex_observability.py"
CODEX_HOOKS_JSON="$HOME/.codex/hooks.json"
LAUNCHER_DIR="$HOME/.claude/sybermem"
UNIFIED_LAUNCHER_PATH="$LAUNCHER_DIR/launch_hook.py"
LAUNCHER_PATH="$LAUNCHER_DIR/launch_record_change_on_stop.py"
SESSION_LAUNCHER_PATH="$LAUNCHER_DIR/launch_session_start_context.py"
MANIFEST_PATH="$LAUNCHER_DIR/managed-install.json"
REMOVER_PATH="$LAUNCHER_DIR/safe-managed-remove.py"
CLI_DIR="$HOME/.claude/sybermem/cli"
CLI_VENV="$CLI_DIR/venv"
CLI_WRAPPER="$CLI_DIR/sybermem"
OPENCODE_PLUGIN_DIR="$HOME/.config/opencode/plugins"

CLAUDE_PYTHON=""
for candidate in python python3; do
    command -v "$candidate" >/dev/null 2>&1 || continue
    executable="$("$candidate" -c 'import os,sys; p=os.path.realpath(sys.executable); assert os.path.isabs(p) and os.path.isfile(p) and os.access(p,os.X_OK) and (os.name != "nt" or p.lower().endswith(".exe")); print(p)' 2>/dev/null)" || continue
    [ -n "$executable" ] || continue
    if command -v cygpath >/dev/null 2>&1; then executable="$(cygpath -u "$executable")" || continue; fi
    [ -f "$executable" ] && [ -x "$executable" ] && "$executable" -c 'import sys; sys.exit(0)' >/dev/null 2>&1 || continue
    CLAUDE_PYTHON="$executable"
    break
done
[ -n "$CLAUDE_PYTHON" ] || { echo "Error: no working real Python executable (python/python3); Claude runtime not verified" >&2; exit 1; }
python() { "$CLAUDE_PYTHON" "$@"; }

echo "=== SyberMem Remote Install ==="
echo ""

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Downloading from GitHub..."
curl -sL "$TARBALL_URL" | tar xz -C "$TMPDIR"

SKILLS_SRC="$TMPDIR/$ARCHIVE_PREFIX/packages/claude-skills"
LAUNCHER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/global-stop-hook-launcher.py"
UNIFIED_LAUNCHER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/global-hook-launcher.py"
SESSION_LAUNCHER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/global-session-start-launcher.py"
PLUGIN_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/packages/opencode-plugin/sybermem.ts"
CORE_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/packages/core"
CLI_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/packages/cli"
CODEX_HOOK_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/.codex/hooks/user_prompt.py"
CODEX_SESSION_HOOK_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/.codex/hooks/session_start.py"
CODEX_SESSION_END_HOOK_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/.codex/hooks/session_end.py"
CODEX_STOP_HOOK_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/.codex/hooks/stop.py"
CODEX_POST_COMPACT_HOOK_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/.codex/hooks/post_compact.py"
CODEX_OBSERVABILITY_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/.codex/hooks/_codex_observability.py"
MANIFEST_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/managed-install.json"
REMOVER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/safe-managed-remove.py"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "Error: skills not found in archive"
    exit 1
fi

safe_remove_managed_dir() {
    python "$REMOVER_SOURCE" child --root "$1" --name "$(basename "$2")"
}

install_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    for retired in sybermem-phase-confirm sybermem-team-publish sybermem-team-summary sybermem-link; do
        safe_remove_managed_dir "$target" "$target/$retired"
    done
    for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-resume sybermem-digest sybermem-phase-analyze using-sybermem sybermem-update sybermem-search sybermem-theme-digest sybermem-habit sybermem-uninstall sybermem-install; do
        if [ -d "$SKILLS_SRC/$skill" ]; then
            safe_remove_managed_dir "$target" "$target/$skill"
            cp -r "$SKILLS_SRC/$skill" "$target/"
            echo "  [$label] installed: /$skill"
        fi
    done
}

install_skills "$CLAUDE_SKILLS" "Claude Code"
install_skills "$OPENCODE_SKILLS" "OpenCode"
install_skills "$CODEX_SKILLS" "Codex"

install_codex_user_prompt_hook() {
    if [ ! -f "$CODEX_HOOK_SOURCE" ] || [ ! -f "$CODEX_SESSION_HOOK_SOURCE" ] || [ ! -f "$CODEX_SESSION_END_HOOK_SOURCE" ] || [ ! -f "$CODEX_STOP_HOOK_SOURCE" ] || [ ! -f "$CODEX_POST_COMPACT_HOOK_SOURCE" ]; then
        echo "  [Codex] skipped hooks: one or more sources were not found"
        return
    fi

    mkdir -p "$CODEX_HOOK_DIR"
    cp "$CODEX_HOOK_SOURCE" "$CODEX_HOOK_PATH"
    cp "$CODEX_SESSION_HOOK_SOURCE" "$CODEX_SESSION_HOOK_PATH"
    cp "$CODEX_SESSION_END_HOOK_SOURCE" "$CODEX_SESSION_END_HOOK_PATH"
    cp "$CODEX_STOP_HOOK_SOURCE" "$CODEX_STOP_HOOK_PATH"
    cp "$CODEX_POST_COMPACT_HOOK_SOURCE" "$CODEX_POST_COMPACT_HOOK_PATH"
    if [ -f "$CODEX_OBSERVABILITY_SOURCE" ]; then
        cp "$CODEX_OBSERVABILITY_SOURCE" "$CODEX_OBSERVABILITY_PATH"
    fi
    chmod +x "$CODEX_HOOK_PATH"
    chmod +x "$CODEX_SESSION_HOOK_PATH"
    chmod +x "$CODEX_SESSION_END_HOOK_PATH"
    chmod +x "$CODEX_STOP_HOOK_PATH"
    chmod +x "$CODEX_POST_COMPACT_HOOK_PATH"

    CODEX_HOOK_PATH="$CODEX_HOOK_PATH" CODEX_SESSION_HOOK_PATH="$CODEX_SESSION_HOOK_PATH" CODEX_SESSION_END_HOOK_PATH="$CODEX_SESSION_END_HOOK_PATH" CODEX_STOP_HOOK_PATH="$CODEX_STOP_HOOK_PATH" CODEX_POST_COMPACT_HOOK_PATH="$CODEX_POST_COMPACT_HOOK_PATH" CODEX_HOOKS_JSON="$CODEX_HOOKS_JSON" python - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

hook_path = Path(os.environ["CODEX_HOOK_PATH"])
session_hook_path = Path(os.environ["CODEX_SESSION_HOOK_PATH"])
session_end_hook_path = Path(os.environ["CODEX_SESSION_END_HOOK_PATH"])
stop_hook_path = Path(os.environ["CODEX_STOP_HOOK_PATH"])
post_compact_hook_path = Path(os.environ["CODEX_POST_COMPACT_HOOK_PATH"])
hooks_json = Path(os.environ["CODEX_HOOKS_JSON"])
prompt_managed = {
    "type": "command",
    "command": f'python "{hook_path}"',
    "additionalContextLimit": 6000,
    "statusMessage": "SyberMem：召回相关项目记忆…",
}
session_managed = {
    "type": "command",
    "command": f'python "{session_hook_path}"',
    "additionalContextLimit": 6000,
    "statusMessage": "SyberMem：加载项目记忆与规范…",
}
session_end_managed = {
    "type": "command",
    "command": f'python "{session_end_hook_path}"',
    "statusMessage": "SyberMem：结算本会话召回命中…",
}
stop_managed = {
    "type": "command",
    "command": f'python "{stop_hook_path}"',
    "statusMessage": "SyberMem：检查是否需要记录本次改动…",
}
post_compact_managed = {
    "type": "command",
    "command": f'python "{post_compact_hook_path}"',
    "statusMessage": "SyberMem：标记 compaction 以便下次会话续接…",
}

data: dict[str, object] = {}
if hooks_json.is_file():
    try:
        loaded = json.loads(hooks_json.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    except json.JSONDecodeError:
        data = {}

hooks = data.get("hooks")
if not isinstance(hooks, dict):
    hooks = {}
    data["hooks"] = hooks

def handlers_for(event_name: str) -> list[object]:
    event = hooks.get(event_name)
    if isinstance(event, list):
        return event
    if event is None:
        return []
    return [event]

def without_managed(handlers: list[object], marker: str) -> list[object]:
    return [handler for handler in handlers if not (isinstance(handler, dict) and marker in str(handler.get("command", "")))]

hooks["UserPromptSubmit"] = without_managed(handlers_for("UserPromptSubmit"), "sybermem_user_prompt.py") + [prompt_managed]
hooks["SessionStart"] = without_managed(handlers_for("SessionStart"), "sybermem_session_start.py") + [session_managed]
hooks["SessionEnd"] = without_managed(handlers_for("SessionEnd"), "sybermem_session_end.py") + [session_end_managed]
hooks["Stop"] = without_managed(handlers_for("Stop"), "sybermem_stop.py") + [stop_managed]
hooks["PostCompact"] = without_managed(handlers_for("PostCompact"), "sybermem_post_compact.py") + [post_compact_managed]
hooks_json.parent.mkdir(parents=True, exist_ok=True)
hooks_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
    echo "  [Codex] installed UserPromptSubmit hook: $CODEX_HOOK_PATH"
    echo "  [Codex] installed SessionStart hook: $CODEX_SESSION_HOOK_PATH"
    echo "  [Codex] installed SessionEnd hook: $CODEX_SESSION_END_HOOK_PATH"
    echo "  [Codex] installed Stop hook: $CODEX_STOP_HOOK_PATH"
    echo "  [Codex] installed PostCompact hook: $CODEX_POST_COMPACT_HOOK_PATH"
    echo "  [Codex] updated hooks.json without removing unrelated hooks: $CODEX_HOOKS_JSON"
}

install_codex_user_prompt_hook

# Global launchers: only needed by the Claude Code lifecycle hooks.
python "$TMPDIR/$ARCHIVE_PREFIX/scripts/claude-runtime-deploy.py" --root "$TMPDIR/$ARCHIVE_PREFIX" --home "$HOME" || exit 1

mkdir -p "$CLI_DIR"
python -m venv "$CLI_VENV"
"$CLI_VENV/bin/python" -m pip install --upgrade pip
"$CLI_VENV/bin/pip" install --upgrade --force-reinstall "$CORE_SOURCE" "$CLI_SOURCE"
cat > "$CLI_WRAPPER" <<'EOF'
#!/bin/bash
# Do NOT export SYBERMEM_HOME: it used to split the user-habit store away from the
# documented ~/.sybermem home. The launcher only locates the venv now; Core resolves
# the canonical home so launcher and bare `sybermem` share one habit store.
exec "$HOME/.claude/sybermem/cli/venv/bin/sybermem" "$@"
EOF
chmod +x "$CLI_WRAPPER"
echo "  [Global] installed sybermem CLI: $CLI_WRAPPER"



# Make `sybermem` resolvable without editing the user's shell rc: symlink into
# ~/.local/bin (a conventional per-user bin dir on PATH on most systems). We never
# rewrite shell rc files; if it is not on PATH we print honest guidance below.
LOCAL_BIN="$HOME/.local/bin"
SYBERMEM_ON_PATH=0
mkdir -p "$LOCAL_BIN"
if ln -sf "$CLI_WRAPPER" "$LOCAL_BIN/sybermem" 2>/dev/null; then
    echo "  [Global] linked sybermem into PATH dir: $LOCAL_BIN/sybermem"
    case ":$PATH:" in
        *":$LOCAL_BIN:"*) SYBERMEM_ON_PATH=1 ;;
    esac
fi

# OpenCode deployment is shared with Python and Windows entrypoints.
python "$TMPDIR/$ARCHIVE_PREFIX"/scripts/opencode-install.py install --root "$TMPDIR/$ARCHIVE_PREFIX"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Available Skills:"
echo "  /sybermem-init-project  — Initialize or refresh SyberMem in the current project"
echo "  /sybermem-record        — Create a record (auto-detects type)"
echo "  /sybermem-summary       — Generate weekly/monthly reports"
echo "  /sybermem-resume        — Build a read-only restart view for the current project"
echo "  /sybermem-digest        — Create a durable phase digest from existing records"
echo "  /sybermem-phase-analyze — Build or refresh the persistent phase index from project history"
echo "  /using-sybermem         — Show current SyberMem status and the recommended next command"
echo "  /sybermem-update        — Refresh global skills, then re-check the current project"
echo "  /sybermem-search        — Search/query records by keyword, topic, phase range, date range, or record ID"
echo "  /sybermem-theme-digest  — Create a durable topic-level digest that compresses one theme across multiple related phases or records"

echo "  /sybermem-habit         — Manage user-level habit memory and reminders"
echo "  /sybermem-uninstall     — Safely choose project-level or global uninstall"
echo "  /sybermem-install       — Install the complete SyberMem system from a fresh machine (new-user entrypoint)"
echo ""
if [ "$SYBERMEM_ON_PATH" = "1" ]; then
    echo "sybermem CLI is installed and on PATH. You can now run: sybermem project init --register"
else
    echo "sybermem CLI is installed at: $CLI_WRAPPER"
    echo "It was linked into $LOCAL_BIN/sybermem. If \`sybermem\` still is not found, add $LOCAL_BIN to PATH,"
    echo "or run it by full path: $CLI_WRAPPER project init --register"
fi
echo ""
echo "Next: open your project and run /sybermem-update"
echo "If you only want the local project refresh check, run /sybermem-init-project"
echo ""
echo "Note: updating global skills does not automatically refresh project managed files; run /sybermem-update in the project (it removes legacy AGENTS.md / CLAUDE.md protocol blocks)"
echo "Global Claude hook runtime deployed; project settings NOT migrated. Run sybermem project refresh inside each project. Host behavior is unverified."
