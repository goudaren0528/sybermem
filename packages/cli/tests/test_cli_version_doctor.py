from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli import main as main_module


def test_cli_version_prints_installed_version(monkeypatch, capsys) -> None:
    monkeypatch.setattr(main_module, "get_installed_version", lambda: "9.9.9")
    monkeypatch.setattr(sys, "argv", ["sybermem", "version"])

    exit_code = main_module.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "9.9.9"
    assert captured.err == ""


def test_cli_version_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(main_module, "get_installed_version", lambda: "9.9.9")
    monkeypatch.setattr(sys, "argv", ["sybermem", "version", "--format", "json"])

    exit_code = main_module.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {"installed": "9.9.9"}


def test_cli_doctor_json_flags_outdated_project(tmp_path: Path, monkeypatch, capsys) -> None:
    project_root = tmp_path / "project"
    (project_root / ".sybermem").mkdir(parents=True)
    (project_root / ".sybermem" / "project.yaml").write_text(
        "schema_version: 1\nslug: demo\nsybermem_version: 0.0.1\n", encoding="utf-8"
    )
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr("sybermem_core.doctor.get_installed_version", lambda: "1.0.0")
    monkeypatch.setattr(sys, "argv", ["sybermem", "doctor", "--format", "json"])

    exit_code = main_module.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["installed"] == "1.0.0"
    assert payload["project"] == "0.0.1"
    assert payload["outdated"] is True
    assert payload["recommendation"] == "/sybermem-update"


def test_cli_doctor_text_current_project(tmp_path: Path, monkeypatch, capsys) -> None:
    project_root = tmp_path / "project"
    (project_root / ".sybermem").mkdir(parents=True)
    (project_root / ".sybermem" / "project.yaml").write_text(
        "schema_version: 1\nslug: demo\nsybermem_version: 1.0.0\n", encoding="utf-8"
    )
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr("sybermem_core.doctor.get_installed_version", lambda: "1.0.0")
    monkeypatch.setattr(sys, "argv", ["sybermem", "doctor"])

    exit_code = main_module.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "current with the installed SyberMem" in captured.out
    assert captured.err == ""


def test_doctor_runtime_json_keeps_default_contract_and_ignores_old_logs(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    memory = project / ".sybermem"
    memory.mkdir(parents=True)
    (memory / "project.yaml").write_text("schema_version: 1\nslug: demo\nsybermem_version: 0.0.1\n", encoding="utf-8")
    (memory / ".memory-usage.jsonl").write_text('{"session":"past","timestamp":"2099-01-01T00:00:00Z","event":"inject"}\n', encoding="utf-8")
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in memory.iterdir()}
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project)
    monkeypatch.setattr("sybermem_core.doctor.get_installed_version", lambda: "1.0.0")
    monkeypatch.setattr(sys, "argv", ["sybermem", "doctor", "--format", "json"])
    assert main_module.main() == 0
    baseline = json.loads(capsys.readouterr().out)
    assert baseline == {"installed": "1.0.0", "project": "0.0.1", "outdated": True, "recommendation": "/sybermem-update"}
    monkeypatch.setattr(sys, "argv", ["sybermem", "doctor", "--runtime", "--format", "json"])
    assert main_module.main() == 0
    payload = json.loads(capsys.readouterr().out)
    runtime = payload.pop("runtime")
    assert payload == baseline
    assert runtime["installation"]["status"] == "available"
    assert runtime["installation"]["version"] == "1.0.0"
    assert "package metadata or bundled fallback" in runtime["installation"]["evidence"]
    assert runtime["project_stamp"]["status"] == "stamped"
    assert runtime["project_stamp"]["outdated"] is True
    assert runtime["host_loaded"]["status"] == "unknown"
    assert runtime["current_turn_delivery"]["status"] == "unknown"
    assert "No live" in runtime["host_loaded"]["reason"]
    assert "No live" in runtime["current_turn_delivery"]["reason"]
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in memory.iterdir()} == before


def test_doctor_runtime_no_project_and_text(monkeypatch, capsys):
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: None)
    monkeypatch.setattr("sybermem_core.doctor.get_installed_version", lambda: "1.0.0")
    monkeypatch.setattr(sys, "argv", ["sybermem", "doctor", "--runtime", "--format", "json"])
    assert main_module.main() == 0
    data = json.loads(capsys.readouterr().out)
    assert data["runtime"]["project_stamp"]["status"] == "not_found"
    assert data["runtime"]["host_loaded"]["status"] == "unknown"
    monkeypatch.setattr(sys, "argv", ["sybermem", "doctor", "--runtime"])
    assert main_module.main() == 0
    text = capsys.readouterr().out
    assert "CLI/core available: available" in text
    assert "Project stamp: not_found" in text
    assert "Current host loaded: unknown" in text
    assert "Current turn context delivery: unknown" in text
    assert "Next check:" in text


def test_doctor_rejects_unapproved_identity_flags(monkeypatch, capsys):
    import pytest
    for flag in ("--host", "--session", "--turn"):
        monkeypatch.setattr(sys, "argv", ["sybermem", "doctor", "--runtime", flag, "synthetic"])
        with pytest.raises(SystemExit) as exc:
            main_module.main()
        assert exc.value.code == 2
        capsys.readouterr()
