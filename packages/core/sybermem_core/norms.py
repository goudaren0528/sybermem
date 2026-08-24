from __future__ import annotations

from pathlib import Path
import re
from typing import Final, TypedDict

from .records import iter_record_files, parse_project_yaml, parse_record_file
from .retrieval import classify_lifecycle

# The constitution is a deliberately scarce, always-on layer: only active, non-conflicted,
# GLOBAL norms, capped hard so it never becomes background noise. Scoped norms are NOT in
# the constitution — they surface through context-matched recall instead.
CONSTITUTION_MAX: Final = 5
# A scoped norm needs a real overlap with the current context to surface. This mirrors the
# habit relevance idea (weighted, CJK-aware) rather than the recall high-signal floor of 12,
# because a norm statement is short. A scope-tag match is the strong signal; otherwise a
# norm needs >=2 distinct statement/topic term overlaps.
SCOPED_RELEVANCE_MIN: Final = 2

_GLOBAL_SCOPE_TOKENS: Final = frozenset({"global", "project", "all", "*"})
_CJK_RE: Final = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


class Norm(TypedDict):
    record_id: str
    title: str
    statement: str
    scope: str
    lifecycle: str
    path: str


def _statement(row: dict) -> str:
    # Prefer key_conclusion (the norm template maps the imperative statement there);
    # fall back to the title so a norm is never rendered empty.
    return (row.get("key_conclusion") or row.get("title") or "").strip()


def _to_norm(row: dict, lifecycle: str) -> Norm:
    return {
        "record_id": row.get("record_id", ""),
        "title": row.get("title", ""),
        "statement": _statement(row),
        "scope": (row.get("scope") or "").strip(),
        "lifecycle": lifecycle,
        "path": row.get("path", ""),
    }


def _iter_norm_rows(root: Path):
    meta = parse_project_yaml(root)
    project_id = meta.get("project_id", "")
    slug = meta.get("slug", root.name)
    for path in iter_record_files(root):
        if "/norms/" not in str(path).replace("\\", "/"):
            continue
        row = parse_record_file(path, project_id, slug)
        if row.get("type") != "norm":
            continue
        yield row


def _lifecycle_of(row: dict) -> str:
    return classify_lifecycle(
        row.get("status", ""),
        row.get("superseded_by", ""),
        "[archived]" in row.get("content", ""),
        declared=row.get("lifecycle", ""),
    )


def _is_global(scope: str) -> bool:
    if not scope:
        return False
    tokens = {t.strip().lower() for t in scope.split(",") if t.strip()}
    return bool(tokens & _GLOBAL_SCOPE_TOKENS)


def active_norms(root: Path) -> list[Norm]:
    """Return every active (non-superseded/archived/conflicted) norm."""
    out: list[Norm] = []
    for row in _iter_norm_rows(root):
        lifecycle = _lifecycle_of(row)
        if lifecycle == "active":
            out.append(_to_norm(row, lifecycle))
    return out


def constitution(root: Path, *, limit: int = CONSTITUTION_MAX) -> list[Norm]:
    """Return the bounded, always-on set of active GLOBAL norms (the project constitution).

    Deterministically ordered by record_id so the same session always sees the same set;
    capped at `limit` so it stays a scarce, high-signal layer rather than noise.
    """
    globals_only = [n for n in active_norms(root) if _is_global(n["scope"])]
    globals_only.sort(key=lambda n: n["record_id"])
    return globals_only[:limit]


class NormCoverage(TypedDict):
    active: int
    global_: int
    scoped: int
    constitution_used: int
    constitution_max: int


def norm_coverage(root: Path) -> NormCoverage:
    """Snapshot of norm health for memory-stats: active count, global vs scoped split,
    and how much of the bounded constitution budget is used."""
    active = active_norms(root)
    globals_ = [n for n in active if _is_global(n["scope"])]
    return {
        "active": len(active),
        "global_": len(globals_),
        "scoped": len(active) - len(globals_),
        "constitution_used": min(len(globals_), CONSTITUTION_MAX),
        "constitution_max": CONSTITUTION_MAX,
    }


def _terms(value: str) -> set[str]:
    terms = {t.lower() for t in re.findall(r"[\w-]+", value) if t.strip()}
    terms = {t for t in terms if not _CJK_RE.search(t)}
    grams: set[str] = set()
    for run in re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", value):
        for i, ch in enumerate(run):
            if i + 1 < len(run):
                grams.add(run[i : i + 2])
    return terms | grams


def _scope_matches_context(scope: str, context_terms: set[str]) -> bool:
    # A scope like "topic:auth" / "path:packages/core/**" / "tool:pnpm" matches when its
    # payload tokens intersect the context terms. Global scopes are handled by the
    # constitution lane, not here.
    if _is_global(scope):
        return False
    scope_terms = _terms(scope.replace(":", " ").replace("/", " ").replace("*", " "))
    scope_terms -= {"topic", "path", "tool", "toolchain"}
    return bool(scope_terms & context_terms)


def scoped_norms(root: Path, context: str, *, limit: int = CONSTITUTION_MAX) -> list[Norm]:
    """Return active NON-global norms relevant to the current context.

    Relevance: a scope-tag match (strong), or >=SCOPED_RELEVANCE_MIN distinct statement/
    topic term overlaps with the context. Keeps norms context-scoped without touching the
    ordinary recall high-signal gate.
    """
    context_terms = _terms(context)
    if not context_terms:
        return []
    scored: list[tuple[int, Norm]] = []
    for norm in active_norms(root):
        if _is_global(norm["scope"]):
            continue
        scope_match = _scope_matches_context(norm["scope"], context_terms)
        overlap = len(_terms(norm["statement"]).intersection(context_terms))
        if scope_match:
            scored.append((100 + overlap, norm))
        elif overlap >= SCOPED_RELEVANCE_MIN:
            scored.append((overlap, norm))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["record_id"]))
    return [norm for _, norm in scored[:limit]]


# Emergent nomination (P1): detect constraints that RECUR across decision/requirement
# records and look like they should be crystallized into a norm. This is a CANDIDATE
# generator only — it never creates a norm; the digest/theme skills surface candidates
# for confirmation-first crystallization. Run at digest time (not the hot path).
NOMINATION_MIN_OCCURRENCES: Final = 3
_IMPERATIVE_RE: Final = re.compile(
    r"\b(must|must not|never|always|require[sd]?|do not|don't|avoid|shall|forbidden)\b|"
    r"(必须|禁止|不得|不能|一律|总是|应当|务必|严禁|避免)",
    re.IGNORECASE,
)


class NormNomination(TypedDict):
    evidence: list[str]  # record ids that expressed the recurring constraint
    occurrences: int
    sample: str  # one representative constraint sentence (bounded)
    reason: str


def _constraint_sentences(content: str) -> list[str]:
    out: list[str] = []
    for raw in re.split(r"(?<=[.!?。！？\n])", content):
        line = raw.strip()
        if not line or line.startswith(("#", "-", "|", "```")):
            continue
        if _IMPERATIVE_RE.search(line):
            out.append(line[:200])
    return out


def _covered_by_active_norm(terms: set[str], active: list[Norm]) -> bool:
    for norm in active:
        norm_terms = _terms(norm["statement"])
        if norm_terms and len(norm_terms & terms) / max(len(terms), 1) >= 0.5:
            return True
    return False


def nominate_norm_candidates(root: Path, *, min_occurrences: int = NOMINATION_MIN_OCCURRENCES) -> list[NormNomination]:
    """Return recurring-constraint candidates worth crystallizing into norms.

    Scans decision/requirement records for imperative constraint sentences, clusters them
    by token overlap, and nominates clusters seen in >= min_occurrences DISTINCT records
    that are not already covered by an active norm. Candidate-only; confirmation-first.
    """
    active = active_norms(root)
    meta = parse_project_yaml(root)
    project_id = meta.get("project_id", "")
    slug = meta.get("slug", root.name)
    # Collect (record_id, sentence, terms) for every constraint sentence.
    items: list[tuple[str, str, set[str]]] = []
    for path in iter_record_files(root):
        row = parse_record_file(path, project_id, slug)
        if row.get("type") not in {"decision", "requirement"}:
            continue
        rid = row.get("record_id", "")
        for sentence in _constraint_sentences(row.get("content", "")):
            terms = _terms(sentence)
            if len(terms) >= 3:
                items.append((rid, sentence, terms))
    # Greedy clustering by >=0.5 token overlap; require distinct records.
    clusters: list[dict] = []
    for rid, sentence, terms in items:
        placed = False
        for cluster in clusters:
            if len(cluster["terms"] & terms) / max(len(terms), 1) >= 0.5:
                cluster["records"].add(rid)
                cluster["terms"] |= terms
                placed = True
                break
        if not placed:
            clusters.append({"records": {rid}, "terms": set(terms), "sample": sentence})
    nominations: list[NormNomination] = []
    for cluster in clusters:
        if len(cluster["records"]) < min_occurrences:
            continue
        if _covered_by_active_norm(cluster["terms"], active):
            continue
        nominations.append({
            "evidence": sorted(cluster["records"]),
            "occurrences": len(cluster["records"]),
            "sample": cluster["sample"],
            "reason": f"Constraint recurred across {len(cluster['records'])} records and is not covered by an active norm; consider crystallizing a norm.",
        })
    nominations.sort(key=lambda n: (-n["occurrences"], n["sample"]))
    return nominations
