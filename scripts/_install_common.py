from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Final


SKILLS: Final = (
    "sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-resume",
    "sybermem-digest", "sybermem-phase-analyze", "using-sybermem", "sybermem-update",
    "sybermem-search", "sybermem-link", "sybermem-theme-digest", "sybermem-habit",
    "sybermem-uninstall",
)
RETIRED_SKILLS: Final = ("sybermem-phase-confirm", "sybermem-team-publish", "sybermem-team-summary")
CODEX_EVENTS: Final = (
    ("UserPromptSubmit", "user_prompt.py", "sybermem_user_prompt.py", "SyberMem prompt context adds bounded Codex recall and habit reminders when relevant.", 6000),
    ("SessionStart", "session_start.py", "sybermem_session_start.py", "SyberMem session context adds bounded Codex startup context when available.", 6000),
    ("Stop", "stop.py", "sybermem_stop.py", "SyberMem Stop nudge adds bounded record reminders without looping.", None),
    ("PostCompact", "post_compact.py", "sybermem_post_compact.py", "SyberMem PostCompact marks compact re-seed for the next SessionStart.", None),
)


def _copy_tree(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True)


def _remove_managed(root: Path, name: str, remover: Path) -> None:
    subprocess.run(
        [sys.executable, str(remover), "child", "--root", str(root), "--name", name],
        check=True,
    )


def _sync_skills(source: Path, home: Path, remover: Path) -> None:
    for target, label in (
        (home / ".claude" / "skills", "Claude Code"),
        (home / ".config" / "opencode" / "skills", "OpenCode"),
        (home / ".agents" / "skills", "Codex"),
    ):
        target.mkdir(parents=True, exist_ok=True)
        for name in RETIRED_SKILLS:
            _remove_managed(target, name, remover)
        for name in SKILLS:
            skill_source = source / name
            if skill_source.is_dir():
                _remove_managed(target, name, remover)
                _copy_tree(skill_source, target / name)
                print(f"  [{label}] updated: /{name}")


def _install_codex_hooks(root: Path, home: Path) -> None:
    source_dir = root / ".codex" / "hooks"
    names = ("user_prompt.py", "session_start.py", "stop.py", "post_compact.py")
    if not all((source_dir / name).is_file() for name in names):
        print("  [Codex] skipped hooks: one or more sources were not found")
        return
    hook_dir = home / ".codex" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    installed = {name: hook_dir / f"sybermem_{name}" for name in names}
    for name, target in installed.items():
        shutil.copy2(source_dir / name, target)

    hooks_path = home / ".codex" / "hooks.json"
    data: dict[str, object] = {}
    if hooks_path.is_file():
        try:
            loaded = json.loads(hooks_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            loaded = {}
        if isinstance(loaded, dict):
            data = loaded
    raw_hooks = data.get("hooks")
    hooks: dict[str, object] = raw_hooks if isinstance(raw_hooks, dict) else {}
    data["hooks"] = hooks
    for event, source_name, installed_name, message, context_limit in CODEX_EVENTS:
        raw_handlers = hooks.get(event)
        handlers = raw_handlers if isinstance(raw_handlers, list) else ([] if raw_handlers is None else [raw_handlers])
        marker = installed_name
        kept = [handler for handler in handlers if not (isinstance(handler, dict) and marker in str(handler.get("command", "")))]
        managed: dict[str, object] = {"type": "command", "command": f'python "{installed[source_name]}"', "message": message}
        if context_limit is not None:
            managed["additionalContextLimit"] = context_limit
        hooks[event] = [*kept, managed]
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  [Codex] updated hooks.json without removing unrelated hooks: {hooks_path}")


def _install_runtime(root: Path, home: Path) -> None:
    launcher_dir = home / ".claude" / "sybermem"
    launcher_dir.mkdir(parents=True, exist_ok=True)
    for name in ("managed-install.json", "safe-managed-remove.py"):
        shutil.copy2(root / "scripts" / name, launcher_dir / name)
    shutil.copy2(root / "scripts" / "global-stop-hook-launcher.py", launcher_dir / "launch_record_change_on_stop.py")
    session_launcher = root / "scripts" / "global-session-start-launcher.py"
    if session_launcher.is_file():
        shutil.copy2(session_launcher, launcher_dir / "launch_session_start_context.py")

    cli_dir = launcher_dir / "cli"
    cli_dir.mkdir(parents=True, exist_ok=True)
    venv = cli_dir / "venv"
    python_exe = venv / ("Scripts" if os.name == "nt" else "bin") / "python"
    pip_exe = venv / ("Scripts" if os.name == "nt" else "bin") / "pip"
    if not python_exe.is_file():
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(pip_exe), "install", "--upgrade", "--force-reinstall", str(root / "packages" / "core"), str(root / "packages" / "cli")], check=True)
    if os.name == "nt":
        (cli_dir / "sybermem.cmd").write_text(
            '@echo off\nset "SYBERMEM_HOME=%USERPROFILE%\\.claude\\sybermem\\cli"\n"%SYBERMEM_HOME%\\venv\\Scripts\\sybermem.exe" %*\n',
            encoding="ascii",
        )
    else:
        wrapper = cli_dir / "sybermem"
        wrapper.write_text('#!/bin/sh\nexec "$HOME/.claude/sybermem/cli/venv/bin/sybermem" "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
    version = root / "VERSION"
    if version.is_file():
        shutil.copy2(version, launcher_dir / "VERSION")


def install_from_checkout(root: Path) -> None:
    """Install a checkout into all supported user-level SyberMem locations."""
    home = Path.home()
    remover = root / "scripts" / "safe-managed-remove.py"
    _sync_skills(root / "packages" / "claude-skills", home, remover)
    _install_codex_hooks(root, home)
    _install_runtime(root, home)
    plugin_dir = home / ".config" / "opencode"
    plugin_source = root / "packages" / "opencode-plugin" / "sybermem.ts"
    if plugin_dir.exists() and plugin_source.is_file():
        (plugin_dir / "plugins").mkdir(parents=True, exist_ok=True)
        shutil.copy2(plugin_source, plugin_dir / "plugins" / "sybermem.ts")
        print(f"  [OpenCode] updated plugin: {plugin_dir / 'plugins' / 'sybermem.ts'}")
