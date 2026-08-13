from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Final, TypeAlias, TypedDict


HOOK_EVENT_NAME: Final = "UserPromptSubmit"
REMINDER_HEADING: Final = "## User Habit Reminder"
SYBERMEM_TIMEOUT_SECONDS: Final = 5


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


def _habit_markdown(prompt: str) -> str:
    command = _sybermem_command()
    if command is None:
        return ""
    result = subprocess.run(
        [
            *command,
            "context",
            "habit",
            "--context",
            prompt,
            "--delivery",
            "prompt-time",
            "--format",
            "markdown",
        ],
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
    if not markdown.startswith(REMINDER_HEADING):
        return None
    additional_context = markdown if markdown.endswith("\n") else f"{markdown}\n"
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
        output = _hook_output(_habit_markdown(prompt))
        if output is not None:
            sys.stdout.write(json.dumps(output, ensure_ascii=False))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
