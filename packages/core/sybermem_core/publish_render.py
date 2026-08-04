from __future__ import annotations

import json
from pathlib import Path


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
    phase_label = phase["id"] or "(no phase)"
    phase_name = phase.get("name", "")
    digest_tail = []
    if phase["id"]:
        digest_tail.append(f"Current phase remains {phase['id']}")
    if phase_name:
        digest_tail.append(phase_name)

    progress = []
    if status["recent_records"]:
        progress.append(f"{len(status['recent_records'])} recent record updates were published")
    if phase["id"]:
        progress.append(f"Active phase is {phase['id']}{(' — ' + phase_name) if phase_name else ''}")

    focus = []
    if phase_name:
        focus.append(f"Current work is centered on {phase_name.lower()}")
    elif phase["id"]:
        focus.append(f"Current work is centered on {phase['id']}")
    else:
        focus.append("Current work is still too early to resolve into an active phase")

    risks = []
    if status["open_bugs"]:
        risks.append(f"Open bugs still need attention ({len(status['open_bugs'])})")
    if status["open_requirements"]:
        risks.append(f"Open requirements remain unresolved ({len(status['open_requirements'])})")
    if not risks:
        risks.append("No major risks surfaced from the current project status snapshot")

    next_items = status["next"][:] if status["next"] else []
    if not next_items:
        if status["open_bugs"] or status["open_requirements"]:
            next_items.append("Resolve the open bugs and requirements before the next publication cycle")
        elif phase_name:
            next_items.append(f"Continue advancing the current {phase_name.lower()} phase")
        else:
            next_items.append("Continue gathering enough material to clarify the active phase and next milestone")

    lines = [
        f"# {status['slug']} — Team Project Summary",
        "",
        f"- Updated at: {status['as_of']}",
        f"- Source commit: {source_commit}",
        "",
        "## Current Focus",
    ]
    lines.extend([f"- {item}" for item in focus])
    lines.extend(["", "## Recent Progress"])
    lines.extend([f"- {item}" for item in progress] if progress else ["- No significant recent progress detected"])
    lines.extend(["", "## Risks / Attention"])
    lines.extend([f"- {item}" for item in risks])
    lines.extend(["", "## Open Bugs"])
    lines.extend([f"- {bid}" for bid in status["open_bugs"]] if status["open_bugs"] else ["- none"])
    lines.extend(["", "## Open Requirements"])
    lines.extend([f"- {rid}" for rid in status["open_requirements"]] if status["open_requirements"] else ["- none"])
    lines.extend(["", "## Next"])
    lines.extend([f"- {item}" for item in next_items])
    lines.extend(["", "## Supporting Signals"])
    lines.append(f"- Active Phase: {phase_label}{(' — ' + phase_name) if phase_name else ''}")
    lines.append(f"- Open Bugs: {len(status['open_bugs'])}")
    lines.append(f"- Open Requirements: {len(status['open_requirements'])}")
    if digest_tail:
        lines.append(f"- Context: {'; '.join(digest_tail)}")
    return "\n".join(lines) + "\n"


def parse_published_status(project_dir: Path) -> dict:
    status_md = project_dir / "current-status.md"
    meta_json = project_dir / "meta.json"
    if not status_md.is_file() or not meta_json.is_file():
        return {}

    meta = json.loads(meta_json.read_text(encoding="utf-8"))
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
        "source_scope": meta.get("source_scope", ""),
        "local_changes_after_publish": bool(meta.get("local_changes_after_publish", False)),
        "stale": bool(meta.get("stale", False)),
        "conflict": bool(meta.get("conflict", False)),
        "review_required": bool(meta.get("review_required", False)),
    }


def render_team_overview(team_id: str, summaries: list[dict]) -> str:
    active = []
    stale = []
    attention = []
    sources = []
    summaries = sorted(summaries, key=lambda s: s.get("published_at", ""), reverse=True)

    for summary in summaries:
        _append_overview_summary(summary, active, stale, attention, sources)

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


def _append_overview_summary(summary: dict, active: list[str], stale: list[str], attention: list[str], sources: list[str]) -> None:
    slug = summary["slug"]
    phase_line = summary.get("phase_line", "")
    published_at = summary.get("published_at", "")
    if phase_line and phase_line != "(no phase)":
        active.append(f"- {slug} → {phase_line}")
    else:
        attention.append(f"- {slug} — no active phase")
    if published_at:
        stale.append(f"- {slug} — {published_at[:10]}")
    if summary.get("open_bugs"):
        attention.append(f"- {slug} — open bugs: {len(summary['open_bugs'])}")
    if summary.get("open_requirements"):
        attention.append(f"- {slug} — open requirements: {len(summary['open_requirements'])}")
    if summary.get("local_changes_after_publish"):
        attention.append(f"- {slug} — local Project changes after last publish")
    if summary.get("stale"):
        attention.append(f"- {slug} — stale publication preview")
    if summary.get("conflict"):
        attention.append(f"- {slug} — source conflict requires review")
    if summary.get("review_required"):
        attention.append(f"- {slug} — review required for next publish")
    sources.append(_published_source_line(summary))


def _published_source_line(summary: dict) -> str:
    slug = summary["slug"]
    source_phase = bool(summary.get("source_phase_digest"))
    source_theme = bool(summary.get("source_theme_digest"))
    if source_phase and source_theme:
        line = f"- {slug} → phase digest available, theme digest available"
    elif source_phase:
        line = f"- {slug} → phase digest available"
    elif source_theme:
        line = f"- {slug} → theme digest available"
    else:
        line = f"- {slug} → no digest published"
    if summary.get("source_scope"):
        return f"{line} ({summary['source_scope']})"
    return line


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
