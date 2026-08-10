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


def build_context(root: Path) -> str:
    """Build the additionalContext string for Claude Code."""
    index_path = root / ".sybermem" / "INDEX.md"
    if not index_path.is_file():
        return "SyberMem startup context:\nNo .sybermem/INDEX.md found. Run /sybermem-init-project to initialize."

    index_text = index_path.read_text(encoding="utf-8")
    conclusions = parse_conclusions(index_text)
    topics = parse_topic_index(index_text)
    phase_info = parse_phase_index(root)
    project_info = parse_project_identity(root)

    lines: list[str] = ["SyberMem startup context:"]

    if project_info["exists"] and project_info.get("slug"):
        lines.append(f"Project: {project_info['slug']} ({project_info.get('project_id', 'no id')}).")

    lines.append(f"Loaded {len(conclusions)} key conclusions from SyberMem.")

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
