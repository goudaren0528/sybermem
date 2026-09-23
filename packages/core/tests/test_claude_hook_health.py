"""Read-only health diagnostic for Claude managed hook deployment."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from sybermem_core import claude_hook_contract as contract
from sybermem_core.project_refresh_settings import migrate_settings_file


ROOT = Path(__file__).resolve().parents[3]
CANONICAL = ROOT / "packages/claude-skills/sybermem-init-project/project-files"
MIRROR = ROOT / "skills/sybermem-init-project/project-files"
HEALTH = CANONICAL / ".sybermem/hooks/check_project_health.py"


def load_health():
    spec = importlib.util.spec_from_file_location("claude_project_health_test", HEALTH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def health(monkeypatch):
    monkeypatch.setattr(contract, "probe_claude_version", lambda: contract.MIN_EXEC_VERSION)
    return load_health()


def settings(root, hooks):
    path = root / ".claude/settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"env": {"SYBERMEM_RECORD_MODE": "remind"}, "hooks": hooks}), encoding="utf-8")


def group(hook):
    return [{"hooks": [hook]}]


def entry(identity, timeout=30):
    return {"type": "exec", "command": sys.executable,
            "args": [str(contract.LAUNCHER_PATH), identity, "--timeout-seconds", str(contract.safe_child_timeout(timeout))],
            "timeout": timeout}


def test_template_is_not_executable_and_mirror_is_identical():
    template = json.loads((CANONICAL / ".claude/settings.json").read_text(encoding="utf-8-sig"))
    for groups in template["hooks"].values():
        for item in groups:
            for hook in item["hooks"]:
                assert hook["type"] != "command"
                assert hook["type"] == "sybermem-template"
    for rel in (".claude/settings.json", ".sybermem/hooks/check_project_health.py"):
        assert (CANONICAL / rel).read_bytes() == (MIRROR / rel).read_bytes()


def test_relative_managed_detected_without_touching_third_party(health, tmp_path, monkeypatch):
    monkeypatch.setattr(contract, "LAUNCHER_PATH", tmp_path / "launch_hook.py")
    contract.LAUNCHER_PATH.write_text("# dummy\n", encoding="utf-8")
    settings(tmp_path, {"UserPromptSubmit": group({"type": "command", "command": "python .sybermem/hooks/user_prompt.py"}),
                        "Stop": group({"type": "command", "command": "third-party-hook --private"})})
    result = health.check_settings_json(tmp_path)
    assert result["status"] == "error"
    assert any("relative" in error for error in result["errors"])
    assert all("third-party" not in error for error in result["errors"])
    assert any("sybermem project refresh" in error for error in result["errors"])


def test_missing_launcher_python_target_and_unsafe_timeout(health, tmp_path, monkeypatch):
    launcher = tmp_path / "launch_hook.py"
    monkeypatch.setattr(contract, "LAUNCHER_PATH", launcher)
    hook = entry("user_prompt")
    hook["command"] = str(tmp_path / "missing-python")
    hook["args"][3] = "30"
    settings(tmp_path, {"UserPromptSubmit": group(hook)})
    errors = health.check_settings_json(tmp_path)["errors"]
    assert any("Python executable" in x for x in errors)
    assert any("launcher" in x for x in errors)
    assert any("target hook" in x for x in errors)
    assert any("unsafe timeout" in x for x in errors)


def test_unknown_or_old_host_is_error(health, tmp_path, monkeypatch):
    for version in (None, (2, 1, 138)):
        monkeypatch.setattr(contract, "probe_claude_version", lambda: version)
        settings(tmp_path, {})
        assert any("upgrade Claude Code" in x for x in health.check_settings_json(tmp_path)["errors"])


def test_read_only_main_does_not_self_update(health, tmp_path, monkeypatch, capsys):
    (tmp_path / ".sybermem").mkdir()
    (tmp_path / ".sybermem/project.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    settings(tmp_path, {})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(health, "GLOBAL_TEMPLATE_PROJECT_FILES", (tmp_path / "globally-installed",))
    monkeypatch.setattr(health.subprocess, "run", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must not launch hooks or self-update")))
    monkeypatch.setattr(health, "resolve_sybermem_root", lambda: tmp_path)
    assert health.main(read_only=True) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["files"][".claude/settings.json"]["status"] == "error"
    assert report["overall"] == "needs_update"


def test_core_unavailable_valid_exec_reports_without_running_anything(health, tmp_path, monkeypatch):
    launcher = tmp_path / "launch_hook.py"
    launcher.write_text("# launcher\n", encoding="utf-8")
    monkeypatch.setattr(contract, "LAUNCHER_PATH", launcher)
    hook = entry("user_prompt")
    settings(tmp_path, {"UserPromptSubmit": group(hook)})
    original = (tmp_path / ".claude/settings.json").read_bytes()
    monkeypatch.setattr(health, "_contract", lambda: None)
    monkeypatch.setattr(health.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no hooks or self-update")))
    result = health.check_settings_json(tmp_path)
    assert result["status"] == "error"
    assert any("core hook contract unavailable" in error for error in result["errors"])
    assert result["has_user_prompt_hook"] is False
    assert (tmp_path / ".claude/settings.json").read_bytes() == original


def test_displaced_same_name_is_not_claimed_or_removed_on_refresh(health, tmp_path, monkeypatch):
    launcher = tmp_path / "managed" / "launch_hook.py"
    launcher.parent.mkdir()
    launcher.write_text("# launcher\n", encoding="utf-8")
    monkeypatch.setattr(contract, "LAUNCHER_PATH", launcher)
    displaced = tmp_path / "third-party" / "launch_hook.py"
    foreign = entry("user_prompt")
    foreign["args"][0] = str(displaced)
    settings(tmp_path, {"UserPromptSubmit": group(foreign)})
    before = health.check_settings_json(tmp_path)
    assert before["status"] == "error"
    assert not before["has_user_prompt_hook"]
    assert any("managed hook missing" in error for error in before["errors"])
    assert any("project refresh preserves it" in warning for warning in before["warnings"])
    assert all("launcher path not managed" not in error for error in before["errors"])

    template = (CANONICAL / ".claude/settings.json").read_text(encoding="utf-8-sig")
    assert migrate_settings_file(tmp_path, template, version=contract.MIN_EXEC_VERSION,
                                 python=Path(sys.executable), launcher=launcher) == "enabled"
    updated = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    user_hooks = [hook for group_item in updated["hooks"]["UserPromptSubmit"] for hook in group_item["hooks"]]
    assert foreign in user_hooks
    assert any(hook["args"][0] == str(launcher) for hook in user_hooks if hook is not foreign)
    after = health.check_settings_json(tmp_path)
    assert after["has_user_prompt_hook"]
    assert any("project refresh preserves it" in warning for warning in after["warnings"])
    assert all("launcher path not managed" not in error for error in after["errors"])
    assert all("third-party" not in error for error in after["errors"])
    assert migrate_settings_file(tmp_path, template, version=contract.MIN_EXEC_VERSION,
                                 python=Path(sys.executable), launcher=launcher) == "fresh"
