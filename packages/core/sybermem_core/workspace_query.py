from __future__ import annotations

from dataclasses import dataclass

from .search_query import QueryTerms, fts_query, like_patterns


@dataclass(frozen=True, slots=True)
class WorkspaceFilters:
    project: str | None
    type_: str | None
    project_status: str | None


def workspace_like_query(terms: QueryTerms) -> tuple[str, list[str]]:
    patterns = like_patterns(terms)
    if not patterns:
        patterns = ["__NO_QUERY_TERMS__"]
    clauses = " OR ".join(
        [
            "r.title LIKE ?",
            "r.content LIKE ?",
            "r.record_id LIKE ?",
            "r.topics LIKE ?",
            "r.fixes LIKE ?",
            "r.implements LIKE ?",
            "r.related LIKE ?",
        ]
    )
    where = " OR ".join(f"({clauses})" for _ in patterns)
    return (
        f"""
            SELECT r.project_id, r.slug, r.record_id, r.type, r.title, r.path, r.created_at,
                   r.content, r.topics, r.status, r.superseded_by, r.fixes, r.implements, r.related
            FROM records r
            JOIN projects p ON p.project_id = r.project_id
            WHERE {where}
        """,
        [pattern for pattern in patterns for _ in range(7)],
    )


def workspace_fts_query(terms: QueryTerms) -> tuple[str, list[str]]:
    return (
        """
            SELECT r.project_id, r.slug, r.record_id, r.type, r.title, r.path, r.created_at,
                   r.content, r.topics, r.status, r.superseded_by, r.fixes, r.implements, r.related
            FROM records r
            JOIN projects p ON p.project_id = r.project_id
            JOIN records_fts f ON f.rowid = r.rowid AND f.record_id = r.record_id AND f.slug = r.slug
            WHERE records_fts MATCH ?
        """,
        [fts_query(terms)],
    )


def workspace_guidance_query() -> tuple[str, list[str]]:
    return (
        """
            SELECT r.project_id, r.slug, r.record_id, r.type, r.title, r.path, r.created_at,
                   r.content, r.topics, r.status, r.superseded_by, r.fixes, r.implements, r.related
            FROM records r
            JOIN projects p ON p.project_id = r.project_id
            WHERE 1 = 1
        """,
        [],
    )


def apply_workspace_filters(
    sql: str,
    params: list[str],
    filters: WorkspaceFilters,
) -> tuple[str, list[str]]:
    if filters.project:
        sql += " AND r.slug = ?"
        params.append(filters.project)
    if filters.type_:
        sql += " AND r.type = ?"
        params.append(filters.type_)
    if filters.project_status:
        sql += " AND p.status = ?"
        params.append(filters.project_status)
    sql += " ORDER BY r.slug, r.created_at DESC"
    return sql, params
