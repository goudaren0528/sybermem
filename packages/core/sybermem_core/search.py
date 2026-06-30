from __future__ import annotations

from pathlib import Path
import sqlite3

from .index import index_db_path
from .project import resolve_project_root
from .records import iter_record_files, parse_project_yaml, parse_record_file


def search_project(query: str) -> list[dict[str, str]]:
    root = resolve_project_root()
    if root is None:
        return []
    meta = parse_project_yaml(root)
    project_id = meta.get("project_id", "")
    slug = meta.get("slug", root.name)
    results: list[dict[str, str]] = []
    q = query.lower()
    for rf in iter_record_files(root):
        row = parse_record_file(rf, project_id, slug)
        haystack = f"{row['record_id']} {row['title']} {row['content']} {row['topics']}".lower()
        if q in haystack:
            row['score'] = 1.0
            results.append(row)
    return results


def search_workspace(query: str) -> list[dict[str, str]]:
    db = index_db_path()
    if not db.is_file():
        raise FileNotFoundError("workspace index not built; run `sybermem index build`")
    conn = sqlite3.connect(db)
    q = f'%{query}%'
    rows = conn.execute(
        "SELECT project_id, slug, record_id, type, title, path, created_at FROM records WHERE title LIKE ? OR content LIKE ? OR record_id LIKE ? OR topics LIKE ? ORDER BY slug, created_at DESC",
        (q, q, q, q)
    ).fetchall()
    conn.close()
    return [
        {
            "project_id": r[0],
            "slug": r[1],
            "record_id": r[2],
            "type": r[3],
            "title": r[4],
            "path": r[5],
            "created_at": r[6],
            "score": 1.0,
        }
        for r in rows
    ]
