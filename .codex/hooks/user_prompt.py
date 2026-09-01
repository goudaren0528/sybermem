from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Final, TypeAlias, TypedDict
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import _codex_observability as _obs
except Exception:  # pragma: no cover - observability is optional/fail-open
    _obs = None  # type: ignore[assignment]


HOOK_EVENT_NAME: Final = "UserPromptSubmit"
CODEX_CONTEXT_HEADING: Final = "## SyberMem Codex Context"
RECALL_HEADING: Final = "## SyberMem Recall Hints"
REMINDER_HEADING: Final = "## User Habit Reminder"
NORMS_HEADING: Final = "## Relevant Project Norms"
SYBERMEM_TIMEOUT_SECONDS: Final = 5
RECORD_INTENT_PATH: Final = ".sybermem/.record-intent.json"
RECORD_ID_RE: Final = re.compile(r"\b(?:change|decision|requirement|bug|digest|habit|norm)-[a-z0-9-]+\b", re.IGNORECASE)


def _system_message_enabled() -> bool:
    """B2 gate. Default ON; explicit falsey values turn the per-turn systemMessage off."""
    raw = os.environ.get("SYBERMEM_CODEX_SYSTEM_MESSAGE", "").strip().lower()
    return raw not in {"0", "false", "no", "off"}


class HookInput(TypedDict, total=False):
    prompt: str
    userPrompt: str


class HookSpecificOutput(TypedDict):
    hookEventName: str
    additionalContext: str


class HookOutput(TypedDict, total=False):
    hookSpecificOutput: HookSpecificOutput
    systemMessage: str


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


def _parse_stdin(stdin_text: str) -> tuple[str | None, str]:
    """Return (prompt, session_id). session_id is "" when absent."""
    data: JsonValue = json.loads(stdin_text)
    if not isinstance(data, dict):
        return None, ""
    prompt = _string_field(data, "userPrompt") or _string_field(data, "prompt")
    session_id = _string_field(data, "session_id") or _string_field(data, "sessionId") or ""
    return (prompt if prompt else None), session_id


def _string_field(data: dict[str, JsonValue], key: str) -> str | None:
    value = data.get(key)
    if isinstance(value, str):
        return value
    return None


def _run_cli(args: list[str]) -> str:
    command = _sybermem_command()
    if command is None:
        return ""
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
    if result.returncode != 0:
        return ""
    return result.stdout


def _context_markdown(prompt: str, kind: str) -> str:
    if kind == "recall":
        return _run_cli(["context", "recall", "--query", prompt, "--format", "markdown"])
    return _run_cli(["context", "habit", "--context", prompt, "--delivery", "prompt-time", "--format", "markdown"])


def _recall_json(prompt: str) -> tuple[list[str], list[str], str]:
    """A4: precise recall counts/ids/abstention via JSON.

    Returns (record_ids, match_classes, abstention_reason). Fail-open to empty.
    """
    raw = _run_cli(["context", "recall", "--query", prompt, "--format", "json"])
    if not raw.strip():
        return [], [], ""
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return [], [], ""
    if not isinstance(payload, dict):
        return [], [], ""
    results = payload.get("results")
    record_ids: list[str] = []
    match_classes: list[str] = []
    if isinstance(results, list):
        for row in results:
            if not isinstance(row, dict):
                continue
            rid = str(row.get("record_id", "")).strip().lower()
            if rid:
                record_ids.append(rid)
            match = str(row.get("match", "")).strip().lower()
            if match:
                match_classes.append(match)
    abstention = payload.get("abstention")
    reason = str(abstention).strip() if isinstance(abstention, str) else ""
    return record_ids, match_classes, reason


def _core_paths() -> list[Path]:
    paths: list[Path] = []
    source_root = Path(__file__).resolve().parents[2]
    paths.append(source_root / "packages" / "core")

    fixed = _fixed_launcher()
    if os.name == "nt":
        paths.append(fixed.parent / "venv" / "Lib" / "site-packages")
    else:
        lib = fixed.parent / "venv" / "lib"
        if lib.is_dir():
            paths.extend(path / "site-packages" for path in lib.glob("python*"))
    return paths


def _ensure_core_import_path() -> None:
    for path in _core_paths():
        if path.exists():
            value = str(path)
            if value not in sys.path:
                sys.path.insert(0, value)


def _capture_record_intent(prompt: str) -> None:
    _ensure_core_import_path()
    from sybermem_core.project import resolve_project_root
    from sybermem_core.record_intent import WRITE_CLASSIFICATIONS, classify_record_intent

    root = resolve_project_root()
    if root is None:
        return
    candidate = classify_record_intent(root, prompt)
    classification = candidate.get("classification", "defer")
    if classification not in WRITE_CLASSIFICATIONS:
        return
    payload = {
        "record_intent": True,
        "classification": classification,
        "action": candidate.get("action", "/sybermem-record"),
        "reason": candidate.get("reason", ""),
        "source": "codex-user-prompt-submit",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "matched_pattern": classification,
        "phrase": "",
    }
    (root / RECORD_INTENT_PATH).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _scoped_norms_section(prompt: str) -> str:
    """Render a '## Relevant Project Norms' section for scoped norms matching this prompt.

    Global norms are delivered by SessionStart (the constitution); this surfaces only
    scoped norms via 'norms list --scope scoped --context <prompt>' (JSON). Fail-open.
    """
    command = _sybermem_command()
    if command is None:
        return ""
    try:
        result = subprocess.run(
            [*command, "norms", "list", "--scope", "scoped", "--context", prompt, "--format", "json"],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False, timeout=SYBERMEM_TIMEOUT_SECONDS,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return ""
        norms = json.loads(result.stdout).get("norms")
        if not isinstance(norms, list) or not norms:
            return ""
        lines = ["## Relevant Project Norms"]
        for norm in norms:
            if not isinstance(norm, dict):
                continue
            statement = str(norm.get("statement", "")).strip()
            record_id = str(norm.get("record_id", "")).strip()
            scope = str(norm.get("scope", "")).strip() or "scoped"
            if statement:
                lines.append(f"- [{record_id}] ({scope}) {statement}")
        return "\n".join(lines) if len(lines) > 1 else ""
    except Exception:
        return ""


def _count_bullets(section: str, prefix: str = "- ") -> int:
    return sum(1 for line in section.splitlines() if line.strip().startswith(prefix))


def _ids_in(text: str) -> list[str]:
    seen: list[str] = []
    for match in RECORD_ID_RE.findall(text):
        lowered = match.lower()
        if lowered not in seen:
            seen.append(lowered)
    return seen


class Injection:
    """Per-turn injection summary: the sections plus the lane counts/ids for marker,
    systemMessage, and journaling. Keeps one source of truth so all three agree."""

    def __init__(self) -> None:
        self.sections: list[str] = []
        self.recall_ids: list[str] = []
        self.recall_match_classes: list[str] = []
        self.recall_abstention_reason = ""
        self.recall_chars = 0
        self.habit_count = 0
        self.habit_ids: list[str] = []
        self.habit_chars = 0
        self.norm_count = 0
        self.norm_ids: list[str] = []
        self.norm_chars = 0

    @property
    def recall_count(self) -> int:
        return len(self.recall_ids)

    @property
    def injected(self) -> bool:
        return bool(self.sections)

    @property
    def injected_ids(self) -> list[str]:
        merged: list[str] = []
        for rid in (*self.recall_ids, *self.habit_ids, *self.norm_ids):
            if rid not in merged:
                merged.append(rid)
        return merged


def _collect_injection(prompt: str) -> Injection:
    inj = Injection()
    # Recall: JSON for precise counts/ids/abstention (A4), markdown for the model text.
    recall_ids, match_classes, reason = _recall_json(prompt)
    inj.recall_abstention_reason = reason
    recall_md = _context_markdown(prompt, "recall").strip()
    if recall_md.startswith(RECALL_HEADING):
        inj.sections.append(recall_md)
        inj.recall_ids = recall_ids or _ids_in(recall_md)
        inj.recall_match_classes = match_classes
        inj.recall_chars = len(recall_md)
    # Habit reminder (markdown is the contract surface).
    habit_md = _context_markdown(prompt, "habit").strip()
    if habit_md.startswith(REMINDER_HEADING):
        inj.sections.append(habit_md)
        inj.habit_ids = [rid for rid in _ids_in(habit_md) if rid.startswith("habit-")]
        inj.habit_count = _count_bullets(habit_md, "- [habit-") or (1 if habit_md else 0)
        inj.habit_chars = len(habit_md)
    # Scoped norms.
    norms_md = _scoped_norms_section(prompt).strip()
    if norms_md.startswith(NORMS_HEADING):
        inj.sections.append(norms_md)
        inj.norm_ids = [rid for rid in _ids_in(norms_md) if rid.startswith("norm-")]
        inj.norm_count = _count_bullets(norms_md, "- [norm-")
        inj.norm_chars = len(norms_md)
    return inj


def _summary_marker(inj: Injection) -> str:
    """B3: enhanced marker with per-lane counts, record ids, and a restate instruction
    so the model surfaces recall to the user (the only Desktop-visible path).
    """
    lines = [
        CODEX_CONTEXT_HEADING,
        "",
        f"（请在你回复的第一行原样告知用户：⭐ SyberMem 本轮参考了 {inj.recall_count} 条项目记忆 · {inj.habit_count} 条习惯 · {inj.norm_count} 条规范）",
        "",
        f"本轮注入摘要：recall={inj.recall_count}, habit={inj.habit_count}, norm={inj.norm_count}",
    ]
    lines.append(f"- [recall] {', '.join(inj.recall_ids) if inj.recall_ids else '（无）'}")
    lines.append(f"- [habit] {', '.join(inj.habit_ids) if inj.habit_ids else '（无）'}")
    lines.append(f"- [norms] {', '.join(inj.norm_ids) if inj.norm_ids else '（无）'}")
    return "\n".join(lines)


def _system_message(inj: Injection) -> str:
    return f"⭐ SyberMem 本轮注入 recall={inj.recall_count} habit={inj.habit_count} norm={inj.norm_count}"


def _hook_output(inj: Injection) -> HookOutput | None:
    if not inj.injected:
        return None
    additional_context = "\n\n".join([_summary_marker(inj), *inj.sections]) + "\n"
    output: HookOutput = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "additionalContext": additional_context,
        }
    }
    if _system_message_enabled():
        output["systemMessage"] = _system_message(inj)
    return output


def _journal(root_str: str, session_id: str, inj: Injection) -> None:
    """A1: write recall-debug + memory-usage rows. Fail-open."""
    if _obs is None:
        return
    try:
        root = Path(root_str)
        _obs.append_recall_debug(
            root,
            injected=inj.recall_count > 0,
            record_ids=inj.recall_ids,
            match_classes=inj.recall_match_classes,
            reason="high-signal-recall" if inj.recall_count > 0 else (inj.recall_abstention_reason or "no-high-signal-recall"),
        )
        _obs.append_memory_usage_turn(
            root,
            session_id=session_id,
            recall_items=inj.recall_count,
            recall_chars=inj.recall_chars,
            habit_items=inj.habit_count,
            habit_chars=inj.habit_chars,
            norm_items=inj.norm_count,
            norm_chars=inj.norm_chars,
            injected_ids=inj.injected_ids,
        )
    except Exception:
        pass


def _resolve_root_str() -> str:
    try:
        _ensure_core_import_path()
        from sybermem_core.project import resolve_project_root

        root = resolve_project_root()
        return str(root) if root is not None else ""
    except Exception:
        return ""


def main() -> int:  # noqa: BROAD_EXCEPT_OK
    try:
        prompt, session_id = _parse_stdin(sys.stdin.read())
        if prompt is None:
            return 0
        try:
            _capture_record_intent(prompt)
        except Exception:
            pass
        inj = _collect_injection(prompt)
        try:
            root_str = _resolve_root_str()
            if root_str:
                _journal(root_str, session_id, inj)
        except Exception:
            pass
        output = _hook_output(inj)
        if output is not None:
            _write_stdout(json.dumps(output, ensure_ascii=False))
    except Exception:
        return 0
    return 0


def _write_stdout(text: str) -> None:
    """Write to stdout as UTF-8 regardless of the console's default encoding.

    The additionalContext marker and systemMessage carry non-ASCII (⭐, CJK). On a
    Windows console defaulting to GBK, sys.stdout.write would raise
    UnicodeEncodeError and the whole hook would silently emit nothing. Reconfigure
    to UTF-8 (fall back to a manual UTF-8 buffer write), so Codex always receives
    valid JSON.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stdout.write(text)
    except Exception:
        try:
            sys.stdout.buffer.write(text.encode("utf-8"))
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
