from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json


def now_iso() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat(timespec="seconds")


def read_team_yaml(team_root: Path) -> str:
    team_yaml = team_root / "team.yaml"
    if not team_yaml.is_file():
        raise FileNotFoundError(f"Missing team.yaml in Team repo: {team_root}")
    for line in team_yaml.read_text(encoding="utf-8").splitlines():
        if line.startswith("team_id:"):
            return line.split(":", 1)[1].strip()
    return ""


def load_summary_state(dashboards_dir: Path) -> dict:
    state_path = dashboards_dir / ".summary-state.json"
    if not state_path.is_file():
        return {"last_generated_at": "", "last_seen_projects": {}}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_summary_state(dashboards_dir: Path, state: dict) -> Path:
    path = dashboards_dir / ".summary-state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_project_publications(team_root: Path) -> list[dict]:
    projects_root = team_root / "projects"
    items = []
    if not projects_root.is_dir():
        return items

    for child in sorted(projects_root.iterdir()):
        if not child.is_dir():
            continue
        meta_json = child / "meta.json"
        status_md = child / "current-status.md"
        if not meta_json.is_file() or not status_md.is_file():
            continue
        meta = json.loads(meta_json.read_text(encoding="utf-8"))
        status_text = status_md.read_text(encoding="utf-8")

        phase_line = ""
        for line in status_text.splitlines():
            if line.startswith("- phase-") or line.startswith("- (no phase)"):
                phase_line = line[2:].strip()
                break

        open_bugs = []
        open_requirements = []
        section = None
        for line in status_text.splitlines():
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

        items.append({
            "slug": child.name,
            "published_at": meta.get("published_at", ""),
            "phase_line": phase_line,
            "source_phase_digest": meta.get("source_phase_digest", ""),
            "source_theme_digest": meta.get("source_theme_digest", ""),
            "open_bugs": open_bugs,
            "open_requirements": open_requirements,
        })
    return items


def build_team_management_summary(team_root: Path) -> dict[str, Path | dict | str]:
    team_root = team_root.resolve()
    dashboards_dir = team_root / "dashboards"
    dashboards_dir.mkdir(parents=True, exist_ok=True)

    team_id = read_team_yaml(team_root)
    publications = load_project_publications(team_root)
    state = load_summary_state(dashboards_dir)
    previous_seen = state.get("last_seen_projects", {})

    generated_at = now_iso()
    recent_cutoff = datetime.fromisoformat(generated_at) - timedelta(hours=48)

    progress = []
    attention = []
    deep_review = []
    recent_updates = []
    next_seen = {}

    for p in publications:
        slug = p["slug"]
        published_at = p.get("published_at", "")
        next_seen[slug] = published_at

        if published_at and previous_seen.get(slug) != published_at:
            progress.append({
                "slug": slug,
                "change_type": "status_update",
                "published_at": published_at,
                "phase": p.get("phase_line", ""),
            })

        if published_at:
            try:
                published_dt = datetime.fromisoformat(published_at)
                if published_dt >= recent_cutoff:
                    recent_updates.append({"slug": slug, "published_at": published_at})
                else:
                    days_old = (datetime.fromisoformat(generated_at) - published_dt).days
                    if days_old > 3:
                        attention.append({"slug": slug, "reason": "stale", "count": days_old})
            except Exception:
                pass

        if not p.get("phase_line") or p.get("phase_line") == "(no phase)":
            attention.append({"slug": slug, "reason": "no_active_phase", "count": 0})
        if p.get("open_bugs"):
            attention.append({"slug": slug, "reason": "open_bugs", "count": len(p["open_bugs"])})
        if p.get("open_requirements"):
            attention.append({"slug": slug, "reason": "open_requirements", "count": len(p["open_requirements"])})

        if p.get("source_phase_digest"):
            deep_review.append({"slug": slug, "reason": "new_phase_digest"})
        elif p.get("source_theme_digest"):
            deep_review.append({"slug": slug, "reason": "new_theme_digest"})
        elif p.get("open_bugs") and p.get("open_requirements"):
            deep_review.append({"slug": slug, "reason": "multiple_attention_signals"})

    md_lines = [
        "# Team Management Summary",
        "",
        f"- Generated at: {generated_at}",
        f"- Team: {team_id}",
        "- Baseline: since last summary",
        "- Recent window: last 48 hours",
        "",
        "## Progress Since Last Summary",
    ]
    if progress:
        for item in progress:
            phase = item.get("phase", "")
            phase_tail = f"; current phase {phase}" if phase else ""
            md_lines.append(f"- {item['slug']} — published a new update{phase_tail}")
    else:
        md_lines.append("- none")

    md_lines.extend(["", "## Attention Needed"])
    if attention:
        for item in attention:
            if item["reason"] == "stale":
                md_lines.append(f"- {item['slug']} — stale for {item['count']} days")
            elif item["reason"] == "no_active_phase":
                md_lines.append(f"- {item['slug']} — no active phase")
            elif item["reason"] == "open_bugs":
                md_lines.append(f"- {item['slug']} — open bugs: {item['count']}")
            elif item["reason"] == "open_requirements":
                md_lines.append(f"- {item['slug']} — open requirements: {item['count']}")
    else:
        md_lines.append("- none")

    md_lines.extend(["", "## Worth Deeper Review"])
    if deep_review:
        for item in deep_review:
            md_lines.append(f"- {item['slug']} — {item['reason']}")
    else:
        md_lines.append("- none")

    md_lines.extend(["", "## Recently Updated Projects"])
    if recent_updates:
        for item in recent_updates:
            md_lines.append(f"- {item['slug']} — {item['published_at'][:10]}")
    else:
        md_lines.append("- none")

    summary_md = dashboards_dir / "latest-management-summary.md"
    summary_json = dashboards_dir / "latest-management-summary.json"
    summary_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    payload = {
        "generated_at": generated_at,
        "team_id": team_id,
        "baseline": "since_last_summary",
        "recent_window_hours": 48,
        "progress": progress,
        "attention": attention,
        "deep_review_candidates": deep_review,
        "recent_updates": recent_updates,
    }
    summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state_path = save_summary_state(dashboards_dir, {
        "last_generated_at": generated_at,
        "last_seen_projects": next_seen,
    })

    return {
        "team_id": team_id,
        "team_path": str(team_root).replace('\\', '/'),
        "summary_markdown": summary_md,
        "summary_json": summary_json,
        "summary_state": state_path,
        "payload": payload,
    }
