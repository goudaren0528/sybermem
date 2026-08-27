import json
import sqlite3
import sys
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli.main import cmd_search
from sybermem_core import workspace_search as workspace_search_module


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def write_record(root: Path, subdir: str, filename: str, frontmatter: list[str], body: str) -> None:
    records = root / ".sybermem" / subdir
    records.mkdir(exist_ok=True)
    (records / filename).write_text("\n".join(["---", *frontmatter, "---", "", body]) + "\n", encoding="utf-8")


def test_cli_search_json_preserves_expansion_provenance(monkeypatch, capsys) -> None:
    # Given: Core returns a relation-expanded row with bounded provenance metadata
    monkeypatch.setattr(
        "sybermem_cli.main.search_project",
        lambda query: [
            {
                "slug": "demo",
                "record_id": "change-001",
                "title": "Implemented requirement",
                "type": "change",
                "score": 9.0,
                "expanded_from": "requirement-001",
                "expansion_relation": "implements",
            }
        ],
    )

    # When: project search is requested as JSON
    exit_code = cmd_search(
        Namespace(
            query="requirement-001",
            scope="project",
            project=None,
            type=None,
            project_status=None,
            format="json",
        )
    )

    # Then: the raw Core row reaches machine consumers without losing provenance
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["results"][0]["expanded_from"] == "requirement-001"
    assert payload["results"][0]["expansion_relation"] == "implements"


def test_cli_search_text_prints_concise_expansion_provenance(monkeypatch, capsys) -> None:
    # Given: Core returns one relation-expanded result
    monkeypatch.setattr(
        "sybermem_cli.main.search_project",
        lambda query: [
            {
                "slug": "demo",
                "record_id": "change-001",
                "title": "Implemented requirement",
                "type": "change",
                "score": 9.0,
                "expanded_from": "requirement-001",
                "expansion_relation": "implements",
            }
        ],
    )

    # When: project search is rendered as text
    exit_code = cmd_search(
        Namespace(
            query="requirement-001",
            scope="project",
            project=None,
            type=None,
            project_status=None,
            format="text",
        )
    )

    # Then: one compact provenance line explains why the result was expanded
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "  - Expanded from: requirement-001 via implements" in output


def test_cli_search_text_prints_source_kind_and_conflict_note(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: equally strong authoritative project records that produce conflict metadata
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-04-001-first-policy.md",
        ["type: decision", "date: 2026-08-04", "title: First conflict policy", "status: decided"],
        "## Summary\ncli-conflict-token should use policy A.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-04-002-second-policy.md",
        ["type: decision", "date: 2026-08-04", "title: Second conflict policy", "status: decided"],
        "## Summary\ncli-conflict-token should use policy B.",
    )
    monkeypatch.chdir(project_root)

    # When: the existing text CLI search renderer is used
    exit_code = cmd_search(
        Namespace(
            query="cli-conflict-token",
            scope="project",
            project=None,
            type=None,
            project_status=None,
            format="text",
        )
    )

    # Then: the additive continuity metadata is visible in text output too
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "  - Source: manual" in output
    assert "  - Freshness: conflicted" in output
    assert "  - Conflict: parallel authoritative records match; review before relying on either" in output


def test_cli_search_text_prints_successor_guidance(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a superseded decision and its successor are both present on disk
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-04-001-old-policy.md",
        [
            "type: decision",
            "date: 2026-08-04",
            "title: Old cli-successor policy",
            "status: decided",
            "superseded_by: decision-002",
        ],
        "## Summary\ncli-successor used the old policy.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-05-002-new-policy.md",
        ["type: decision", "date: 2026-08-05", "title: New cli-successor policy", "status: decided"],
        "## Summary\ncli-successor uses the new policy.",
    )
    monkeypatch.chdir(project_root)

    # When: the text CLI renderer presents explicit historical search results
    exit_code = cmd_search(
        Namespace(
            query="old cli-successor",
            scope="project",
            project=None,
            type=None,
            project_status=None,
            format="text",
        )
    )

    # Then: the historical hit points to the current successor guidance
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "  - Successor: decision-002 New cli-successor policy" in output
    assert "  - Current guidance: Prefer successor decision-002 for current guidance." in output


def test_cli_workspace_search_reports_rebuild_for_stale_schema(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a stale workspace index created before the records.status column existed
    db_path = tmp_path / "sybermem.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            slug TEXT,
            name TEXT,
            path TEXT,
            remote TEXT,
            status TEXT,
            last_seen_commit TEXT,
            last_indexed_at TEXT
        );
        CREATE TABLE records (
            project_id TEXT,
            slug TEXT,
            record_id TEXT,
            type TEXT,
            title TEXT,
            content TEXT,
            topics TEXT,
            path TEXT,
            created_at TEXT,
            superseded_by TEXT,
            fixes TEXT,
            implements TEXT,
            related TEXT
        );
        CREATE VIRTUAL TABLE records_fts USING fts5(record_id, title, content, topics, slug, fixes, implements, related);
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(workspace_search_module, "index_db_path", lambda: db_path)

    # When: workspace search hits the stale schema through the CLI boundary
    exit_code = cmd_search(
        Namespace(
            query="workspace",
            scope="workspace",
            project=None,
            type=None,
            project_status=None,
            format="text",
        )
    )

    # Then: users get an actionable rebuild instruction instead of a Python traceback
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "sybermem index build" in captured.err
    assert "Traceback" not in captured.err
