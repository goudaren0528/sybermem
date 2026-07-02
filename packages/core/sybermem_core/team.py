from __future__ import annotations

from pathlib import Path
import subprocess

from .identity import now_iso
from .storage import ensure_dir


def render_team_yaml(team_id: str, name: str, remote: str) -> str:
    return (
        f"schema_version: 1\n"
        f"team_id: {team_id}\n"
        f"name: {name}\n"
        f"repository:\n"
        f"  remote: {remote}\n"
        f"created_at: {now_iso()}\n"
    )


def git_remote(root: Path) -> str:
    try:
        r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def is_valid_team_repo(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists() and (path / "team.yaml").is_file()


def init_team_repo(path: Path, team_id: str, name: str, remote: str) -> dict[str, str]:
    if path.exists() and not path.is_dir():
        raise ValueError(f"Path exists but is not a directory: {path}")

    created = False
    if not path.exists():
        ensure_dir(path)
        created = True

    git_dir = path / ".git"
    if not git_dir.exists():
        # If the directory already existed but is not a git repo, refuse.
        if not created and any(path.iterdir()):
            raise ValueError(f"Path exists but is not a git repository: {path}")
        subprocess.run(["git", "init"], cwd=path, check=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=path, check=False)

    current_remote = git_remote(path)
    if current_remote:
        if current_remote != remote:
            raise ValueError(f"Existing origin remote differs: {current_remote}")
    else:
        subprocess.run(["git", "remote", "add", "origin", remote], cwd=path, check=True)

    # Create Team directory skeleton
    for sub in [
        "projects",
        "lessons/candidates",
        "lessons/accepted",
        "lessons/rejected",
        "lessons/deprecated",
        "standards",
        "architecture",
        "publications",
        "dashboards",
    ]:
        ensure_dir(path / sub)

    team_yaml = path / "team.yaml"
    if not team_yaml.exists():
        team_yaml.write_text(render_team_yaml(team_id, name, remote), encoding="utf-8")
        status = "created"
    else:
        status = "existing"

    # Initial commit and push for new repos
    pushed = False
    if status == "created":
        subprocess.run(["git", "add", "."], cwd=path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init: team repo skeleton"],
            cwd=path, check=True,
        )
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=path, capture_output=True, text=True, check=False,
        )
        pushed = push_result.returncode == 0
        if not pushed:
            import sys
            print("Warning: initial push failed. Check that the remote repo exists and is accessible.", file=sys.stderr)

    return {
        "status": status,
        "team_id": team_id,
        "name": name,
        "path": str(path).replace('\\', '/'),
        "remote": remote,
        "pushed": str(pushed).lower(),
    }
