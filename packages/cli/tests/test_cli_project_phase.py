from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli import main as main_module
from sybermem_core.phase_index import PhaseApplyError


def test_cli_phase_analyze_json_calls_core_and_emits_json_only(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a project root and a Core analyze payload
    project_root = tmp_path / "project"
    project_root.mkdir()
    payload = {"status": "analyzed", "phases": [{"phase_id": "phase-001", "title": "x", "covered_records": ["change-001"]}]}
    called: dict[str, Path] = {}

    def fake_analyze(root: Path) -> dict:
        called["root"] = root
        return payload

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "analyze_phases", fake_analyze)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "phase", "analyze", "--format", "json"])

    # When
    exit_code = main_module.main()

    # Then
    captured = capsys.readouterr()
    assert exit_code == 0
    assert called == {"root": project_root}
    assert json.loads(captured.out) == payload
    assert captured.err == ""


def test_cli_phase_analyze_text_prints_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: Core reports two confirmed phases
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(
        main_module,
        "analyze_phases",
        lambda root: {"status": "analyzed", "phases": [{"phase_id": "phase-001", "title": "a", "covered_records": ["change-001"]}, {"phase_id": "phase-002", "title": "b", "covered_records": ["bug-001", "bug-002"]}]},
    )
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "phase", "analyze"])

    # When
    exit_code = main_module.main()

    # Then
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "analyzed: 2 phase(s)" in captured.out


def test_cli_phase_analyze_returns_1_without_project_root(monkeypatch, capsys) -> None:
    # Given: no project root
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: None)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "phase", "analyze"])

    # When
    exit_code = main_module.main()

    # Then
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "No SyberMem project root found.\n"


def test_cli_phase_analyze_with_from_json_persists_semantic_payload(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a payload file and a Core apply result
    project_root = tmp_path / "project"
    project_root.mkdir()
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps({"phases": [{"title": "Auth", "covered_records": ["change-001"]}]}), encoding="utf-8")
    seen: dict[str, object] = {}

    def fake_apply(root: Path, payload: dict) -> dict:
        seen["root"] = root
        seen["payload"] = payload
        return {"status": "analyzed", "phases": [{"phase_id": "phase-001", "title": "Auth", "covered_records": ["change-001"]}]}

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "apply_phase_payload", fake_apply)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "phase", "analyze", "--from-json", str(payload_file), "--format", "json"])

    # When
    exit_code = main_module.main()

    # Then
    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen["root"] == project_root
    assert seen["payload"] == {"phases": [{"title": "Auth", "covered_records": ["change-001"]}]}
    assert json.loads(captured.out)["phases"][0]["title"] == "Auth"


def test_cli_phase_analyze_with_from_json_non_dict_exits_cleanly(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: valid JSON that is not an object (a list) — must not leak a traceback
    project_root = tmp_path / "project"
    (project_root / ".sybermem" / "analysis").mkdir(parents=True)
    (project_root / ".sybermem" / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    payload_file = tmp_path / "payload.json"
    payload_file.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "phase", "analyze", "--from-json", str(payload_file)])

    # When: the real Core path runs (not mocked)
    exit_code = main_module.main()

    # Then: clean exit 1, message on stderr, no traceback
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "phases" in captured.err
    assert "Traceback" not in captured.err


def test_cli_phase_analyze_with_from_json_reports_clean_error_for_bad_payload(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: Core rejects the payload
    project_root = tmp_path / "project"
    project_root.mkdir()
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps({"phases": [{"title": "Bad", "covered_records": ["change-999"]}]}), encoding="utf-8")

    def fail_apply(root: Path, payload: dict) -> dict:
        raise PhaseApplyError("unknown record id in phase 'Bad': change-999")

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "apply_phase_payload", fail_apply)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "phase", "analyze", "--from-json", str(payload_file)])

    # When
    exit_code = main_module.main()

    # Then
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "change-999" in captured.err
    assert "Traceback" not in captured.err
