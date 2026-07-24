from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core import search as search_module
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
    monkeypatch.setattr(search_module, "index_db_path", lambda: db_path)

    # When: workspace search matches through relation metadata
    rows = search_workspace("bug-123")

    # Then: search returns relation metadata without a schema error
    assert rows[0]["fixes"] == "bug-123"
    assert rows[0]["implements"] == "requirement-456"
    assert rows[0]["related"] == "decision-789"
    assert rows[0]["match"] == "relation"
