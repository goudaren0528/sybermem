from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import uuid


def generate_project_id() -> str:
    return f"prj_{uuid.uuid4().hex[:16]}"


def derive_slug(root: Path) -> str:
    remote = git_remote(root)
    if remote:
        slug = remote.rstrip("/").split("/")[-1]
        if slug.endswith(".git"):
            slug = slug[:-4]
        return slug
    return root.name


def git_remote(root: Path) -> str:
    try:
        r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def git_default_branch(root: Path) -> str:
    try:
        r = subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def now_iso() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat(timespec="seconds")


def render_project_yaml(project_id: str, slug: str, root: Path) -> str:
    return (
        f"schema_version: 1\n"
        f"project_id: {project_id}\n"
        f"slug: {slug}\n"
        f"name: {slug}\n"
        f"repository:\n"
        f"  remote: {git_remote(root)}\n"
        f"  default_branch: {git_default_branch(root)}\n"
        f"created_at: {now_iso()}\n"
    )
