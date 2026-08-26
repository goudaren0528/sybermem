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
MAX_LATEST_DIGEST_CONCLUSIONS: Final = 5


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


def _sybermem_json(*args: str, ok_returncodes: tuple[int, ...] = (0,)) -> dict[str, JsonValue] | None:
    """Run a SyberMem JSON command and fail open on launcher/CLI/parse errors."""
    command = _sybermem_command()
    if command is None:
        return None
    try:
        result = subprocess.run(
            [*command, *args],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            timeout=SYBERMEM_TIMEOUT_SECONDS,
        )
        if result.returncode not in ok_returncodes or not result.stdout.strip():
            return None
        payload = json.loads(result.stdout)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _digest_backlog_line() -> str:
    """Return a one-line digest-backlog heads-up, or '' when below threshold/unavailable.

    Reuses `sybermem digest status --format json` (single source of truth) so Codex gets
    the same "haven't digested accumulated work" signal as OpenCode/Claude, with no
    duplicated coverage logic. Fail-open: any error yields no line.
    """
    try:
        payload = _sybermem_json("digest", "status", "--format", "json", ok_returncodes=(0, 1))
        if payload is None:
            return ""
        backlog = payload.get("backlog") or {}
        uncovered = int(backlog.get("uncovered", 0) or 0)
        if uncovered < DIGEST_BACKLOG_THRESHOLD:
            return ""
        days = int(backlog.get("days_since_latest_digest", 0) or 0)
        age = f" (last digest {days}d ago)" if backlog.get("has_digest") and days > 0 else ""
        return f"\u2b50 Digest heads-up: {uncovered} records are not covered by any digest yet{age}. Consider /sybermem-digest to compress the accumulated work."
    except Exception:
        return ""


def _latest_digest_block() -> str:
    """Return the current latest-digest core conclusions block, or '' when unusable.

    Trusts the CLI freshness verdict before surfacing digest conclusions as current facts.
    Fail-open on no digest, stale/unknown status, CLI failure, timeout, or malformed JSON.
    """
    try:
        status_payload = _sybermem_json("digest", "status", "--format", "json", ok_returncodes=(0, 1))
        if status_payload is None:
            return ""
        digests = status_payload.get("digests")
        if not isinstance(digests, list) or not digests:
            return ""
        latest_payload = _sybermem_json("digest", "latest", "--format", "json")
        if latest_payload is None:
            return ""
        record_id = str(latest_payload.get("record_id", "")).strip()
        title = str(latest_payload.get("title", "")).strip()
        if not record_id or not title:
            return ""
        latest_verdict = ""
        for digest in digests:
            if not isinstance(digest, dict):
                continue
            digest_record_id = str(digest.get("record_id", "")).strip()
            if digest_record_id != record_id:
                continue
            latest_verdict = str(digest.get("verdict", "")).strip()
            break
        if latest_verdict != "current":
            return ""
        raw_conclusions = latest_payload.get("conclusions")
        if not isinstance(raw_conclusions, list):
            return ""
        conclusions: list[str] = []
        for item in raw_conclusions:
            if not isinstance(item, str):
                continue
            line = item.strip()
            if not line.startswith("- "):
                continue
            conclusions.append(line)
            if len(conclusions) >= MAX_LATEST_DIGEST_CONCLUSIONS:
                break
        if not conclusions:
            return ""
        return "\n".join([f"### Latest Digest: {title}", *conclusions])
    except Exception:
        return ""


def _pending_habit_line() -> str:
    """Return a durable pending-habit-candidate reminder line, or '' when none.

    A candidate captured passively (`.habit-intent.json`) is NOT an active habit and is
    never injected on its own — the user must confirm it via /sybermem-habit. Surfacing
    it at SessionStart (non-throttled) is what makes the user actually notice and
    confirm; without it, habit injection stays silent forever. Reuses the CLI's
    `habit awareness --format json` (single source of truth). Fail-open.
    """
    try:
        payload = _sybermem_json("habit", "awareness", "--format", "json")
        if payload is None or not payload.get("pending_intent"):
            return ""
        reminder = payload.get("pending_reminder")
        message = ""
        if isinstance(reminder, dict):
            raw = reminder.get("message")
            if isinstance(raw, str):
                message = raw.strip()
        if not message:
            message = (
                "A reusable preference is pending — confirm it with /sybermem-habit so it "
                "can be remembered and injected in future sessions."
            )
        return f"\U0001f4a1 Habit candidate: {message}"
    except Exception:
        return ""


def _constitution_block() -> str:
    """Return the binding-global-norms constitution block, or '' when none/unavailable.

    Reuses `sybermem norms list --scope global --format json` (single source of truth) so
    Codex sessions are governed by binding norms from startup. Fail-open, timeout-bounded.
    """
    try:
        payload = _sybermem_json("norms", "list", "--scope", "global", "--format", "json")
        if payload is None:
            return ""
        norms = payload.get("norms")
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
    latest_digest = _latest_digest_block()
    constitution = _constitution_block()
    pending_habit = _pending_habit_line()
    extras = "\n\n".join(part for part in (latest_digest, constitution, backlog_line, pending_habit) if part)
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
