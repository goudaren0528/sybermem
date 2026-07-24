from __future__ import annotations

from pathlib import Path
import json
import sqlite3
import subprocess

from .storage import ensure_dir
from .records import parse_project_yaml, iter_record_files, parse_record_file
from .registry import load_registry, update_registry_index_metadata
from .identity import now_iso


def index_db_path() -> Path:
    return Path.home() / ".sybermem" / "index" / "sybermem.db"


def index_state_path() -> Path:
    return Path.home() / ".sybermem" / "index" / "index-state.json"


def current_head(root: Path) -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def init_schema(conn: sqlite3.Connection) -> None:
    """Ensure the current Phase 2 schema exists.

    If an older Phase 1 schema is detected (missing columns like `name`),
    rebuild the derived tables in-place. The DB is a cache and can always be
    reconstructed from Markdown.
    """
    # Detect whether the existing projects table matches the Phase 2 shape.
    needs_rebuild = False
    try:
        project_cols = [row[1] for row in conn.execute("PRAGMA table_info(projects)").fetchall()]
        if project_cols and "name" not in project_cols:
            needs_rebuild = True
        record_cols = {row[1] for row in conn.execute("PRAGMA table_info(records)").fetchall()}
        if record_cols and not {"fixes", "implements", "related"}.issubset(record_cols):
            needs_rebuild = True
        fts_cols = {row[1] for row in conn.execute("PRAGMA table_info(records_fts)").fetchall()}
        if fts_cols and not {"fixes", "implements", "related"}.issubset(fts_cols):
            needs_rebuild = True
    except sqlite3.DatabaseError:
        needs_rebuild = True

    if needs_rebuild:
        conn.executescript(
            """
            DROP TABLE IF EXISTS records;
            DROP TABLE IF EXISTS projects;
            DROP TABLE IF EXISTS records_fts;
            """
        )

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            slug TEXT,
            name TEXT,
            path TEXT,
            remote TEXT,
            status TEXT,
            last_seen_commit TEXT,
            last_indexed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS records (
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
            superseded_by TEXT,
            fixes TEXT,
            implements TEXT,
            related TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(record_id, title, content, topics, slug, fixes, implements, related);
        """
    )


def rebuild_index(project_filter: str | None = None) -> dict[str, int]:
    db = index_db_path()
    state = index_state_path()
    ensure_dir(db.parent)
    conn = sqlite3.connect(db)
    init_schema(conn)

    projects = load_registry()
    indexed_projects = 0
    indexed_records = 0

    for p in projects:
        if project_filter and p.get("slug") != project_filter:
            continue
        root = Path(p["path"])
        if not (root / ".sybermem" / "INDEX.md").is_file():
            update_registry_index_metadata(p["project_id"], commit="", indexed_at=now_iso(), status="missing")
            continue

        head = current_head(root)
        if head and p.get("last_seen_commit") == head:
            continue

        conn.execute("DELETE FROM records WHERE project_id = ?", (p["project_id"],))
        conn.execute("DELETE FROM projects WHERE project_id = ?", (p["project_id"],))

        proj_meta = parse_project_yaml(root)
        slug = proj_meta.get("slug") or p.get("slug", "")
        conn.execute(
            "INSERT INTO projects(project_id, slug, name, path, remote, status, last_seen_commit, last_indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                p["project_id"],
                slug,
                p.get("name", slug),
                p["path"],
                p.get("remote", ""),
                "active",
                head,
                now_iso(),
            ),
        )
        for rf in iter_record_files(root):
            row = parse_record_file(rf, p["project_id"], slug)
            conn.execute(
                "INSERT INTO records(project_id, slug, record_id, type, title, content, topics, path, created_at, status, superseded_by, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row["project_id"], row["slug"], row["record_id"], row["type"], row["title"],
                    row["content"], row["topics"], row["path"], row["created_at"], row["status"], row["superseded_by"],
                    row["fixes"], row["implements"], row["related"]
                )
            )
            conn.execute(
                "INSERT INTO records_fts(record_id, title, content, topics, slug, fixes, implements, related) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (row["record_id"], row["title"], row["content"], row["topics"], row["slug"], row["fixes"], row["implements"], row["related"])
            )
            indexed_records += 1
        indexed_projects += 1
        update_registry_index_metadata(p["project_id"], commit=head, indexed_at=now_iso(), status="active")

    conn.commit()
    conn.close()
    state.write_text(json.dumps({
        "schema_version": 2,
        "last_built_at": now_iso(),
        "projects_indexed": indexed_projects,
        "records_indexed": indexed_records,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"projects": indexed_projects, "records": indexed_records}
