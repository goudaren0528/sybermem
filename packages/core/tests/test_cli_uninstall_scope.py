from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
CODEX_HOOKS = ("sybermem_user_prompt.py", "sybermem_session_start.py", "sybermem_stop.py", "sybermem_post_compact.py")


def _pythonpath() -> str:
    parts = [str(ROOT / "packages" / "core"), str(ROOT / "packages" / "cli")]
    existing = os.environ.get("PYTHONPATH")
    if existing:
        parts.append(existing)
    return os.pathsep.join(parts)


def _run_cli(args: list[str], cwd: Path, home: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": _pythonpath(), "USERPROFILE": str(home), "HOME": str(home)}
    return subprocess.run(
        [sys.executable, "-m", "sybermem_cli.main", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _seed_global_install(home: Path) -> None:
    manifest = json.loads((ROOT / "scripts" / "managed-install.json").read_text(encoding="utf-8"))
    for root in (home / ".claude" / "skills", home / ".config" / "opencode" / "skills", home / ".agents" / "skills"):
        for name in [*manifest["skills"], *manifest["retired_skills"]]:
            skill = root / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("managed\n", encoding="utf-8")

    runtime = home / ".claude" / "sybermem"
    (runtime / "cli").mkdir(parents=True)
    (runtime / "cli" / "sybermem.cmd").write_text("managed\n", encoding="utf-8")
    for name in ("launch_record_change_on_stop.py", "launch_session_start_context.py", "VERSION"):
        (runtime / name).write_text("managed\n", encoding="utf-8")
    shutil.copy2(ROOT / "scripts" / "managed-install.json", runtime / "managed-install.json")
    shutil.copy2(ROOT / "scripts" / "safe-managed-remove.py", runtime / "safe-managed-remove.py")

    plugin = home / ".config" / "opencode" / "plugins" / "sybermem.ts"
    plugin.parent.mkdir(parents=True)
    plugin.write_text("managed\n", encoding="utf-8")

    codex = home / ".codex" / "hooks"
    codex.mkdir(parents=True)
    for name in CODEX_HOOKS:
        (codex / name).write_text("managed\n", encoding="utf-8")
    (home / ".codex" / "hooks.json").write_text(
        '{"hooks":{"SessionStart":[{"type":"command","command":"python sybermem_session_start.py"},{"type":"command","command":"python other.py"}]}}',
        encoding="utf-8",
    )


def test_top_level_project_scope_uninstall_deactivates_current_project(tmp_path: Path) -> None:
    # Given: a managed project with Claude runtime wiring and durable records
    project = tmp_path / "project"
    nested = project / "src"
    nested.mkdir(parents=True)
    (project / ".sybermem" / "changes").mkdir(parents=True)
    record = project / ".sybermem" / "changes" / "change-abc.md"
    record.write_text("history\n", encoding="utf-8")
    settings = project / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text('{"env":{"SYBERMEM_RECORD_MODE":"auto","KEEP":"1"},"hooks":{"SessionStart":[1],"Other":[2]}}', encoding="utf-8")

    # When: the new top-level uninstall command is scoped to the current project
    result = _run_cli(["uninstall", "--scope", "project", "--format", "json"], cwd=nested, home=tmp_path / "home")

    # Then: project runtime is deactivated while record history survives
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "project_deactivated"
    assert record.read_text(encoding="utf-8") == "history\n"
    updated = json.loads(settings.read_text(encoding="utf-8"))
    assert updated == {"env": {"KEEP": "1"}, "hooks": {"Other": [2]}}


def test_global_scope_requires_explicit_confirmation(tmp_path: Path) -> None:
    # Given: a globally installed SyberMem runtime
    home = tmp_path / "home"
    _seed_global_install(home)

    # When: global uninstall is requested without confirmation
    result = _run_cli(["uninstall", "--scope", "global"], cwd=tmp_path, home=home)

    # Then: it refuses before removing tools or hooks
    assert result.returncode == 2
    assert "--yes" in result.stderr
    assert (home / ".claude" / "sybermem" / "cli").exists()


def test_global_scope_uninstall_cleans_tools_hooks_and_keeps_project_records(tmp_path: Path) -> None:
    # Given: a global install plus a separate project history directory
    home = tmp_path / "home"
    _seed_global_install(home)
    project_record = tmp_path / "project" / ".sybermem" / "changes" / "change-abc.md"
    project_record.parent.mkdir(parents=True)
    project_record.write_text("history\n", encoding="utf-8")

    # When: global uninstall is explicitly confirmed
    result = _run_cli(["uninstall", "--scope", "global", "--yes", "--format", "json"], cwd=tmp_path, home=home)

    # Then: managed global hooks/tools are removed and project records survive
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "global_uninstalled"
    assert project_record.read_text(encoding="utf-8") == "history\n"
    assert not (home / ".claude" / "sybermem" / "cli").exists()
    assert not (home / ".config" / "opencode" / "plugins" / "sybermem.ts").exists()
    for name in CODEX_HOOKS:
        assert not (home / ".codex" / "hooks" / name).exists()
    hooks_json = (home / ".codex" / "hooks.json").read_text(encoding="utf-8")
    assert "sybermem_session_start.py" not in hooks_json
    assert "other.py" in hooks_json
