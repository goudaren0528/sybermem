from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Final, TypeAlias, TypedDict


HOOK_EVENT_NAME: Final = "Stop"
NUDGE_STATE_FILE: Final = ".nudge-state.json"
RECORD_THRESHOLD: Final = 5
HIGH_SIGNAL_FILES: Final = ("README.md", "INSTALL.md", "AGENTS.md", "CLAUDE.md")


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class StopOutput(TypedDict):
    decision: str
    reason: str
    systemMessage: str


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


def _is_stop(stdin_text: str) -> bool:
    data: JsonValue = json.loads(stdin_text or "{}")
    if not isinstance(data, dict):
        return False
    if data.get("stop_hook_active") is True:
        return False
    event_name = data.get("hookEventName") or data.get("hook_event_name")
    return event_name in {None, HOOK_EVENT_NAME}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout


def _changed_files(root: Path) -> list[str]:
    files: list[str] = []
    for output in (_git(root, "diff", "--name-only"), _git(root, "diff", "--cached", "--name-only"), _git(root, "ls-files", "--others", "--exclude-standard")):
        for line in output.splitlines():
            file = line.strip().replace("\\", "/")
            if not file or file.startswith((".git/", ".sybermem/", ".claude/", ".codex/", "node_modules/")):
                continue
            if file not in files:
                files.append(file)
    return files


def _state_path(root: Path) -> Path:
    return root / ".sybermem" / NUDGE_STATE_FILE


def _load_state(root: Path) -> dict[str, JsonValue]:
    try:
        data = json.loads(_state_path(root).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(root: Path, state: dict[str, JsonValue]) -> None:
    _state_path(root).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _reason(files: list[str]) -> str | None:
    if len(files) >= RECORD_THRESHOLD or any(file in HIGH_SIGNAL_FILES for file in files):
        return "SyberMem: this change looks important enough for a manual /sybermem-record so the reason and impact are preserved."
    return None


def _output(reason: str) -> StopOutput:
    return {
        "decision": "block",
        "reason": reason,
        "systemMessage": "SyberMem Stop nudge requested a bounded follow-up.",
    }


def main() -> int:  # noqa: BROAD_EXCEPT_OK
    try:
        if not _is_stop(sys.stdin.read()):
            return 0
        root = _project_root()
        if root is None:
            return 0
        files = _changed_files(root)
        if not files:
            return 0
        fingerprint = json.dumps(files, ensure_ascii=False)
        state = _load_state(root)
        if state.get("codex_stop_fingerprint") == fingerprint:
            return 0
        reason = _reason(files)
        if reason is None:
            _save_state(root, {**state, "codex_stop_fingerprint": fingerprint})
            return 0
        _save_state(root, {**state, "codex_stop_fingerprint": fingerprint, "last_nudge_type": "record", "last_theme": "codex"})
        sys.stdout.write(json.dumps(_output(reason), ensure_ascii=False))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
