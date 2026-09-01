from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

# Reuse the launcher fixtures + project helper from the Codex habit hook tests.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_codex_habit_hook import create_sybermem_project, write_routed_launcher  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
USER_PROMPT_HOOK = ROOT / ".codex" / "hooks" / "user_prompt.py"
SESSION_END_HOOK = ROOT / ".codex" / "hooks" / "session_end.py"


def _run_in_project(hook: Path, payload: dict, project: Path, home: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "PATH": f"{home / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    return subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        cwd=project,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env=env,
        timeout=10,
    )


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_record_files_launcher(home: Path, payload: dict) -> None:
    launcher = home / ".claude" / "sybermem" / "cli" / ("sybermem.cmd" if os.name == "nt" else "sybermem")
    launcher.parent.mkdir(parents=True, exist_ok=True)
    script = home / "record_files_launcher.py"
    script.write_text(
        "from __future__ import annotations\n"
        "import json\n"
        "import sys\n"
        f"payload = {payload!r}\n"
        "args = sys.argv[1:]\n"
        "if 'project' in args and 'record-files' in args:\n"
        "    sys.stdout.write(json.dumps(payload))\n",
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


def test_user_prompt_hook_journals_recall_debug_and_memory_usage(tmp_path: Path) -> None:
    # Given: a SyberMem project and a launcher returning high-signal recall
    project = create_sybermem_project(tmp_path)
    write_routed_launcher(
        tmp_path,
        {
            "context recall": "## SyberMem Recall Hints\n\n- STAR change-1: Recall this.",
            "context habit": "",
        },
    )
    payload = {"hookEventName": "UserPromptSubmit", "userPrompt": "architecture work", "session_id": "ses_codex_1"}

    # When: the Codex UserPromptSubmit hook runs inside the project
    result = _run_in_project(USER_PROMPT_HOOK, payload, project, tmp_path)
    assert result.returncode == 0

    # Then: it writes a codex recall-debug inject row and a codex memory-usage turn row
    debug = _read_jsonl(project / ".sybermem" / ".recall-debug.jsonl")
    usage = _read_jsonl(project / ".sybermem" / ".memory-usage.jsonl")
    assert len(debug) == 1
    assert debug[0]["source"] == "codex-user-prompt"
    assert debug[0]["event"] == "inject"
    assert len(usage) == 1
    assert usage[0]["host"] == "codex"
    assert usage[0]["session_id"] == "ses_codex_1"
    assert usage[0]["recall_items"] == 1


def test_user_prompt_hook_journals_abstain_without_memory_usage(tmp_path: Path) -> None:
    # Given: a project where nothing matches (recall/habit/norms all empty)
    project = create_sybermem_project(tmp_path)
    write_routed_launcher(tmp_path, {"context recall": "", "context habit": "", "norms list": ""})
    payload = {"hookEventName": "UserPromptSubmit", "userPrompt": "unrelated", "session_id": "ses_codex_2"}

    # When
    result = _run_in_project(USER_PROMPT_HOOK, payload, project, tmp_path)
    assert result.returncode == 0

    # Then: an abstain row is recorded, but no memory-usage row (mirrors OpenCode:
    # pure-abstain turns must not pollute lane statistics)
    debug = _read_jsonl(project / ".sybermem" / ".recall-debug.jsonl")
    usage = _read_jsonl(project / ".sybermem" / ".memory-usage.jsonl")
    assert len(debug) == 1
    assert debug[0]["event"] == "abstain"
    assert usage == []
    # And stdout stays empty (fail-open, nothing injected)
    assert result.stdout == ""


def test_session_end_hook_writes_outcome_with_precision(tmp_path: Path) -> None:
    # Given: a project where a prior turn injected change-1, change-1 anchors a file
    # that was edited this session (simulated via record-files launcher output).
    project = create_sybermem_project(tmp_path)
    # Seed a codex memory-usage turn row for this session with an injected id.
    usage_path = project / ".sybermem" / ".memory-usage.jsonl"
    usage_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "host": "codex",
                "session_id": "ses_end",
                "timestamp": "2026-09-01T09:00:00+08:00",
                "total_items": 1,
                "total_chars": 10,
                "recall_items": 1,
                "recall_chars": 10,
                "habit_items": 0,
                "habit_chars": 0,
                "norm_items": 0,
                "norm_chars": 0,
                "startup_items": 0,
                "startup_chars": 0,
                "injected_ids": ["change-1"],
                "startup_present": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    # Make change-1 anchor a real file and actually edit it so precision can be 1.0.
    edited = project / "src.py"
    edited.write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=project, capture_output=True, check=False)
    _write_record_files_launcher(tmp_path, {"records": {"change-1": ["src.py"]}})

    payload = {"hookEventName": "SessionEnd", "session_id": "ses_end"}
    result = _run_in_project(SESSION_END_HOOK, payload, project, tmp_path)
    assert result.returncode == 0

    # Then: a session_outcome row and recall-outcomes row are appended with a full hit.
    usage = _read_jsonl(usage_path)
    outcome_rows = [row for row in usage if row.get("event") == "session_outcome"]
    assert len(outcome_rows) == 1
    assert outcome_rows[0]["host"] == "codex"
    assert outcome_rows[0]["session_id"] == "ses_end"
    assert outcome_rows[0]["recall_evidence_available"] is True
    assert outcome_rows[0]["recall_measurable"] == 1
    assert outcome_rows[0]["recall_unmeasurable"] == 0
    assert outcome_rows[0]["recall_hit"] == 1
    outcomes = _read_jsonl(project / ".sybermem" / ".recall-outcomes.jsonl")
    assert outcomes[0]["precision"] == 1.0


def test_session_end_hook_is_noop_without_injected_ids(tmp_path: Path) -> None:
    # Given: a project with no prior codex turns for this session
    project = create_sybermem_project(tmp_path)
    write_routed_launcher(tmp_path, {})
    payload = {"hookEventName": "SessionEnd", "session_id": "ses_none"}

    # When
    result = _run_in_project(SESSION_END_HOOK, payload, project, tmp_path)

    # Then: nothing is written and the hook fails open
    assert result.returncode == 0
    usage = _read_jsonl(project / ".sybermem" / ".memory-usage.jsonl")
    assert usage == []
