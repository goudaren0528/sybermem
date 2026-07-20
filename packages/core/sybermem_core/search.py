from __future__ import annotations

from pathlib import Path
import sqlite3

from .index import index_db_path
from .project import resolve_project_root
from .records import iter_record_files, parse_project_yaml, parse_record_file
from .retrieval import (
    classify_authority,
    classify_freshness,
    classify_lifecycle,
    classify_source_kind,
)


def _with_retrieval_metadata(row: dict[str, str]) -> dict[str, str]:
    source_kind = classify_source_kind(row["path"])
    authority = classify_authority(source_kind, row.get("title", ""), row.get("content", ""))
    archived = "[archived]" in row.get("content", "")
    lifecycle = classify_lifecycle(row.get("status", ""), row.get("superseded_by", ""), archived)
    freshness = classify_freshness(lifecycle)
    enriched = dict(row)
    enriched["source_kind"] = source_kind
    enriched["authority"] = authority
    enriched["lifecycle"] = lifecycle
    enriched["freshness"] = freshness
    enriched["related_digest"] = ""
    return enriched


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
            results.append(_with_retrieval_metadata(row))
    return results


def search_workspace(query: str, *, project: str | None = None, type_: str | None = None, project_status: str | None = None) -> list[dict[str, str]]:
    db = index_db_path()
    if not db.is_file():
        raise FileNotFoundError("workspace index not built; run `sybermem index build`")
    conn = sqlite3.connect(db)

    # Try FTS5 first; fall back to LIKE if FTS table is missing
    has_fts = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records_fts'").fetchone()
    if has_fts:
        fts_query = query.strip()
        sql = """
            SELECT r.project_id, r.slug, r.record_id, r.type, r.title, r.path, r.created_at
            FROM records r
            JOIN projects p ON p.project_id = r.project_id
            JOIN records_fts f ON f.rowid = r.rowid
            WHERE records_fts MATCH ?
        """
        params: list[str] = [fts_query]
    else:
        q = f'%{query}%'
        sql = """
            SELECT r.project_id, r.slug, r.record_id, r.type, r.title, r.path, r.created_at
            FROM records r
            JOIN projects p ON p.project_id = r.project_id
            WHERE (r.title LIKE ? OR r.content LIKE ? OR r.record_id LIKE ? OR r.topics LIKE ?)
        """
        params = [q, q, q, q]

    if project:
        sql += " AND r.slug = ?"
        params.append(project)
    if type_:
        sql += " AND r.type = ?"
        params.append(type_)
    if project_status:
        sql += " AND p.status = ?"
        params.append(project_status)
    sql += " ORDER BY r.slug, r.created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [
        _with_retrieval_metadata(
            {
                "project_id": r[0],
                "slug": r[1],
                "record_id": r[2],
                "type": r[3],
                "title": r[4],
                "path": r[5],
                "created_at": r[6],
                "content": "",
                "topics": "",
                "status": "",
                "superseded_by": "",
                "fixes": "",
                "implements": "",
                "related": "",
                "score": 1.0,
            }
        )
        for r in rows
    ]
