from argparse import Namespace
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli.main import cmd_digest_latest, cmd_digest_status
from sybermem_core.digest_coverage import compute_coverage_hash


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def write_file(root: Path, rel: str, text: str) -> None:
    path = root / ".sybermem" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_digest(root: Path, name: str, record_id: str, sources: list[str], coverage_hash: str | None) -> None:
    fm = [
        "type: digest",
        "kind: phase",
        "date: 2026-08-05",
        f"title: {record_id}",
        f"record_id: {record_id}",
        "status: completed",
        "source_records:",
        *[f"  - {s}" for s in sources],
    ]
    if coverage_hash is not None:
        fm.append(f"coverage_hash: {coverage_hash}")
    text = "\n".join(["---", *fm, "---", "", "## Core Conclusions\n- s"]) + "\n"
    write_file(root, f"digests/{name}", text)


def test_cli_digest_status_json_reports_counts(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\norig\n")
    write_digest(root, "d.md", "digest-ok", ["changes/a.md"], compute_coverage_hash(root, ["changes/a.md"]))
    monkeypatch.chdir(root)

    exit_code = cmd_digest_status(Namespace(format="json"))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert '"total": 1' in out
    assert '"current": 1' in out


def test_cli_digest_status_stale_exits_1(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\norig\n")
    write_digest(root, "d.md", "digest-stale", ["changes/a.md"], compute_coverage_hash(root, ["changes/a.md"]))
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\nMUTATED\n")
    monkeypatch.chdir(root)

    exit_code = cmd_digest_status(Namespace(format="text"))

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "stale" in out
    assert "digest-stale" in out


def test_cli_digest_status_no_digests_ok(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    monkeypatch.chdir(root)

    exit_code = cmd_digest_status(Namespace(format="text"))

    assert exit_code == 0
    assert "No digests found." in capsys.readouterr().out


def test_cli_digest_status_no_project_root_exits_1(tmp_path: Path, monkeypatch, capsys) -> None:
    from sybermem_cli import main as main_module

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: None)

    exit_code = cmd_digest_status(Namespace(format="json"))

    assert exit_code == 1


def test_cli_digest_latest_json_returns_conclusions(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\norig\n")
    write_digest(root, "d.md", "digest-ok", ["changes/a.md"], compute_coverage_hash(root, ["changes/a.md"]))
    monkeypatch.chdir(root)

    exit_code = cmd_digest_latest(Namespace(format="json"))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert '"record_id": "digest-ok"' in out
    assert "Core Conclusions" not in out  # only the bullet, not the header
    assert "- s" in out


def test_cli_digest_latest_no_digest_reports_none(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    monkeypatch.chdir(root)

    exit_code = cmd_digest_latest(Namespace(format="text"))

    assert exit_code == 0
    assert "No digest found." in capsys.readouterr().out
