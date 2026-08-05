from argparse import Namespace
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli.main import cmd_resume


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def test_cli_resume_json_returns_checkpoint(tmp_path: Path, monkeypatch, capsys) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    monkeypatch.chdir(project_root)

    exit_code = cmd_resume(Namespace(mode="fast", format="json"))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert '"mode"' in out
    assert '"fast"' in out


def test_cli_resume_all_modes_succeed(tmp_path: Path, monkeypatch, capsys) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    monkeypatch.chdir(project_root)

    for mode in ("fast", "standard", "deep"):
        exit_code = cmd_resume(Namespace(mode=mode, format="json"))
        assert exit_code == 0
        out = capsys.readouterr().out
        assert f'"{mode}"' in out


def test_cli_resume_text_prints_without_error(tmp_path: Path, monkeypatch, capsys) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    monkeypatch.chdir(project_root)

    exit_code = cmd_resume(Namespace(mode="fast", format="text"))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "resume (fast)" in out
    assert "next action:" in out


def test_cli_resume_no_project_root_exits_1(tmp_path: Path, monkeypatch, capsys) -> None:
    # A bare directory with no .sybermem ancestor resolves to no project root.
    from sybermem_cli import main as main_module

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: None)

    exit_code = cmd_resume(Namespace(mode="fast", format="json"))

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "No SyberMem project root found." in err
