from __future__ import annotations

from pathlib import Path
from .registry import load_registry
from .status import project_status


def build_portfolio() -> dict:
    projects = []
    for entry in load_registry():
        path = Path(entry["path"])
        if not path.exists():
            projects.append({
                "project_id": entry["project_id"],
                "slug": entry["slug"],
                "status": "missing",
                "phase": {"id": "", "name": "", "lifecycle": ""},
                "reason": "path not accessible",
            })
            continue

        if (path / ".sybermem" / "INDEX.md").is_file():
            status = project_status(path)
            projects.append({
                "project_id": entry["project_id"],
                "slug": entry["slug"],
                "status": entry.get("status", "active"),
                "phase": status["phase"],
                "reason": "",
            })

    return {"projects": projects}
