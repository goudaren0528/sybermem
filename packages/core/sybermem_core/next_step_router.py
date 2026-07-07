from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json

from .project import read_team_from_project_yaml
from .status import project_status, publication_readiness
from .publish import latest_phase_digest, latest_theme_digest


def recommend_next_step(root: Path) -> dict[str, str]:
    status = project_status(root)
    readiness = publication_readiness(root)
    team = read_team_from_project_yaml(root)

    phase_digest = latest_phase_digest(root)
    theme_digest = latest_theme_digest(root)

    # 1) record > digest > team-publish
    if readiness["record_count"] >= 1 and not phase_digest and not theme_digest:
        return {
            "action": "/sybermem-record",
            "reason": "This round has meaningful project changes, but no durable manual record exists yet."
        }

    if readiness["enough_material"] and not phase_digest:
        return {
            "action": "/sybermem-digest",
            "reason": "The current project has enough material for a phase digest, but no digest exists yet."
        }

    if team.get("team_path"):
        team_root = Path(team["team_path"])
        meta_path = team_root / "projects" / status["slug"] / "meta.json"
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            published_at = meta.get("published_at", "")
            if published_at:
                try:
                    published_dt = datetime.fromisoformat(published_at)
                    if datetime.fromisoformat(status["as_of"]) - published_dt > timedelta(days=2):
                        return {
                            "action": "/sybermem-team-publish",
                            "reason": "This project has a Team association but has not been published to Team memory recently."
                        }
                except Exception:
                    pass
        else:
            return {
                "action": "/sybermem-team-publish",
                "reason": "This project is linked to Team memory but has not been published there yet."
            }

    return {
        "action": "/sybermem-summary",
        "reason": "Project memory is in a healthy state; review the current summary for context."
    }
