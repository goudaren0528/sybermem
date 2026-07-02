from __future__ import annotations

from pathlib import Path

from .project import resolve_project_root
from .records import parse_project_yaml
from .status import project_status, publication_readiness


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


def latest_phase_digest(root: Path) -> str:
    digests_dir = root / ".sybermem" / "digests"
    if not digests_dir.is_dir():
        return ""
    files = sorted(digests_dir.glob("*.md"))
    return str(files[-1]).replace('\\', '/') if files else ""


def latest_theme_digest(root: Path) -> str:
    digests_dir = root / ".sybermem" / "theme-digests"
    if not digests_dir.is_dir():
        return ""
    files = sorted(digests_dir.glob("*.md"))
    return str(files[-1]).replace('\\', '/') if files else ""


def parse_published_status(project_dir: Path) -> dict[str, str | list[str]]:
    status_md = project_dir / "current-status.md"
    meta_json = project_dir / "meta.json"
    if not status_md.is_file() or not meta_json.is_file():
        return {}

    import json as _json
    meta = _json.loads(meta_json.read_text(encoding="utf-8"))
    text = status_md.read_text(encoding="utf-8")

    phase_line = ""
    for line in text.splitlines():
        if line.startswith("- phase-") or line.startswith("- (no phase)"):
            phase_line = line[2:].strip()
            break

    open_bugs = []
    open_requirements = []
    section = None
    for line in text.splitlines():
        if line.startswith("## Open Bugs"):
            section = "bugs"
            continue
        if line.startswith("## Open Requirements"):
            section = "reqs"
            continue
        if line.startswith("## "):
            section = None
            continue
        if section == "bugs" and line.startswith("- ") and line.strip() != "- none":
            open_bugs.append(line[2:].strip())
        if section == "reqs" and line.startswith("- ") and line.strip() != "- none":
            open_requirements.append(line[2:].strip())

    return {
        "slug": project_dir.name,
        "published_at": meta.get("published_at", ""),
        "phase_line": phase_line,
        "open_bugs": open_bugs,
        "open_requirements": open_requirements,
        "source_phase_digest": meta.get("source_phase_digest", ""),
        "source_theme_digest": meta.get("source_theme_digest", ""),
    }


def render_team_overview(team_id: str, summaries: list[dict]) -> str:
    active = []
    stale = []
    attention = []
    sources = []

    summaries = sorted(summaries, key=lambda s: s.get("published_at", ""), reverse=True)

    for s in summaries:
        slug = s["slug"]
        phase_line = s.get("phase_line", "")
        published_at = s.get("published_at", "")
        source_phase = bool(s.get("source_phase_digest"))
        source_theme = bool(s.get("source_theme_digest"))

        if phase_line and phase_line != "(no phase)":
            active.append(f"- {slug} → {phase_line}")
        else:
            attention.append(f"- {slug} — no active phase")

        if published_at:
            stale.append(f"- {slug} — {published_at[:10]}")

        if s.get("open_bugs"):
            attention.append(f"- {slug} — open bugs: {len(s['open_bugs'])}")
        if s.get("open_requirements"):
            attention.append(f"- {slug} — open requirements: {len(s['open_requirements'])}")

        if source_phase and source_theme:
            sources.append(f"- {slug} → phase digest available, theme digest available")
        elif source_phase:
            sources.append(f"- {slug} → phase digest available")
        elif source_theme:
            sources.append(f"- {slug} → theme digest available")
        else:
            sources.append(f"- {slug} → no digest published")

    lines = [
        "# Team Overview",
        "",
        f"- Updated at: {summaries[0]['published_at'] if summaries else ''}",
        f"- Team: {team_id}",
        "",
        "## Active Projects",
    ]
    lines.extend(active or ["- none"])
    lines.extend(["", "## Recently Updated"])
    lines.extend(stale or ["- none"])
    lines.extend(["", "## Needs Attention"])
    lines.extend(attention or ["- none"])
    lines.extend(["", "## Published Sources"])
    lines.extend(sources or ["- none"])
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

    readiness = publication_readiness(root)
    if not readiness["enough_material"]:
        raise ValueError(
            "Project does not yet have enough meaningful material to publish to Team memory "
            f"(records={readiness['record_count']}, decisions={readiness['decision_count']}, completed_phases={readiness['completed_phase_count']})."
        )

    status = project_status(root)
    slug = project_meta.get("slug", root.name)
    source_commit = project_meta.get("repository.commit", "")
    phase_digest = latest_phase_digest(root)
    theme_digest = latest_theme_digest(root)

    project_dir = team_root / "projects" / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    project_md = project_dir / "project.md"
    current_status_md = project_dir / "current-status.md"
    meta_json = project_dir / "meta.json"

    project_md.write_text(render_project_card(project_meta, team_id), encoding="utf-8")
    current_status_md.write_text(render_current_status(status, source_commit), encoding="utf-8")
    import json as _json
    meta_json.write_text(_json.dumps({
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "published_at": status["as_of"],
        "source_commit": source_commit,
        "source_phase_digest": phase_digest,
        "source_theme_digest": theme_digest,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Rebuild team-wide overview from all published project summaries
    dashboards_dir = team_root / "dashboards"
    dashboards_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    projects_root = team_root / "projects"
    for child in sorted(projects_root.iterdir()):
        if child.is_dir():
            parsed = parse_published_status(child)
            if parsed:
                summaries.append(parsed)
    overview = dashboards_dir / "current-overview.md"
    overview.write_text(render_team_overview(team_id, summaries), encoding="utf-8")

    # Auto-commit and push to remote
    import subprocess
    subprocess.run(
        ["git", "add", f"projects/{slug}/", "dashboards/"],
        cwd=team_root, check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"publish: {slug} status update"],
        cwd=team_root, check=True,
    )
    # Push if origin exists
    remote_check = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=team_root, capture_output=True, text=True, check=False,
    )
    pushed = False
    if remote_check.returncode == 0 and remote_check.stdout.strip():
        push_result = subprocess.run(
            ["git", "push", "origin"],
            cwd=team_root, capture_output=True, text=True, check=False,
        )
        pushed = push_result.returncode == 0

    return {
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "team_path": str(team_root).replace('\\', '/'),
        "files": [
            str(project_md).replace('\\', '/'),
            str(current_status_md).replace('\\', '/'),
            str(meta_json).replace('\\', '/'),
            str(overview).replace('\\', '/'),
        ],
        "source_phase_digest": phase_digest,
        "source_theme_digest": theme_digest,
        "pushed": pushed,
    }
