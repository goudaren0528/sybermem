from __future__ import annotations

from pathlib import Path
from .digest_governance import digest_backlog
from .records import iter_record_files, parse_record_file
from .registry import load_registry
from .status import project_status


# Read-only cross-project portfolio built from the Hub registry. This is the sanctioned
# cross-project view now that Team publication is removed: it reads each registered
# project's local .sybermem/ data (including ignored derived INDEX, status, digest
# coverage, and latest record) WITHOUT
# writing any Git state, project files, or a second aggregation repository.


def _latest_record_date(root: Path) -> str:
    latest = ""
    for path in iter_record_files(root):
        row = parse_record_file(path, "", "")
        created = row.get("created_at", "")
        if created and created > latest:
            latest = created
    return latest


def _is_sybermem_project(root: Path) -> bool:
    """Return whether *root* has the canonical project identity.

    INDEX.md is a local derived artifact and therefore must not participate in
    deciding whether a registered path is a SyberMem project.
    """
    sybermem = root / ".sybermem"
    if (sybermem / "project.yaml").is_file():
        return True
    return any((sybermem / name).is_dir() for name in (
        "changes", "decisions", "requirements", "bugs", "norms", "digests", "theme-digests",
    ))


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
                "open_bugs": 0,
                "open_requirements": 0,
                "digest_uncovered": 0,
                "latest_record_date": "",
                "reason": "path not accessible",
            })
            continue

        if not _is_sybermem_project(path):
            projects.append({
                "project_id": entry["project_id"],
                "slug": entry["slug"],
                "status": "uninitialized",
                "phase": {"id": "", "name": "", "lifecycle": ""},
                "open_bugs": 0,
                "open_requirements": 0,
                "digest_uncovered": 0,
                "latest_record_date": "",
                "reason": "no .sybermem/project.yaml or canonical record directories",
            })
            continue

        status = project_status(path)
        backlog = digest_backlog(path)
        projects.append({
            "project_id": entry["project_id"],
            "slug": entry["slug"],
            "status": entry.get("status", "active"),
            "phase": status["phase"],
            # Locally-derivable attention signals — no Team publish trust envelope,
            # no preview hash, no dashboards.
            "open_bugs": len(status.get("open_bugs", [])),
            "open_requirements": len(status.get("open_requirements", [])),
            "digest_uncovered": backlog.get("uncovered", 0),
            "latest_record_date": _latest_record_date(path),
            "index_status": "present" if (path / ".sybermem" / "INDEX.md").is_file() else "missing",
            "reason": "" if (path / ".sybermem" / "INDEX.md").is_file() else "INDEX.md missing; run sybermem project index build",
        })

    return {"projects": projects}
