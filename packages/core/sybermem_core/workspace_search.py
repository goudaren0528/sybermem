from __future__ import annotations

from typing import TypeAlias
import sqlite3

from .index import index_db_path
from .retrieval import apply_successor_guidance, derive_continuity_metadata
from .search_query import score_row, query_terms
from .workspace_query import WorkspaceFilters, apply_workspace_filters, workspace_fts_query, workspace_guidance_query, workspace_like_query


SearchValue: TypeAlias = str | float
SearchRow: TypeAlias = dict[str, SearchValue]
WORKSPACE_REBUILD_MESSAGE = "workspace index schema is stale or incompatible; run `sybermem index build`"
REQUIRED_WORKSPACE_RECORD_COLUMNS = frozenset(
    {"project_id", "slug", "record_id", "type", "title", "content", "topics", "path", "created_at", "status", "superseded_by", "fixes", "implements", "related"}
)
REQUIRED_WORKSPACE_PROJECT_COLUMNS = frozenset({"project_id", "slug", "status"})


class WorkspaceIndexIncompatibleError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(WORKSPACE_REBUILD_MESSAGE)


def search_workspace(query: str, *, project: str | None = None, type_: str | None = None, project_status: str | None = None) -> list[SearchRow]:
    db = index_db_path()
    if not db.is_file():
        raise FileNotFoundError("workspace index not built; run `sybermem index build`")
    with sqlite3.connect(db) as conn:
        _ensure_workspace_schema(conn)
        terms = query_terms(query)
        filters = WorkspaceFilters(project=project, type_=type_, project_status=project_status)

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

        guidance_sql, guidance_params = workspace_guidance_query()
        guidance_sql, guidance_params = apply_workspace_filters(guidance_sql, guidance_params, filters)
        guidance_rows = [_with_retrieval_metadata(_workspace_row(record), match_reason="") for record in conn.execute(guidance_sql, guidance_params).fetchall()]

    results: list[SearchRow] = []
    for record in rows:
        row = _workspace_row(record)
        row["score"] = 1.0
        overlap = score_row(_score_input(row), terms)
        if overlap is None:
            continue
        row["score"] = overlap.score
        row["matched_fields"] = str(overlap.matched_fields)
        enriched = _with_retrieval_metadata(row, match_reason=overlap.match)
        enriched["match"] = overlap.match
        results.append(enriched)
    apply_successor_guidance(results, guidance_rows)
    return results


def _with_retrieval_metadata(row: SearchRow, *, match_reason: str) -> SearchRow:
    enriched = dict(row)
    metadata = derive_continuity_metadata(row, match_reason=match_reason)
    enriched["source_kind"] = metadata["source_kind"]
    enriched["authority"] = metadata["authority"]
    enriched["lifecycle"] = metadata["lifecycle"]
    enriched["freshness"] = metadata["freshness"]
    enriched["match_reason"] = metadata["match_reason"]
    enriched["related_digest"] = metadata["related_digest"]
    enriched["conflict_note"] = metadata["conflict_note"]
    enriched["summary"] = metadata["summary"]
    return enriched


def _ensure_workspace_schema(conn: sqlite3.Connection) -> None:
    record_cols = {row[1] for row in conn.execute("PRAGMA table_info(records)").fetchall()}
    project_cols = {row[1] for row in conn.execute("PRAGMA table_info(projects)").fetchall()}
    if not REQUIRED_WORKSPACE_RECORD_COLUMNS.issubset(record_cols) or not REQUIRED_WORKSPACE_PROJECT_COLUMNS.issubset(project_cols):
        raise WorkspaceIndexIncompatibleError


def _workspace_row(record: tuple[SearchValue | None, ...]) -> SearchRow:
    return {
        "project_id": record[0] or "",
        "slug": record[1] or "",
        "record_id": record[2] or "",
        "type": record[3] or "",
        "title": record[4] or "",
        "path": record[5] or "",
        "created_at": record[6] or "",
        "content": record[7] or "",
        "topics": record[8] or "",
        "status": record[9] or "",
        "superseded_by": record[10] or "",
        "fixes": record[11] or "",
        "implements": record[12] or "",
        "related": record[13] or "",
    }


def _text(row: SearchRow, key: str) -> str:
    value = row.get(key, "")
    return value if isinstance(value, str) else str(value)


def _score_input(row: SearchRow) -> dict[str, str]:
    return {key: _text(row, key) for key in ("record_id", "title", "content", "topics", "fixes", "implements", "related")}
