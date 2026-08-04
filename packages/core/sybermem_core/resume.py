from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Literal, TypedDict

from . import next_step_router
from .publish import latest_phase_digest, latest_theme_digest
from .records import iter_record_files, parse_project_yaml, parse_record_file
from .retrieval import classify_authority, derive_summary
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

    checkpoint = {
        "mode": mode,
        "project": _project_identity(root),
        "active_phase": status["phase"],
        "progress": progress,
        "risks": _risk_summary(signals) if mode != "fast" else [],
        "next_action": next_action,
        "confidence": confidence,
        "freshness": freshness,
        "recommendation_reason": next_action["reason"],
    }
    if mode in {"standard", "deep"}:
        checkpoint["digest_coverage"] = _digest_coverage(signals)
    if mode == "deep":
        checkpoint["read_targets"] = _read_targets(root, progress, signals)
    return checkpoint


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
    phase_state = _phase_state(root)
    return ResumeSignals(
        phase_state=phase_state,
        phase_digest_path=latest_phase_digest(root),
        theme_digest_path=latest_theme_digest(root),
        open_bugs=list(status["open_bugs"]),
        open_requirements=list(status["open_requirements"]),
    )


def _phase_state(root: Path) -> str:
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
        source_kind = _source_kind(record["path"])
        authority = classify_authority(source_kind, record["title"], record["content"])
        if authority == "evidence":
            continue
        records.append((record.get("created_at", ""), _source_priority(source_kind), record["path"], record))
    records.sort(reverse=True)
    return [_resume_item(record, include_summary=include_summary) for _, _, _, record in records[:3]]


def _source_kind(path: str) -> str:
    if "/digests/" in path or "/theme-digests/" in path:
        return "digest"
    return "manual"


def _source_priority(source_kind: str) -> int:
    if source_kind == "manual":
        return 1
    return 0


def _phase_boundary_date(text: str) -> str:
    match = re.search(r"(?m)^- last_record_boundary: .+\((\d{4}-\d{2}-\d{2})\)", text)
    return match.group(1) if match else ""


def _latest_source_date(root: Path) -> str:
    latest_date = ""
    meta = parse_project_yaml(root)
    for path in iter_record_files(root):
        record = parse_record_file(path, meta.get("project_id", ""), meta.get("slug", root.name))
        source_kind = _source_kind(record["path"])
        authority = classify_authority(source_kind, record["title"], record["content"])
        if authority == "evidence":
            continue
        latest_date = max(latest_date, record.get("created_at", ""))
    return latest_date


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
