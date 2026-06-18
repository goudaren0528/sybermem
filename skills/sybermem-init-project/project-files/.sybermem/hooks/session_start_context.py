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


def parse_conclusions(index_text: str) -> list[str]:
    match = re.search(
        r"## Key Conclusions\s*\n([\s\S]*?)(?=\n---|\n## )", index_text
    )
    if not match:
        return []
    return [
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith("- [")
    ]


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
    """Return phase-index metadata: status, last_git_boundary, active_phase, confirmed_count."""
    phase_path = root / ".sybermem" / "analysis" / "phase-index.md"
    if not phase_path.is_file():
        return {"exists": False}

    content = phase_path.read_text(encoding="utf-8")
    status_match = re.search(r"^- status:\s*(.+)", content, re.MULTILINE)
    boundary_match = re.search(r"^- last_git_boundary:\s*(\S+)", content, re.MULTILINE)
    phases = re.findall(r"### Phase: (.+)", content)

    return {
        "exists": True,
        "status": status_match.group(1).strip() if status_match else "unknown",
        "last_git_boundary": boundary_match.group(1).strip() if boundary_match else None,
        "active_phase": phases[-1] if phases else None,
        "confirmed_count": len(phases),
    }


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


def build_context(root: Path) -> str:
    """Build the additionalContext string for Claude Code."""
    index_path = root / ".sybermem" / "INDEX.md"
    if not index_path.is_file():
        return "SyberMem startup context:\nNo .sybermem/INDEX.md found. Run /sybermem-init-project to initialize."

    index_text = index_path.read_text(encoding="utf-8")
    conclusions = parse_conclusions(index_text)
    topics = parse_topic_index(index_text)
    phase_info = parse_phase_index(root)

    lines: list[str] = ["SyberMem startup context:"]
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

    if conclusions:
        lines.append("")
        lines.append("Key Conclusions:")
        for c in conclusions:
            lines.append(c)

    if topics:
        lines.append("")
        lines.append("Topic Index:")
        for topic, records in sorted(topics.items()):
            lines.append(f"- {topic}: {', '.join(records)}")

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
