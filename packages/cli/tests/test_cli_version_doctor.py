from __future__ import annotations

import json
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
