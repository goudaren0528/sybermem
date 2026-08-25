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
        project_id = next((l.split(":", 1)[1].strip() for l in text.splitlines() if l.startswith("project_id:")), "")
        slug = next((l.split(":", 1)[1].strip() for l in text.splitlines() if l.startswith("slug:")), root.name)
        return ("existing", project_id, slug)
    project_id = generate_project_id()
    slug = derive_slug(root)
    proj.write_text(render_project_yaml(project_id, slug, root), encoding="utf-8")
    return ("created", project_id, slug)


def is_sybermem_project(root: Path) -> bool:
    return (root / ".sybermem").is_dir()
