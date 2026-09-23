"""Focused CLI-resolution tests for the package checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

import pytest


CHECKER = Path(__file__).with_name("check-plugin-package.py")


@pytest.fixture
def checker():
    spec = importlib.util.spec_from_file_location("package_checker", CHECKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("resolved", [None, r"C:\Program Files\Claude Code\claude.exe"])
def test_main_resolves_cli_once_and_validates_both_manifests(checker, monkeypatch, capsys, tmp_path, resolved):
    # Isolate command resolution from the unrelated static distribution checks.
    for name in vars(checker):
        if name.startswith("check_"):
            monkeypatch.setattr(checker, name, lambda *args: None)
    monkeypatch.setattr(checker, "check_skill_tree_parity", lambda root: ["skill"])
    lookups = []
    monkeypatch.setattr(checker.shutil, "which", lambda name: lookups.append(name) or resolved)
    calls = []
    monkeypatch.setattr(checker, "claude_validate", lambda root, target, cli: calls.append((target, cli)))

    assert checker.main(tmp_path) == 0
    assert lookups == ["claude"]
    assert calls == ([(tmp_path / ".claude-plugin" / name, resolved) for name in ("plugin.json", "marketplace.json")] if resolved else [])
    assert ("claude CLI not found" if resolved is None else "claude plugins validate") in capsys.readouterr().out


@pytest.mark.parametrize("windows,cli", [
    (False, "/opt/Claude Code/bin/claude"),
    (True, r"C:\Program Files\Claude Code\claude.exe"),
    (True, r"C:\Program Files\Claude Code\claude.CMD"),
    (True, r"C:\Program Files\Claude Code\claude.bat"),
])
def test_validate_uses_resolved_executable_and_quotes_batch_shim(checker, monkeypatch, tmp_path, windows, cli):
    monkeypatch.setattr(checker.os, "name", "nt" if windows else "posix")
    monkeypatch.setenv("ComSpec", r"C:\Windows\System32\cmd.exe")
    recorded = []

    def fake_run(command, **kwargs):
        recorded.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    target = tmp_path / "manifest with spaces.json"
    checker.claude_validate(tmp_path, target, cli)

    command, kwargs = recorded[0]
    assert command == [cli, "plugins", "validate", str(target)]
    assert kwargs["shell"] is (windows and Path(cli).suffix.lower() in {".cmd", ".bat"})
    assert kwargs["cwd"] == tmp_path
    assert kwargs["check"] is False


def test_validate_reports_cli_failure(checker, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(checker.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 5, "bad", "error"))
    with pytest.raises(SystemExit, match="1"):
        checker.claude_validate(tmp_path, tmp_path / "plugin.json", "claude.exe")
    assert "baderror" in capsys.readouterr().err
