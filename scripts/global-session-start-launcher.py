#!/usr/bin/env python3
"""Global launcher for SyberMem SessionStart hook.

Resolves the SyberMem project root from the current working directory,
then delegates to the project-level session_start_context.py script.
Mirrors the pattern of global-stop-hook-launcher.py.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def resolve_sybermem_root() -> Path | None:
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


def main() -> int:
    root = resolve_sybermem_root()
    if root is None:
        return 0

    target = root / ".sybermem" / "hooks" / "session_start_context.py"
    if not target.is_file():
        return 0

    result = subprocess.run([sys.executable, str(target)], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
