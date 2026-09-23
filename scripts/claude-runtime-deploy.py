"""Deploy only the managed Claude hook runtime, rejecting links before any write.

This protects against pre-existing symlinks/junctions, not concurrent path swaps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys


HOOKS = {
    "launch_record_change_on_stop.py": "record_change_on_stop",
    "launch_session_start_context.py": "session_start_context",
    "launch_user_prompt.py": "user_prompt",
    "launch_recall_outcome_on_stop.py": "recall_outcome_on_stop",
}
SOURCES = {
    "launch_hook.py": "global-hook-launcher.py",
    "managed-install.json": "managed-install.json",
    "safe-managed-remove.py": "safe-managed-remove.py",
    "opencode-install.py": "opencode-install.py",
    "VERSION": "../VERSION",
}


def _plain(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise RuntimeError(f"Claude runtime unsafe linked path: {part}")


def verify_deployment(root: Path, home: Path) -> None:
    """Read-only acceptance of the actual installed bytes; never import or run hooks."""
    root = Path(os.path.abspath(root))
    target = Path(os.path.abspath(home)) / ".claude" / "sybermem"
    sources = {name: root / "scripts" / filename for name, filename in SOURCES.items()}
    if not sources["VERSION"].is_file():
        sources.pop("VERSION")
    try:
        python = Path(sys.executable)
        if not python.is_absolute() or not python.is_file() or not os.access(python, os.X_OK):
            raise RuntimeError("real Python executable unavailable")
        manifest = json.loads((target / "managed-install.json").read_text(encoding="utf-8"))
        expected = {*sources, *HOOKS}
        if not expected.issubset(set(manifest["runtime_files"])):
            raise RuntimeError("manifest omits managed runtime files")
        for name in expected:
            path = target / name
            _plain(path)
            data = path.read_bytes()
            if name in sources and hashlib.sha256(data).digest() != hashlib.sha256(sources[name].read_bytes()).digest():
                raise RuntimeError(f"runtime byte mismatch: {name}")
            if name.endswith(".py"):
                compile(data, str(path), "exec")  # No pyc and no real project hook execution.
            if name in HOOKS and (f"{HOOKS[name]!r}".encode() not in data or b"from launch_hook import main" not in data):
                raise RuntimeError(f"runtime shim invalid: {name}")
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        raise RuntimeError("Claude runtime deployment not verified") from exc


def deploy(root: Path, home: Path) -> None:
    root = Path(os.path.abspath(root))
    home = Path(os.path.abspath(home))
    target = home / ".claude" / "sybermem"
    sources = {name: root / "scripts" / filename for name, filename in SOURCES.items()}
    if not sources["VERSION"].is_file():
        sources.pop("VERSION")
    names = (*sources, *HOOKS)
    # Batch validation: no target may be written if any target/source is unsafe.
    for name in names:
        _plain(target / name)
    for source in sources.values():
        _plain(source)
        if not source.is_file() or not source.resolve().is_relative_to(root.resolve()):
            raise RuntimeError(f"Claude runtime source missing or outside checkout: {source}")
    _plain(target)
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        _plain(target / name)  # Recheck immediately before each write.
        if name in sources:
            _plain(sources[name])
            shutil.copy2(sources[name], target / name)
        else:
            (target / name).write_text(
                "from pathlib import Path\nimport sys\n"
                "sys.path.insert(0, str(Path(__file__).resolve().parent))\n"
                "from launch_hook import main\n"
                f"sys.argv = [sys.argv[0], {HOOKS[name]!r}, *sys.argv[1:]]\n"
                "raise SystemExit(main())\n", encoding="utf-8")
    verify_deployment(root, home)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--home", type=Path, required=True)
    options = parser.parse_args()
    try:
        deploy(options.root, options.home)
    except (OSError, ValueError, RuntimeError, SyntaxError, KeyError, TypeError):
        print("Claude runtime deployment failed verification; installation not accepted.", file=sys.stderr)
        raise SystemExit(1)
