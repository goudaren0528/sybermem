from argparse import Namespace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli.main import cmd_norms_list, cmd_norms_nominate


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    (sybermem / "norms").mkdir(parents=True)
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def write_norm(root: Path, name: str, record_id: str, scope: str, statement: str) -> None:
    text = "\n".join([
        "---", "type: norm", f"record_id: {record_id}", "date: 2026-08-20",
        f"title: {statement}", "authority: authoritative", "status: active",
        f"scope: {scope}", f"key_conclusion: {statement}", "---", "", f"## Norm Statement\n{statement}",
    ]) + "\n"
    (root / ".sybermem" / "norms" / name).write_text(text, encoding="utf-8")


def test_cli_norms_list_global_json(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    write_norm(root, "g.md", "norm-001", "global", "Use pnpm in this repo")
    write_norm(root, "s.md", "norm-002", "topic:auth", "Sessions expire in 30m")
    monkeypatch.chdir(root)

    exit_code = cmd_norms_list(Namespace(scope="global", context="", format="json"))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert '"record_id": "norm-001"' in out
    assert "norm-002" not in out  # scoped not in global lane


def test_cli_norms_list_scoped_by_context(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    write_norm(root, "s.md", "norm-002", "topic:auth", "Sessions expire in 30 minutes")
    monkeypatch.chdir(root)

    exit_code = cmd_norms_list(Namespace(scope="scoped", context="fixing the auth login flow", format="json"))

    assert exit_code == 0
    assert '"record_id": "norm-002"' in capsys.readouterr().out


def test_cli_norms_list_all_combines_constitution_and_scoped(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    write_norm(root, "g.md", "norm-001", "global", "Use pnpm")
    write_norm(root, "s.md", "norm-002", "topic:auth", "Auth sessions expire")
    monkeypatch.chdir(root)

    exit_code = cmd_norms_list(Namespace(scope="all", context="auth work", format="json"))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "norm-001" in out and "norm-002" in out


def test_cli_norms_list_none(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    monkeypatch.chdir(root)

    exit_code = cmd_norms_list(Namespace(scope="global", context="", format="text"))

    assert exit_code == 0
    assert "No matching norms." in capsys.readouterr().out


def _write_decision(root: Path, name: str, record_id: str, body: str) -> None:
    (root / ".sybermem" / "decisions").mkdir(parents=True, exist_ok=True)
    text = "\n".join(["---", "type: decision", f"record_id: {record_id}", "date: 2026-08-20", f"title: {record_id}", "---", "", body]) + "\n"
    (root / ".sybermem" / "decisions" / name).write_text(text, encoding="utf-8")


def test_cli_norms_nominate_json(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    _write_decision(root, "d1.md", "decision-001", "All HTTP handlers must validate input at the boundary.")
    _write_decision(root, "d2.md", "decision-002", "HTTP handlers must validate input at the boundary first.")
    _write_decision(root, "d3.md", "decision-003", "Every HTTP handler must validate input at the boundary.")
    monkeypatch.chdir(root)

    exit_code = cmd_norms_nominate(Namespace(format="json"))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert '"occurrences": 3' in out
    assert "decision-001" in out


def test_cli_norms_nominate_none(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    monkeypatch.chdir(root)

    exit_code = cmd_norms_nominate(Namespace(format="text"))

    assert exit_code == 0
    assert "No norm nominations." in capsys.readouterr().out
