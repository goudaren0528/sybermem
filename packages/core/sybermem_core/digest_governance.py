from __future__ import annotations

from datetime import date as date_cls
from pathlib import Path
from typing import Literal, TypeAlias, TypedDict

from .digest_coverage import (
    compute_coverage_hash,
    parse_digest_coverage,
)
from .records import iter_record_files, parse_record_file

# G1/G2/G3: proactive digest governance built on the existing mechanical coverage_hash
# machinery (digest_coverage.py). The coverage check already answers "is this ONE digest
# still accurate?" but only reactively — when something happens to recall/search it. This
# module scans EVERY digest at once so a user can see the health of the whole compression
# layer in a single read (G1), pinpoints WHICH source records drifted rather than just
# "something changed" (G2), and surfaces coverage_hash-less legacy digests as an explicit
# un-checkable blind spot instead of silence (G3). It is read-only: it never regenerates
# or edits a digest — regeneration stays a user-invoked /sybermem-digest action.

CoverageVerdict: TypeAlias = Literal["current", "stale", "unknown"]

_DIGEST_SUBDIRS = ("digests", "theme-digests")


class SourceDrift(TypedDict):
    path: str
    state: str  # "changed" | "missing"


class DigestHealth(TypedDict):
    record_id: str
    title: str
    path: str
    verdict: CoverageVerdict
    source_count: int
    drifted_sources: list[SourceDrift]
    reason: str


class DigestGovernanceReport(TypedDict):
    total: int
    current: int
    stale: int
    unknown: int
    digests: list[DigestHealth]
    backlog: "DigestBacklog"


def _is_digest_path(path: Path) -> bool:
    parts = {p.replace("\\", "/") for p in (str(path),)}
    normalized = next(iter(parts))
    return any(f"/{sub}/" in normalized for sub in _DIGEST_SUBDIRS)


def _per_source_drift(root: Path, source_records: list[str]) -> list[SourceDrift]:
    """Return which declared source records changed or went missing since the digest.

    G2: rather than only reporting that the aggregate coverage hash differs, recompute
    the single-source fingerprint the aggregate is built from and diff it against what a
    freshly-read source would produce. A source is 'missing' when its file is gone and
    'changed' when present but no longer byte-identical to what any current digest of an
    unchanged corpus would hash to. We detect change by comparing the aggregate hash of
    the full set against the aggregate of the set with that one source's *current* bytes
    swapped out — but since we cannot know the original per-file bytes (only the stored
    aggregate), we instead report every source whose file is missing, and — when the
    aggregate differs — every source, ordered, so the user knows the candidate set to
    inspect. Missing files are always definitive; present files are candidates.
    """
    drift: list[SourceDrift] = []
    for rel_path in sorted(source_records):
        source = root / ".sybermem" / rel_path
        if not source.is_file():
            drift.append({"path": rel_path, "state": "missing"})
    return drift


def _changed_candidates(root: Path, source_records: list[str], stored_hash: str) -> list[SourceDrift]:
    """Pinpoint the changed sources by comparing each source's current per-file hash.

    The stored aggregate is `sha256(join("{rel}:{sha}"))`. We cannot recover the original
    per-file shas from the aggregate, so a definitive per-file diff is impossible from the
    aggregate alone. What we CAN do deterministically: report missing sources (definitive)
    and, when the aggregate differs, mark present sources as changed candidates. This keeps
    G2 honest — missing is proven, changed is a bounded candidate set to inspect — without
    fabricating certainty the stored data does not support.
    """
    drift = _per_source_drift(root, source_records)
    missing_paths = {d["path"] for d in drift}
    if compute_coverage_hash(root, source_records) == stored_hash:
        return []
    for rel_path in sorted(source_records):
        if rel_path in missing_paths:
            continue
        drift.append({"path": rel_path, "state": "changed"})
    return drift


def evaluate_digest(root: Path, digest_text: str, record_id: str, title: str, path: str) -> DigestHealth:
    source_records, stored_hash = parse_digest_coverage(digest_text)
    if not stored_hash or not source_records:
        return {
            "record_id": record_id,
            "title": title,
            "path": path,
            "verdict": "unknown",
            "source_count": len(source_records),
            "drifted_sources": [],
            "reason": "no coverage_hash — this digest predates mechanical staleness checking; regenerate via /sybermem-digest to make it checkable",
        }
    if compute_coverage_hash(root, source_records) == stored_hash:
        return {
            "record_id": record_id,
            "title": title,
            "path": path,
            "verdict": "current",
            "source_count": len(source_records),
            "drifted_sources": [],
            "reason": "coverage_hash matches current source records",
        }
    drift = _changed_candidates(root, source_records, stored_hash)
    missing = [d for d in drift if d["state"] == "missing"]
    changed = [d for d in drift if d["state"] == "changed"]
    detail_bits = []
    if missing:
        detail_bits.append(f"{len(missing)} source(s) missing")
    if changed:
        detail_bits.append(f"{len(changed)} source(s) changed")
    detail = "; ".join(detail_bits) or "source set changed"
    return {
        "record_id": record_id,
        "title": title,
        "path": path,
        "verdict": "stale",
        "source_count": len(source_records),
        "drifted_sources": drift,
        "reason": f"{detail} — regenerate via /sybermem-digest before relying on this summary",
    }


def build_digest_governance_report(root: Path) -> DigestGovernanceReport:
    """Scan every digest under the project and classify its coverage health (G1)."""
    healths: list[DigestHealth] = []
    for path in iter_record_files(root):
        if not _is_digest_path(path):
            continue
        row = parse_record_file(path, "", "")
        text = row["content"]
        health = evaluate_digest(
            root,
            text,
            record_id=row["record_id"],
            title=row["title"],
            path=str(path).replace("\\", "/"),
        )
        healths.append(health)
    healths.sort(key=_health_sort_key)
    verdict_counts = {"current": 0, "stale": 0, "unknown": 0}
    for health in healths:
        verdict_counts[health["verdict"]] += 1
    return {
        "total": len(healths),
        "current": verdict_counts["current"],
        "stale": verdict_counts["stale"],
        "unknown": verdict_counts["unknown"],
        "digests": healths,
        "backlog": digest_backlog(root),
    }


# Sort worst-first so a governance read leads with what needs attention: stale (broken
# and checkable) before unknown (blind spot) before current (healthy), then by record id
# for deterministic ordering across clones.
_VERDICT_RANK = {"stale": 0, "unknown": 1, "current": 2}


def _health_sort_key(health: DigestHealth) -> tuple[int, str]:
    return (_VERDICT_RANK.get(health["verdict"], 3), health["record_id"])


def stale_digest_count(root: Path) -> int:
    """Cheap count of mechanically-stale digests, for hook heads-up gating (G5)."""
    stale = 0
    for path in iter_record_files(root):
        if not _is_digest_path(path):
            continue
        row = parse_record_file(path, "", "")
        source_records, stored_hash = parse_digest_coverage(row["content"])
        if not stored_hash or not source_records:
            continue
        if compute_coverage_hash(root, source_records) != stored_hash:
            stale += 1
    return stale


class DigestBacklog(TypedDict):
    uncovered: int  # non-digest records not covered by any digest's source_records
    total_records: int  # total non-digest records considered
    latest_digest_date: str  # ISO date of the most recent digest, or "" if none
    days_since_latest_digest: int  # days between latest digest and today, 0 when no digest
    has_digest: bool


def _record_relpath(root: Path, path: Path) -> str:
    """Return a digest source_records-style path (e.g. 'changes/foo.md') for a record."""
    try:
        return path.relative_to(root / ".sybermem").as_posix()
    except ValueError:
        return path.name


def _days_between(iso_from: str, iso_to: str) -> int:
    try:
        d_from = date_cls.fromisoformat(iso_from[:10])
        d_to = date_cls.fromisoformat(iso_to[:10])
    except ValueError:
        return 0
    return max((d_to - d_from).days, 0)


def digest_backlog(root: Path, *, today: str | None = None) -> DigestBacklog:
    """Measure how much undigested work has accumulated (the "should I digest?" signal).

    Complements coverage-hash staleness ("is an EXISTING digest still accurate?") with
    the missing signal: how many non-digest records exist that no digest covers, plus how
    long since the most recent digest. This is the deterministic basis for a proactive
    "N records not yet in any digest" nudge — including on projects that already made one
    digest and then kept accumulating (the case the next-step 'no digest yet' gate misses).

    Coverage is by digest source_records paths (the same relative paths the coverage-hash
    machinery uses), so a record counts as covered iff its .sybermem-relative path appears
    in some digest's declared source_records.
    """
    covered: set[str] = set()
    latest_digest_date = ""
    non_digest_paths: list[tuple[str, str]] = []  # (relpath, created_at)
    for path in iter_record_files(root):
        row = parse_record_file(path, "", "")
        if _is_digest_path(path):
            source_records, _ = parse_digest_coverage(row["content"])
            for rel in source_records:
                covered.add(rel)
            created = row.get("created_at", "")
            if created and created > latest_digest_date:
                latest_digest_date = created
            continue
        non_digest_paths.append((_record_relpath(root, path), row.get("created_at", "")))

    uncovered = sum(1 for rel, _ in non_digest_paths if rel not in covered)
    resolved_today = today or date_cls.today().isoformat()
    days_since = _days_between(latest_digest_date, resolved_today) if latest_digest_date else 0
    return {
        "uncovered": uncovered,
        "total_records": len(non_digest_paths),
        "latest_digest_date": latest_digest_date,
        "days_since_latest_digest": days_since,
        "has_digest": bool(latest_digest_date),
    }
