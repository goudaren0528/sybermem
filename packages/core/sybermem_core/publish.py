from __future__ import annotations

from pathlib import Path

from .project import resolve_project_root
from .records import parse_project_yaml
from .status import project_status


def render_project_card(project_meta: dict[str, str], team_id: str) -> str:
    return (
        f"# {project_meta.get('slug', '')}\n\n"
        f"- Project ID: {project_meta.get('project_id', '')}\n"
        f"- Slug: {project_meta.get('slug', '')}\n"
        f"- Name: {project_meta.get('name', project_meta.get('slug', ''))}\n"
        f"- Repository: {project_meta.get('remote', '')}\n"
        f"- Team: {team_id}\n"
        f"- Registered at: {project_meta.get('created_at', '')}\n"
    )


def render_current_status(status: dict, source_commit: str) -> str:
    phase = status["phase"]
    lines = [
        f"# {status['slug']} — Current Status",
        "",
        f"- Updated at: {status['as_of']}",
        f"- Source commit: {source_commit}",
        "",
        "## Active Phase",
        f"- {phase['id'] or '(no phase)'}{(' — ' + phase['name']) if phase['name'] else ''}",
        "",
        "## Recent Records",
    ]
    if status["recent_records"]:
        lines.extend([f"- {r}" for r in status["recent_records"]])
    else:
        lines.append("- none")

    lines.extend(["", "## Open Bugs"])
    if status["open_bugs"]:
        lines.extend([f"- {r}" for r in status["open_bugs"]])
    else:
        lines.append("- none")

    lines.extend(["", "## Open Requirements"])
    if status["open_requirements"]:
        lines.extend([f"- {r}" for r in status["open_requirements"]])
    else:
        lines.append("- none")

    lines.extend(["", "## Next"])
    if status["next"]:
        lines.extend([f"- {n}" for n in status["next"]])
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def read_team_yaml(team_root: Path) -> tuple[str, str]:
    team_yaml = team_root / "team.yaml"
    if not team_yaml.is_file():
        raise FileNotFoundError(f"Missing team.yaml in Team repo: {team_root}")
    team_id = ""
    remote = ""
    for line in team_yaml.read_text(encoding="utf-8").splitlines():
        if line.startswith("team_id:"):
            team_id = line.split(":", 1)[1].strip()
        elif line.strip().startswith("remote:"):
            remote = line.split(":", 1)[1].strip()
    return team_id, remote


def publish_status(team_path: Path) -> dict[str, object]:
    root = resolve_project_root()
    if root is None:
        raise ValueError("No SyberMem project root found.")

    team_root = team_path.resolve()
    if not team_root.exists():
        raise FileNotFoundError(f"Team repo path not found: {team_root}")
    if not (team_root / ".git").exists():
        raise ValueError(f"Path exists but is not a Team Git repo: {team_root}")

    team_id, _ = read_team_yaml(team_root)
    project_meta = parse_project_yaml(root)
    if not project_meta.get("project_id"):
        raise ValueError("Current project has no project.yaml identity. Run `sybermem project init --register` first.")

    status = project_status(root)
    slug = project_meta.get("slug", root.name)
    source_commit = project_meta.get("repository.commit", "")

    project_dir = team_root / "projects" / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    project_md = project_dir / "project.md"
    current_status_md = project_dir / "current-status.md"

    project_md.write_text(render_project_card(project_meta, team_id), encoding="utf-8")
    current_status_md.write_text(render_current_status(status, source_commit), encoding="utf-8")

    return {
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "team_path": str(team_root).replace('\\', '/'),
        "files": [
            str(project_md).replace('\\', '/'),
            str(current_status_md).replace('\\', '/'),
        ],
    }
