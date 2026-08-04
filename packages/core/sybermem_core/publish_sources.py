from __future__ import annotations

from pathlib import Path


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
            changed.append(str(dst).replace('\\', '/'))
    return len(files), changed
