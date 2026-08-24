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


_MAX_STATEMENT_CHARS: Final = 300


def _statement(row: dict) -> str:
    # Prefer key_conclusion (the norm template maps the imperative statement there);
    # fall back to the title so a norm is never rendered empty. Bounded so an oversized
    # frontmatter value can never inject unbounded authoritative text into a prompt.
    raw = (row.get("key_conclusion") or row.get("title") or "").strip()
    normalized = " ".join(raw.split())
    if len(normalized) <= _MAX_STATEMENT_CHARS:
        return normalized
    return normalized[: _MAX_STATEMENT_CHARS - 3].rstrip() + "..."


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
    capped at min(limit, CONSTITUTION_MAX) so a caller can never widen past the hard cap
    (the constitution must stay a scarce, high-signal layer).
    """
    effective = max(0, min(limit, CONSTITUTION_MAX))
    globals_only = [n for n in active_norms(root) if _is_global(n["scope"])]
    globals_only.sort(key=lambda n: n["record_id"])
    return globals_only[:effective]


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


# Generic tokens that carry no relevance signal on their own — mostly CJK imperative /
# filler bigrams and common English words. A norm must NOT surface just because a prompt
# shares these. Mirrors the habit subsystem's stopword hardening.
_STOP_TERMS: Final = frozenset({
    "must", "should", "always", "never", "avoid", "use", "the", "and", "for", "with",
    "必须", "禁止", "不得", "不能", "一律", "总是", "应当", "务必", "严禁", "避免",
    "使用", "项目", "处理", "进行", "需要", "可以", "一个", "这个", "我们", "以及",
})


def _terms(value: str) -> set[str]:
    terms: set[str] = set()
    for term in re.findall(r"[\w-]+", value):
        if not term.strip():
            continue
        if _CJK_RE.search(term):
            # Mixed run like "auth认证": keep ASCII sub-runs (so English scope/statement
            # tokens still match) and drop the CJK blob (grams are emitted below).
            for ascii_run in re.findall(r"[0-9a-zA-Z_-]+", term):
                terms.add(ascii_run.lower())
        else:
            terms.add(term.lower())
    for run in re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", value):
        for i in range(len(run)):
            if i + 1 < len(run):
                terms.add(run[i : i + 2])  # CJK bigram
    return terms


def _strong_terms(value: str) -> set[str]:
    # Terms strong enough to establish relevance: multi-character, not a stopword. A single
    # CJK char or a common filler word is too weak to surface an unrelated norm.
    return {t for t in _terms(value) if len(t) >= 2 and t not in _STOP_TERMS}


def _scope_matches_context(scope: str, context_terms: set[str]) -> bool:
    # A scope like "topic:auth" / "path:packages/core/**" / "tool:pnpm" matches when its
    # payload tokens intersect the context terms (exact token), OR a scope token appears as
    # a substring of a context token (so "auth" matches "authentication"). Global scopes
    # are handled by the constitution lane, not here.
    if _is_global(scope):
        return False
    scope_terms = _terms(scope.replace(":", " ").replace("/", " ").replace("*", " "))
    scope_terms -= {"topic", "path", "tool", "toolchain"}
    scope_terms = {t for t in scope_terms if len(t) >= 2}
    if scope_terms & context_terms:
        return True
    # Substring alias: a short scope token contained in a longer context token.
    return any(len(s) >= 3 and any(s in c for c in context_terms) for s in scope_terms)


def scoped_norms(root: Path, context: str, *, limit: int = CONSTITUTION_MAX) -> list[Norm]:
    """Return active NON-global norms relevant to the current context.

    Relevance: a scope-tag match (strong), or >=SCOPED_RELEVANCE_MIN distinct STRONG
    statement overlaps (multi-char, non-stopword) with the context. Keeps norms context-
    scoped without touching the ordinary recall high-signal gate, and — like the habit
    subsystem — a single common token or CJK filler bigram is never enough to surface an
    unrelated norm.
    """
    context_terms = _terms(context)
    if not context_terms:
        return []
    context_strong = {t for t in context_terms if len(t) >= 2 and t not in _STOP_TERMS}
    scored: list[tuple[int, Norm]] = []
    for norm in active_norms(root):
        if _is_global(norm["scope"]):
            continue
        scope_match = _scope_matches_context(norm["scope"], context_terms)
        strong_overlap = len(_strong_terms(norm["statement"]).intersection(context_strong))
        if scope_match:
            scored.append((100 + strong_overlap, norm))
        elif strong_overlap >= SCOPED_RELEVANCE_MIN:
            scored.append((strong_overlap, norm))
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


# Same-scope conflict detection (P2 governance): two ACTIVE norms in the same scope with
# high statement overlap are a likely contradiction/duplication that should be resolved
# (supersede one, or reword scopes). This is advisory — it never edits or deactivates a
# norm; it just surfaces the pair for the user to resolve.
CONFLICT_OVERLAP_MIN: Final = 0.5


class NormConflict(TypedDict):
    scope: str
    norms: list[str]  # conflicting active norm ids in the same scope
    reason: str


def _scope_key(scope: str) -> str:
    return ",".join(sorted(t.strip().lower() for t in scope.split(",") if t.strip()))


def norm_conflicts(root: Path) -> list[NormConflict]:
    """Return pairs/groups of active norms in the same scope with high statement overlap."""
    active = active_norms(root)
    by_scope: dict[str, list[Norm]] = {}
    for norm in active:
        by_scope.setdefault(_scope_key(norm["scope"]), []).append(norm)
    conflicts: list[NormConflict] = []
    for scope_key, group in by_scope.items():
        if len(group) < 2:
            continue
        # Cluster within the scope by statement token overlap.
        clustered: list[dict] = []
        for norm in group:
            terms = _terms(norm["statement"])
            placed = False
            for cluster in clustered:
                if terms and len(cluster["terms"] & terms) / max(len(terms), 1) >= CONFLICT_OVERLAP_MIN:
                    cluster["ids"].append(norm["record_id"])
                    cluster["terms"] |= terms
                    placed = True
                    break
            if not placed:
                clustered.append({"ids": [norm["record_id"]], "terms": set(terms)})
        for cluster in clustered:
            if len(cluster["ids"]) >= 2:
                conflicts.append({
                    "scope": scope_key or "unscoped",
                    "norms": sorted(cluster["ids"]),
                    "reason": "Multiple active norms in the same scope with overlapping statements — supersede one or narrow their scopes.",
                })
    conflicts.sort(key=lambda c: (c["scope"], c["norms"]))
    return conflicts
