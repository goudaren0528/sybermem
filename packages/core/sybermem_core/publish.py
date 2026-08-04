from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .project import resolve_project_root, read_team_from_project_yaml, write_team_to_project_yaml
from .publish_render import parse_published_status, read_team_yaml, render_current_status, render_project_card, render_team_overview
from .publish_sources import latest_phase_digest, latest_theme_digest, sync_markdown_history
from .records import parse_project_yaml
from .status import build_publication_preview, project_status, publication_readiness, team_publication_metadata


def _resolve_publish_context(team_path: Path | None) -> tuple[Path, Path, str, dict[str, str]]:
    root = resolve_project_root()
    if root is None:
        raise ValueError("No SyberMem project root found.")

    if team_path is None:
        saved = read_team_from_project_yaml(root)
        if saved.get("team_path"):
            team_path = Path(saved["team_path"])
        else:
            raise ValueError(
                "No --team-path provided and no team association found in project.yaml. "
                "Run `sybermem publish status --team-path <path>` to set it, "
                "or `sybermem team init` to create a Team repo first."
            )

    team_root = team_path.resolve()
    if not team_root.exists():
        raise FileNotFoundError(f"Team repo path not found: {team_root}")
    if not (team_root / ".git").exists():
        raise ValueError(f"Path exists but is not a Team Git repo: {team_root}")

    team_id, _ = read_team_yaml(team_root)
    project_meta = parse_project_yaml(root)
    if not project_meta.get("project_id"):
        raise ValueError("Current project has no project.yaml identity. Run `sybermem project init --register` first.")
    return root, team_root, team_id, project_meta


def _ensure_publication_ready(root: Path) -> None:
    readiness = publication_readiness(root)
    if not readiness["enough_material"]:
        raise ValueError(
            "Project does not yet have enough meaningful material to publish to Team memory "
            f"(records={readiness['record_count']}, decisions={readiness['decision_count']}, completed_phases={readiness['completed_phase_count']})."
        )


def publish_status_preview(team_path: Path | None = None) -> dict[str, object]:
    """Return the read-only Team publish preview for the current Project."""
    root, team_root, team_id, project_meta = _resolve_publish_context(team_path)
    _ensure_publication_ready(root)
    preview = build_publication_preview(root)
    preview.update({
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": project_meta.get("slug", root.name),
        "team_path": str(team_root).replace('\\', '/'),
    })
    return preview


def publish_status(team_path: Path | None = None, preview_source_hash: str | None = None) -> dict[str, object]:
    root, team_root, team_id, project_meta = _resolve_publish_context(team_path)
    _ensure_publication_ready(root)
    preview = build_publication_preview(root)
    slug = project_meta.get("slug", root.name)
    if preview_source_hash is not None and preview_source_hash != preview["source_hash"]:
        return {
            "status": "stale_preview",
            "team_id": team_id,
            "project_id": project_meta["project_id"],
            "slug": slug,
            "team_path": str(team_root).replace('\\', '/'),
            "expected_source_hash": preview_source_hash,
            "preview": preview,
        }

    status = project_status(root)
    source_commit = project_meta.get("repository.commit", "")
    phase_digest = latest_phase_digest(root)
    theme_digest = latest_theme_digest(root)
    project_dir = team_root / "projects" / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    project_md = project_dir / "project.md"
    current_status_md = project_dir / "current-status.md"
    meta_json = project_dir / "meta.json"
    phase_digests_dir = project_dir / "phase-digests"
    theme_digests_dir = project_dir / "theme-digests"
    project_md.write_text(render_project_card(project_meta, team_id), encoding="utf-8")
    current_status_md.write_text(render_current_status(status, source_commit), encoding="utf-8")
    phase_count, _phase_changed = sync_markdown_history(root / ".sybermem" / "digests", phase_digests_dir)
    theme_count, _theme_changed = sync_markdown_history(root / ".sybermem" / "theme-digests", theme_digests_dir)

    latest_phase_published = str(phase_digests_dir / Path(phase_digest).name).replace('\\', '/') if phase_digest else ""
    latest_theme_published = str(theme_digests_dir / Path(theme_digest).name).replace('\\', '/') if theme_digest else ""
    meta_json.write_text(json.dumps(_published_meta(team_id, project_meta, slug, status["as_of"], source_commit, preview, phase_digest, theme_digest, latest_phase_published, latest_theme_published, phase_count, theme_count), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overview = _rebuild_team_overview(team_root, team_id)
    pushed = _commit_and_push(team_root, slug)
    write_team_to_project_yaml(root, team_id, str(team_root).replace('\\', '/'))
    return {
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "team_path": str(team_root).replace('\\', '/'),
        "files": [str(project_md).replace('\\', '/'), str(current_status_md).replace('\\', '/'), str(meta_json).replace('\\', '/'), str(overview).replace('\\', '/')],
        "source_phase_digest": phase_digest,
        "source_theme_digest": theme_digest,
        "preview": preview,
        "team_metadata": team_publication_metadata(root, slug, preview=preview),
        "pushed": pushed,
    }


def _published_meta(
    team_id: str,
    project_meta: dict[str, str],
    slug: str,
    published_at: str,
    source_commit: str,
    preview: dict,
    phase_digest: str,
    theme_digest: str,
    latest_phase_published: str,
    latest_theme_published: str,
    phase_count: int,
    theme_count: int,
) -> dict:
    return {
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "published_at": published_at,
        "source_commit": source_commit,
        "source_revision": preview["source_revision"],
        "source_hash": preview["source_hash"],
        "source_scope": preview["source_scope"],
        "selected_records": preview["selected_records"],
        "selected_digests": preview["selected_digests"],
        "freshness": preview["freshness"],
        "conflicts": preview["conflicts"],
        "local_changes_after_publish": False,
        "stale": preview["freshness"] == "stale",
        "conflict": bool(preview["conflicts"]),
        "review_required": bool(preview["review_required"]),
        "source_phase_digest": phase_digest,
        "source_theme_digest": theme_digest,
        "latest_phase_digest": latest_phase_published,
        "latest_theme_digest": latest_theme_published,
        "phase_digest_count": phase_count,
        "theme_digest_count": theme_count,
    }


def _rebuild_team_overview(team_root: Path, team_id: str) -> Path:
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
    return overview


def _commit_and_push(team_root: Path, slug: str) -> bool:
    subprocess.run(["git", "add", f"projects/{slug}/", "dashboards/"], cwd=team_root, check=True, capture_output=True, text=True)
    diff_check = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=team_root, check=False, capture_output=True, text=True)
    has_changes = diff_check.returncode == 1
    if has_changes:
        subprocess.run(["git", "commit", "-m", f"publish: {slug} status update"], cwd=team_root, check=True, capture_output=True, text=True)
    remote_check = subprocess.run(["git", "remote", "get-url", "origin"], cwd=team_root, capture_output=True, text=True, check=False)
    if has_changes and remote_check.returncode == 0 and remote_check.stdout.strip():
        push_result = subprocess.run(["git", "push", "origin"], cwd=team_root, capture_output=True, text=True, check=False)
        return push_result.returncode == 0
    return False
