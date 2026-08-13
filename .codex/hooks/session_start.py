from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Final, TypeAlias, TypedDict


HOOK_EVENT_NAME: Final = "SessionStart"
SESSION_HEADING: Final = "## SyberMem Manual Session Context"
SYBERMEM_TIMEOUT_SECONDS: Final = 5
COMPACT_MARKER_FILE: Final = ".codex-compact-marker.json"


class HookSpecificOutput(TypedDict):
    hookEventName: str
    additionalContext: str


class HookOutput(TypedDict):
    hookSpecificOutput: HookSpecificOutput


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def _fixed_launcher() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".claude" / "sybermem" / "cli" / "sybermem.cmd"
    return Path(os.environ.get("HOME", str(Path.home()))) / ".claude" / "sybermem" / "cli" / "sybermem"


def _sybermem_command() -> list[str] | None:
    fixed = _fixed_launcher()
    if fixed.is_file():
        return [str(fixed)]
    bare = shutil.which("sybermem")
    if bare:
        return [bare]
    return None


def _project_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    while True:
        has_sybermem = (current / ".sybermem").is_dir()
        has_settings = (current / ".claude" / "settings.json").is_file()
        has_index = (current / ".sybermem" / "INDEX.md").is_file()
        if has_sybermem and (has_settings or has_index):
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _session_start_source(stdin_text: str) -> str | None:
    data: JsonValue = json.loads(stdin_text or "{}")
    if not isinstance(data, dict):
        return None
    event_name = data.get("hookEventName") or data.get("hook_event_name")
    if event_name not in {None, HOOK_EVENT_NAME}:
        return None
    source = data.get("source")
    return source if isinstance(source, str) else "startup"


def _compact_marker(root: Path | None) -> Path | None:
    if root is None:
        return None
    marker = root / ".sybermem" / COMPACT_MARKER_FILE
    return marker if marker.is_file() else None


def _session_markdown() -> str:
    command = _sybermem_command()
    if command is None:
        return ""
    result = subprocess.run(
        [*command, "context", "session", "--format", "markdown"],
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=SYBERMEM_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def _hook_output(markdown: str) -> HookOutput | None:
    markdown = markdown.strip()
    if not markdown.startswith(SESSION_HEADING):
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "additionalContext": f"{markdown}\n",
        }
    }


def main() -> int:  # noqa: BROAD_EXCEPT_OK
    try:
        source = _session_start_source(sys.stdin.read())
        if source is None:
            return 0
        root = _project_root()
        marker = _compact_marker(root)
        if source == "compact" and marker is None:
            return 0
        output = _hook_output(_session_markdown())
        if output is not None:
            sys.stdout.write(json.dumps(output, ensure_ascii=False))
            if source == "compact" and marker is not None:
                marker.unlink(missing_ok=True)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
