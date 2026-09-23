"""Integration contracts against the shipped Claude installation template."""
import json
from pathlib import Path

import pytest

from sybermem_core import claude_hook_contract as contract
from sybermem_core.project_refresh import refresh_project
from sybermem_core.project_refresh_settings import migrate_settings_file


CANONICAL_ROOT = Path(__file__).resolve().parents[3] / "packages" / "claude-skills" / "sybermem-init-project" / "project-files"
CANONICAL = (CANONICAL_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8-sig")
IDS = ["user_prompt", "session_start_context", "record_change_on_stop", "recall_outcome_on_stop"]


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    python = tmp_path / "python.exe"
    launcher = tmp_path / ".claude" / "sybermem" / "launch_hook.py"
    launcher.parent.mkdir(parents=True)
    python.touch()
    launcher.touch()
    monkeypatch.setattr(contract, "LAUNCHER_PATH", launcher)
    monkeypatch.setattr(contract, "executable_python", lambda: python)
    monkeypatch.setattr(contract, "probe_claude_version", lambda: (2, 1, 280))
    return python, launcher


def _managed(settings):
    return [h for event in ("UserPromptSubmit", "SessionStart", "Stop")
            for group in settings.get("hooks", {}).get(event, []) for h in group.get("hooks", [])
            if h.get("type") == "exec"]


def _no_placeholder(settings):
    return all(h.get("type") != "sybermem-template" for groups in settings.get("hooks", {}).values()
               if isinstance(groups, list) for group in groups if isinstance(group, dict)
               for h in group.get("hooks", []) if isinstance(h, dict))


def test_canonical_new_install_and_idempotent_upgrade(tmp_path, runtime):
    python, launcher = runtime
    project = tmp_path / "project"
    assert migrate_settings_file(project, CANONICAL, version=(2, 1, 280), python=python, launcher=launcher) == "enabled"
    path = project / ".claude" / "settings.json"
    hooks = _managed(json.loads(path.read_text()))
    assert [h["args"][1] for h in hooks] == IDS
    assert all(h["type"] == "exec" and h["command"] == str(python)
               and h["args"][0] == str(launcher) for h in hooks)
    assert [h["args"][3] for h in hooks] == ["5", "10", "20", "5"]
    assert _no_placeholder(json.loads(path.read_text()))
    before = path.read_bytes()
    assert migrate_settings_file(project, CANONICAL, version=(2, 1, 280), python=python, launcher=launcher) == "fresh"
    assert path.read_bytes() == before


def test_canonical_upgrade_preserves_user_matchers_and_overrides(tmp_path, runtime):
    python, launcher = runtime
    project = tmp_path / "project"
    path = project / ".claude" / "settings.json"
    path.parent.mkdir(parents=True)
    third = {"type": "command", "command": "python user_defined.py"}
    old = {"env": {"SYBERMEM_RECORD_MODE": "auto"}, "hooks": {
        "SessionStart": [
            {"matcher": "startup", "hooks": [{"type": "command", "command": "python .sybermem/hooks/session_start_context.py", "timeout": 30}, third]},
            {"matcher": "resume", "hooks": [{"type": "command", "command": "python .sybermem/hooks/session_start_context.py", "timeout": 30}]},
        ]}}
    path.write_text(json.dumps(old))
    assert migrate_settings_file(project, CANONICAL, version=(2, 1, 280), python=python, launcher=launcher) == "enabled"
    data = json.loads(path.read_text())
    assert data["env"]["SYBERMEM_RECORD_MODE"] == "auto"
    assert [g.get("matcher") for g in data["hooks"]["SessionStart"]] == ["startup", "resume"]
    assert data["hooks"]["SessionStart"][0]["hooks"][1] == third
    assert [h["args"][1] for h in _managed(data)] == IDS[:1] + [IDS[1]] * 2 + IDS[2:]
    assert _no_placeholder(data)
    before = path.read_bytes()
    assert migrate_settings_file(project, CANONICAL, version=(2, 1, 280), python=python, launcher=launcher) == "fresh"
    assert path.read_bytes() == before


def test_canonical_startup_only_does_not_add_unmatched_session(tmp_path, runtime):
    python, launcher = runtime
    project = tmp_path / "project"
    path = project / ".claude" / "settings.json"
    path.parent.mkdir(parents=True)
    third = {"type": "command", "command": "python custom.py"}
    path.write_text(json.dumps({"env": {"SYBERMEM_RECORD_MODE": "auto"}, "hooks": {
        "SessionStart": [{"matcher": "startup", "hooks": [third, {
            "type": "command", "command": "python .sybermem/hooks/session_start_context.py",
            "timeout": 40, "statusMessage": "keep"}]}]}}))
    assert migrate_settings_file(project, CANONICAL, version=(2, 1, 280), python=python, launcher=launcher) == "enabled"
    data = json.loads(path.read_text())
    groups = data["hooks"]["SessionStart"]
    assert len(groups) == 1 and groups[0]["matcher"] == "startup"
    assert groups[0]["hooks"][0] == third
    assert groups[0]["hooks"][1]["timeout"] == 40
    assert groups[0]["hooks"][1]["statusMessage"] == "keep"
    assert groups[0]["hooks"][1]["args"][3] == "20"
    assert data["env"]["SYBERMEM_RECORD_MODE"] == "auto"
    assert [h["args"][1] for h in _managed(data)] == IDS
    before = path.read_bytes()
    assert migrate_settings_file(project, CANONICAL, version=(2, 1, 280), python=python, launcher=launcher) == "fresh"
    assert path.read_bytes() == before


@pytest.mark.parametrize("version,missing", [((2, 1, 138), False), ((2, 1, 280), True)])
def test_canonical_unavailable_runtime_no_placeholder_or_version(tmp_path, runtime, monkeypatch, version, missing):
    python, launcher = runtime
    if missing:
        launcher.unlink()
    monkeypatch.setattr(contract, "probe_claude_version", lambda: version)
    project = tmp_path / "project"
    report = refresh_project(project, template_roots=(CANONICAL_ROOT,))
    assert report["overall"] == "failed"
    assert report["claude_hooks"] == ("error_unsafe_state" if missing else "disabled_requires_upgrade")
    path = project / ".claude" / "settings.json"
    assert not path.exists()
    assert "sybermem_version:" not in (project / ".sybermem" / "project.yaml").read_text()
    # Existing placeholders from a partially copied template must be disabled.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(CANONICAL)
    assert migrate_settings_file(project, CANONICAL, version=version, python=python, launcher=launcher) != "enabled"
    assert _no_placeholder(json.loads(path.read_text()))


def test_canonical_dry_run_does_not_write(tmp_path, runtime):
    python, launcher = runtime
    project = tmp_path / "project"
    assert migrate_settings_file(project, CANONICAL, version=(2, 1, 280), python=python,
                                 launcher=launcher, dry_run=True) == "enabled"
    assert not (project / ".claude").exists()
    path = project / ".claude" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(CANONICAL)
    before = path.read_bytes()
    assert migrate_settings_file(project, CANONICAL, version=(2, 1, 280), python=python,
                                 launcher=launcher, dry_run=True) == "enabled"
    assert path.read_bytes() == before
    assert not path.with_name(path.name + ".sybermem.bak").exists()


def test_unknown_placeholder_never_executed(tmp_path, runtime):
    python, launcher = runtime
    project = tmp_path / "project"
    template = json.loads(CANONICAL)
    template["hooks"]["Stop"][0]["hooks"].append({"type": "sybermem-template", "command": "python .sybermem/hooks/unknown.py"})
    assert migrate_settings_file(project, json.dumps(template), version=(2, 1, 280),
                                 python=python, launcher=launcher) == "enabled"
    settings = json.loads((project / ".claude" / "settings.json").read_text())
    assert [h["args"][1] for h in _managed(settings)] == IDS
    assert _no_placeholder(settings)
