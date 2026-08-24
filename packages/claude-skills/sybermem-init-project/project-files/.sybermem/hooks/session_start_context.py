#!/usr/bin/env python3
"""SyberMem SessionStart hook — injects project memory context into Claude Code sessions.

Reads Key Conclusions, Topic Index, phase-index status, and stale signals.
Outputs structured JSON with hookSpecificOutput.additionalContext.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def resolve_sybermem_root() -> Path | None:
    """Walk up from cwd to find the nearest SyberMem project root."""
    current = Path.cwd().resolve()
    git_root = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip()).resolve()
    except Exception:
        pass

    while True:
        has_sybermem = (current / ".sybermem").is_dir()
        has_settings = (current / ".claude" / "settings.json").is_file()
        has_index = (current / ".sybermem" / "INDEX.md").is_file()
        if has_sybermem and (has_settings or has_index):
            return current
        if git_root and current == git_root:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def run_git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd or Path.cwd(),
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def parse_conclusions(index_text: str) -> list[str]:
    match = re.search(
        r"## Key Conclusions\s*\n([\s\S]*?)(?=\n---|\n## )", index_text
    )
    if not match:
        return []
    lines = [
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith("- [")
    ]
    # Sort by date extracted from conclusion (YYYY-MM-DD) so most recent comes last
    def _date_key(line: str) -> str:
        m = re.search(r"\((\d{4}-\d{2}-\d{2})\)", line)
        return m.group(1) if m else ""
    lines.sort(key=_date_key)
    return lines


def parse_topic_index(index_text: str) -> dict[str, list[str]]:
    match = re.search(
        r"## Topic Index\s*\n([\s\S]*?)(?=\n---|\n## |$)", index_text
    )
    if not match:
        return {}
    topics: dict[str, list[str]] = {}
    for line in match.group(1).splitlines():
        m = re.match(r"^- (\S+):\s*(.+)", line)
        if m:
            topics[m.group(1)] = [s.strip() for s in m.group(2).split(",")]
    return topics


def parse_phase_index(root: Path) -> dict:
    """Return phase-index metadata: status, last_git_boundary, active_phase, confirmed_count.

    `active_phase` prefers the last phase block whose `- lifecycle: active` line is
    present. If no phase declares lifecycle (older format) or none are active,
    falls back to the last `### Phase:` heading in document order.
    """
    phase_path = root / ".sybermem" / "analysis" / "phase-index.md"
    if not phase_path.is_file():
        return {"exists": False}

    content = phase_path.read_text(encoding="utf-8")
    status_match = re.search(r"^- status:\s*(.+)", content, re.MULTILINE)
    boundary_match = re.search(r"^- last_git_boundary:\s*(\S+)", content, re.MULTILINE)
    phases = re.findall(r"### Phase: (.+)", content)

    # Lifecycle-aware active phase selection: scan each phase block for an
    # `- lifecycle: active` marker and remember the last one. Falls back to
    # document order when no phase declares lifecycle.
    active_phase: str | None = None
    blocks = re.split(r"(?m)^### Phase: ", content)
    for block in blocks[1:]:
        title = block.splitlines()[0].strip() if block.splitlines() else None
        if not title:
            continue
        header_match = re.search(r"^- lifecycle:\s*(\S+)", block, re.MULTILINE)
        if header_match and header_match.group(1).strip() == "active":
            active_phase = title
    if active_phase is None and phases:
        active_phase = phases[-1]

    return {
        "exists": True,
        "status": status_match.group(1).strip() if status_match else "unknown",
        "last_git_boundary": boundary_match.group(1).strip() if boundary_match else None,
        "active_phase": active_phase,
        "confirmed_count": len(phases),
    }


def parse_project_identity(root: Path) -> dict:
    """Read .sybermem/project.yaml and return project_id and slug."""
    proj_path = root / ".sybermem" / "project.yaml"
    if not proj_path.is_file():
        return {"exists": False}
    content = read_text(proj_path)
    if content is None:
        return {"exists": False}
    # Simple line-based parsing (no PyYAML dependency)
    project_id = None
    slug = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("project_id:"):
            project_id = line.split(":", 1)[1].strip()
        elif line.startswith("slug:"):
            slug = line.split(":", 1)[1].strip()
    return {"exists": True, "project_id": project_id, "slug": slug}


def _user_home() -> Path | None:
    import os
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    return Path(home) if home else None


def read_installed_version() -> str:
    """Read the installed SyberMem version marker written by the install scripts."""
    home = _user_home()
    if home is None:
        return ""
    marker = home / ".claude" / "sybermem" / "VERSION"
    text = read_text(marker)
    return text.strip() if text else ""


def read_project_version(root: Path) -> str:
    """Read sybermem_version from .sybermem/project.yaml (empty if absent)."""
    content = read_text(root / ".sybermem" / "project.yaml")
    if content is None:
        return ""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("sybermem_version:"):
            return line.split(":", 1)[1].strip()
    return ""


def _parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for raw in version.strip().split("."):
        digits = ""
        for ch in raw:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def project_is_outdated(root: Path) -> dict:
    """Whether a MANAGED project should be nudged to run /sybermem-update. Fail-open.

    Tri-state so OLD projects bootstrap into version tracking:
    - installed unknown (no VERSION marker) -> not outdated.
    - not a managed project (no .sybermem/project.yaml) -> not outdated.
    - managed but no sybermem_version stamp (predates the field) -> outdated.
    - managed and stamp < installed -> outdated.
    """
    installed = read_installed_version()
    project = read_project_version(root)
    is_managed = (root / ".sybermem" / "project.yaml").is_file()
    if not installed or not is_managed:
        return {"outdated": False, "installed": installed, "project": project}
    if not project:
        return {"outdated": True, "installed": installed, "project": project}
    pa, pb = _parse_version(project), _parse_version(installed)
    width = max(len(pa), len(pb))
    pa += (0,) * (width - len(pa))
    pb += (0,) * (width - len(pb))
    return {"outdated": pa < pb, "installed": installed, "project": project}


def detect_stale_signal(root: Path, boundary_commit: str | None) -> dict:
    """Compare phase-index boundary to current HEAD."""
    if not boundary_commit:
        return {"stale": False, "commits_ahead": 0}

    head = run_git("rev-parse", "HEAD", cwd=root)
    if not head or head == boundary_commit:
        return {"stale": False, "commits_ahead": 0}

    count_str = run_git(
        "rev-list", "--count", f"{boundary_commit}..HEAD", cwd=root
    )
    try:
        count = int(count_str)
    except (ValueError, TypeError):
        count = 0

    return {
        "stale": count >= 3,
        "commits_ahead": count,
        "boundary": boundary_commit,
        "head": head[:7],
    }


def latest_record_date(root: Path) -> str:
    """Return the newest YYYY-MM-DD prefix across canonical record files, or ''."""
    latest = ""
    syb = root / ".sybermem"
    for subdir in ("changes", "decisions", "requirements", "bugs"):
        record_dir = syb / subdir
        if not record_dir.is_dir():
            continue
        for path in record_dir.glob("*.md"):
            m = re.match(r"(\d{4}-\d{2}-\d{2})-", path.name)
            if m and m.group(1) > latest:
                latest = m.group(1)
    return latest


DIGEST_BACKLOG_THRESHOLD = 5


def detect_stale_digests(root: Path) -> dict:
    """Read digest governance status via the CLI, for proactive heads-ups.

    Shells to `sybermem digest status --format json` (the single source of truth in
    sybermem_core.digest_governance) rather than reimplementing coverage-hash logic in
    the hook. Returns both the mechanically-stale count AND the backlog snapshot
    (uncovered records + age), so one CLI call feeds both the stale and the "haven't
    digested in a while" heads-ups. Fail-open to no signal when the CLI is unavailable or
    errors, so session start never breaks. This only surfaces heads-ups — it never
    regenerates a digest.
    """
    empty = {"stale": 0, "uncovered": 0, "days_since_latest_digest": 0, "has_digest": False}
    try:
        result = subprocess.run(
            ["sybermem", "digest", "status", "--format", "json"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", check=False,
        )
        if result.returncode not in (0, 1) or not result.stdout.strip():
            return empty
        import json as _json
        payload = _json.loads(result.stdout)
        backlog = payload.get("backlog") or {}
        return {
            "stale": int(payload.get("stale", 0) or 0),
            "uncovered": int(backlog.get("uncovered", 0) or 0),
            "days_since_latest_digest": int(backlog.get("days_since_latest_digest", 0) or 0),
            "has_digest": bool(backlog.get("has_digest", False)),
        }
    except Exception:
        return empty


def detect_constitution(root: Path) -> list[dict]:
    """Return active GLOBAL norms (the project constitution) via the CLI.

    Shells to `sybermem norms list --scope global --format json` (single source of truth
    in sybermem_core.norms) so binding global norms govern the session from startup.
    Fail-open to [] when the CLI is unavailable or errors.
    """
    try:
        result = subprocess.run(
            ["sybermem", "norms", "list", "--scope", "global", "--format", "json"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        import json as _json
        payload = _json.loads(result.stdout)
        norms = payload.get("norms")
        return [n for n in norms if isinstance(n, dict)] if isinstance(norms, list) else []
    except Exception:
        return []


def detect_record_gap(root: Path) -> dict:
    """Count git commits since the most recent record, to nudge timely recording.

    Record timeliness is the lifeblood of a memory system: reasons and impact
    evaporate across sessions. We surface a proactive reminder (not an action) when
    at least 3 commits have landed since the last durable record. Fail-open to no
    reminder when git or dates are unavailable.
    """
    latest = latest_record_date(root)
    if not latest:
        return {"nudge": False, "commits_since_record": 0}
    count_str = run_git("rev-list", "--count", f"--since={latest}", "HEAD", cwd=root)
    try:
        count = int(count_str)
    except (ValueError, TypeError):
        count = 0
    return {"nudge": count >= 3, "commits_since_record": count, "since": latest}


def _version_nudge_line(root: Path) -> str | None:
    """Return an update-available line when the project trails installed SyberMem."""
    version = project_is_outdated(root)
    if not version["outdated"]:
        return None
    was_refreshed = (
        f"was last refreshed with {version['project']}"
        if version["project"]
        else "predates SyberMem version tracking"
    )
    return (
        f"⭐ Update available: SyberMem {version['installed']} is installed but this "
        f"project {was_refreshed}. Run /sybermem-update to apply the latest fixes "
        "to this project."
    )


def build_context(root: Path) -> str:
    """Build the additionalContext string for Claude Code."""
    index_path = root / ".sybermem" / "INDEX.md"
    version_line = _version_nudge_line(root)
    if not index_path.is_file():
        base = "SyberMem startup context:\nNo .sybermem/INDEX.md found. Run /sybermem-init-project to initialize."
        # Norms live under .sybermem/norms/ independent of INDEX.md, so the binding
        # constitution must still govern a norm-only / partially-initialized project.
        constitution = detect_constitution(root)
        if constitution:
            base += "\nProject Norms (binding — follow unless the user explicitly overrides):"
            for norm in constitution:
                statement = str(norm.get("statement", "")).strip()
                record_id = str(norm.get("record_id", "")).strip()
                if statement:
                    base += f"\n- [{record_id}] {statement}"
        return f"{base}\n{version_line}" if version_line else base

    index_text = index_path.read_text(encoding="utf-8")
    conclusions = parse_conclusions(index_text)
    topics = parse_topic_index(index_text)
    phase_info = parse_phase_index(root)
    project_info = parse_project_identity(root)

    lines: list[str] = ["SyberMem startup context:"]

    if version_line:
        lines.append(version_line)

    if project_info["exists"] and project_info.get("slug"):
        lines.append(f"Project: {project_info['slug']} ({project_info.get('project_id', 'no id')}).")

    lines.append(f"Loaded {len(conclusions)} key conclusions from SyberMem.")

    # Project constitution: binding global norms, injected at session start so they govern
    # the work regardless of prompt relevance. Highest priority, so surfaced right away.
    constitution = detect_constitution(root)
    if constitution:
        lines.append("Project Norms (binding — follow unless the user explicitly overrides):")
        for norm in constitution:
            statement = str(norm.get("statement", "")).strip()
            record_id = str(norm.get("record_id", "")).strip()
            if statement:
                lines.append(f"- [{record_id}] {statement}")

    if topics:
        topic_names = ", ".join(sorted(topics.keys()))
        lines.append(f"Relevant topics: {topic_names}.")

    if phase_info["exists"]:
        lines.append(
            f"Phase index: {phase_info['status']}. "
            f"{phase_info['confirmed_count']} confirmed phases."
        )
        if phase_info["active_phase"]:
            lines.append(f"Active phase: {phase_info['active_phase']}.")

        stale = detect_stale_signal(root, phase_info.get("last_git_boundary"))
        if stale["stale"]:
            lines.append(
                f"Stale signal: phase-index last git boundary is {stale['boundary']}, "
                f"current HEAD is {stale['head']} ({stale['commits_ahead']} commits ahead)."
            )
    else:
        lines.append("Phase index: not found. Run /sybermem-phase-analyze to create it.")

    record_gap = detect_record_gap(root)
    if record_gap["nudge"]:
        lines.append(
            f"Record reminder: {record_gap['commits_since_record']} commits since the last record "
            f"({record_gap['since']}). If this round did meaningful work, consider /sybermem-record "
            "to capture the reason and impact while it is fresh."
        )

    # Digest governance heads-up (G5): a scarce ⭐ marker fires only when a genuinely
    # load-bearing signal exists — one or more phase/theme digests are mechanically stale
    # because their source records changed. This never regenerates a digest; it points
    # the user at /sybermem-digest so drifted summaries stop reading as authoritative.
    digest_status = detect_stale_digests(root)
    if digest_status["stale"] > 0:
        lines.append(
            f"⭐ Digest heads-up: {digest_status['stale']} digest(s) are stale — their source "
            "records changed since the summary was written. Run /sybermem-digest to regenerate, "
            "or `sybermem digest status` to see which sources drifted."
        )
    # Backlog heads-up: enough undigested work has accumulated to be worth compressing.
    # Complements the stale check (which only fires for EXISTING drifted digests) so a
    # long-running project that keeps recording but never digests still gets a signal.
    if digest_status["uncovered"] >= DIGEST_BACKLOG_THRESHOLD:
        age_note = (
            f" (last digest {digest_status['days_since_latest_digest']}d ago)"
            if digest_status["has_digest"] and digest_status["days_since_latest_digest"] > 0
            else ""
        )
        lines.append(
            f"⭐ Digest heads-up: {digest_status['uncovered']} records are not covered by any digest yet"
            f"{age_note}. Consider /sybermem-digest to compress the accumulated work."
        )

    if conclusions:
        lines.append("")
        lines.append("Key Conclusions:")
        # Only inject the most recent 5 conclusions to keep context lean
        for c in conclusions[-5:]:
            lines.append(c)

    return "\n".join(lines)


def main() -> int:
    root = resolve_sybermem_root()
    if root is None:
        return 0

    context = build_context(root)

    output = json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    })
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
