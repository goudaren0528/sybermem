#!/usr/bin/env python3
"""Copy packaged Claude skills into the plugin-facing skills tree."""
from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = ROOT / "packages" / "claude-skills"
TARGET_ROOT = ROOT / "skills"


def iter_top_level_skill_dirs(source_root: Path) -> list[Path]:
    return sorted(path for path in source_root.iterdir() if path.is_dir())


def sync_skill_dir(source_dir: Path, target_root: Path) -> None:
    target_dir = target_root / source_dir.name
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)


def main() -> int:
    if not SOURCE_ROOT.is_dir():
        raise SystemExit(f"Missing source skill tree: {SOURCE_ROOT}")

    TARGET_ROOT.mkdir(exist_ok=True)

    for source_dir in iter_top_level_skill_dirs(SOURCE_ROOT):
        sync_skill_dir(source_dir, TARGET_ROOT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
