from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core import index as index_module
from sybermem_core import search as search_module
from sybermem_core.index import init_schema, rebuild_index
from sybermem_core.search import search_workspace


def write_project(root: Path, project_id: str, slug: str) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text(
        f"project_id: {project_id}\nslug: {slug}\n",
        encoding="utf-8",
    )


def write_record(root: Path, filename: str, content: str) -> None:
    records = root / ".sybermem" / "changes"
    records.mkdir(exist_ok=True)
    (records / filename).write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "date: 2026-08-04",
                "title: Test record",
                "status: implemented",
                "---",
                "",
                content,
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_rebuild_index_removes_stale_fts_rows(tmp_path: Path, monkeypatch) -> None:
    # Given: a project whose indexed record is replaced between rebuilds
    db_path = tmp_path / "sybermem.db"
    state_path = tmp_path / "index-state.json"
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root, "project-1", "demo")
    old_record = "2026-08-04-001-old.md"
    write_record(project_root, old_record, "ghost-token")
    registry = [
        {
            "project_id": "project-1",
            "slug": "demo",
            "name": "Demo",
            "path": str(project_root),
            "remote": "",
            "last_seen_commit": "",
            "status": "active",
        }
    ]
    monkeypatch.setattr(index_module, "index_db_path", lambda: db_path)
    monkeypatch.setattr(index_module, "index_state_path", lambda: state_path)
    monkeypatch.setattr(index_module, "load_registry", lambda: registry)
    monkeypatch.setattr(index_module, "current_head", lambda root: "commit-1")
    monkeypatch.setattr(
        index_module,
        "update_registry_index_metadata",
        lambda project_id, *, commit, indexed_at, status: None,
    )
    monkeypatch.setattr(search_module, "index_db_path", lambda: db_path)
    rebuild_index()

    (project_root / ".sybermem" / "changes" / old_record).unlink()
    write_record(project_root, "2026-08-04-002-new.md", "fresh-token")

    # When: the same project is rebuilt from canonical Markdown
    rebuild_index()

    # Then: stale FTS content from the removed Markdown record is gone
    assert search_workspace("ghost-token") == []
    assert search_workspace("fresh-token")[0]["record_id"] == "change-002"


def test_search_workspace_rejects_mismatched_fts_rowid(tmp_path: Path, monkeypatch) -> None:
    # Given: a corrupted derived FTS row points at an unrelated records.rowid
    db_path = tmp_path / "sybermem.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    conn.execute(
        "INSERT INTO projects(project_id, slug, name, path, remote, status, last_seen_commit, last_indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("project-1", "demo", "Demo", str(tmp_path), "", "active", "abc123", "2026-08-04"),
    )
    conn.execute(
        "INSERT INTO records(rowid, project_id, slug, record_id, type, title, content, topics, path, created_at, status, superseded_by, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            1,
            "project-1",
            "demo",
            "change-001",
            "change",
            "Safe record",
            "safe content",
            "",
            str(tmp_path / "safe.md"),
            "2026-08-04",
            "implemented",
            "",
            "",
            "",
            "",
        ),
    )
    conn.execute(
        "INSERT INTO records_fts(rowid, record_id, title, content, topics, slug, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (1, "change-999", "Ghost record", "mismatch-token", "", "demo", "", "", ""),
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(search_module, "index_db_path", lambda: db_path)

    # When: FTS matches the corrupted row
    rows = search_workspace("mismatch-token")

    # Then: the rowid-only join must not return the unrelated canonical record
    assert rows == []


def test_old_schema_rebuild_reindexes_project_even_when_commit_is_current(tmp_path: Path, monkeypatch) -> None:
    # Given: a Phase 1 cache schema and registry metadata already at HEAD
    db_path = tmp_path / "sybermem.db"
    state_path = tmp_path / "index-state.json"
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root, "project-1", "demo")
    write_record(project_root, "2026-08-04-001-current.md", "current-token")
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            slug TEXT,
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
    conn.commit()
    conn.close()
    registry = [
        {
            "project_id": "project-1",
            "slug": "demo",
            "name": "Demo",
            "path": str(project_root),
            "remote": "",
            "last_seen_commit": "head-commit",
            "status": "active",
        }
    ]
    monkeypatch.setattr(index_module, "index_db_path", lambda: db_path)
    monkeypatch.setattr(index_module, "index_state_path", lambda: state_path)
    monkeypatch.setattr(index_module, "load_registry", lambda: registry)
    monkeypatch.setattr(index_module, "current_head", lambda root: "head-commit")
    monkeypatch.setattr(
        index_module,
        "update_registry_index_metadata",
        lambda project_id, *, commit, indexed_at, status: None,
    )
    monkeypatch.setattr(search_module, "index_db_path", lambda: db_path)

    # When: rebuild_index migrates the disposable cache schema
    summary = rebuild_index()

    # Then: the unchanged project is still repopulated from Markdown
    assert summary == {"projects": 1, "records": 1}
    assert search_workspace("current-token")[0]["record_id"] == "change-001"


def test_search_workspace_falls_back_when_fts_match_raises_operational_error(tmp_path: Path, monkeypatch) -> None:
    # Given: a workspace DB whose LIKE path can answer the query
    db_path = tmp_path / "sybermem.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    conn.execute("DROP TABLE records_fts")
    conn.execute(
        "INSERT INTO projects(project_id, slug, name, path, remote, status, last_seen_commit, last_indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("project-1", "demo", "Demo", str(tmp_path), "", "active", "abc123", "2026-08-04"),
    )
    conn.execute(
        "INSERT INTO records(project_id, slug, record_id, type, title, content, topics, path, created_at, status, superseded_by, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "project-1",
            "demo",
            "change-001",
            "change",
            "Fallback record",
            "fallback-token",
            "",
            str(tmp_path / "fallback.md"),
            "2026-08-04",
            "implemented",
            "",
            "",
            "",
            "",
        ),
    )
    conn.execute("CREATE TABLE records_fts(rowid INTEGER PRIMARY KEY, content TEXT)")
    conn.commit()
    conn.close()
    monkeypatch.setattr(search_module, "index_db_path", lambda: db_path)

    # When: the malformed FTS table raises during MATCH execution
    rows = search_workspace("fallback-token")

    # Then: workspace search safely falls back to LIKE search
    assert rows[0]["record_id"] == "change-001"


def test_search_workspace_escapes_terms_and_falls_back_from_fts_syntax_error(tmp_path: Path, monkeypatch) -> None:
    # Given: a workspace DB with FTS enabled and a record matchable through safe terms
    db_path = tmp_path / "sybermem.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    conn.execute(
        "INSERT INTO projects(project_id, slug, name, path, remote, status, last_seen_commit, last_indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("project-1", "demo", "Demo", str(tmp_path), "", "active", "abc123", "2026-08-04"),
    )
    conn.execute(
        "INSERT INTO records(project_id, slug, record_id, type, title, content, topics, path, created_at, status, superseded_by, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "project-1",
            "demo",
            "change-001",
            "change",
            "Safe syntax fallback",
            "alpha beta content",
            "search",
            str(tmp_path / "fallback.md"),
            "2026-08-04",
            "implemented",
            "",
            "",
            "",
            "",
        ),
    )
    conn.execute(
        "INSERT INTO records_fts(record_id, title, content, topics, slug, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("change-001", "Safe syntax fallback", "alpha beta content", "search", "demo", "", "", ""),
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(search_module, "index_db_path", lambda: db_path)

    # When: a user prompt includes FTS metacharacters that used to make MATCH brittle
    rows = search_workspace('alpha OR "unterminated beta')

    # Then: search does not raise and still recalls through safe term fallback
    assert [row["record_id"] for row in rows] == ["change-001"]
