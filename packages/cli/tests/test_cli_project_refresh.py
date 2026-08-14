from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli import main as main_module


def test_cli_project_refresh_json_calls_core_and_emits_json_only(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a SyberMem project root and a Core refresh payload
    project_root = tmp_path / "project"
    project_root.mkdir()
    payload = {
        "root": str(project_root).replace("\\", "/"),
        "overall": "updated",
        "files": {"AGENTS.md": {"status": "updated"}},
        "actions_needed": ["replace protocol block in AGENTS.md (preserve content outside block)"],
        "actions_applied": ["replace protocol block in AGENTS.md (preserve content outside block)"],
        "actions_skipped": [],
        "preserved_custom": ["AGENTS.md"],
    }
    called: dict[str, Path] = {}

    def fake_refresh(root: Path) -> dict[str, object]:
        called["root"] = root
        return payload

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "refresh_project", fake_refresh)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--format", "json"])

    # When: the refresh command is invoked through the parser boundary
    exit_code = main_module.main()

    # Then: it calls Core with the resolved root and writes only JSON to stdout
    captured = capsys.readouterr()
    assert exit_code == 0
    assert called == {"root": project_root}
    assert json.loads(captured.out) == payload
    assert captured.err == ""


def test_cli_project_refresh_text_prints_concise_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: Core reports one applied action and one preserved custom file
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(
        main_module,
        "refresh_project",
        lambda root: {
            "root": str(root).replace("\\", "/"),
            "overall": "updated",
            "files": {"AGENTS.md": {"status": "updated"}},
            "actions_needed": ["replace protocol block in AGENTS.md (preserve content outside block)"],
            "actions_applied": ["replace protocol block in AGENTS.md (preserve content outside block)"],
            "actions_skipped": [],
            "preserved_custom": ["AGENTS.md"],
        },
    )
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh"])

    # When: text mode is used
    exit_code = main_module.main()

    # Then: the summary is concise and human-readable
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == "updated: applied 1 action(s), skipped 0, preserved custom 1\n"


def test_cli_project_refresh_returns_1_without_project_root(monkeypatch, capsys) -> None:
    # Given: the command is invoked outside any SyberMem project
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: None)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh"])

    # When: the parser dispatches the refresh command
    exit_code = main_module.main()

    # Then: it fails with a concise stderr message
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "No SyberMem project root found.\n"


def test_cli_project_refresh_returns_clean_error_for_refresh_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: Core refresh rejects a project-local managed path
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)

    def fail_refresh(root: Path) -> dict[str, object]:
        raise ValueError("managed path is a symlink: AGENTS.md")

    monkeypatch.setattr(main_module, "refresh_project", fail_refresh)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh"])

    # When: the parser dispatches the refresh command
    exit_code = main_module.main()

    # Then: the CLI reports a concise error without a traceback
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "managed path is a symlink: AGENTS.md\n"
    assert "Traceback" not in captured.err
