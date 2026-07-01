from __future__ import annotations

from pathlib import Path
import re
from .records import parse_project_yaml, iter_record_files, parse_record_file
from .identity import now_iso


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
    open_bugs = [r["record_id"] for r in all_records if r.get("type") == "bug"]
    open_requirements = [r["record_id"] for r in all_records if r.get("type") == "requirement"]

    return {
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
