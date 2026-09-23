"""Isolated static health checks; never run project hooks."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sybermem_core import claude_hook_contract as contract
from sybermem_core.claude_hook_health import TARGETS, check_managed_claude_hooks


def _link(source: Path, destination: Path, *, directory: bool = False) -> None:
    try:
        if directory and os.name == "nt":
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(destination), str(source)], capture_output=True)
            if result.returncode:
                pytest.skip("junction creation unavailable")
        else:
            destination.symlink_to(source, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"link creation unavailable: {exc}")


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    root = tmp_path / "project"
    launcher = tmp_path / "runtime" / "launch_hook.py"
    launcher.parent.mkdir()
    launcher.write_text("raise RuntimeError('DO_NOT_RUN')\n")
    monkeypatch.setattr(contract, "LAUNCHER_PATH", launcher)
    targets = root / ".sybermem" / "hooks"
    targets.mkdir(parents=True)
    for name in TARGETS.values():
        (targets / name).write_text("raise RuntimeError('DO_NOT_RUN')\n")
    events = {"UserPromptSubmit": ["user_prompt"], "SessionStart": ["session_start_context"],
              "Stop": ["record_change_on_stop", "recall_outcome_on_stop"]}
    hooks = {event: [{"hooks": [{"type": "exec", "command": str(contract.executable_python()),
               "args": [str(launcher), identity, "--timeout-seconds", "20"], "timeout": 30}
              for identity in ids]}] for event, ids in events.items()}
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"hooks": hooks}))
    return root, launcher


def test_normal_four_hooks_static_fresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    assert check_managed_claude_hooks(root, version=(2, 1, 280))["status"] == "fresh"


def test_only_current_interpreter_alias_normalized_not_arbitrary_config_link(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    alias = tmp_path / "python-alias"
    real = Path(sys.executable).resolve()
    try:
        alias.symlink_to(real)
    except (OSError, NotImplementedError):
        if os.name != "nt":
            pytest.skip("interpreter alias creation unavailable")
        # Windows symlink privileges are optional; a .cmd alias cannot be exec.
        pytest.skip("Windows interpreter symlink permission unavailable")
    monkeypatch.setattr(contract.sys, "executable", str(alias))
    assert contract.executable_python() == real
    assert check_managed_claude_hooks(root, version=(2, 1, 280))["status"] == "fresh"
    settings = root / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["hooks"]["Stop"][0]["hooks"][0]["command"] = str(alias)
    settings.write_text(json.dumps(data))
    assert check_managed_claude_hooks(root, version=(2, 1, 280))["status"] == "error"


def test_target_junction_outside_never_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    hooks = root / ".sybermem" / "hooks"
    outside = tmp_path / "outside"
    hooks.rename(outside)
    _link(outside, hooks, directory=True)
    result = check_managed_claude_hooks(root, version=(2, 1, 280))
    assert result["status"] == "error"
    assert any("target hook" in error for error in result["errors"])


def test_linked_launcher_ancestor_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, launcher = _fixture(tmp_path, monkeypatch)
    outside = tmp_path / "elsewhere"
    launcher.parent.rename(outside)
    _link(outside, launcher.parent, directory=True)
    assert check_managed_claude_hooks(root, version=(2, 1, 280))["status"] == "error"


def test_linked_settings_never_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    settings = root / ".claude" / "settings.json"
    outside = tmp_path / "external.json"
    settings.rename(outside)
    _link(outside, settings)
    assert check_managed_claude_hooks(root, version=(2, 1, 280)) == {
        "status": "error", "errors": ["unsafe managed settings or launcher path"]}


def test_settings_ancestor_junction_never_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    settings_dir = root / ".claude"
    outside = tmp_path / "external-settings"
    settings_dir.rename(outside)
    _link(outside, settings_dir, directory=True)
    assert check_managed_claude_hooks(root, version=(2, 1, 280)) == {
        "status": "error", "errors": ["unsafe managed settings or launcher path"]}
