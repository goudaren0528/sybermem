from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

from .project import resolve_project_root
from .records import iter_record_files, parse_project_yaml, parse_record_file
from .retrieval import (
    apply_successor_guidance,
    classify_source_kind,
    compact_abstention_row,
    derive_continuity_metadata,
)
from .search_query import QueryTerms, query_terms, score_row
from .workspace_search import WorkspaceIndexIncompatibleError, search_workspace, workspace_index_staleness


SearchValue: TypeAlias = str | float
SearchRow: TypeAlias = dict[str, SearchValue]


class ProjectRootNotFoundError(RuntimeError):
    """Raised when project-scope search runs outside a SyberMem project root."""

    def __init__(self) -> None:
        super().__init__("No SyberMem project root found.")


# Process-local parsed-record cache: root -> (fingerprint, rows).
# Transparent: results are identical to re-parsing; only avoids redundant work
# within a single process (e.g. search_project + its compact fallback).
_ROW_CACHE: dict[str, tuple[float, list[SearchRow]]] = {}


def _records_fingerprint(root: Path) -> float:
    latest = 0.0
    for subdir in ("changes", "decisions", "requirements", "bugs", "digests", "theme-digests"):
        record_dir = root / ".sybermem" / subdir
        if not record_dir.is_dir():
            continue
        try:
            latest = max(latest, record_dir.stat().st_mtime)
            for path in record_dir.glob("*.md"):
                latest = max(latest, path.stat().st_mtime)
        except OSError:
            continue
    return latest


def _load_all_rows(root: Path, project_id: str, slug: str) -> list[SearchRow]:
    """Return freshly-copied parsed record rows, reusing a cached parse when unchanged.

    Callers mutate the returned rows (score/matched_fields), so we always hand out
    shallow copies of each row dict. The cache holds pristine parses keyed by the
    record directories' mtime fingerprint, making it transparent to results.
    """
    key = str(root)
    fingerprint = _records_fingerprint(root)
    cached = _ROW_CACHE.get(key)
    if cached is not None and cached[0] == fingerprint:
        pristine = cached[1]
    else:
        pristine = [_search_row(parse_record_file(rf, project_id, slug)) for rf in iter_record_files(root)]
        _ROW_CACHE[key] = (fingerprint, pristine)
    return [dict(row) for row in pristine]


def _with_retrieval_metadata(
    row: SearchRow,
    *,
    match_reason: str,
    related_digest: str = "",
    archived: bool = False,
) -> SearchRow:
    enriched = dict(row)
    metadata = derive_continuity_metadata(row, match_reason=match_reason, related_digest=related_digest, archived=archived)
    enriched["source_kind"] = metadata["source_kind"]
    enriched["authority"] = metadata["authority"]
    enriched["lifecycle"] = metadata["lifecycle"]
    enriched["freshness"] = metadata["freshness"]
    enriched["match_reason"] = metadata["match_reason"]
    enriched["related_digest"] = metadata["related_digest"]
    enriched["conflict_note"] = metadata["conflict_note"]
    enriched["summary"] = metadata["summary"]
    return enriched


def _text(row: SearchRow, key: str) -> str:
    value = row.get(key, "")
    return value if isinstance(value, str) else str(value)


def _score_input(row: SearchRow) -> dict[str, str]:
    return {key: _text(row, key) for key in ("record_id", "title", "content", "topics", "fixes", "implements", "related")}


def _search_row(row: dict[str, str]) -> SearchRow:
    converted: SearchRow = {}
    for key, value in row.items():
        converted[key] = value
    return converted


def _record_keys(row: SearchRow) -> set[str]:
    normalized = _text(row, "path").replace("\\", "/")
    keys = {_text(row, "record_id"), Path(normalized).name}
    if "/.sybermem/" in normalized:
        keys.add(normalized.split("/.sybermem/", 1)[1])
    return {key for key in keys if key}


def _digest_coverage(rows: list[SearchRow]) -> dict[str, str]:
    coverage: dict[str, str] = {}
    for row in rows:
        if classify_source_kind(_text(row, "path"), _text(row, "title"), _text(row, "content")) != "digest":
            continue
        digest_id = _text(row, "record_id")
        in_sources = False
        for line in _text(row, "content").splitlines():
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


def _related_digest(row: SearchRow, coverage: dict[str, str]) -> str:
    for key in _record_keys(row):
        if key in coverage:
            return coverage[key]
    return ""


def _archived_record_ids(root: Path) -> set[str]:
    index = root / ".sybermem" / "INDEX.md"
    if not index.is_file():
        return set()
    archived: set[str] = set()
    in_archived = False
    for line in index.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_archived = stripped == "## Archived Conclusions"
            continue
        if not in_archived:
            continue
        if stripped.startswith("- [") and "]" in stripped:
            archived.add(stripped.split("[", 1)[1].split("]", 1)[0])
    return archived


def _annotate_conflicts(rows: list[SearchRow]) -> None:
    related_authoritative_ranks: dict[str, int] = {}
    for row in rows:
        if row.get("authority") != "authoritative":
            continue
        for digest_id in _related_digest_ids(row):
            related_authoritative_ranks[digest_id] = max(related_authoritative_ranks.get(digest_id, 0), _created_rank(row))
    for row in rows:
        digest_id = _text(row, "record_id")
        if row.get("source_kind") == "digest" and related_authoritative_ranks.get(digest_id, 0) > _created_rank(row):
            row["freshness"] = "stale"
            row["conflict_note"] = "historical digest; newer authoritative record exists"
    equal_strength: dict[tuple[str, str, str, int], int] = {}
    for row in rows:
        if _text(row, "authority") != "authoritative" or _text(row, "freshness") != "current":
            continue
        key = (_text(row, "authority"), _text(row, "freshness"), str(row.get("score", "")), _created_rank(row))
        equal_strength[key] = equal_strength.get(key, 0) + 1
    for row in rows:
        key = (_text(row, "authority"), _text(row, "freshness"), str(row.get("score", "")), _created_rank(row))
        if equal_strength.get(key, 0) > 1 and not row.get("conflict_note"):
            row["freshness"] = "conflicted"
            row["conflict_note"] = "parallel authoritative records match; review before relying on either"


def _match_type(query: str, row: SearchRow, terms: QueryTerms) -> str:
    q = query.lower().strip()
    record_id = _text(row, "record_id").lower()
    if record_id and record_id in q:
        return "record-id"
    relation_text = f"{_text(row, 'fixes')} {_text(row, 'implements')} {_text(row, 'related')}".lower()
    if any(term in relation_text for term in terms.all):
        return "relation"
    topics = _text(row, "topics").lower()
    if any(term in topics for term in terms.all):
        return "topic"
    return "keyword"


def _created_rank(row: SearchRow) -> int:
    created = _text(row, "created_at")
    return int(created.replace("-", "")) if created else 0


def _related_digest_ids(row: SearchRow) -> set[str]:
    ids = {value for value in (_text(row, "related_digest"),) if value}
    for field in ("fixes", "implements", "related"):
        ids.update(part for part in _text(row, field).replace(",", " ").split() if part.startswith("digest-"))
    return ids


def _compact_match_allowed(score: float, match: str, matched_fields: int) -> bool:
    return match in {"record-id", "relation"} or (score >= 5 and matched_fields >= 2)


def search_project(query: str) -> list[SearchRow]:
    root = resolve_project_root()
    if root is None:
        raise ProjectRootNotFoundError()
    meta = parse_project_yaml(root)
    project_id = meta.get("project_id", "")
    slug = meta.get("slug", root.name)
    results: list[SearchRow] = []
    q = query.lower()
    terms = query_terms(query)
    all_rows = _load_all_rows(root, project_id, slug)
    digest_coverage = _digest_coverage(all_rows)
    archived_ids = _archived_record_ids(root)
    guidance_rows = [_with_retrieval_metadata(row, match_reason="", related_digest=_related_digest(row, digest_coverage), archived=_text(row, "record_id") in archived_ids) for row in all_rows]
    for row in all_rows:
        if not terms.all and _text(row, "record_id").lower() != q:
            continue
        haystack = f"{_text(row, 'record_id')} {_text(row, 'title')} {_text(row, 'content')} {_text(row, 'topics')} {_text(row, 'fixes')} {_text(row, 'implements')} {_text(row, 'related')}".lower()
        if q in haystack:
            row["score"] = 100.0 if _text(row, "record_id").lower() == q else 10.0
            row["matched_fields"] = "1" if _text(row, "record_id").lower() == q else "2"
            match = _match_type(query, row, terms)
            enriched = _with_retrieval_metadata(row, match_reason=match, related_digest=_related_digest(row, digest_coverage), archived=_text(row, "record_id") in archived_ids)
            enriched["match"] = match
            results.append(enriched)
            continue
        overlap = score_row(_score_input(row), terms)
        if overlap is not None:
            row["score"] = overlap.score
            row["matched_fields"] = str(overlap.matched_fields)
            enriched = _with_retrieval_metadata(row, match_reason=overlap.match, related_digest=_related_digest(row, digest_coverage), archived=_text(row, "record_id") in archived_ids)
            enriched["match"] = overlap.match
            results.append(enriched)
    apply_successor_guidance(results, guidance_rows)
    _annotate_conflicts(results)
    return results


def compact_project_search(query: str, limit: int = 3, *, include_abstention: bool = False) -> list[SearchRow]:
    try:
        rows = search_project(query)
    except ProjectRootNotFoundError:
        # Hot-path hook caller: degrade silently when outside a project root.
        return []
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

        fallback_rows: list[SearchRow] = []
        all_rows = _load_all_rows(root, project_id, slug)
        digest_coverage = _digest_coverage(all_rows)
        archived_ids = _archived_record_ids(root)
        for row in all_rows:
            overlap = score_row(_score_input(row), terms)
            if overlap is not None and _compact_match_allowed(overlap.score, overlap.match, overlap.matched_fields):
                row["score"] = overlap.score
                row["matched_fields"] = str(overlap.matched_fields)
                enriched = _with_retrieval_metadata(row, match_reason=overlap.match, related_digest=_related_digest(row, digest_coverage), archived=_text(row, "record_id") in archived_ids)
                enriched["match"] = overlap.match
                fallback_rows.append(enriched)
        rows = fallback_rows

    candidates = rows
    rows = [row for row in rows if _text(row, "authority") != "evidence" and _compact_match_allowed(float(row.get("score", 0.0) or 0.0), _text(row, "match"), int(_text(row, "matched_fields") or "0"))]
    has_current = any(_text(row, "freshness") in {"current", "conflicted"} for row in rows)
    if not has_current:
        rows = []
    _annotate_conflicts(rows)
    if not rows and include_abstention and candidates:
        return [compact_abstention_row(query, candidates)]

    def score(row: SearchRow) -> tuple[int, int, int, int]:
        authority_rank = {"authoritative": 0, "summarized": 1, "evidence": 2}.get(_text(row, "authority") or "summarized", 3)
        freshness_rank = {"current": 0, "historical": 1, "stale": 2}.get(_text(row, "freshness") or "historical", 3)
        match_rank = -int(float(row.get("score", 0.0) or 0.0))
        created_rank = -_created_rank(row)
        return (authority_rank, freshness_rank, match_rank, created_rank)

    rows.sort(key=score)
    return rows[:limit]
