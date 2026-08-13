from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Final, TypeAlias


HOOK_EVENT_NAME: Final = "PostCompact"
MARKER_FILE: Final = ".codex-compact-marker.json"


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


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


def _payload(stdin_text: str) -> dict[str, JsonValue] | None:
    data: JsonValue = json.loads(stdin_text or "{}")
    if not isinstance(data, dict):
        return None
    event_name = data.get("hookEventName") or data.get("hook_event_name")
    if event_name not in {None, HOOK_EVENT_NAME}:
        return None
    return data


def main() -> int:  # noqa: BROAD_EXCEPT_OK
    try:
        data = _payload(sys.stdin.read())
        if data is None:
            return 0
        root = _project_root()
        if root is None:
            return 0
        trigger = data.get("trigger") if isinstance(data.get("trigger"), str) else "unknown"
        marker = {
            "hook_event_name": HOOK_EVENT_NAME,
            "trigger": trigger,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        (root / ".sybermem" / MARKER_FILE).write_text(json.dumps(marker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
