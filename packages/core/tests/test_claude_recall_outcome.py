from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / "packages" / "claude-skills" / "sybermem-init-project" / "project-files" / ".sybermem" / "hooks" / "recall_outcome_on_stop.py"
WRAPPER = ROOT / "skills" / "sybermem-init-project" / "project-files" / ".sybermem" / "hooks" / "recall_outcome_on_stop.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("claude_recall_outcome", HOOK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / ".sybermem").mkdir(parents=True)
    (project / ".claude").mkdir()
    (project / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=project, capture_output=True, check=True)
    return project


def _launcher(home: Path, records: dict[str, list[str]]) -> None:
    launcher = home / ".claude" / "sybermem" / "cli" / ("sybermem.cmd" if os.name == "nt" else "sybermem")
    launcher.parent.mkdir(parents=True)
    script = home / "record_files.py"
    script.write_text(
        "import json, sys\n"
        f"records = {records!r}\n"
        "if sys.argv[1:3] == ['project', 'record-files']:\n"
        "    print(json.dumps({'records': records}))\n",
        encoding="utf-8",
    )
    if os.name == "nt":
        launcher.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    else:
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)


def _run(project: Path, home: Path, session_id: str = "claude-session") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"hookEventName": "Stop", "session_id": session_id}),
        cwd=project,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(home), "USERPROFILE": str(home)},
        timeout=10,
    )


def _write_usage(project: Path, rows: list[object]) -> Path:
    path = project / ".sybermem" / ".memory-usage.jsonl"
    path.write_text("\n".join(json.dumps(row) if not isinstance(row, str) else row for row in rows) + "\n", encoding="utf-8")
    return path


def test_claude_collector_writes_core_schema_for_hit_and_unmeasurable(tmp_path: Path) -> None:
    project = _project(tmp_path)
    home = tmp_path / "home"
    _launcher(home, {"change-1": ["src.py"]})
    (project / "src.py").write_text("print('edited')\n", encoding="utf-8")
    usage_path = _write_usage(project, [{"host": "claude", "session_id": "claude-session", "injected_ids": ["change-1", "missing-anchor"]}])

    result = _run(project, home)

    assert result.returncode == 0
    outcomes = _read_jsonl(project / ".sybermem" / ".recall-outcomes.jsonl")
    assert len(outcomes) == 1
    outcome = outcomes[0]
    # Exact field contract consumed by memory_stats._recall_outcome_entries.
    assert set(outcome) == {"timestamp", "session", "injected", "measurable", "unmeasurable", "hit", "precision"}
    assert outcome["timestamp"]
    assert outcome["session"] == "claude-session"
    assert outcome["injected"] == 1
    assert outcome["measurable"] == 1
    assert outcome["unmeasurable"] == 1
    assert outcome["hit"] == 1
    assert outcome["precision"] == 1.0

    usage = _read_jsonl(usage_path)
    session_outcomes = [row for row in usage if row.get("event") == "session_outcome"]
    assert len(session_outcomes) == 1
    assert session_outcomes[0]["host"] == "claude"


def test_claude_collector_fails_open_on_garbage_usage_and_no_ids(tmp_path: Path) -> None:
    project = _project(tmp_path)
    home = tmp_path / "home"
    _launcher(home, {})
    usage_path = project / ".sybermem" / ".memory-usage.jsonl"
    garbage = "not json\n[]\n"
    usage_path.write_text(garbage, encoding="utf-8")

    result = _run(project, home)

    assert result.returncode == 0
    assert not (project / ".sybermem" / ".recall-outcomes.jsonl").exists()
    assert usage_path.read_text(encoding="utf-8") == garbage  # no bogus outcome row


def test_claude_collector_writes_no_outcome_without_injected_ids(tmp_path: Path) -> None:
    project = _project(tmp_path)
    home = tmp_path / "home"
    _launcher(home, {})
    _write_usage(project, [{"host": "claude", "session_id": "claude-session", "injected_ids": []}])

    result = _run(project, home)

    assert result.returncode == 0
    assert not (project / ".sybermem" / ".recall-outcomes.jsonl").exists()
    assert not any(row.get("event") == "session_outcome" for row in _read_jsonl(project / ".sybermem" / ".memory-usage.jsonl"))


def test_skills_wrapper_resolves_packages_implementation() -> None:
    # hooks -> .sybermem -> project-files -> skill -> skills -> repository root.
    repo_root = WRAPPER.resolve().parents[5]
    target = repo_root / "packages" / "claude-skills" / "sybermem-init-project" / "project-files" / ".sybermem" / "hooks" / "recall_outcome_on_stop.py"
    assert repo_root == ROOT
    assert target == HOOK
    assert target.is_file()
