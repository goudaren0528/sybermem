#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final


ROOT: Final = Path(os.environ.get("SYBERMEM_CHECK_ROOT", Path(__file__).resolve().parent.parent)).resolve()

DISTRIBUTION_SCRIPTS: Final = [
    Path("scripts/install.sh"),
    Path("scripts/install.ps1"),
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
    Path("scripts/uninstall.sh"),
    Path("scripts/uninstall.ps1"),
]
VISIBLE_SKILL_SCRIPTS: Final = [
    Path("scripts/install.sh"),
    Path("scripts/install.ps1"),
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
]
OPENCODE_PLUGIN_UPDATE_SCRIPTS: Final = [
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
]
REMOTE_INSTALL_SCRIPTS: Final = [
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
]
NO_CACHE_ROOTS: Final = [
    Path("packages/claude-skills"),
    Path("packages/core"),
    Path("packages/cli"),
    Path("skills"),
]
PUBLIC_DOCS: Final = [
    Path("README.md"),
    Path("README.en.md"),
    Path("INSTALL.md"),
    Path("CHANGELOG.md"),
    Path("GEMINI.md"),
    Path(".opencode/INSTALL.md"),
]
PACKAGE_METADATA: Final = [
    Path(".claude-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
    Path(".cursor-plugin/plugin.json"),
    Path(".codex-plugin/plugin.json"),
    Path(".kimi-plugin/plugin.json"),
    Path("gemini-extension.json"),
    Path("hooks/hooks.json"),
    Path("packages/core/pyproject.toml"),
    Path("packages/cli/pyproject.toml"),
]


def rel(path: Path, root: Path) -> str:
    """Return a stable repository-relative path for diagnostics."""
    return path.relative_to(root).as_posix()


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def check_json(path: Path, root: Path) -> None:
    if not path.is_file():
        fail(f"Missing file: {rel(path, root)}")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {rel(path, root)}: {exc}")


def check_hook_wiring(root: Path) -> None:
    hook_path = root / "hooks" / "user-prompt-submit"
    if not hook_path.is_file():
        fail("Missing file: hooks/user-prompt-submit")
    if hook_path.suffix:
        fail("hooks/user-prompt-submit must remain extensionless")

    hook_text = hook_path.read_text(encoding="utf-8")
    required_fragments = [
        "CLAUDE_PROJECT_DIR:-$(pwd)",
        "$root/.sybermem/hooks/user_prompt.py",
        "$root/.sybermem/hooks/task_recall.py",
        'python "$script" "$@"',
        "2>/dev/null || exit 0",
    ]
    for fragment in required_fragments:
        if fragment not in hook_text:
            fail(f"hooks/user-prompt-submit is missing required wiring: {fragment}")

    hooks_path = root / "hooks" / "hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))["hooks"]
    for event_name in ["SessionStart", "Stop", "UserPromptSubmit"]:
        if event_name not in hooks:
            fail(f"hooks/hooks.json is missing {event_name} hook entry")

    prompt_hooks = hooks["UserPromptSubmit"]
    commands = [
        hook["command"]
        for group in prompt_hooks
        for hook in group.get("hooks", [])
        if hook.get("type") == "command"
    ]
    expected_command = '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" user-prompt-submit'
    if expected_command not in commands:
        fail(f"hooks/hooks.json is missing command entry: {expected_command}")


def top_level_skill_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        fail(f"Missing directory: {rel(root, ROOT)}")
    return sorted(path for path in root.iterdir() if path.is_dir())


def skill_names(source_root: Path) -> list[str]:
    names = [path.name for path in top_level_skill_dirs(source_root)]
    if not names:
        fail(f"No skill directories found in {rel(source_root, ROOT)}")
    for name in names:
        skill_file = source_root / name / "SKILL.md"
        if not skill_file.is_file():
            fail(f"Skill {name} is missing {rel(skill_file, ROOT)}")
    return names


def relative_files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def check_skill_tree_parity(root: Path) -> list[str]:
    source_root = root / "packages" / "claude-skills"
    plugin_root = root / "skills"
    source_names = skill_names(source_root)
    plugin_names = skill_names(plugin_root)
    if source_names != plugin_names:
        fail(
            "Skill directory mismatch between packages/claude-skills and skills:\n"
            f"  source={source_names}\n"
            f"  plugin={plugin_names}"
        )

    for skill_name in source_names:
        source_dir = source_root / skill_name
        plugin_dir = plugin_root / skill_name
        source_files = relative_files(source_dir)
        plugin_files = relative_files(plugin_dir)
        if source_files != plugin_files:
            fail(
                f"Skill file mismatch for {skill_name}:\n"
                f"  source={','.join(path.as_posix() for path in source_files)}\n"
                f"  plugin={','.join(path.as_posix() for path in plugin_files)}"
            )
        for relative_path in source_files:
            source_file = source_dir / relative_path
            plugin_file = plugin_dir / relative_path
            if source_file.read_bytes() != plugin_file.read_bytes():
                fail(f"Skill mirror content differs: {rel(plugin_file, root)} != {rel(source_file, root)}")

    return source_names


def check_distribution_script_coverage(root: Path, names: list[str]) -> None:
    for script in DISTRIBUTION_SCRIPTS:
        script_path = root / script
        if not script_path.is_file():
            fail(f"Missing distribution script: {script.as_posix()}")
        script_text = script_path.read_text(encoding="utf-8")
        missing = [name for name in names if name not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing skill inventory entries: {', '.join(missing)}")

    for script in VISIBLE_SKILL_SCRIPTS:
        script_text = (root / script).read_text(encoding="utf-8")
        missing = [name for name in names if f"/{name}" not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing user-facing skill output: {', '.join(missing)}")


def check_opencode_plugin_update_wiring(root: Path) -> None:
    for script in OPENCODE_PLUGIN_UPDATE_SCRIPTS:
        script_text = (root / script).read_text(encoding="utf-8")
        required_fragments = [
            "packages/opencode-plugin/sybermem.ts" if script.suffix == ".sh" else "packages\\opencode-plugin\\sybermem.ts",
            ".config/opencode/plugins" if script.suffix == ".sh" else ".config\\opencode\\plugins",
            "sybermem.ts",
        ]
        missing = [fragment for fragment in required_fragments if fragment not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing OpenCode plugin update wiring: {', '.join(missing)}")


def check_remote_runtime_refresh_wiring(root: Path) -> None:
    for script in REMOTE_INSTALL_SCRIPTS:
        script_text = (root / script).read_text(encoding="utf-8")
        required_fragments = [
            "packages/core" if script.suffix == ".sh" else "packages\\core",
            "packages/cli" if script.suffix == ".sh" else "packages\\cli",
            "--upgrade",
            "--force-reinstall",
        ]
        missing = [fragment for fragment in required_fragments if fragment not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing remote runtime refresh wiring: {', '.join(missing)}")


def check_no_python_cache_artifacts(root: Path) -> None:
    offenders: list[str] = []
    for relative_root in NO_CACHE_ROOTS:
        tree = root / relative_root
        if not tree.exists():
            continue
        for path in tree.rglob("*"):
            if path.name == "__pycache__" or path.name == ".pytest_cache" or path.suffix == ".pyc":
                offenders.append(rel(path, root))
    if offenders:
        fail("Python cache artifacts must not be distributed:\n  " + "\n  ".join(sorted(offenders)))


def check_required_files(root: Path) -> None:
    for path in [*PUBLIC_DOCS, *PACKAGE_METADATA]:
        full_path = root / path
        if not full_path.is_file():
            fail(f"Missing file: {path.as_posix()}")
        if full_path.suffix == ".json":
            check_json(full_path, root)


def claude_validate(root: Path, target: Path) -> None:
    """Run `claude plugins validate` against a manifest when the CLI is available."""
    result = subprocess.run(
        ["claude", "plugins", "validate", str(target)],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        fail(f"claude plugins validate failed for {rel(target, root)}:\n{result.stdout}{result.stderr}")


VERSION_PYPROJECT_FILES: Final = [
    Path("packages/core/pyproject.toml"),
    Path("packages/cli/pyproject.toml"),
]
VERSION_JSON_FILES: Final = [
    Path(".claude-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
    Path(".codex-plugin/plugin.json"),
    Path(".cursor-plugin/plugin.json"),
    Path(".kimi-plugin/plugin.json"),
    Path("gemini-extension.json"),
]


def check_version_consistency(root: Path) -> None:
    import re

    version_file = root / "VERSION"
    if not version_file.is_file():
        fail("Missing file: VERSION (single-source version). Run scripts/sync-version.py.")
    expected = version_file.read_text(encoding="utf-8").strip()
    if not expected:
        fail("VERSION file is empty")

    pyproject_re = re.compile(r'(?m)^version\s*=\s*"([^"]*)"')
    for rel_path in VERSION_PYPROJECT_FILES:
        text = (root / rel_path).read_text(encoding="utf-8")
        match = pyproject_re.search(text)
        if not match or match.group(1) != expected:
            found = match.group(1) if match else "(none)"
            fail(f"{rel_path.as_posix()} version {found} != VERSION {expected}; run scripts/sync-version.py")

    for rel_path in VERSION_JSON_FILES:
        data = json.loads((root / rel_path).read_text(encoding="utf-8"))
        # marketplace.json nests the version under plugins[*]; others have it top-level.
        if "plugins" in data and isinstance(data["plugins"], list):
            versions = [p.get("version") for p in data["plugins"]]
            bad = [v for v in versions if v != expected]
            if bad or not versions:
                fail(f"{rel_path.as_posix()} plugin version {bad or '(none)'} != VERSION {expected}; run scripts/sync-version.py")
        elif data.get("version") != expected:
            fail(f"{rel_path.as_posix()} version {data.get('version')} != VERSION {expected}; run scripts/sync-version.py")


def main(root: Path = ROOT) -> int:
    check_required_files(root)
    check_hook_wiring(root)
    check_no_python_cache_artifacts(root)
    check_version_consistency(root)
    names = check_skill_tree_parity(root)
    check_distribution_script_coverage(root, names)
    check_opencode_plugin_update_wiring(root)
    check_remote_runtime_refresh_wiring(root)

    claude_cli = shutil.which("claude")
    if claude_cli:
        claude_validate(root, root / ".claude-plugin" / "plugin.json")
        claude_validate(root, root / ".claude-plugin" / "marketplace.json")
        print(f"OK ({len(names)} skills; static checks + claude plugins validate)")
    else:
        print(f"OK ({len(names)} skills; static checks only; claude CLI not found, skipped plugins validate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
