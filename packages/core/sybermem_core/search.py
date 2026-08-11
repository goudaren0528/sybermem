from __future__ import annotations

import os
from pathlib import Path
from typing import TypeAlias

from .digest_coverage import digest_coverage_verdict
from .project import resolve_project_root
from .records import iter_record_files, parse_project_yaml, parse_record_file
from .retrieval import (
    apply_successor_guidance,
    classify_source_kind,
    compact_abstention_row,
    derive_continuity_metadata,
)
from .search_query import QueryTerms, query_terms, score_row
from .semantic_recall import semantic_scores
from .workspace_search import WorkspaceIndexIncompatibleError, search_workspace, workspace_index_staleness


# E2: opt-in semantic supplement. Off by default so the hot path keeps its current
# token/compute economy; enable per-project via SYBERMEM_SEMANTIC_RECALL=1.
SEMANTIC_RECALL_ENV: str = "SYBERMEM_SEMANTIC_RECALL"
# Cosine floor for a semantic-only supplement. Deliberately high: char n-gram cosine
# is noisy, so only strong lexical/morphological overlap earns a supplemental hit.
SEMANTIC_SIMILARITY_FLOOR: float = 0.30


def _semantic_recall_enabled() -> bool:
    return os.environ.get(SEMANTIC_RECALL_ENV, "") == "1"


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


def _annotate_digest_coverage(root: Path, rows: list[SearchRow]) -> None:
    """Mechanically flag digests whose declared source records have changed (E3).

    Only digests carrying a `coverage_hash` are checkable; legacy digests without it
    are left untouched (verdict "unknown"). A stale digest is marked historical so
    recall stops treating a drifted summary as current authoritative context.
    """
    for row in rows:
        if row.get("source_kind") != "digest":
            continue
        verdict = digest_coverage_verdict(root, _text(row, "content"))
        if verdict == "stale":
            row["freshness"] = "stale"
            if not row.get("conflict_note"):
                row["conflict_note"] = "digest source records changed after this digest was written; regenerate before relying on it"


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
    return match in {"record-id", "relation", "semantic"} or (score >= 5 and matched_fields >= 2)


def _add_semantic_supplement(query: str, lexical_rows: list[SearchRow]) -> list[SearchRow]:
    """Append semantic-only recall candidates lexical scoring missed (E2, opt-in).

    Char n-gram cosine recovers synonym-ish / rephrased / typo'd hits. Supplements are
    tagged match="semantic" with a bounded score kept below the high-signal floor, so
    they surface in explicit search but never auto-inject on the recall hot path.
    """
    root = resolve_project_root()
    if root is None:
        return lexical_rows
    meta = parse_project_yaml(root)
    project_id = meta.get("project_id", "")
    slug = meta.get("slug", root.name)
    all_rows = _load_all_rows(root, project_id, slug)
    scored = semantic_scores(query, [{"title": _text(r, "title"), "topics": _text(r, "topics"), "content": _text(r, "content")} for r in all_rows])
    if not scored:
        return lexical_rows
    seen = {_text(row, "record_id") for row in lexical_rows}
    digest_coverage = _digest_coverage(all_rows)
    archived_ids = _archived_record_ids(root)
    supplemented = list(lexical_rows)
    for index, similarity in scored:
        if similarity < SEMANTIC_SIMILARITY_FLOOR:
            break  # scored is descending; nothing further can clear the floor
        row = all_rows[index]
        record_id = _text(row, "record_id")
        if record_id in seen:
            continue
        # Map similarity in [floor, 1] to a bounded score in [5, 10) — admitted by the
        # compact gate but always below the high-signal floor (12), so never auto-injected.
        row["score"] = round(5.0 + 5.0 * min(similarity, 0.99), 3)
        row["matched_fields"] = "2"
        enriched = _with_retrieval_metadata(row, match_reason="semantic", related_digest=_related_digest(row, digest_coverage), archived=record_id in archived_ids)
        enriched["match"] = "semantic"
        supplemented.append(enriched)
        seen.add(record_id)
    return supplemented


# High-signal recall gate (E1). Automatic prompt-time injection is far more costly in
# trust than a missed hint: a wrong hint pollutes the agent's context, a missing hint
# costs nothing. So the hot-path hook injects ONLY strong matches — exact record-id,
# an explicit relation match, or a lexical score clearly above the compact floor.
# Bare keyword overlap, however current/authoritative, stays silent on the hook path;
# explicit `/sybermem-search` still surfaces it.
HIGH_SIGNAL_SCORE: TypeAlias = float
HIGH_SIGNAL_SCORE_FLOOR: HIGH_SIGNAL_SCORE = 12.0


def _is_high_signal(row: SearchRow) -> bool:
    match = _text(row, "match")
    if match in {"record-id", "relation"}:
        return True
    score = float(row.get("score", 0.0) or 0.0)
    return score >= HIGH_SIGNAL_SCORE_FLOOR


def high_signal_recall_hints(query: str, limit: int = 3) -> tuple[list[SearchRow], str]:
    """Return only high-signal recall rows for automatic prompt injection (E1).

    Returns (rows, abstention_reason). When rows is empty, abstention_reason explains
    why in one bounded phrase for local debug logging; it is never injected into the
    prompt. rows is a strict subset of compact_project_search under the high-signal gate.
    """
    rows = compact_project_search(query, limit=limit)
    high_signal = [row for row in rows if _is_high_signal(row)]
    if high_signal:
        return high_signal[:limit], ""
    if rows:
        return [], "matched rows were keyword-only and below the high-signal floor"
    diagnostic = compact_project_search(query, limit=limit, include_abstention=True)
    if diagnostic and _text(diagnostic[0], "result") == "no_reliable_recall":
        return [], _text(diagnostic[0], "reason")
    return [], "no candidate records matched the prompt"


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
    if _semantic_recall_enabled():
        results = _add_semantic_supplement(query, results)
    apply_successor_guidance(results, guidance_rows)
    _annotate_digest_coverage(root, results)
    _annotate_conflicts(results)
    results.sort(key=_explicit_sort_key)
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

    if _semantic_recall_enabled():
        rows = _add_semantic_supplement(query, rows)

    candidates = rows
    rows = [row for row in rows if _text(row, "authority") != "evidence" and _compact_match_allowed(float(row.get("score", 0.0) or 0.0), _text(row, "match"), int(_text(row, "matched_fields") or "0"))]
    has_current = any(_text(row, "freshness") in {"current", "conflicted"} for row in rows)
    if not has_current:
        rows = []
    _annotate_conflicts(rows)
    if not rows and include_abstention and candidates:
        return [compact_abstention_row(query, candidates)]

    rows.sort(key=_compact_sort_key)
    return rows[:limit]


# E5: rank by match *specificity* before freshness/recency. Authority still leads (we
# never float low-trust evidence above authoritative), but among trustworthy hits a
# precisely-matched record (exact id > relation > topic > keyword) must not be buried
# under a newer, generically-matched one. Recency is only the final tiebreak.
_MATCH_SPECIFICITY: dict[str, int] = {"record-id": 0, "relation": 1, "topic": 2, "keyword": 3}


def _compact_sort_key(row: SearchRow) -> tuple[int, int, int, int, int]:
    authority_rank = {"authoritative": 0, "summarized": 1, "evidence": 2}.get(_text(row, "authority") or "summarized", 3)
    specificity_rank = _MATCH_SPECIFICITY.get(_text(row, "match"), 4)
    freshness_rank = {"current": 0, "historical": 1, "stale": 2}.get(_text(row, "freshness") or "historical", 3)
    match_rank = -int(float(row.get("score", 0.0) or 0.0))
    created_rank = -_created_rank(row)
    return (authority_rank, specificity_rank, freshness_rank, match_rank, created_rank)


# Explicit `sybermem search` sort: unlike compact recall (which leads with trust so a
# wrong hint never outranks an authoritative one on the hot path), user-facing search
# should surface the most *relevant* record first. Rank by raw score, then match
# specificity (exact id > relation > topic > keyword), then recency as the tiebreak.
def _explicit_sort_key(row: SearchRow) -> tuple[float, int, int]:
    score_rank = -float(row.get("score", 0.0) or 0.0)
    specificity_rank = _MATCH_SPECIFICITY.get(_text(row, "match"), 4)
    created_rank = -_created_rank(row)
    return (score_rank, specificity_rank, created_rank)
