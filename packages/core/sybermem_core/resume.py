from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from . import next_step_router
from .digest_sources import latest_phase_digest, latest_theme_digest
from .records import iter_record_files, parse_project_yaml, parse_record_file
from .retrieval import classify_authority, classify_source_kind, derive_summary
from .status import project_status, publication_readiness

ResumeMode = Literal["fast", "standard", "deep"]


class ResumeModeError(ValueError):
    """Raised when a resume checkpoint mode is not supported."""


class ResumeItem(TypedDict):
    record_id: str
    type: str
    title: str
    status: str
    freshness: str
    summary: str
    path: str


class ResumeAction(TypedDict):
    action: str
    reason: str


@dataclass(frozen=True, slots=True)
class ResumeSignals:
    phase_state: str
    phase_digest_path: str
    theme_digest_path: str
    open_bugs: list[str]
    open_requirements: list[str]


def build_resume_checkpoint(project_root: Path, mode: ResumeMode = "fast") -> dict:  # noqa: DICT_OK
    """Build a bounded, read-only current-state resume checkpoint."""
    if mode not in {"fast", "standard", "deep"}:
        raise ResumeModeError(mode)

    root = project_root.resolve()
    if not (root / ".sybermem").is_dir():
        return _empty_checkpoint(root, mode)

    status = project_status(root)
    signals = _resume_signals(root, status)
    readiness = publication_readiness(root)
    next_action = next_step_router.recommend_next_step_read_only(
        root,
        status=status,
        readiness=readiness,
        phase_digest=signals.phase_digest_path,
        theme_digest=signals.theme_digest_path,
        phase_state=signals.phase_state,
    )
    progress = _recent_authoritative_progress(root, include_summary=mode != "deep")
    confidence = _confidence(status, signals)
    freshness = _freshness(status, signals)

    risks = _risk_summary(signals) if mode != "fast" else []
    checkpoint = {
        "mode": mode,
        "project": _project_identity(root),
        "active_phase": status["phase"],
        "progress": progress,
        "risks": risks,
        "next_action": next_action,
        "confidence": confidence,
        "confidence_reasons": _confidence_reasons(status, signals),
        "freshness": freshness,
        "recommendation_reason": next_action["reason"],
        "brief": _brief(status, progress, signals, next_action, confidence, freshness),
    }
    if mode in {"standard", "deep"}:
        checkpoint["digest_coverage"] = _digest_coverage(signals)
    if mode == "deep":
        checkpoint["read_targets"] = _read_targets(root, progress, signals)
    return checkpoint


def _brief(
    status: dict,  # noqa: DICT_OK
    progress: list[ResumeItem],
    signals: ResumeSignals,
    next_action: ResumeAction,
    confidence: str,
    freshness: str,
) -> list[str]:
    """Compose a 3-4 line human-readable resume brief from existing fields (A4).

    Deterministic and read-only — a plain-language lead so `fast` resume reads like a
    briefing instead of a field dump. Structured fields remain the authoritative source.
    """
    phase = status["phase"]
    phase_label = phase.get("name") or phase.get("id") or "no active phase"
    lines = [f"You are in phase \"{phase_label}\" ({confidence} confidence, {freshness} state)."]
    if progress:
        latest = progress[0]
        lines.append(f"Most recent work: [{latest['record_id']}] {latest['title']}.")
    else:
        lines.append("No recent authoritative records yet.")
    open_items = list(signals.open_bugs) + list(signals.open_requirements)
    if open_items:
        lines.append(f"Open items to watch: {', '.join(open_items[:3])}.")
    lines.append(f"Suggested next: {next_action['action']} — {next_action['reason']}")
    return lines


def _empty_checkpoint(root: Path, mode: ResumeMode) -> dict:  # noqa: DICT_OK
    action = {
        "action": "/sybermem-init-project",
        "reason": "No SyberMem project state exists at this path.",
    }
    return {
        "mode": mode,
        "project": {"status": "no_project", "project_id": "", "slug": root.name, "path": _path(root)},
        "active_phase": {"id": "", "name": "", "lifecycle": "unknown"},
        "progress": [],
        "risks": [],
        "next_action": action,
        "confidence": "low",
        "freshness": "missing",
        "recommendation_reason": action["reason"],
    }


def _resume_signals(root: Path, status: dict) -> ResumeSignals:  # noqa: DICT_OK
    phase_state = next_step_router.compute_phase_state(root)
    return ResumeSignals(
        phase_state=phase_state,
        phase_digest_path=latest_phase_digest(root),
        theme_digest_path=latest_theme_digest(root),
        open_bugs=list(status["open_bugs"]),
        open_requirements=list(status["open_requirements"]),
    )


def _project_identity(root: Path) -> dict[str, str]:
    meta = parse_project_yaml(root)
    return {
        "project_id": meta.get("project_id", ""),
        "slug": meta.get("slug", root.name),
        "path": _path(root),
    }


def _recent_authoritative_progress(root: Path, *, include_summary: bool) -> list[ResumeItem]:
    records = []
    meta = parse_project_yaml(root)
    for path in iter_record_files(root):
        record = parse_record_file(path, meta.get("project_id", ""), meta.get("slug", root.name))
        source_kind = classify_source_kind(record["path"], record["title"], record["content"], declared=record.get("source_kind", ""))
        authority = classify_authority(source_kind, record["title"], record["content"], declared=record.get("authority", ""))
        if authority == "evidence":
            continue
        records.append(record)
    # Deterministic recency ordering. `date` is date-only (YYYY-MM-DD), so multiple
    # records on the same day would otherwise order arbitrarily. A stable identity
    # tiebreak (record_id then normalized path) makes same-day ordering reproducible
    # across clones/checkouts — deliberately NOT file mtime, which is not a durable
    # project-memory fact. Manual records still outrank generated ones on the same day.
    records.sort(key=_progress_sort_key, reverse=True)
    return [_resume_item(record, include_summary=include_summary) for record in records[:3]]


def _progress_sort_key(record: dict[str, str]) -> tuple[str, int, str, str]:
    source_kind = classify_source_kind(
        record["path"], record["title"], record["content"], declared=record.get("source_kind", "")
    )
    return (
        record.get("created_at", ""),
        _source_priority(source_kind),
        record.get("record_id", ""),
        record.get("path", ""),
    )


def _source_priority(source_kind: str) -> int:
    if source_kind == "manual":
        return 1
    return 0


def _resume_item(record: dict[str, str], *, include_summary: bool) -> ResumeItem:
    item: ResumeItem = {
        "record_id": record["record_id"],
        "type": record["type"],
        "title": record["title"],
        "status": record["status"],
        "freshness": "current" if record["status"] not in {"resolved", "completed"} else "historical",
        "summary": "",
        "path": record["path"],
    }
    if include_summary:
        item["summary"] = derive_summary(record["content"], record["title"])
    return item


def _risk_summary(signals: ResumeSignals) -> list[dict[str, str]]:
    risks = [{"kind": "open_bug", "record_id": record_id} for record_id in signals.open_bugs[:3]]
    if risks:
        return risks
    return [{"kind": "open_requirement", "record_id": record_id} for record_id in signals.open_requirements[:3]]


def _digest_coverage(signals: ResumeSignals) -> dict[str, str]:
    return {
        "phase_digest": _record_id_from_path(signals.phase_digest_path),
        "theme_digest": _record_id_from_path(signals.theme_digest_path),
    }


def _read_targets(root: Path, progress: list[ResumeItem], signals: ResumeSignals) -> list[str]:
    targets = []
    phase_index = root / ".sybermem" / "analysis" / "phase-index.md"
    if phase_index.is_file():
        targets.append(_relative_path(root, phase_index))
    for item in progress:
        targets.append(_relative_path(root, Path(item["path"])))
    for digest_path in [signals.phase_digest_path, signals.theme_digest_path]:
        if digest_path:
            targets.append(_relative_path(root, Path(digest_path)))
    return list(dict.fromkeys(targets))[:8]


def _confidence(status: dict, signals: ResumeSignals) -> str:  # noqa: DICT_OK
    if signals.phase_state != "current":
        return "low"
    if not status["phase"].get("id"):
        return "medium"
    if signals.open_bugs or signals.open_requirements:
        return "medium"
    return "high"


def _confidence_reasons(status: dict, signals: ResumeSignals) -> list[str]:  # noqa: DICT_OK
    """Explain the confidence label without expanding the 3-level enum (Oracle P2).

    The label stays low|medium|high (a finer scale would be false precision for an
    AI consumer). These deterministic reason strings expose the drivers behind it so
    a consumer can see *why* confidence is what it is.
    """
    reasons: list[str] = []
    if signals.phase_state == "current":
        reasons.append("phase index is current")
    elif signals.phase_state == "missing":
        reasons.append("phase index is missing")
    else:
        reasons.append("phase index is stale")
    reasons.append("active phase id present" if status["phase"].get("id") else "no active phase id")
    reasons.append(f"{len(signals.open_bugs)} open bugs")
    reasons.append(f"{len(signals.open_requirements)} open requirements")
    return reasons


def _freshness(status: dict, signals: ResumeSignals) -> str:  # noqa: DICT_OK
    if signals.phase_state != "current":
        return "stale"
    if status["phase"].get("id"):
        return "current"
    return "partial"


def _record_id_from_path(path: str) -> str:
    if not path:
        return ""
    meta = parse_record_file(Path(path), "", "")
    return meta["record_id"]


def _relative_path(root: Path, path: Path) -> str:
    return _path(path).removeprefix(f"{_path(root)}/")


def _path(path: Path) -> str:
    return str(path).replace("\\", "/")
