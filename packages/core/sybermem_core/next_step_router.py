from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json
import re
import subprocess

from .project import read_team_from_project_yaml
from .status import project_status, publication_readiness
from .publish import latest_phase_digest, latest_theme_digest
from .record_intent import RecordCandidate, classify_record_intent, route_record_candidate


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
    status = project_status(root)
    readiness = publication_readiness(root)
    phase_digest = latest_phase_digest(root)
    theme_digest = latest_theme_digest(root)

    first_pass = recommend_next_step_read_only(
        root,
        status=status,
        readiness=readiness,
        phase_digest=phase_digest,
        theme_digest=theme_digest,
    )
    if first_pass["action"] == "/sybermem-phase-analyze":
        return first_pass

    return recommend_next_step_read_only(
        root,
        status=status,
        readiness=readiness,
        phase_digest=phase_digest,
        theme_digest=theme_digest,
        commit_gap=_count_commits_since_last_record(root),
    )


def recommend_next_step_read_only(
    root: Path,
    *,
    status: dict | None = None,
    readiness: dict | None = None,
    phase_digest: str | None = None,
    theme_digest: str | None = None,
    commit_gap: int | None = None,
    phase_state: str | None = None,
    record_candidate: RecordCandidate | None = None,
) -> dict[str, str]:
    status = status or project_status(root)
    readiness = readiness or publication_readiness(root)
    phase_digest = latest_phase_digest(root) if phase_digest is None else phase_digest
    theme_digest = latest_theme_digest(root) if theme_digest is None else theme_digest
    team = read_team_from_project_yaml(root)

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

    # 1) record > digest > team-publish
    if record_candidate is not None:
        routed_candidate = route_record_candidate(record_candidate)
        return routed_candidate

    # Only recommend record if there is unrecorded work (commit gap), not just because records exist
    if commit_gap is not None and commit_gap >= 3 and not phase_digest and not theme_digest:
        return {
            "action": "/sybermem-record",
            "reason": f"There are {commit_gap} commits since the last record. Consider creating a durable record for this round of work."
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
