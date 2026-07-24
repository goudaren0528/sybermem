from __future__ import annotations

from pathlib import Path
import re
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


def _query_terms(query: str) -> list[str]:
    return [term for term in re.findall(r"[a-zA-Z0-9_-]+", query.lower()) if len(term) >= 3]


def _match_type(query: str, row: dict[str, str], terms: list[str]) -> str:
    q = query.lower().strip()
    record_id = row.get("record_id", "").lower()
    if record_id and record_id in q:
        return "record-id"
    relation_text = f"{row.get('fixes', '')} {row.get('implements', '')} {row.get('related', '')}".lower()
    if any(term in relation_text for term in terms):
        return "relation"
    topics = row.get("topics", "").lower()
    if any(term in topics for term in terms):
        return "topic"
    return "keyword"


def _created_rank(row: dict[str, str]) -> int:
    created = row.get("created_at", "")
    return int(created.replace("-", "")) if created else 0


def _fts_query(query: str) -> str:
    return '"' + query.strip().replace('"', '""') + '"'


def search_project(query: str) -> list[dict[str, str]]:
    root = resolve_project_root()
    if root is None:
        return []
    meta = parse_project_yaml(root)
    project_id = meta.get("project_id", "")
    slug = meta.get("slug", root.name)
    results: list[dict[str, str]] = []
    q = query.lower()
    terms = _query_terms(query)
    for rf in iter_record_files(root):
        row = parse_record_file(rf, project_id, slug)
        haystack = f"{row['record_id']} {row['title']} {row['content']} {row['topics']} {row.get('fixes', '')} {row.get('implements', '')} {row.get('related', '')}".lower()
        if q in haystack:
            row["score"] = 100.0 if row["record_id"].lower() == q else 10.0
            enriched = _with_retrieval_metadata(row)
            enriched["match"] = _match_type(query, row, terms)
            results.append(enriched)
    return results


def compact_project_search(query: str, limit: int = 3) -> list[dict[str, str]]:
    rows = search_project(query)
    if not rows:
        root = resolve_project_root()
        if root is None:
            return []
        meta = parse_project_yaml(root)
        project_id = meta.get("project_id", "")
        slug = meta.get("slug", root.name)
        terms = _query_terms(query)
        if not terms:
            return []

        fallback_rows: list[dict[str, str]] = []
        for rf in iter_record_files(root):
            row = parse_record_file(rf, project_id, slug)
            haystack = f"{row['record_id']} {row['title']} {row['topics']} {row.get('fixes', '')} {row.get('implements', '')} {row.get('related', '')}".lower()
            match_count = sum(1 for term in terms if term in haystack)
            if match_count:
                row["score"] = float(match_count)
                enriched = _with_retrieval_metadata(row)
                enriched["match"] = _match_type(query, row, terms)
                fallback_rows.append(enriched)
        rows = fallback_rows

    def score(row: dict[str, str]) -> tuple[int, int, int, int]:
        authority_rank = {"authoritative": 0, "summarized": 1, "evidence": 2}.get(row.get("authority", "summarized"), 3)
        freshness_rank = {"current": 0, "historical": 1, "stale": 2}.get(row.get("freshness", "historical"), 3)
        match_rank = -int(float(row.get("score", 0.0) or 0.0))
        created_rank = -_created_rank(row)
        return (authority_rank, freshness_rank, match_rank, created_rank)

    rows.sort(key=score)
    return rows[:limit]


def search_workspace(query: str, *, project: str | None = None, type_: str | None = None, project_status: str | None = None) -> list[dict[str, str]]:
    db = index_db_path()
    if not db.is_file():
        raise FileNotFoundError("workspace index not built; run `sybermem index build`")
    conn = sqlite3.connect(db)
    terms = _query_terms(query)

    # Try FTS5 first; fall back to LIKE if FTS table is missing
    has_fts = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records_fts'").fetchone()
    if has_fts:
        fts_query = _fts_query(query)
        sql = """
            SELECT r.project_id, r.slug, r.record_id, r.type, r.title, r.path, r.created_at,
                   r.content, r.topics, r.status, r.superseded_by, r.fixes, r.implements, r.related
            FROM records r
            JOIN projects p ON p.project_id = r.project_id
            JOIN records_fts f ON f.rowid = r.rowid
            WHERE records_fts MATCH ?
        """
        params: list[str] = [fts_query]
    else:
        q = f'%{query}%'
        sql = """
            SELECT r.project_id, r.slug, r.record_id, r.type, r.title, r.path, r.created_at,
                   r.content, r.topics, r.status, r.superseded_by, r.fixes, r.implements, r.related
            FROM records r
            JOIN projects p ON p.project_id = r.project_id
            WHERE (r.title LIKE ? OR r.content LIKE ? OR r.record_id LIKE ? OR r.topics LIKE ? OR r.fixes LIKE ? OR r.implements LIKE ? OR r.related LIKE ?)
        """
        params = [q, q, q, q, q, q, q]

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

    results = []
    for r in rows:
        row = {
            "project_id": r[0],
            "slug": r[1],
            "record_id": r[2],
            "type": r[3],
            "title": r[4],
            "path": r[5],
            "created_at": r[6],
            "content": r[7] or "",
            "topics": r[8] or "",
            "status": r[9] or "",
            "superseded_by": r[10] or "",
            "fixes": r[11] or "",
            "implements": r[12] or "",
            "related": r[13] or "",
            "score": 1.0,
        }
        enriched = _with_retrieval_metadata(row)
        enriched["match"] = _match_type(query, row, terms)
        results.append(enriched)
    return results
