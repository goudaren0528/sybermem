from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / ".codex" / "hooks" / "user_prompt.py"
SESSION_HOOK = ROOT / ".codex" / "hooks" / "session_start.py"
STOP_HOOK = ROOT / ".codex" / "hooks" / "stop.py"
POST_COMPACT_HOOK = ROOT / ".codex" / "hooks" / "post_compact.py"


def run_hook(payload: str, home: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["PATH"] = f"{home / 'bin'}{os.pathsep}{env.get('PATH', '')}"
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


def run_session_hook(payload: str, home: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["PATH"] = f"{home / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    return subprocess.run(
        [sys.executable, str(SESSION_HOOK)],
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


def write_routed_launcher(home: Path, outputs: dict[str, str], exit_code: int = 0) -> Path:
    launcher = home / ".claude" / "sybermem" / "cli" / ("sybermem.cmd" if os.name == "nt" else "sybermem")
    launcher.parent.mkdir(parents=True)
    script = home / "launcher.py"
    script.write_text(
        "from __future__ import annotations\n"
        "import json\n"
        "import sys\n"
        f"outputs = {outputs!r}\n"
        "args = sys.argv[1:]\n"
        "key = ''\n"
        "if 'context' in args and 'session' in args:\n"
        "    key = 'context session'\n"
        "elif 'context' in args and 'recall' in args:\n"
        "    key = 'context recall'\n"
        "elif 'context' in args and 'habit' in args:\n"
        "    key = 'context habit'\n"
        "sys.stdout.write(outputs.get(key, ''))\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    if os.name == "nt":
        launcher.write_text(
            "@echo off\r\n"
            f'"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
    else:
        launcher.write_text(f"#!/bin/sh\nexec {sys.executable!r} {str(script)!r} \"$@\"\n", encoding="utf-8")
        launcher.chmod(0o700)
    return launcher


def create_sybermem_project(root: Path) -> Path:
    project = root / "project"
    (project / ".sybermem").mkdir(parents=True)
    (project / ".claude").mkdir()
    (project / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (project / ".sybermem" / "project.yaml").write_text("project_id: test\nslug: test\n", encoding="utf-8")
    return project


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


def test_codex_session_start_hook_emits_additional_context(tmp_path: Path) -> None:
    # Given: the fixed launcher returns session context for Codex startup
    session_context = "## SyberMem Manual Session Context\n\n- Project is ready."
    write_routed_launcher(tmp_path, {"context session": session_context})
    payload = json.dumps({"hookEventName": "SessionStart", "source": "startup"})

    # When: Codex invokes the SessionStart hook
    result = run_session_hook(payload, tmp_path)

    # Then: stdout contains a SessionStart additionalContext packet
    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "## SyberMem Manual Session Context\n\n- Project is ready.\n",
        }
    }
    assert result.stderr == ""


def test_codex_user_prompt_hook_combines_recall_and_habit(tmp_path: Path) -> None:
    # Given: recall and habit context both match the same prompt
    recall = "## SyberMem Recall Hints\n\n- STAR change-1: Recall this architecture."
    habit = "## User Habit Reminder\n\n- Apply the saved workflow habit."
    write_routed_launcher(tmp_path, {"context recall": recall, "context habit": habit})
    payload = json.dumps({"hookEventName": "UserPromptSubmit", "userPrompt": "planning task"})

    # When: Codex invokes the user prompt hook
    result = run_hook(payload, tmp_path)

    # Then: both sections are composed into one additionalContext packet
    assert result.returncode == 0
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert context == (
        "## SyberMem Recall Hints\n\n- STAR change-1: Recall this architecture.\n\n"
        "## User Habit Reminder\n\n- Apply the saved workflow habit.\n"
    )
    assert result.stderr == ""


def test_codex_user_prompt_hook_emits_recall_without_habit(tmp_path: Path) -> None:
    # Given: only project recall has high-signal results
    recall = "## SyberMem Recall Hints\n\n- HINT decision-1: Use the current approach."
    write_routed_launcher(tmp_path, {"context recall": recall, "context habit": ""})
    payload = json.dumps({"hookEventName": "UserPromptSubmit", "userPrompt": "architecture"})

    # When: the hook runs
    result = run_hook(payload, tmp_path)

    # Then: recall context still reaches Codex without requiring a habit reminder
    assert result.returncode == 0
    assert json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] == f"{recall}\n"
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


def test_codex_session_start_hook_outputs_nothing_when_cli_fails(tmp_path: Path) -> None:
    # Given: the fixed launcher exists but cannot produce startup context
    write_fixed_launcher(tmp_path, "## SyberMem Manual Session Context\n\n- Hidden failure.", exit_code=7)
    payload = json.dumps({"hookEventName": "SessionStart"})

    # When: the SessionStart hook runs
    result = run_session_hook(payload, tmp_path)

    # Then: it fails open without surfacing partial output
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_codex_user_prompt_hook_captures_bounded_record_intent(tmp_path: Path) -> None:
    # Given: Codex runs from a SyberMem project and the prompt asks to record a change
    project = create_sybermem_project(tmp_path)
    write_routed_launcher(tmp_path, {"context recall": "", "context habit": ""})
    payload = json.dumps({"hookEventName": "UserPromptSubmit", "userPrompt": "Record this change about Codex recall parity"})

    # When: the hook runs in the project directory
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        cwd=project,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path), "PATH": f"{tmp_path / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"},
        timeout=5,
    )

    # Then: it writes only bounded classifier metadata, not the raw prompt
    intent_path = project / ".sybermem" / ".record-intent.json"
    assert result.returncode == 0
    assert result.stdout == ""
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    assert intent["record_intent"] is True
    assert intent["classification"] == "change"
    assert intent["action"] == "/sybermem-record"
    assert intent["source"] == "codex-user-prompt-submit"
    assert intent["matched_pattern"] == "change"
    assert intent["phrase"] == ""
    assert "Codex recall parity" not in json.dumps(intent, ensure_ascii=False)


def test_codex_user_prompt_hook_does_not_capture_blocked_record_intent(tmp_path: Path) -> None:
    # Given: a prompt contains secret-like text and must not become durable metadata
    project = create_sybermem_project(tmp_path)
    write_routed_launcher(tmp_path, {"context recall": "", "context habit": ""})
    payload = json.dumps({"hookEventName": "UserPromptSubmit", "userPrompt": "Record this token=abc123secret"})

    # When: the hook runs in the project directory
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        cwd=project,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path), "PATH": f"{tmp_path / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"},
        timeout=5,
    )

    # Then: it fails open and does not write a record-intent file
    assert result.returncode == 0
    assert result.stdout == ""
    assert not (project / ".sybermem" / ".record-intent.json").exists()
