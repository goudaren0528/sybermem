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
CODEX_HOOKS_JSON="$HOME/.codex/hooks.json"
LAUNCHER_DIR="$HOME/.claude/sybermem"
LAUNCHER_PATH="$LAUNCHER_DIR/launch_record_change_on_stop.py"
SESSION_LAUNCHER_PATH="$LAUNCHER_DIR/launch_session_start_context.py"
CLI_DIR="$HOME/.claude/sybermem/cli"
CLI_VENV="$CLI_DIR/venv"
CLI_WRAPPER="$CLI_DIR/sybermem"
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
CORE_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/packages/core"
CLI_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/packages/cli"
CODEX_HOOK_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/.codex/hooks/user_prompt.py"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "Error: skills not found in archive"
    exit 1
fi

install_skills() {
    local target="$1"
    local label="$2"
    mkdir -p "$target"
    rm -rf "$target/init-project" "$target/record" "$target/summary"
    for skill in sybermem-init-project sybermem-record sybermem-summary sybermem-resume sybermem-digest sybermem-phase-analyze sybermem-phase-confirm using-sybermem sybermem-update sybermem-search sybermem-link sybermem-theme-digest sybermem-team-publish sybermem-team-summary sybermem-habit; do
        if [ -d "$SKILLS_SRC/$skill" ]; then
            rm -rf "$target/$skill"
            cp -r "$SKILLS_SRC/$skill" "$target/"
            echo "  [$label] installed: /$skill"
        fi
    done
}

install_skills "$CLAUDE_SKILLS" "Claude Code"
install_skills "$OPENCODE_SKILLS" "OpenCode"
install_skills "$CODEX_SKILLS" "Codex"

install_codex_user_prompt_hook() {
    if [ ! -f "$CODEX_HOOK_SOURCE" ]; then
        echo "  [Codex] skipped user prompt hook: source not found at $CODEX_HOOK_SOURCE"
        return
    fi

    mkdir -p "$CODEX_HOOK_DIR"
    cp "$CODEX_HOOK_SOURCE" "$CODEX_HOOK_PATH"
    chmod +x "$CODEX_HOOK_PATH"

    CODEX_HOOK_PATH="$CODEX_HOOK_PATH" CODEX_HOOKS_JSON="$CODEX_HOOKS_JSON" python - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

hook_path = Path(os.environ["CODEX_HOOK_PATH"])
hooks_json = Path(os.environ["CODEX_HOOKS_JSON"])
command = f'python "{hook_path}"'
managed = {
    "type": "command",
    "command": command,
    "additionalContextLimit": 6000,
    "message": "SyberMem user habit reminders add Codex prompt context when relevant.",
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

event = hooks.get("UserPromptSubmit")
if isinstance(event, list):
    handlers = event
elif event is None:
    handlers = []
else:
    handlers = [event]

def is_managed(value: object) -> bool:
    return isinstance(value, dict) and "sybermem_user_prompt.py" in str(value.get("command", ""))

hooks["UserPromptSubmit"] = [handler for handler in handlers if not is_managed(handler)] + [managed]
hooks_json.parent.mkdir(parents=True, exist_ok=True)
hooks_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
    echo "  [Codex] installed UserPromptSubmit hook: $CODEX_HOOK_PATH"
    echo "  [Codex] updated hooks.json without removing unrelated hooks: $CODEX_HOOKS_JSON"
}

install_codex_user_prompt_hook

# Global launchers: only needed by the Claude Code lifecycle hooks.
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

# sybermem CLI/runtime: install unconditionally. OpenCode skills (search/record/
# using-sybermem) call the `sybermem` CLI, so gating this on ~/.claude would leave
# OpenCode-only machines with skills that invoke a runtime that was never installed.
mkdir -p "$CLI_DIR"
python -m venv "$CLI_VENV"
"$CLI_VENV/bin/python" -m pip install --upgrade pip
"$CLI_VENV/bin/pip" install --upgrade --force-reinstall "$CORE_SOURCE" "$CLI_SOURCE"
cat > "$CLI_WRAPPER" <<'EOF'
#!/bin/bash
SYBERMEM_HOME="$HOME/.claude/sybermem/cli"
exec "$SYBERMEM_HOME/venv/bin/sybermem" "$@"
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
echo "  /sybermem-resume        — Build a read-only restart view for the current project"
echo "  /sybermem-digest        — Create a durable phase digest from existing records"
echo "  /sybermem-phase-analyze — Build or refresh the persistent phase index from project history"
echo "  /sybermem-phase-confirm — Confirm or adjust candidate phases in the phase index"
echo "  /using-sybermem         — Show current SyberMem status and the recommended next command"
echo "  /sybermem-update        — Refresh global skills, then re-check the current project"
echo "  /sybermem-search        — Search/query records by keyword, topic, phase range, date range, or record ID"
echo "  /sybermem-link          — Add a forward relation between two existing records (implements / fixes / related / superseded-by)"
echo "  /sybermem-theme-digest  — Create a durable topic-level digest that compresses one theme across multiple related phases or records"
echo "  /sybermem-team-publish  — Publish the current project into Team memory"
echo "  /sybermem-team-summary  — Generate the Team management summary"
echo "  /sybermem-habit         — Manage user-level habit memory and reminders"
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
echo "Note: updating global skills does not automatically refresh project AGENTS.md / CLAUDE.md files"
echo "Stop hook subdirectory compatibility is now provided by the global launcher at ~/.claude/sybermem/launch_record_change_on_stop.py"
