from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Final, TypeAlias, TypedDict
from datetime import datetime, timezone


HOOK_EVENT_NAME: Final = "UserPromptSubmit"
CODEX_CONTEXT_HEADING: Final = "## SyberMem Codex Context"
RECALL_HEADING: Final = "## SyberMem Recall Hints"
REMINDER_HEADING: Final = "## User Habit Reminder"
NORMS_HEADING: Final = "## Relevant Project Norms"
SYBERMEM_TIMEOUT_SECONDS: Final = 5
RECORD_INTENT_PATH: Final = ".sybermem/.record-intent.json"


class HookInput(TypedDict, total=False):
    prompt: str
    userPrompt: str


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


def _prompt_from_stdin(stdin_text: str) -> str | None:
    data: JsonValue = json.loads(stdin_text)
    if not isinstance(data, dict):
        return None
    prompt = _string_field(data, "userPrompt") or _string_field(data, "prompt")
    if prompt:
        return prompt
    return None


def _string_field(data: dict[str, JsonValue], key: str) -> str | None:
    value = data.get(key)
    if isinstance(value, str):
        return value
    return None


def _context_markdown(prompt: str, kind: str) -> str:
    command = _sybermem_command()
    if command is None:
        return ""
    if kind == "recall":
        args = [
            *command,
            "context",
            "recall",
            "--query",
            prompt,
            "--format",
            "markdown",
        ]
    else:
        args = [
            *command,
            "context",
            "habit",
            "--context",
            prompt,
            "--delivery",
            "prompt-time",
            "--format",
            "markdown",
        ]
    result = subprocess.run(
        args,
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


def _context_sections(prompt: str) -> list[str]:
    sections: list[str] = []
    for kind, heading in (("recall", RECALL_HEADING), ("habit", REMINDER_HEADING)):
        markdown = _context_markdown(prompt, kind).strip()
        if markdown.startswith(heading):
            sections.append(markdown)
    norms = _scoped_norms_section(prompt)
    if norms:
        sections.append(norms)
    return sections


def _summary_marker(sections: list[str]) -> str:
    lines = [CODEX_CONTEXT_HEADING, "", "SyberMem injected context for this Codex turn:"]
    for section in sections:
        if section.startswith(RECALL_HEADING):
            lines.append("- [recall] Project recall")
        elif section.startswith(REMINDER_HEADING):
            lines.append("- [habit] User habit reminder")
        elif section.startswith(NORMS_HEADING):
            lines.append("- [norms] Relevant project norms")
    return "\n".join(lines)


def _hook_output(sections: list[str]) -> HookOutput | None:
    if not sections:
        return None
    additional_context = "\n\n".join([_summary_marker(sections), *sections]) + "\n"
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "additionalContext": additional_context,
        }
    }


def main() -> int:  # noqa: BROAD_EXCEPT_OK
    try:
        prompt = _prompt_from_stdin(sys.stdin.read())
        if prompt is None:
            return 0
        try:
            _capture_record_intent(prompt)
        except Exception:
            pass
        output = _hook_output(_context_sections(prompt))
        if output is not None:
            sys.stdout.write(json.dumps(output, ensure_ascii=False))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
