from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core import workspace_search as workspace_search_module
from sybermem_core.index import init_schema
from sybermem_core.search import search_workspace


def record_columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(records)").fetchall()}


def test_init_schema_creates_relation_columns() -> None:
    # Given: a new workspace index database
    conn = sqlite3.connect(":memory:")

    # When: the schema is initialized
    init_schema(conn)

    # Then: relation metadata required by search_workspace is present
    assert {"fixes", "implements", "related"}.issubset(record_columns(conn))


def test_init_schema_rebuilds_old_records_table_without_relation_columns() -> None:
    # Given: an existing cache DB with the old records shape
    conn = sqlite3.connect(":memory:")
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
            status TEXT,
            superseded_by TEXT
        );
        """
    )

    # When: the schema is initialized by current code
    init_schema(conn)

    # Then: the derived cache is rebuilt with relation columns
    assert {"fixes", "implements", "related"}.issubset(record_columns(conn))


def test_search_workspace_returns_relation_metadata(tmp_path: Path, monkeypatch) -> None:
    # Given: an indexed workspace record with relation frontmatter fields
    db_path = tmp_path / "sybermem.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    conn.execute(
        "INSERT INTO projects(project_id, slug, name, path, remote, status, last_seen_commit, last_indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("project-1", "demo", "Demo", str(tmp_path), "", "active", "abc123", "2026-07-24"),
    )
    conn.execute(
        "INSERT INTO records(project_id, slug, record_id, type, title, content, topics, path, created_at, status, superseded_by, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "project-1",
            "demo",
            "change-001",
            "change",
            "Repair workspace search",
            "Search result content",
            "search,relations",
            str(tmp_path / ".sybermem" / "changes" / "2026-07-24-001-repair.md"),
            "2026-07-24",
            "implemented",
            "",
            "bug-123",
            "requirement-456",
            "decision-789",
        ),
    )
    conn.execute(
        "INSERT INTO records_fts(record_id, title, content, topics, slug, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "change-001",
            "Repair workspace search",
            "Search result content",
            "search,relations",
            "demo",
            "bug-123",
            "requirement-456",
            "decision-789",
        ),
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(workspace_search_module, "index_db_path", lambda: db_path)

    # When: workspace search matches through relation metadata
    rows = search_workspace("bug-123")

    # Then: search returns relation metadata without a schema error
    assert rows[0]["fixes"] == "bug-123"
    assert rows[0]["implements"] == "requirement-456"
    assert rows[0]["related"] == "decision-789"
    assert rows[0]["match"] == "relation"


def test_search_workspace_adds_successor_guidance_for_superseded_records(tmp_path: Path, monkeypatch) -> None:
    # Given: a workspace index with a superseded decision and its current successor
    db_path = tmp_path / "sybermem.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    conn.execute(
        "INSERT INTO projects(project_id, slug, name, path, remote, status, last_seen_commit, last_indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("project-1", "demo", "Demo", str(tmp_path), "", "active", "abc123", "2026-08-04"),
    )
    rows = [
        (
            "project-1",
            "demo",
            "decision-001",
            "decision",
            "Old workspace successor policy",
            "Old workspace-successor policy text.",
            "",
            str(tmp_path / ".sybermem" / "decisions" / "2026-08-04-001-old.md"),
            "2026-08-04",
            "decided",
            "decision-002",
            "",
            "",
            "",
        ),
        (
            "project-1",
            "demo",
            "decision-002",
            "decision",
            "New workspace successor policy",
            "New workspace-successor policy text.",
            "",
            str(tmp_path / ".sybermem" / "decisions" / "2026-08-05-002-new.md"),
            "2026-08-05",
            "decided",
            "",
            "",
            "",
            "",
        ),
    ]
    conn.executemany(
        "INSERT INTO records(project_id, slug, record_id, type, title, content, topics, path, created_at, status, superseded_by, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.executemany(
        "INSERT INTO records_fts(record_id, title, content, topics, slug, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [(row[2], row[4], row[5], row[6], row[1], row[11], row[12], row[13]) for row in rows],
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(workspace_search_module, "index_db_path", lambda: db_path)

    # When: workspace search returns the historical hit
    results = search_workspace("old workspace-successor")

    # Then: workspace results carry the same successor/current guidance as project search
    old = next(row for row in results if row["record_id"] == "decision-001")
    assert old["successor_record"] == "decision-002"
    assert old["successor_title"] == "New workspace successor policy"
    assert old["current_record"] == "decision-002"
    assert old["current_guidance"] == "Prefer successor decision-002 for current guidance."
