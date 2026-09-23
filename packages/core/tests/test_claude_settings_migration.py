import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from sybermem_core.claude_hook_contract import probe_claude_version, safe_child_timeout, supports_exec
from sybermem_core.project_refresh_settings import migrate_settings_file
from sybermem_core import project_refresh_settings as settings_module


def _hook(script, timeout=30):
    return {"type": "command", "command": f"python .sybermem/hooks/{script}", "timeout": timeout}


def _fixture(tmp_path):
    root = tmp_path / "project"
    path = root / ".claude" / "settings.json"
    path.parent.mkdir(parents=True)
    python = tmp_path / "python.exe"
    launcher = tmp_path / ".claude" / "sybermem" / "launch_hook.py"
    launcher.parent.mkdir(parents=True)
    python.touch()
    launcher.touch()
    template = {"hooks": {
        "UserPromptSubmit": [{"hooks": [_hook("user_prompt.py", 30)]}],
        "SessionStart": [{"hooks": [_hook("session_start_context.py", 30)]}],
        "Stop": [{"hooks": [_hook("record_change_on_stop.py", 60), _hook("recall_outcome_on_stop.py", 30)]}],
    }}
    return root, path, python, launcher, json.dumps(template)


def test_version_contract():
    from subprocess import CompletedProcess, TimeoutExpired

    for text, expected in [(b"Claude Code 2.1.280\n", (2, 1, 280)), (b"2.1.280 (Claude Code)", (2, 1, 280)), (b"2.1.139", (2, 1, 139)),
                           (b"2.1.138", (2, 1, 138)), (b"2.1.280-rc1", None), (b"unknown", None)]:
        assert probe_claude_version(runner=lambda *a, **k: CompletedProcess([], 0, text)) == expected
    assert probe_claude_version(runner=lambda *a, **k: CompletedProcess([], 1, b"2.1.280")) is None
    assert probe_claude_version(runner=lambda *a, **k: CompletedProcess([], 0, b"2.1.280" + b" " * 8192)) is None
    assert probe_claude_version(runner=lambda *a, **k: (_ for _ in ()).throw(TimeoutExpired("claude", 3))) is None
    assert supports_exec((2, 1, 139)) and not supports_exec((2, 1, 138)) and not supports_exec(None)
    assert safe_child_timeout(30) == 20 and safe_child_timeout(10) == 5
    with pytest.raises(ValueError):
        safe_child_timeout(6)


def test_migrate_preserves_order_and_idempotence(tmp_path, monkeypatch):
    root, path, python, launcher, template = _fixture(tmp_path)
    monkeypatch.setattr("sybermem_core.claude_hook_contract.LAUNCHER_PATH", launcher)
    third = {"type": "command", "command": "python third/user_prompt.py", "custom": True}
    old = {"hooks": {
        "UserPromptSubmit": [{"hooks": [third, _hook("detect_record_intent.py"), _hook("task_recall.py")], "matcher": ""}],
        "Stop": [{"hooks": [_hook("record_change_on_stop.py"), third]}],
    }, "permissions": {"allow": ["Bash(*)"]}}
    path.write_text(json.dumps(old))
    assert migrate_settings_file(root, template, version=(2, 1, 280), python=python, launcher=launcher) == "enabled"
    migrated = json.loads(path.read_text())
    assert json.loads(path.with_name("settings.json.sybermem.bak").read_text()) == old
    assert migrated["permissions"] == old["permissions"]
    prompt = migrated["hooks"]["UserPromptSubmit"][0]["hooks"]
    assert prompt[0] == third and len(prompt) == 2
    assert prompt[1]["type"] == "exec" and prompt[1]["command"] == str(python)
    assert prompt[1]["args"] == [str(launcher), "user_prompt", "--timeout-seconds", "20"]
    assert migrated["hooks"]["Stop"][0]["hooks"][1] == third
    assert [h["args"][1] for g in migrated["hooks"]["Stop"] for h in g["hooks"] if h["type"] == "exec"] == ["record_change_on_stop", "recall_outcome_on_stop"]
    before = path.read_bytes()
    assert migrate_settings_file(root, template, version=(2, 1, 280), python=python, launcher=launcher) == "fresh"
    assert path.read_bytes() == before


def test_old_host_disables_only_owned_and_does_not_install_new(tmp_path):
    root, path, python, launcher, template = _fixture(tmp_path)
    assert migrate_settings_file(root, template, version=(2, 1, 138)) == "disabled_requires_upgrade"
    assert not path.exists()
    third = {"type": "command", "command": "python elsewhere/user_prompt.py"}
    old = {"hooks": {"UserPromptSubmit": [{"hooks": [third, _hook("user_prompt.py")]}]}}
    path.write_text(json.dumps(old))
    assert migrate_settings_file(root, template, version=(2, 1, 138)) == "disabled_requires_upgrade"
    assert json.loads(path.read_text())["hooks"]["UserPromptSubmit"][0]["hooks"] == [third]


def _unknown_placeholder_fixture(tmp_path):
    root, path, python, launcher, template = _fixture(tmp_path)
    third = {"type": "command", "command": "python thirdparty.py"}
    unknown = {"type": "sybermem-template", "command": "python .sybermem/hooks/unknown.py"}
    old = {"permissions": {"allow": ["Bash(*)"]}, "hooks": {
        "UserPromptSubmit": [{"matcher": "", "hooks": [unknown, third]}],
    }}
    original = (json.dumps(old, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    path.write_bytes(original)
    backup = path.with_name(path.name + ".sybermem.bak")
    return root, path, template, old, third, original, backup


def test_old_host_unknown_placeholder_cleanup_transaction(tmp_path):
    root, path, template, old, third, original, backup = _unknown_placeholder_fixture(tmp_path)
    assert migrate_settings_file(root, template, version=(2, 1, 138)) == "disabled_requires_upgrade"
    assert backup.read_bytes() == original
    cleaned = json.loads(path.read_text())
    assert cleaned["permissions"] == old["permissions"]
    assert cleaned["hooks"]["UserPromptSubmit"] == [{"matcher": "", "hooks": [third]}]
    before = path.read_bytes()
    assert migrate_settings_file(root, template, version=(2, 1, 138)) == "disabled_requires_upgrade"
    assert path.read_bytes() == before
    assert backup.read_bytes() == original


def test_old_host_unknown_only_placeholder_removed(tmp_path):
    root, path, _, _, _, _, backup = _unknown_placeholder_fixture(tmp_path)
    unknown_only = {"hooks": {"Stop": [{"hooks": [
        {"type": "sybermem-template", "command": "python .sybermem/hooks/unknown.py"},
    ]}]}}
    original = json.dumps(unknown_only, separators=(",", ":")).encode()
    path.write_bytes(original)
    assert migrate_settings_file(root, "{}", version=(2, 1, 138)) == "disabled_requires_upgrade"
    assert backup.read_bytes() == original
    assert json.loads(path.read_text())["hooks"]["Stop"] == []
    before = path.read_bytes()
    assert migrate_settings_file(root, "{}", version=(2, 1, 138)) == "disabled_requires_upgrade"
    assert path.read_bytes() == before
    assert backup.read_bytes() == original


def test_old_host_unknown_placeholder_dry_run(tmp_path):
    root, path, template, _, _, original, backup = _unknown_placeholder_fixture(tmp_path)
    assert migrate_settings_file(root, template, version=(2, 1, 138), dry_run=True) == "disabled_requires_upgrade"
    assert path.read_bytes() == original
    assert not backup.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_settings_junction_cannot_change_outside_settings(tmp_path):
    root, path, _, _, template = _fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    external = outside / "settings.json"
    original = json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": [_hook("user_prompt.py")] }]}}).encode()
    external.write_bytes(original)
    path.parent.rmdir()
    subprocess.run(["cmd", "/c", "mklink", "/J", str(path.parent), str(outside)],
                   check=True, capture_output=True)
    try:
        for dry_run in (False, True):
            assert migrate_settings_file(root, template, version=(2, 1, 138), dry_run=dry_run) == "error_unsafe_state"
            assert external.read_bytes() == original
            assert not (outside / "settings.json.sybermem.bak").exists()
    finally:
        path.parent.rmdir()


def test_backup_symlink_rejected_without_settings_change(tmp_path):
    root, path, _, _, template = _fixture(tmp_path)
    original = json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": [_hook("user_prompt.py")]}]}}).encode()
    path.write_bytes(original)
    outside = tmp_path / "outside-backup"
    outside.write_bytes(b"outside")
    backup = path.with_name(path.name + ".sybermem.bak")
    try:
        backup.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink not supported: {exc}")
    assert migrate_settings_file(root, template, version=(2, 1, 138)) == "error_unsafe_state"
    assert migrate_settings_file(root, template, version=(2, 1, 138), dry_run=True) == "error_unsafe_state"
    assert path.read_bytes() == original
    assert outside.read_bytes() == b"outside"


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_backup_junction_rejected_without_settings_change(tmp_path):
    root, path, _, _, template = _fixture(tmp_path)
    original = json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": [_hook("user_prompt.py")]}]}}).encode()
    path.write_bytes(original)
    outside = tmp_path / "outside-backup-directory"
    outside.mkdir()
    backup = path.with_name(path.name + ".sybermem.bak")
    subprocess.run(["cmd", "/c", "mklink", "/J", str(backup), str(outside)],
                   check=True, capture_output=True)
    try:
        assert migrate_settings_file(root, template, version=(2, 1, 138)) == "error_unsafe_state"
        assert path.read_bytes() == original
        assert list(outside.iterdir()) == []
    finally:
        backup.rmdir()


@pytest.mark.parametrize("failure", ["backup", "replace", "postwrite"])
def test_old_host_unknown_placeholder_failure_is_safe(tmp_path, monkeypatch, failure):
    root, path, template, old, third, original, backup = _unknown_placeholder_fixture(tmp_path)
    atomic = settings_module._atomic
    read_text = Path.read_text

    if failure in ("backup", "replace"):
        def failing_atomic(target, content):
            if (failure == "backup" and target == backup) or (failure == "replace" and target == path):
                raise OSError("injected write failure")
            return atomic(target, content)
        monkeypatch.setattr(settings_module, "_atomic", failing_atomic)
    else:
        def failing_verification(target, *args, **kwargs):
            if target == path and backup.exists():
                return "{}"  # Valid JSON that differs from the intended settings.
            return read_text(target, *args, **kwargs)
        monkeypatch.setattr(Path, "read_text", failing_verification)

    assert migrate_settings_file(root, template, version=(2, 1, 138)) == "error_unsafe_state"
    if failure == "backup":
        assert not backup.exists()
    else:
        assert backup.read_bytes() == original
    if failure != "postwrite":
        assert path.read_bytes() == original
    else:
        restored = json.loads(path.read_bytes())
        assert restored["permissions"] == old["permissions"]
        assert restored["hooks"]["UserPromptSubmit"] == [{"matcher": "", "hooks": [third]}]
        assert b"sybermem-template" not in path.read_bytes()


def test_missing_launcher_and_write_failure(tmp_path):
    root, path, python, launcher, template = _fixture(tmp_path)
    path.write_text(json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": [_hook("user_prompt.py")]}]}}))
    assert migrate_settings_file(root, template, version=(2, 1, 280), python=python, launcher=tmp_path / "missing") == "error_unsafe_state"
    assert json.loads(path.read_text())["hooks"]["UserPromptSubmit"] == []
    path.write_text(json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": [_hook("user_prompt.py")]}]}}))
    with patch("sybermem_core.project_refresh_settings.os.replace", side_effect=PermissionError):
        assert migrate_settings_file(root, template, version=(2, 1, 280), python=python, launcher=launcher) == "error_unsafe_state"


def test_session_matcher_scopes_remain_distinct(tmp_path, monkeypatch):
    root, path, python, launcher, template = _fixture(tmp_path)
    monkeypatch.setattr("sybermem_core.claude_hook_contract.LAUNCHER_PATH", launcher)
    third = {"type": "command", "command": "python custom.py"}
    path.write_text(json.dumps({"hooks": {"SessionStart": [
        {"matcher": "startup", "hooks": [_hook("session_start_context.py"), third]},
        {"matcher": "resume", "hooks": [_hook("session_start_context.py")]},
        {"matcher": "resume", "hooks": [_hook("session_start_context.py")]},
    ]}}))
    assert migrate_settings_file(root, template, version=(2, 1, 280), python=python, launcher=launcher) == "enabled"
    groups = json.loads(path.read_text())["hooks"]["SessionStart"]
    assert [group.get("matcher") for group in groups] == ["startup", "resume"]
    assert groups[0]["hooks"][1] == third
    assert all(group["hooks"][0]["args"][1] == "session_start_context" for group in groups)
    before = path.read_bytes()
    assert migrate_settings_file(root, template, version=(2, 1, 280), python=python, launcher=launcher) == "fresh"
    assert path.read_bytes() == before
