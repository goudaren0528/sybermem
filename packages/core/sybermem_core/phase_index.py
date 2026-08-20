from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .identity import now_iso
from .records import iter_record_files, parse_project_yaml, parse_record_file


PHASE_REL: Final = Path(".sybermem") / "analysis" / "phase-index.md"


class PhaseApplyError(ValueError):
    """Raised when an agent-provided phase payload references unknown or duplicated records."""


@dataclass(frozen=True, slots=True)
class _Record:
    record_id: str
    created_at: str
    topic: str


def analyze_phases(root: Path) -> dict:
    """Deterministically group records into confirmed phases and persist the index.

    This is the fail-safe path: it never depends on an agent writing Markdown by
    hand, so a project that has records can always reach an ``analyzed`` phase
    index. Grouping uses month + primary-topic buckets — mechanical but stable.
    """
    records = _load_records(root)
    if not records:
        _write_phase_index(root, [], status="not_yet_analyzed")
        return {"status": "not_yet_analyzed", "phases": []}
    phases = _group_records(records)
    _write_phase_index(root, phases, status="analyzed")
    return {"status": "analyzed", "phases": phases}


def apply_phase_payload(root: Path, payload: dict) -> dict:
    """Persist an agent-provided semantic grouping after validating it against real records.

    This is the primary phase-analysis path: the agent (e.g. driven by
    ``/sybermem-digest``) reads the full record history and produces a higher-quality
    grouping than the mechanical ``analyze_phases`` fallback. Core validates every
    covered record exists and is covered by exactly one phase, then writes the index
    deterministically through the same canonical renderer and atomic write both paths
    use.
    """
    if not isinstance(payload, dict):
        raise PhaseApplyError("payload must be a JSON object with a 'phases' list")
    known = {rec.record_id for rec in _load_records(root)}
    raw_phases = payload.get("phases")
    if not isinstance(raw_phases, list) or not raw_phases:
        raise PhaseApplyError("payload must contain a non-empty 'phases' list")
    phases: list[dict] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_phases, start=1):
        title = str(raw.get("title", "")).strip() if isinstance(raw, dict) else ""
        if not title:
            raise PhaseApplyError(f"phase #{index} is missing a title")
        covered = raw.get("covered_records") if isinstance(raw, dict) else None
        if not isinstance(covered, list) or not covered:
            raise PhaseApplyError(f"phase '{title}' must list at least one covered record")
        records = [str(rid).strip() for rid in covered]
        for rid in records:
            if rid not in known:
                raise PhaseApplyError(f"unknown record id in phase '{title}': {rid}")
            if rid in seen:
                raise PhaseApplyError(f"record covered by more than one phase: {rid}")
            seen.add(rid)
        phases.append({"title": title, "covered_records": records})
    orphaned = sorted(known - seen)
    if orphaned:
        raise PhaseApplyError(f"payload leaves records uncovered: {', '.join(orphaned)}")
    numbered = _number_phases(phases)
    _write_phase_index(root, numbered, status="analyzed")
    return {"status": "analyzed", "phases": numbered}


def resolve_record_paths(root: Path, record_ids: list[str]) -> dict[str, str]:
    """Map each canonical record_id to its project-relative path under `.sybermem/`.

    Resolution uses each record file's frontmatter ``record_id:`` field, never the
    filename, because filenames may truncate or reshape the UUID (e.g. a 16-hex
    substring) and therefore cannot be relied on to reconstruct the canonical id.
    Returns ``{record_id: "changes/<file>.md"}``; ids with no matching record file
    are omitted so callers can distinguish missing sources by absence.
    """
    wanted = set(record_ids)
    mapping: dict[str, str] = {}
    sybermem = root / ".sybermem"
    for sub in ("changes", "decisions", "requirements", "bugs"):
        d = sybermem / sub
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.md")):
            row = parse_record_file(path, "", "")
            rid = row.get("record_id", "")
            if rid and rid in wanted:
                mapping[rid] = f"{sub}/{path.name}"
    return mapping


def _load_records(root: Path) -> list[_Record]:
    meta = parse_project_yaml(root)
    out: list[_Record] = []
    for path in iter_record_files(root):
        row = parse_record_file(path, meta.get("project_id", ""), meta.get("slug", root.name))
        record_id = row.get("record_id", "")
        if not record_id:
            continue
        topics = [t for t in row.get("topics", "").split(",") if t.strip()]
        out.append(_Record(record_id=record_id, created_at=row.get("created_at", ""), topic=topics[0].strip() if topics else ""))
    return out


def _group_records(records: list[_Record]) -> list[dict]:
    buckets: dict[tuple[str, str], list[str]] = {}
    order: list[tuple[str, str]] = []
    for rec in sorted(records, key=lambda r: (r.created_at, r.record_id)):
        month = rec.created_at[:7] if len(rec.created_at) >= 7 else "undated"
        key = (month, rec.topic)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(rec.record_id)
    phases: list[dict] = []
    for month, topic in order:
        label = f"{month} {topic}".strip() if topic else month
        phases.append({"title": f"{label} cluster", "covered_records": buckets[(month, topic)]})
    return _number_phases(phases)


def _number_phases(phases: list[dict]) -> list[dict]:
    return [
        {"phase_id": f"phase-{index:03d}", "title": phase["title"], "covered_records": list(phase["covered_records"])}
        for index, phase in enumerate(phases, start=1)
    ]


def _render_phase_index(phases: list[dict], status: str, timestamp: str) -> str:
    analysis_ts = timestamp if status == "analyzed" else "none"
    lines = [
        "# Phase Index",
        "",
        "## Analysis Progress",
        f"- status: {status}",
        f"- last_analysis_at: {analysis_ts}",
        "- last_record_boundary: none",
        "- last_git_boundary: none",
        f"- pending_new_records: {'none' if status == 'analyzed' else 'unknown_until_first_analysis'}",
        "",
        "## Phase Candidates",
        "<!-- use canonical candidate blocks: ### Candidate: <title> + candidate_id/status/covered_records/rationale/proposed_at -->",
        "",
        "## Confirmed Phases",
    ]
    if not phases:
        lines.append("<!-- when confirming the first phase, replace this comment with canonical confirmed blocks: ### Phase: <title> + phase_id/source_candidate_id/status/covered_records/confirmed_at/notes -->")
    else:
        for phase in phases:
            lines.append("")
            lines.append(f"### Phase: {phase['title']}")
            lines.append(f"- phase_id: {phase['phase_id']}")
            lines.append("- status: confirmed")
            lines.append("- lifecycle: active")
            lines.append("- covered_records:")
            for rid in phase["covered_records"]:
                lines.append(f"  - {rid}")
            lines.append(f"- confirmed_at: {timestamp[:10]}")
    lines += ["", "## Coverage Map"]
    if not phases:
        lines.append("<!-- keep exactly one Coverage Map section; replace this comment with mapping lines like `- change-001 -> phase-001` when records are assigned -->")
    else:
        for phase in phases:
            for rid in phase["covered_records"]:
                lines.append(f"- {rid} -> {phase['phase_id']}")
    return "\n".join(lines) + "\n"


def _write_phase_index(root: Path, phases: list[dict], status: str) -> None:
    target = root / PHASE_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    text = _render_phase_index(phases, status, now_iso())
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".phase-index-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, target)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
