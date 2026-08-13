from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / ".codex" / "hooks" / "user_prompt.py"


def run_hook(payload: str, home: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["PATH"] = str(home / "bin")
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env=env,
        timeout=5,
    )


def write_fixed_launcher(home: Path, markdown: str, exit_code: int = 0) -> Path:
    launcher = home / ".claude" / "sybermem" / "cli" / ("sybermem.cmd" if os.name == "nt" else "sybermem")
    launcher.parent.mkdir(parents=True)
    escaped_markdown = markdown.replace("'", "'\"'\"'")
    if os.name == "nt":
        launcher.write_text(
            "@echo off\r\n"
            f"{sys.executable} -c \"import sys; sys.stdout.write({markdown!r})\"\r\n"
            f"exit /b {exit_code}\r\n",
            encoding="utf-8",
        )
    else:
        launcher.write_text(
            "#!/bin/sh\n"
            f"printf '%s' '{escaped_markdown}'\n"
            f"exit {exit_code}\n",
            encoding="utf-8",
        )
        launcher.chmod(0o700)
    return launcher


def test_codex_user_prompt_hook_emits_additional_context_for_habit_reminder(tmp_path: Path) -> None:
    # Given: the fixed user-level launcher returns a Codex-eligible habit reminder
    reminder = "## User Habit Reminder\n\n- Apply the saved workflow habit."
    write_fixed_launcher(tmp_path, reminder)
    payload = json.dumps({"hookEventName": "UserPromptSubmit", "userPrompt": "planning task"})

    # When: Codex invokes the hook with prompt JSON on stdin
    result = run_hook(payload, tmp_path)

    # Then: stdout contains only the UserPromptSubmit additionalContext packet
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output == {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "## User Habit Reminder\n\n- Apply the saved workflow habit.\n",
        }
    }
    assert result.stderr == ""


def test_codex_user_prompt_hook_accepts_prompt_key(tmp_path: Path) -> None:
    # Given: Codex stdin uses the alternate prompt field name
    reminder = "## User Habit Reminder\n\n- Use the prompt field."
    write_fixed_launcher(tmp_path, reminder)
    payload = json.dumps({"prompt": "review handoff"})

    # When: the hook runs
    result = run_hook(payload, tmp_path)

    # Then: the prompt value is accepted and reminder context is emitted
    assert result.returncode == 0
    assert json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"].startswith("## User Habit Reminder")


def test_codex_user_prompt_hook_outputs_nothing_for_empty_cli_markdown(tmp_path: Path) -> None:
    # Given: the habit CLI finds no matching reminder
    write_fixed_launcher(tmp_path, "")
    payload = json.dumps({"userPrompt": "unrelated task"})

    # When: the hook runs
    result = run_hook(payload, tmp_path)

    # Then: it fails open without adding context
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_codex_user_prompt_hook_outputs_nothing_when_cli_fails(tmp_path: Path) -> None:
    # Given: the fixed launcher exists but fails
    write_fixed_launcher(tmp_path, "## User Habit Reminder\n\n- Hidden failure.", exit_code=7)
    payload = json.dumps({"userPrompt": "planning task"})

    # When: the hook runs
    result = run_hook(payload, tmp_path)

    # Then: it fails open without surfacing partial CLI output
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
