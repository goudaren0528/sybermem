from __future__ import annotations

from pathlib import Path


# Neutral digest-path lookups shared by non-Team features (resume, next-step, digest
# injection). These were historically hosted in publish_sources.py, which coupled ordinary
# digest-aware features to the Team publication subsystem. They live here so the Team code
# can be deprecated/removed without touching digest-aware behavior.


def latest_phase_digest(root: Path) -> str:
    digests_dir = root / ".sybermem" / "digests"
    if not digests_dir.is_dir():
        return ""
    files = sorted(digests_dir.glob("*.md"))
    return str(files[-1]).replace("\\", "/") if files else ""


def latest_theme_digest(root: Path) -> str:
    digests_dir = root / ".sybermem" / "theme-digests"
    if not digests_dir.is_dir():
        return ""
    files = sorted(digests_dir.glob("*.md"))
    return str(files[-1]).replace("\\", "/") if files else ""
