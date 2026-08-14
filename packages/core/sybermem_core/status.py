from __future__ import annotations

import json
from pathlib import Path
import re
from .project import project_source_snapshot, read_team_from_project_yaml
from .records import parse_project_yaml, iter_record_files, parse_record_file
from .retrieval import is_open_status
from .identity import now_iso
from .memory_stats import project_memory_stats


def publication_readiness(root: Path) -> dict:
    """Return whether the project has enough meaningful material to publish.

    Threshold (confirmed with the user): publish is allowed when ANY of these are true:
    - at least 2 records
    - at least 1 decision
    - at least 1 completed phase
    """
    all_records = [parse_record_file(p, "", root.name) for p in iter_record_files(root)]
    record_count = len(all_records)
    decision_count = sum(1 for r in all_records if r.get("type") == "decision")

    completed_phase_count = 0
    phase_path = root / ".sybermem" / "analysis" / "phase-index.md"
    if phase_path.is_file():
        for line in phase_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- lifecycle:") and line.split(":", 1)[1].strip() == "completed":
                completed_phase_count += 1

    enough_material = (
        record_count >= 2 or
        decision_count >= 1 or
        completed_phase_count >= 1
    )

    return {
        "record_count": record_count,
        "decision_count": decision_count,
        "completed_phase_count": completed_phase_count,
        "enough_material": enough_material,
    }


def project_status(root: Path) -> dict:
    meta = parse_project_yaml(root)
    phase_path = root / ".sybermem" / "analysis" / "phase-index.md"
    phase_id = ""
    phase_name = ""
    lifecycle = ""
    analysis_status = ""
    if phase_path.is_file():
        lines = phase_path.read_text(encoding="utf-8").splitlines()
        current_name = ""
        current_id = ""
        current_lifecycle = ""
        for line in lines:
            if line.startswith("- status:") and not analysis_status:
                analysis_status = line.split(":", 1)[1].strip()
            if line.startswith("### Phase: "):
                current_name = line.replace("### Phase: ", "").strip()
                current_id = ""
                current_lifecycle = ""
            elif line.startswith("- phase_id:"):
                current_id = line.split(":", 1)[1].strip()
            elif line.startswith("- lifecycle:"):
                current_lifecycle = line.split(":", 1)[1].strip()
                if current_lifecycle == "active":
                    phase_name = current_name
                    phase_id = current_id
                    lifecycle = current_lifecycle
        if not phase_name and analysis_status != "not_yet_analyzed":
            text = phase_path.read_text(encoding="utf-8")
            phases = re.findall(r"(?m)^### Phase: (.+)", text)
            if phases:
                phase_name = phases[-1]

    all_records = [parse_record_file(p, meta.get("project_id", ""), meta.get("slug", root.name)) for p in iter_record_files(root)]
    all_records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    recent_records = [r["record_id"] for r in all_records[:3] if r.get("record_id")]
    open_bugs = [r["record_id"] for r in all_records if r.get("type") == "bug" and is_open_status(r.get("status", ""))]
    open_requirements = [r["record_id"] for r in all_records if r.get("type") == "requirement" and is_open_status(r.get("status", ""))]

    status = {
        "project_id": meta.get("project_id", ""),
        "slug": meta.get("slug", root.name),
        "as_of": now_iso(),
        "phase": {
            "id": phase_id,
            "name": phase_name,
            "lifecycle": lifecycle or "active",
        },
        "recent_records": recent_records,
        "open_bugs": open_bugs,
        "open_requirements": open_requirements,
        "next": [],
    }
    preview = build_publication_preview(root, status=status)
    status["publication"] = {
        "preview": preview,
        "team": team_publication_metadata(root, status["slug"], preview=preview),
    }
    return status


def build_publication_preview(root: Path, status: dict | None = None) -> dict:
    """Build a read-only publish preview from Project canonical records and digests."""
    snapshot = project_source_snapshot(root)
    current_status = status or project_status(root)
    conflicts = []
    for record_id in current_status.get("open_bugs", []):
        conflicts.append({"kind": "open_bug", "record_id": record_id})
    for record_id in current_status.get("open_requirements", []):
        conflicts.append({"kind": "open_requirement", "record_id": record_id})

    phase = current_status.get("phase", {})
    freshness = "current"
    phase_path = root / ".sybermem" / "analysis" / "phase-index.md"
    phase_status = ""
    if phase_path.is_file():
        for line in phase_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- status:"):
                phase_status = line.split(":", 1)[1].strip()
                break
    if not phase_path.is_file() or phase_status == "not_yet_analyzed" or phase.get("lifecycle") == "not_yet_analyzed":
        freshness = "stale"
    return {
        "status": "preview",
        "source_revision": snapshot["source_revision"],
        "source_hash": snapshot["source_hash"],
        "source_scope": snapshot["source_scope"],
        "selected_records": snapshot["selected_records"],
        "selected_digests": snapshot["selected_digests"],
        "freshness": freshness,
        "conflicts": conflicts,
        "review_required": bool(snapshot["selected_records"] or snapshot["selected_digests"]),
    }


def team_publication_metadata(root: Path, slug: str, preview: dict | None = None) -> dict:
    """Return additive Team trust metadata without touching Team or Project files."""
    team = read_team_from_project_yaml(root)
    if not team.get("team_path"):
        return {}

    team_path = Path(team["team_path"])
    meta_path = team_path / "projects" / slug / "meta.json"
    preview = preview or build_publication_preview(root, status={"phase": {}, "open_bugs": [], "open_requirements": []})
    published_at = ""
    source_scope = preview["source_scope"]
    published_hash = ""
    stale = False
    conflict = bool(preview["conflicts"])
    review_required = bool(preview["review_required"])
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        published_at = meta.get("published_at", "")
        source_scope = meta.get("source_scope", source_scope)
        published_hash = meta.get("source_hash", "")
        stale = bool(meta.get("stale", False))
        conflict = bool(meta.get("conflict", conflict))
        review_required = bool(meta.get("review_required", review_required))

    local_changes = bool(published_hash and published_hash != preview["source_hash"])
    return {
        "team_id": team.get("team_id", ""),
        "team_path": str(team_path).replace("\\", "/"),
        "published_at": published_at,
        "source_scope": source_scope,
        "local_changes_after_publish": local_changes,
        "stale": stale or local_changes or preview["freshness"] == "stale",
        "conflict": conflict,
        "review_required": review_required,
    }
