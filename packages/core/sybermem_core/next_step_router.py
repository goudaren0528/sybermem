from __future__ import annotations

from pathlib import Path
import re
import subprocess

from .records import iter_record_files, parse_project_yaml, parse_record_file
from .retrieval import classify_authority, classify_source_kind
from .digest_sources import latest_phase_digest, latest_theme_digest
from .digest_governance import digest_backlog
from .record_intent import RecordCandidate, classify_record_intent, route_record_candidate

# Uncovered-record threshold that re-recommends a digest on an ALREADY-digested project.
# Coarser than the record-gap nudge (3) because a digest compresses a whole batch; 5
# uncovered records is a meaningful accumulation worth compressing.
DIGEST_BACKLOG_THRESHOLD = 5


def _phase_boundary_date(text: str) -> str:
    match = re.search(r"(?m)^- last_record_boundary: .+\((\d{4}-\d{2}-\d{2})\)", text)
    return match.group(1) if match else ""


def _latest_source_date(root: Path) -> str:
    latest_date = ""
    meta = parse_project_yaml(root)
    for path in iter_record_files(root):
        record = parse_record_file(path, meta.get("project_id", ""), meta.get("slug", root.name))
        source_kind = classify_source_kind(record["path"], record["title"], record["content"], declared=record.get("source_kind", ""))
        authority = classify_authority(source_kind, record["title"], record["content"], declared=record.get("authority", ""))
        if authority == "evidence":
            continue
        latest_date = max(latest_date, record.get("created_at", ""))
    return latest_date


def compute_phase_state(root: Path) -> str:
    """Return "missing" | "stale" | "current" for the project phase index.

    Shared source of truth for phase freshness so the CLI `next-step` path and
    `resume` agree. Previously only `resume` computed this and passed it in, so a
    bare `sybermem next-step` could recommend a later-stage action while `resume`
    correctly steered to phase-analyze on a stale index.
    """
    phase_index = root / ".sybermem" / "analysis" / "phase-index.md"
    if not phase_index.is_file():
        return "missing"
    text = phase_index.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("- status:") and line.split(":", 1)[1].strip() == "not_yet_analyzed":
            return "stale"
    boundary_date = _phase_boundary_date(text)
    if boundary_date and _latest_source_date(root) > boundary_date:
        return "stale"
    return "current"


def _count_commits_since_last_record(root: Path) -> int:
    """Count git commits since the most recent record file date."""
    latest_date = ""
    syb = root / ".sybermem"
    for subdir in ("changes", "decisions", "requirements", "bugs"):
        d = syb / subdir
        if not d.is_dir():
            continue
        for p in d.glob("*.md"):
            m = re.match(r"(\d{4}-\d{2}-\d{2})-", p.name)
            if m and m.group(1) > latest_date:
                latest_date = m.group(1)
    if not latest_date:
        return 0
    try:
        r = subprocess.run(
            ["git", "rev-list", "--count", f"--since={latest_date}", "HEAD"],
            cwd=root, capture_output=True, text=True, check=False,
        )
        return int(r.stdout.strip()) if r.returncode == 0 else 0
    except Exception:
        return 0


def recommend_next_step(root: Path) -> dict[str, str]:
    phase_digest = latest_phase_digest(root)
    theme_digest = latest_theme_digest(root)
    # Compute phase freshness here so the CLI `next-step` path uses the same
    # phase-stale signal `resume` already passes in; otherwise the two entrypoints
    # could disagree on a stale phase index.
    phase_state = compute_phase_state(root)
    backlog = digest_backlog(root)

    first_pass = recommend_next_step_read_only(
        root,
        phase_digest=phase_digest,
        theme_digest=theme_digest,
        phase_state=phase_state,
        backlog_uncovered=backlog["uncovered"],
        backlog_total=backlog["total_records"],
    )
    if first_pass["action"] == "/sybermem-phase-analyze":
        return first_pass

    return recommend_next_step_read_only(
        root,
        phase_digest=phase_digest,
        theme_digest=theme_digest,
        phase_state=phase_state,
        commit_gap=_count_commits_since_last_record(root),
        backlog_uncovered=backlog["uncovered"],
        backlog_total=backlog["total_records"],
    )


def recommend_next_step_read_only(
    root: Path,
    *,
    phase_digest: str | None = None,
    theme_digest: str | None = None,
    commit_gap: int | None = None,
    phase_state: str | None = None,
    record_candidate: RecordCandidate | None = None,
    backlog_uncovered: int | None = None,
    backlog_total: int | None = None,
) -> dict[str, str]:
    phase_digest = latest_phase_digest(root) if phase_digest is None else phase_digest
    theme_digest = latest_theme_digest(root) if theme_digest is None else theme_digest
    if backlog_uncovered is None or backlog_total is None:
        _bl = digest_backlog(root)
        backlog_uncovered = _bl["uncovered"] if backlog_uncovered is None else backlog_uncovered
        backlog_total = _bl["total_records"] if backlog_total is None else backlog_total

    # 0) If phase-index is missing or not yet analyzed, recommend phase-analyze first
    if phase_state == "stale":
        return {
            "action": "/sybermem-phase-analyze",
            "reason": "The project phase index is stale relative to newer project memory. Run phase analysis to refresh the structural foundation."
        }
    phase_index_path = root / ".sybermem" / "analysis" / "phase-index.md"
    if phase_index_path.is_file():
        text = phase_index_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("- status:") and line.split(":", 1)[1].strip() == "not_yet_analyzed":
                return {
                    "action": "/sybermem-phase-analyze",
                    "reason": "The project phase index has not been analyzed yet. Run phase analysis to build the structural foundation."
                }
                break
    else:
        return {
            "action": "/sybermem-phase-analyze",
            "reason": "No phase index exists. Run phase analysis to build the structural foundation."
        }

    # 1) record > digest
    if record_candidate is not None:
        routed_candidate = route_record_candidate(record_candidate)
        return routed_candidate

    # Only recommend record if there is unrecorded work (commit gap), not just because records exist
    if commit_gap is not None and commit_gap >= 3 and not phase_digest and not theme_digest:
        return {
            "action": "/sybermem-record",
            "reason": f"There are {commit_gap} commits since the last record. Consider creating a durable record for this round of work."
        }

    # First digest: recommend once enough records exist to be worth compressing. This
    # uses a digest-specific threshold on total records rather than the publish-oriented
    # 'enough_material' gate — "can be published" and "should be compressed" are different
    # questions, and coupling them made the digest nudge fire on as little as one decision.
    if not phase_digest and backlog_total >= DIGEST_BACKLOG_THRESHOLD:
        return {
            "action": "/sybermem-digest",
            "reason": f"The project has {backlog_total} records and no digest yet. Consider a phase digest to compress the accumulated work."
        }

    # Re-recommend a digest on an ALREADY-digested project once enough new records have
    # accumulated that no digest covers them. This closes the gap where the "no digest
    # yet" gate above never fires again after the first digest, so a long-running project
    # could pile up dozens of uncovered records with no proactive compression signal.
    if phase_digest and backlog_uncovered >= DIGEST_BACKLOG_THRESHOLD:
        return {
            "action": "/sybermem-digest",
            "reason": f"{backlog_uncovered} records are not covered by any digest yet. Consider a new phase digest to compress the accumulated work."
        }

    return {
        "action": "/sybermem-summary",
        "reason": "Project memory is in a healthy state; review the current summary for context."
    }
