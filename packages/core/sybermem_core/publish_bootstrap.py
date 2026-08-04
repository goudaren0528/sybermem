from __future__ import annotations

from pathlib import Path

from .project import resolve_project_root, ensure_project_yaml, is_sybermem_project, read_team_from_project_yaml
from .registry import register_project
from .team import is_valid_team_repo
from .publish import publish_status, publish_status_preview


def bootstrap_publish_status(
    team_path: Path | None = None,
    *,
    preview: bool = False,
    preview_source_hash: str | None = None,
) -> dict[str, object]:
    invoked_path = Path.cwd().resolve()
    root = resolve_project_root()
    if root is None:
        if preview:
            return {
                "status": "blocked",
                "reason": "no_project",
                "project": {"path": str(invoked_path).replace('\\', '/')},
                "review_required": False,
            }
        raise ValueError(
            "Current directory is not initialized for SyberMem. "
            "Run `/sybermem-init-project` first so the project can be published to Team memory."
        )

    if not is_sybermem_project(root):
        if preview:
            return {
                "status": "blocked",
                "reason": "no_sybermem_project",
                "project": {"path": str(root).replace('\\', '/')},
                "review_required": False,
            }
        raise ValueError(
            "Current project has no `.sybermem/` directory. "
            "Run `/sybermem-init-project` first so the project can be published to Team memory."
        )

    if preview and not (root / ".sybermem" / "project.yaml").is_file():
        return {
            "status": "blocked",
            "reason": "missing_project_identity",
            "project": {"path": str(invoked_path).replace('\\', '/')},
            "review_required": False,
        }

    status, project_id, slug = ensure_project_yaml(root)
    if status == "created":
        register_project(project_id, slug, root)

    saved_team = read_team_from_project_yaml(root)
    if team_path is None and saved_team.get("team_path"):
        team_path = Path(saved_team["team_path"])

    if team_path is None:
        raise ValueError(
            "No Team association found for this project. "
            "Run `sybermem publish status --team-path <path>` once to set it, "
            "or initialize a Team repo with `sybermem team init`."
        )

    team_root = team_path.resolve()
    if not team_root.exists():
        raise ValueError(
            f"Team repo path does not exist: {team_root}. "
            "Initialize it first with `sybermem team init` or provide a valid existing Team repo path."
        )

    if not is_valid_team_repo(team_root):
        raise ValueError(
            f"Path exists but is not a valid Team repo: {team_root}. "
            "A valid Team repo needs both `.git/` and `team.yaml`."
        )

    if preview:
        return publish_status_preview(team_root)
    return publish_status(team_root, preview_source_hash=preview_source_hash)
