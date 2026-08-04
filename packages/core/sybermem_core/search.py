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
    derive_summary,
)
from .search_query import QueryTerms, query_terms, score_row
from .workspace_query import WorkspaceFilters, apply_workspace_filters, workspace_fts_query, workspace_like_query


def _with_retrieval_metadata(row: dict[str, str], related_digest: str = "") -> dict[str, str]:
    source_kind = classify_source_kind(row["path"], row.get("title", ""), row.get("content", ""))
    authority = classify_authority(source_kind, row.get("title", ""), row.get("content", ""))
    archived = "[archived]" in row.get("content", "")
    lifecycle = classify_lifecycle(row.get("status", ""), row.get("superseded_by", ""), archived)
    freshness = classify_freshness(lifecycle)
    enriched = dict(row)
    enriched["source_kind"] = source_kind
    enriched["authority"] = authority
    enriched["lifecycle"] = lifecycle
    enriched["freshness"] = freshness
    enriched["summary"] = derive_summary(row.get("content", ""), row.get("title", ""))
    enriched["related_digest"] = related_digest
    enriched["conflict_note"] = ""
    return enriched


def _record_keys(row: dict[str, str]) -> set[str]:
    normalized = row.get("path", "").replace("\\", "/")
    keys = {row.get("record_id", ""), Path(normalized).name}
    if "/.sybermem/" in normalized:
        keys.add(normalized.split("/.sybermem/", 1)[1])
    return {key for key in keys if key}


def _digest_coverage(rows: list[dict[str, str]]) -> dict[str, str]:
    coverage: dict[str, str] = {}
    for row in rows:
        if classify_source_kind(row["path"], row.get("title", ""), row.get("content", "")) != "digest":
            continue
        digest_id = row.get("record_id", "")
        in_sources = False
        for line in row.get("content", "").splitlines():
            stripped = line.strip()
            if stripped == "source_records:":
                in_sources = True
                continue
            if in_sources and stripped.startswith("-"):
                coverage[stripped.lstrip("- ").strip()] = digest_id
                continue
            if in_sources and stripped and not line.startswith(" "):
                in_sources = False
    return coverage


def _related_digest(row: dict[str, str], coverage: dict[str, str]) -> str:
    for key in _record_keys(row):
        if key in coverage:
            return coverage[key]
    return ""


def _annotate_conflicts(rows: list[dict[str, str]]) -> None:
    newest_authoritative = max((_created_rank(row) for row in rows if row.get("authority") == "authoritative"), default=0)
    for row in rows:
        if row.get("source_kind") == "digest" and newest_authoritative > _created_rank(row):
            row["conflict_note"] = "historical digest; newer authoritative record exists"


def _match_type(query: str, row: dict[str, str], terms: QueryTerms) -> str:
    q = query.lower().strip()
    record_id = row.get("record_id", "").lower()
    if record_id and record_id in q:
        return "record-id"
    relation_text = f"{row.get('fixes', '')} {row.get('implements', '')} {row.get('related', '')}".lower()
    if any(term in relation_text for term in terms.all):
        return "relation"
    topics = row.get("topics", "").lower()
    if any(term in topics for term in terms.all):
        return "topic"
    return "keyword"


def _created_rank(row: dict[str, str]) -> int:
    created = row.get("created_at", "")
    return int(created.replace("-", "")) if created else 0


def _compact_match_allowed(score: float, match: str, matched_fields: int) -> bool:
    return match in {"record-id", "relation"} or (score >= 5 and matched_fields >= 2)


def search_project(query: str) -> list[dict[str, str]]:
    root = resolve_project_root()
    if root is None:
        return []
    meta = parse_project_yaml(root)
    project_id = meta.get("project_id", "")
    slug = meta.get("slug", root.name)
    results: list[dict[str, str]] = []
    q = query.lower()
    terms = query_terms(query)
    all_rows = [parse_record_file(rf, project_id, slug) for rf in iter_record_files(root)]
    digest_coverage = _digest_coverage(all_rows)
    for row in all_rows:
        haystack = f"{row['record_id']} {row['title']} {row['content']} {row['topics']} {row.get('fixes', '')} {row.get('implements', '')} {row.get('related', '')}".lower()
        if q in haystack:
            row["score"] = 100.0 if row["record_id"].lower() == q else 10.0
            row["matched_fields"] = "1" if row["record_id"].lower() == q else "2"
            enriched = _with_retrieval_metadata(row, _related_digest(row, digest_coverage))
            enriched["match"] = _match_type(query, row, terms)
            results.append(enriched)
            continue
        overlap = score_row(row, terms)
        if overlap is not None:
            row["score"] = overlap.score
            row["matched_fields"] = str(overlap.matched_fields)
            enriched = _with_retrieval_metadata(row, _related_digest(row, digest_coverage))
            enriched["match"] = overlap.match
            results.append(enriched)
    _annotate_conflicts(results)
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
        terms = query_terms(query)
        if not terms.is_meaningful:
            return []

        fallback_rows: list[dict[str, str]] = []
        all_rows = [parse_record_file(rf, project_id, slug) for rf in iter_record_files(root)]
        digest_coverage = _digest_coverage(all_rows)
        for row in all_rows:
            overlap = score_row(row, terms)
            if overlap is not None and _compact_match_allowed(overlap.score, overlap.match, overlap.matched_fields):
                row["score"] = overlap.score
                row["matched_fields"] = str(overlap.matched_fields)
                enriched = _with_retrieval_metadata(row, _related_digest(row, digest_coverage))
                enriched["match"] = overlap.match
                fallback_rows.append(enriched)
        rows = fallback_rows

    rows = [
        row
        for row in rows
        if row.get("authority") != "evidence" and _compact_match_allowed(float(row.get("score", 0.0) or 0.0), row.get("match", ""), int(row.get("matched_fields", "0") or "0"))
    ]
    _annotate_conflicts(rows)

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
    with sqlite3.connect(db) as conn:
        terms = query_terms(query)
        filters = WorkspaceFilters(project=project, type_=type_, project_status=project_status)

        # Try FTS5 first; fall back to LIKE if FTS is missing or unusable.
        has_fts = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records_fts'").fetchone()
        if has_fts and terms.all:
            sql, params = workspace_fts_query(terms)
            sql, params = apply_workspace_filters(sql, params, filters)
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                sql, params = workspace_like_query(terms)
                sql, params = apply_workspace_filters(sql, params, filters)
                rows = conn.execute(sql, params).fetchall()
        else:
            sql, params = workspace_like_query(terms)
            sql, params = apply_workspace_filters(sql, params, filters)
            rows = conn.execute(sql, params).fetchall()

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
        overlap = score_row(row, terms)
        if overlap is None:
            continue
        row["score"] = overlap.score
        row["matched_fields"] = str(overlap.matched_fields)
        enriched = _with_retrieval_metadata(row)
        enriched["match"] = overlap.match
        results.append(enriched)
    return results
