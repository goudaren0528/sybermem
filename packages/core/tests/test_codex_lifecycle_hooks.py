from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
SESSION_HOOK = ROOT / ".codex" / "hooks" / "session_start.py"
STOP_HOOK = ROOT / ".codex" / "hooks" / "stop.py"
POST_COMPACT_HOOK = ROOT / ".codex" / "hooks" / "post_compact.py"


def run_codex_hook(script: Path, payload: str, home: Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["PATH"] = f"{home / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    return subprocess.run(
        [sys.executable, str(script)],
        input=payload,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env=env,
        timeout=5,
    )


def write_routed_launcher(home: Path, outputs: dict[str, str], exit_code: int = 0) -> Path:
    launcher = home / ".claude" / "sybermem" / "cli" / ("sybermem.cmd" if os.name == "nt" else "sybermem")
    launcher.parent.mkdir(parents=True)
    script = home / "launcher.py"
    script.write_text(
        "from __future__ import annotations\n"
        "import sys\n"
        f"outputs = {outputs!r}\n"
        "args = sys.argv[1:]\n"
        "key = 'context session' if 'context' in args and 'session' in args else ''\n"
        "sys.stdout.write(outputs.get(key, ''))\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    if os.name == "nt":
        launcher.write_text("@echo off\r\n" f'"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
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


def init_git_project(project: Path) -> None:
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project, check=True, capture_output=True)
    (project / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=project, check=True, capture_output=True)


def test_codex_stop_hook_outputs_nothing_when_already_active(tmp_path: Path) -> None:
    project = create_sybermem_project(tmp_path)
    payload = json.dumps({"hookEventName": "Stop", "stop_hook_active": True})

    result = run_codex_hook(STOP_HOOK, payload, tmp_path, project)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_codex_stop_hook_blocks_once_for_record_worthy_change(tmp_path: Path) -> None:
    project = create_sybermem_project(tmp_path)
    init_git_project(project)
    (project / "INSTALL.md").write_text("new install notes\n", encoding="utf-8")
    payload = json.dumps({"hookEventName": "Stop", "stop_hook_active": False})

    first = run_codex_hook(STOP_HOOK, payload, tmp_path, project)

    assert first.returncode == 0
    output = json.loads(first.stdout)
    assert output["decision"] == "block"
    assert "/sybermem-record" in output["reason"]
    assert "INSTALL.md" not in output["reason"]

    second = run_codex_hook(STOP_HOOK, payload, tmp_path, project)
    assert second.returncode == 0
    assert second.stdout == ""
    assert second.stderr == ""


def test_codex_post_compact_marks_reseed_without_emitting_context(tmp_path: Path) -> None:
    project = create_sybermem_project(tmp_path)
    payload = json.dumps({"hookEventName": "PostCompact", "trigger": "auto"})

    result = run_codex_hook(POST_COMPACT_HOOK, payload, tmp_path, project)

    assert result.returncode == 0
    assert result.stdout == ""
    marker = json.loads((project / ".sybermem" / ".codex-compact-marker.json").read_text(encoding="utf-8"))
    assert marker["hook_event_name"] == "PostCompact"
    assert marker["trigger"] == "auto"


def test_codex_session_start_compact_source_reseeds_after_marker(tmp_path: Path) -> None:
    project = create_sybermem_project(tmp_path)
    (project / ".sybermem" / ".codex-compact-marker.json").write_text(
        json.dumps({"hook_event_name": "PostCompact", "trigger": "auto"}) + "\n",
        encoding="utf-8",
    )
    session_context = "## SyberMem Manual Session Context\n\n- Re-seed after compact."
    write_routed_launcher(tmp_path, {"context session": session_context})
    payload = json.dumps({"hookEventName": "SessionStart", "source": "compact"})

    result = run_codex_hook(SESSION_HOOK, payload, tmp_path, project)

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert output["hookSpecificOutput"]["additionalContext"] == f"{session_context}\n"
    assert not (project / ".sybermem" / ".codex-compact-marker.json").exists()


def test_codex_session_start_compact_source_requires_marker(tmp_path: Path) -> None:
    project = create_sybermem_project(tmp_path)
    session_context = "## SyberMem Manual Session Context\n\n- No marker."
    write_routed_launcher(tmp_path, {"context session": session_context})
    payload = json.dumps({"hookEventName": "SessionStart", "source": "compact"})

    result = run_codex_hook(SESSION_HOOK, payload, tmp_path, project)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
