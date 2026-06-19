#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def check_json(path: Path) -> None:
    if not path.is_file():
        fail(f"Missing file: {path.relative_to(ROOT)}")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")


check_json(ROOT / ".claude-plugin" / "plugin.json")
check_json(ROOT / ".claude-plugin" / "marketplace.json")
check_json(ROOT / "hooks" / "hooks.json")

skills_dir = ROOT / "skills"
if not skills_dir.is_dir():
    fail("Missing directory: skills")

skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
if len(skill_dirs) < 8:
    fail(f"Expected at least 8 skill directories in skills/, found {len(skill_dirs)}")

required_files = [
    ROOT / "GEMINI.md",
    ROOT / ".cursor-plugin" / "plugin.json",
    ROOT / ".codex-plugin" / "plugin.json",
    ROOT / ".kimi-plugin" / "plugin.json",
    ROOT / ".opencode" / "INSTALL.md",
]
for path in required_files:
    if not path.is_file():
        fail(f"Missing file: {path.relative_to(ROOT)}")


def claude_validate(target: Path) -> None:
    """Run `claude plugins validate` against a manifest when the CLI is available.

    Static JSON checks above catch syntax errors; this catches schema/path
    errors that only the real Claude CLI knows about (e.g. source path rules).
    """
    result = subprocess.run(
        ["claude", "plugins", "validate", str(target)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        fail(
            f"claude plugins validate failed for {target.relative_to(ROOT)}:\n"
            f"{result.stdout}{result.stderr}"
        )


claude_cli = shutil.which("claude")
if claude_cli:
    claude_validate(ROOT / ".claude-plugin" / "plugin.json")
    claude_validate(ROOT / ".claude-plugin" / "marketplace.json")
    print("OK (static checks + claude plugins validate)")
else:
    print("OK (static checks only; claude CLI not found, skipped plugins validate)")

