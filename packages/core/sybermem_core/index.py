from __future__ import annotations

from pathlib import Path
import sqlite3

from .storage import ensure_dir
from .records import parse_project_yaml, iter_record_files, parse_record_file
from .registry import hub_registry_path


def index_db_path() -> Path:
    return Path.home() / ".sybermem" / "index" / "sybermem.db"


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS records;
        DROP TABLE IF EXISTS projects;
        DROP TABLE IF EXISTS records_fts;
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            slug TEXT,
            path TEXT,
            remote TEXT
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
            created_at TEXT
        );
        CREATE VIRTUAL TABLE records_fts USING fts5(record_id, title, content, topics, slug);
        """
    )


def load_registry() -> list[dict[str, str]]:
    path = hub_registry_path()
    if not path.is_file():
        return []
    projects: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  - project_id:"):
            if current:
                projects.append(current)
            current = {"project_id": line.split(":",1)[1].strip()}
        elif current is not None and line.startswith("    slug:"):
            current["slug"] = line.split(":",1)[1].strip()
        elif current is not None and line.startswith("    path:"):
            current["path"] = line.split(":",1)[1].strip()
        elif current is not None and line.startswith("    remote:"):
            current["remote"] = line.split(":",1)[1].strip()
    if current:
        projects.append(current)
    return projects


def rebuild_index(project_filter: str | None = None) -> dict[str, int]:
    db = index_db_path()
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
            continue
        conn.execute(
            "INSERT INTO projects(project_id, slug, path, remote) VALUES (?, ?, ?, ?)",
            (p["project_id"], p.get("slug", ""), p["path"], p.get("remote", ""))
        )
        proj_meta = parse_project_yaml(root)
        slug = proj_meta.get("slug") or p.get("slug", "")
        for rf in iter_record_files(root):
            row = parse_record_file(rf, p["project_id"], slug)
            conn.execute(
                "INSERT INTO records(project_id, slug, record_id, type, title, content, topics, path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["project_id"], row["slug"], row["record_id"], row["type"], row["title"], row["content"], row["topics"], row["path"], row["created_at"])
            )
            conn.execute(
                "INSERT INTO records_fts(record_id, title, content, topics, slug) VALUES (?, ?, ?, ?, ?)",
                (row["record_id"], row["title"], row["content"], row["topics"], row["slug"])
            )
            indexed_records += 1
        indexed_projects += 1

    conn.commit()
    conn.close()
    return {"projects": indexed_projects, "records": indexed_records}
