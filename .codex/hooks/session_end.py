from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Final, TypeAlias

HOOK_EVENT_NAME: Final = "SessionEnd"
# SessionEnd runs with a very tight budget (Codex default 1s, max 3s). Keep every
# subprocess short and bail out to a no-evidence outcome rather than risk a timeout.
GIT_TIMEOUT_SECONDS: Final = 2
CLI_TIMEOUT_SECONDS: Final = 3
MEMORY_USAGE_FILE: Final = ".memory-usage.jsonl"

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import _codex_observability as _obs
except Exception:  # pragma: no cover - observability is optional/fail-open
    _obs = None  # type: ignore[assignment]


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


def _payload(stdin_text: str) -> tuple[dict[str, JsonValue] | None, str]:
    data: JsonValue = json.loads(stdin_text or "{}")
    if not isinstance(data, dict):
        return None, ""
    event_name = data.get("hookEventName") or data.get("hook_event_name")
    if event_name not in {None, HOOK_EVENT_NAME}:
        return None, ""
    session_id = data.get("session_id") or data.get("sessionId") or ""
    return data, (session_id if isinstance(session_id, str) else "")


def _injected_ids_for_session(root: Path, session_id: str) -> list[str]:
    """Aggregate injected record ids this session wrote to .memory-usage.jsonl.

    Reads back the per-turn rows this hook's UserPromptSubmit sibling wrote. When
    session_id is empty (not provided), fall back to all recent codex turns so the
    outcome is still best-effort rather than empty.
    """
    path = root / ".sybermem" / MEMORY_USAGE_FILE
    if not path.is_file():
        return []
    ids: list[str] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(row, dict) or row.get("host") != "codex" or row.get("event") == "session_outcome":
                continue
            if session_id and row.get("session_id") != session_id:
                continue
            for rid in row.get("injected_ids", []) or []:
                if isinstance(rid, str) and rid and rid not in ids:
                    ids.append(rid)
    except OSError:
        return []
    return ids


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except Exception:
        return ""
    return result.stdout if result.returncode == 0 else ""


def _edited_files(root: Path) -> set[str]:
    files: set[str] = set()
    for output in (
        _git(root, "diff", "--name-only"),
        _git(root, "diff", "--cached", "--name-only"),
        _git(root, "ls-files", "--others", "--exclude-standard"),
    ):
        for line in output.splitlines():
            normalized = line.strip().replace("\\", "/")
            if normalized:
                files.add(normalized)
    return files


def _related_files(ids: list[str]) -> dict[str, list[str]]:
    command = _sybermem_command()
    if command is None or not ids:
        return {}
    try:
        result = subprocess.run(
            [*command, "project", "record-files", "--ids", ",".join(ids), "--format", "json"],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            timeout=CLI_TIMEOUT_SECONDS,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        payload = json.loads(result.stdout)
        records = payload.get("records") if isinstance(payload, dict) else None
        if not isinstance(records, dict):
            return {}
        mapping: dict[str, list[str]] = {}
        for key, value in records.items():
            if isinstance(value, list):
                mapping[str(key).lower()] = [str(item).replace("\\", "/") for item in value if isinstance(item, str)]
        return mapping
    except Exception:
        return {}


def _compute_outcome(injected: list[str], related: dict[str, list[str]], edited: set[str]) -> tuple[int, int, int]:
    """Return (measurable, unmeasurable, hit) mirroring recall_outcome.ts.

    A record with no related_files anchor is unmeasurable (excluded from precision
    denominator); an anchored record hits when any related file was edited.
    """
    measurable = 0
    unmeasurable = 0
    hit = 0
    for rid in injected:
        files = related.get(rid.lower(), [])
        if not files:
            unmeasurable += 1
            continue
        measurable += 1
        if any(f in edited for f in files):
            hit += 1
    return measurable, unmeasurable, hit


def main() -> int:  # noqa: BROAD_EXCEPT_OK
    try:
        data, session_id = _payload(sys.stdin.read())
        if data is None or _obs is None:
            return 0
        root = _project_root()
        if root is None:
            return 0
        injected = _injected_ids_for_session(root, session_id)
        if not injected:
            # Nothing was injected this session; no outcome to record.
            return 0
        edited = _edited_files(root)
        related = _related_files(injected)
        if not related:
            # Could not gather related_files within budget: record no-evidence outcome.
            _obs.append_session_outcome(
                root,
                session_id=session_id,
                injected_ids=injected,
                edited_files=len(edited),
                evidence_available=False,
                measurable=0,
                unmeasurable=0,
                hit=0,
            )
            return 0
        measurable, unmeasurable, hit = _compute_outcome(injected, related, edited)
        _obs.append_session_outcome(
            root,
            session_id=session_id,
            injected_ids=injected,
            edited_files=len(edited),
            evidence_available=True,
            measurable=measurable,
            unmeasurable=unmeasurable,
            hit=hit,
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
