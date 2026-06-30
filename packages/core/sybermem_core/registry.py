from __future__ import annotations

from pathlib import Path
from .identity import git_remote, now_iso
from .storage import ensure_dir


RegistryEntry = dict[str, str]


def hub_registry_path() -> Path:
    return Path.home() / ".sybermem" / "projects.yaml"


def load_registry() -> list[RegistryEntry]:
    path = hub_registry_path()
    if not path.is_file():
        return []

    projects: list[RegistryEntry] = []
    current: RegistryEntry | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  - project_id:"):
            if current:
                projects.append(current)
            current = {"project_id": line.split(":", 1)[1].strip()}
        elif current is not None and line.startswith("    slug:"):
            current["slug"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    name:"):
            current["name"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    path:"):
            current["path"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    remote:"):
            current["remote"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    registered_at:"):
            current["registered_at"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    last_indexed_at:"):
            current["last_indexed_at"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    last_seen_commit:"):
            current["last_seen_commit"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    status:"):
            current["status"] = line.split(":", 1)[1].strip()
    if current:
        projects.append(current)
    return projects


def save_registry(projects: list[RegistryEntry]) -> None:
    path = hub_registry_path()
    ensure_dir(path.parent)
    lines = ["schema_version: 1", "projects:"]
    for p in projects:
        lines.extend([
            f"  - project_id: {p['project_id']}",
            f"    slug: {p['slug']}",
            f"    name: {p.get('name', p['slug'])}",
            f"    path: {p['path']}",
            f"    remote: {p.get('remote', '')}",
            f"    registered_at: {p.get('registered_at', now_iso())}",
            f"    last_indexed_at: {p.get('last_indexed_at', '')}",
            f"    last_seen_commit: {p.get('last_seen_commit', '')}",
            f"    status: {p.get('status', 'active')}",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def register_project(project_id: str, slug: str, root: Path) -> None:
    projects = load_registry()
    updated = False
    for p in projects:
        if p.get("project_id") == project_id:
            p["slug"] = slug
            p["name"] = slug
            p["path"] = str(root).replace('\\', '/')
            p["remote"] = git_remote(root)
            p["status"] = "active"
            updated = True
            break
    if not updated:
        projects.append({
            "project_id": project_id,
            "slug": slug,
            "name": slug,
            "path": str(root).replace('\\', '/'),
            "remote": git_remote(root),
            "registered_at": now_iso(),
            "last_indexed_at": "",
            "last_seen_commit": "",
            "status": "active",
        })
    save_registry(projects)


def update_registry_index_metadata(project_id: str, *, commit: str, indexed_at: str, status: str) -> None:
    projects = load_registry()
    for p in projects:
        if p.get("project_id") == project_id:
            p["last_seen_commit"] = commit
            p["last_indexed_at"] = indexed_at
            p["status"] = status
            break
    save_registry(projects)
