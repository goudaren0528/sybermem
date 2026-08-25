from __future__ import annotations

from pathlib import Path


# Team-only digest-history sync. The neutral digest-path lookups (latest_phase_digest /
# latest_theme_digest) moved to digest_sources.py so non-Team features no longer depend on
# the Team publication subsystem; only this Team-specific helper remains here.


def sync_markdown_history(src_dir: Path, dst_dir: Path) -> tuple[int, list[str]]:
    """Sync markdown files from src to dst and return total source count plus changed paths."""
    if not src_dir.is_dir():
        return 0, []

    dst_dir.mkdir(parents=True, exist_ok=True)
    changed = []
    files = sorted(src_dir.glob("*.md"))
    for src in files:
        dst = dst_dir / src.name
        src_text = src.read_text(encoding="utf-8")
        dst_text = dst.read_text(encoding="utf-8") if dst.is_file() else None
        if dst_text != src_text:
            dst.write_text(src_text, encoding="utf-8")
            changed.append(str(dst).replace("\\", "/"))
    return len(files), changed
