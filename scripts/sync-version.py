#!/usr/bin/env python3
"""Single-source the SyberMem version.

Reads the repo-root ``VERSION`` file and rewrites the version string into every
distribution manifest so the 8 sites can never silently diverge:

- packages/core/pyproject.toml   (``version = "..."``)
- packages/cli/pyproject.toml    (``version = "..."``)
- .claude-plugin/plugin.json     (``"version": "..."``)
- .claude-plugin/marketplace.json(``"version": "..."``)
- .codex-plugin/plugin.json      (``"version": "..."``)
- .cursor-plugin/plugin.json     (``"version": "..."``)
- .kimi-plugin/plugin.json       (``"version": "..."``)
- gemini-extension.json          (``"version": "..."``)

Edits are minimal regex substitutions on the version line only; unrelated
content and formatting are preserved. Idempotent: running twice is a no-op.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PYPROJECT_FILES = [
    ROOT / "packages" / "core" / "pyproject.toml",
    ROOT / "packages" / "cli" / "pyproject.toml",
]
JSON_FILES = [
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / ".codex-plugin" / "plugin.json",
    ROOT / ".cursor-plugin" / "plugin.json",
    ROOT / ".kimi-plugin" / "plugin.json",
    ROOT / "gemini-extension.json",
]

PYPROJECT_RE = re.compile(r'(?m)^(version\s*=\s*")[^"]*(")')
JSON_RE = re.compile(r'("version"\s*:\s*")[^"]*(")')


def read_version() -> str:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise SystemExit("VERSION file is empty")
    return version


def _apply(path: Path, pattern: re.Pattern[str], version: str) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text, count = pattern.subn(rf'\g<1>{version}\g<2>', text)
    if count == 0:
        raise SystemExit(f"no version field found in {path.relative_to(ROOT).as_posix()}")
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def sync(version: str) -> list[str]:
    changed: list[str] = []
    for path in PYPROJECT_FILES:
        if _apply(path, PYPROJECT_RE, version):
            changed.append(path.relative_to(ROOT).as_posix())
    for path in JSON_FILES:
        if _apply(path, JSON_RE, version):
            changed.append(path.relative_to(ROOT).as_posix())
    return changed


def main() -> int:
    version = read_version()
    changed = sync(version)
    if changed:
        print(f"synced version {version} into {len(changed)} file(s):")
        for name in changed:
            print(f"  - {name}")
    else:
        print(f"all manifests already at version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
