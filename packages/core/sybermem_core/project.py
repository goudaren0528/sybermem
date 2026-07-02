from __future__ import annotations

from pathlib import Path
from .identity import derive_slug, generate_project_id, render_project_yaml


def resolve_project_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / ".sybermem").is_dir() and (current / ".claude" / "settings.json").is_file():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def ensure_project_yaml(root: Path) -> tuple[str, str, str]:
    proj = root / ".sybermem" / "project.yaml"
    if proj.is_file():
        text = proj.read_text(encoding="utf-8")
        project_id = next((l.split(":",1)[1].strip() for l in text.splitlines() if l.startswith("project_id:")), "")
        slug = next((l.split(":",1)[1].strip() for l in text.splitlines() if l.startswith("slug:")), root.name)
        return ("existing", project_id, slug)
    project_id = generate_project_id()
    slug = derive_slug(root)
    proj.write_text(render_project_yaml(project_id, slug, root), encoding="utf-8")
    return ("created", project_id, slug)


def read_team_from_project_yaml(root: Path) -> dict[str, str]:
    yaml_path = root / ".sybermem" / "project.yaml"
    if not yaml_path.is_file():
        return {}
    team_id = ""
    team_path = ""
    in_team = False
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        if line.rstrip() == "team:":
            in_team = True
            continue
        if in_team and line.startswith("  team_id:"):
            team_id = line.split(":", 1)[1].strip()
        elif in_team and line.startswith("  team_path:"):
            team_path = line.split(":", 1)[1].strip()
        elif not line.startswith(" ") and not line.startswith("\t"):
            in_team = False
    return {"team_id": team_id, "team_path": team_path}


def write_team_to_project_yaml(root: Path, team_id: str, team_path: str) -> None:
    yaml_path = root / ".sybermem" / "project.yaml"
    if not yaml_path.is_file():
        return
    text = yaml_path.read_text(encoding="utf-8")

    # Remove existing team block if present
    lines = text.splitlines()
    new_lines = []
    skip = False
    for line in lines:
        if line.rstrip() == "team:":
            skip = True
            continue
        if skip and (line.startswith("  ") or line.startswith("\t")):
            continue
        skip = False
        new_lines.append(line)

    # Append team block
    new_lines.append("team:")
    new_lines.append(f"  team_id: {team_id}")
    new_lines.append(f"  team_path: {team_path}")

    yaml_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
