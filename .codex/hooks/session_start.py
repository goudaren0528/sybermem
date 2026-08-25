from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Final, TypeAlias, TypedDict


HOOK_EVENT_NAME: Final = "SessionStart"
CODEX_STARTUP_HEADING: Final = "## SyberMem Codex Startup"
SESSION_HEADING: Final = "## SyberMem Manual Session Context"
SYBERMEM_TIMEOUT_SECONDS: Final = 5
COMPACT_MARKER_FILE: Final = ".codex-compact-marker.json"
DIGEST_BACKLOG_THRESHOLD: Final = 5


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


def _digest_backlog_line() -> str:
    """Return a one-line digest-backlog heads-up, or '' when below threshold/unavailable.

    Reuses `sybermem digest status --format json` (single source of truth) so Codex gets
    the same "haven't digested accumulated work" signal as OpenCode/Claude, with no
    duplicated coverage logic. Fail-open: any error yields no line.
    """
    command = _sybermem_command()
    if command is None:
        return ""
    try:
        result = subprocess.run(
            [*command, "digest", "status", "--format", "json"],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False, timeout=SYBERMEM_TIMEOUT_SECONDS,
        )
        if result.returncode not in (0, 1) or not result.stdout.strip():
            return ""
        payload = json.loads(result.stdout)
        backlog = payload.get("backlog") or {}
        uncovered = int(backlog.get("uncovered", 0) or 0)
        if uncovered < DIGEST_BACKLOG_THRESHOLD:
            return ""
        days = int(backlog.get("days_since_latest_digest", 0) or 0)
        age = f" (last digest {days}d ago)" if backlog.get("has_digest") and days > 0 else ""
        return f"\u2b50 Digest heads-up: {uncovered} records are not covered by any digest yet{age}. Consider /sybermem-digest to compress the accumulated work."
    except Exception:
        return ""


def _constitution_block() -> str:
    """Return the binding-global-norms constitution block, or '' when none/unavailable.

    Reuses `sybermem norms list --scope global --format json` (single source of truth) so
    Codex sessions are governed by binding norms from startup. Fail-open, timeout-bounded.
    """
    command = _sybermem_command()
    if command is None:
        return ""
    try:
        result = subprocess.run(
            [*command, "norms", "list", "--scope", "global", "--format", "json"],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False, timeout=SYBERMEM_TIMEOUT_SECONDS,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return ""
        norms = json.loads(result.stdout).get("norms")
        if not isinstance(norms, list) or not norms:
            return ""
        lines = ["Project Norms (binding — follow unless the user explicitly overrides):"]
        for norm in norms:
            if not isinstance(norm, dict):
                continue
            statement = str(norm.get("statement", "")).strip()
            record_id = str(norm.get("record_id", "")).strip()
            if statement:
                lines.append(f"- [{record_id}] {statement}")
        return "\n".join(lines) if len(lines) > 1 else ""
    except Exception:
        return ""


def _hook_output(markdown: str) -> HookOutput | None:
    markdown = markdown.strip()
    if not markdown.startswith(SESSION_HEADING):
        return None
    backlog_line = _digest_backlog_line()
    constitution = _constitution_block()
    extras = "\n".join(part for part in (constitution, backlog_line) if part)
    marker = f"{CODEX_STARTUP_HEADING}\n\nSyberMem injected startup context for this Codex session."
    body = "\n".join(part for part in (markdown, extras) if part)
    context = f"{marker}\n\n{body}\n"
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "additionalContext": context,
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
