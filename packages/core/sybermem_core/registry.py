from __future__ import annotations

from pathlib import Path
from .identity import git_remote, now_iso
from .storage import ensure_dir


def hub_registry_path() -> Path:
    return Path.home() / ".sybermem" / "projects.yaml"


def register_project(project_id: str, slug: str, root: Path) -> None:
    path = hub_registry_path()
    ensure_dir(path.parent)
    projects: list[dict[str, str]] = []
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
        current: dict[str, str] | None = None
        for line in lines:
            if line.startswith("  - project_id:"):
                if current:
                    projects.append(current)
                current = {"project_id": line.split(":",1)[1].strip()}
            elif current is not None and line.startswith("    slug:"):
                current["slug"] = line.split(":",1)[1].strip()
            elif current is not None and line.startswith("    path:"):
                current["path"] = line.split(":",1)[1].strip()
            elif current is not None and line.startswith("    remote:"):
                current["remote"] = line.split(":",1)[1].strip()
            elif current is not None and line.startswith("    registered_at:"):
                current["registered_at"] = line.split(":",1)[1].strip()
        if current:
            projects.append(current)

    updated = False
    for p in projects:
        if p.get("project_id") == project_id:
            p["path"] = str(root).replace('\\', '/')
            p["slug"] = slug
            p["remote"] = git_remote(root)
            updated = True
            break
    if not updated:
        projects.append({
            "project_id": project_id,
            "slug": slug,
            "path": str(root).replace('\\', '/'),
            "remote": git_remote(root),
            "registered_at": now_iso(),
        })

    lines = ["schema_version: 1", "projects:"]
    for p in projects:
        lines.extend([
            f"  - project_id: {p['project_id']}",
            f"    slug: {p['slug']}",
            f"    path: {p['path']}",
            f"    remote: {p.get('remote', '')}",
            f"    registered_at: {p.get('registered_at', now_iso())}",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
