from __future__ import annotations

import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.project_index import DuplicateRecordIdError
from sybermem_cli import main as main_module


def test_cli_project_index_build_json_reports_updated_path(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a SyberMem project root and a derived INDEX write that changes the file
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "write_project_index", lambda root: True)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "index", "build", "--format", "json"])

    # When: the new CLI command is invoked through the parser boundary
    exit_code = main_module.main()

    # Then: it succeeds and reports the updated project INDEX path
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload == {
        "status": "updated",
        "path": str(project_root / ".sybermem" / "INDEX.md").replace("\\", "/"),
    }


def test_cli_project_index_build_text_reports_unchanged_path(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a SyberMem project root whose derived INDEX is already current
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "write_project_index", lambda root: False)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "index", "build"])

    # When: the text CLI path is used
    exit_code = main_module.main()

    # Then: it succeeds and tells the caller nothing changed
    captured = capsys.readouterr()
    index_path = str(project_root / ".sybermem" / "INDEX.md").replace("\\", "/")
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == f"unchanged: {index_path}\n"


def test_cli_project_index_check_returns_1_when_stale(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a SyberMem project root whose checked INDEX is stale
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".sybermem").mkdir()
    (project_root / ".sybermem" / "INDEX.md").write_text("# stale\n", encoding="utf-8")
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "check_project_index", lambda root: False)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "index", "check", "--format", "json"])

    # When: the check command runs through the CLI boundary
    exit_code = main_module.main()

    # Then: it reports stale JSON and exits nonzero
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload == {
        "status": "stale",
        "path": str(project_root / ".sybermem" / "INDEX.md").replace("\\", "/"),
    }


def test_cli_project_index_check_returns_0_when_current(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a SyberMem project root whose derived INDEX is current
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "check_project_index", lambda root: True)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "index", "check", "--format", "json"])

    # When: the check command runs through the CLI boundary
    exit_code = main_module.main()

    # Then: it reports current JSON and exits successfully
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload == {
        "status": "current",
        "path": str(project_root / ".sybermem" / "INDEX.md").replace("\\", "/"),
    }


def test_cli_project_index_build_returns_1_without_project_root(monkeypatch, capsys) -> None:
    # Given: the command is invoked outside any SyberMem project
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: None)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "index", "build"])

    # When: the parser dispatches the build command
    exit_code = main_module.main()

    # Then: it fails with the standard concise root-not-found message
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "No SyberMem project root found.\n"


def test_cli_project_index_build_returns_clean_error_for_duplicate_record_id(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: project INDEX generation detects duplicate canonical record metadata
    project_root = tmp_path / "project"
    project_root.mkdir()
    first = project_root / ".sybermem" / "changes" / "first.md"
    second = project_root / ".sybermem" / "changes" / "second.md"
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)

    def fail_write(root: Path) -> bool:
        raise DuplicateRecordIdError(record_id="change-001", paths=(first, second))

    monkeypatch.setattr(main_module, "write_project_index", fail_write)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "index", "build"])

    # When: the build command runs through the CLI boundary
    exit_code = main_module.main()

    # Then: the error is reported concisely without a traceback
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "duplicate SyberMem record_id 'change-001'" in captured.err
    assert "Traceback" not in captured.err


def test_cli_project_index_check_returns_clean_error_for_duplicate_record_id(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: project INDEX check detects duplicate canonical record metadata
    project_root = tmp_path / "project"
    project_root.mkdir()
    first = project_root / ".sybermem" / "changes" / "first.md"
    second = project_root / ".sybermem" / "changes" / "second.md"
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)

    def fail_check(root: Path) -> bool:
        raise DuplicateRecordIdError(record_id="change-001", paths=(first, second))

    monkeypatch.setattr(main_module, "check_project_index", fail_check)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "index", "check"])

    # When: the check command runs through the CLI boundary
    exit_code = main_module.main()

    # Then: the error is reported concisely without a traceback
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "duplicate SyberMem record_id 'change-001'" in captured.err
    assert "Traceback" not in captured.err


def test_cli_top_level_index_build_still_uses_workspace_index(monkeypatch, capsys) -> None:
    # Given: the existing top-level workspace index build command
    called: dict[str, str | None] = {}

    def fake_rebuild_index(project: str | None) -> dict[str, int]:
        called["project"] = project
        return {"projects": 2, "records": 5}

    monkeypatch.setattr(main_module, "rebuild_index", fake_rebuild_index)
    monkeypatch.setattr(sys, "argv", ["sybermem", "index", "build", "--project", "demo", "--format", "json"])

    # When: the pre-existing workspace CLI command runs
    exit_code = main_module.main()

    # Then: it still dispatches to the workspace SQLite index builder unchanged
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert called == {"project": "demo"}
    assert payload == {"projects": 2, "records": 5}
