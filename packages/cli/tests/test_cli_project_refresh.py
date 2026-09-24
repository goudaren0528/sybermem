from __future__ import annotations

import json
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli import main as main_module


def test_cli_project_refresh_json_calls_core_and_emits_json_only(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a SyberMem project root and a Core refresh payload
    project_root = tmp_path / "project"
    project_root.mkdir()
    payload = {
        "root": str(project_root).replace("\\", "/"),
        "overall": "updated",
        "files": {"AGENTS.md": {"status": "updated"}},
        "actions_needed": ["remove protocol block from AGENTS.md (preserve content outside block)"],
        "actions_applied": ["remove protocol block from AGENTS.md (preserve content outside block)"],
        "actions_skipped": [],
        "preserved_custom": [],
    }
    called: dict[str, Path] = {}

    def fake_refresh(root: Path) -> dict[str, object]:
        called["root"] = root
        return payload

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "refresh_project", fake_refresh)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--format", "json"])

    # When: the refresh command is invoked through the parser boundary
    exit_code = main_module.main()

    # Then: it calls Core with the resolved root and writes only JSON to stdout
    captured = capsys.readouterr()
    assert exit_code == 0
    assert called == {"root": project_root}
    assert json.loads(captured.out) == payload
    assert captured.err == ""


def test_cli_project_refresh_text_prints_concise_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: Core reports one applied action and one preserved custom file
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(
        main_module,
        "refresh_project",
        lambda root: {
            "root": str(root).replace("\\", "/"),
            "overall": "updated",
            "files": {"AGENTS.md": {"status": "updated"}},
            "actions_needed": ["remove protocol block from AGENTS.md (preserve content outside block)"],
            "actions_applied": ["remove protocol block from AGENTS.md (preserve content outside block)"],
            "actions_skipped": [],
            "preserved_custom": [],
        },
    )
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh"])

    # When: text mode is used
    exit_code = main_module.main()

    # Then: the summary is concise and human-readable
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == "updated: applied 1 action(s), skipped 0, preserved custom 0\n"


def test_cli_project_refresh_returns_1_without_project_root(monkeypatch, capsys) -> None:
    # Given: the command is invoked outside any SyberMem project
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: None)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh"])

    # When: the parser dispatches the refresh command
    exit_code = main_module.main()

    # Then: it fails with a concise stderr message
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "No SyberMem project root found.\n"


def test_cli_project_refresh_returns_clean_error_for_refresh_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: Core refresh rejects a project-local managed path
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)

    def fail_refresh(root: Path) -> dict[str, object]:
        raise ValueError("managed path is a symlink: AGENTS.md")

    monkeypatch.setattr(main_module, "refresh_project", fail_refresh)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh"])

    # When: the parser dispatches the refresh command
    exit_code = main_module.main()

    # Then: the CLI reports a concise error without a traceback
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "managed path is a symlink: AGENTS.md\n"
    assert "Traceback" not in captured.err


def test_cli_refresh_reports_disabled_and_unsafe_failure_in_both_formats(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: root)
    for status, guidance in (("disabled_requires_upgrade", "upgrade Claude Code"),
                             ("error_unsafe_state", "repair Python/launcher path")):
        action = f"Claude hooks {status}; {guidance}"
        payload = {"root": str(root), "overall": "failed", "claude_hooks": status,
                   "files": {".claude/settings.json": {"status": "failed", "action": action}},
                   "actions_needed": [action], "actions_applied": [], "actions_skipped": [action],
                   "preserved_custom": []}
        monkeypatch.setattr(main_module, "refresh_project", lambda _: payload)
        for format in ("json", "text"):
            monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--format", format])
            assert main_module.main() == 1
            output = capsys.readouterr().out
            if format == "json":
                assert json.loads(output)["claude_hooks"] == status
                assert guidance in json.loads(output)["actions_skipped"][0]
            else:
                assert status in output and guidance in output


def test_explicit_root_targets_exact_child_without_search_or_markers(tmp_path, monkeypatch, capsys):
    parent = tmp_path / "parent"
    child = parent / "child"
    child.mkdir(parents=True)
    calls = []
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: (_ for _ in ()).throw(AssertionError("ancestor search")))
    monkeypatch.setattr(main_module.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 128, "", "fatal: not a git repository (or any of the parent directories): .git\n"))

    def fake_refresh(root, *, git_env):
        calls.append(root)
        assert git_env["LC_ALL"] == "C" and git_env["LANG"] == "C" and git_env["LANGUAGE"] == "C"
        assert git_env["GIT_DISCOVERY_ACROSS_FILESYSTEM"] == "1"
        return {"root": root.as_posix(), "overall": "fresh", "files": {}, "actions_needed": [],
                "actions_applied": [], "actions_skipped": [], "preserved_custom": []}

    monkeypatch.setattr(main_module, "refresh_project", fake_refresh)
    monkeypatch.chdir(parent)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", "child", "--format", "json"])
    assert main_module.main() == 0
    assert calls == [child.resolve()]
    assert json.loads(capsys.readouterr().out)["root"] == child.as_posix()
    assert not (child / ".sybermem").exists()


def test_explicit_root_refuses_invalid_targets_without_refresh(tmp_path, monkeypatch, capsys):
    file = tmp_path / "file"
    file.write_text("synthetic", encoding="utf-8")
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: (_ for _ in ()).throw(AssertionError("ancestor search")))
    monkeypatch.setattr(main_module, "refresh_project", lambda root: (_ for _ in ()).throw(AssertionError("write")))
    monkeypatch.chdir(tmp_path)
    for value in ("", "  ", "missing", "file"):
        monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", value])
        assert main_module.main() == 1
        captured = capsys.readouterr()
        assert captured.out == "" and "--root" in captured.err
    assert not (tmp_path / "missing").exists()


def test_explicit_root_refuses_ancestor_git_worktree(tmp_path, monkeypatch, capsys):
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: (_ for _ in ()).throw(AssertionError("ancestor search")))
    monkeypatch.setattr(main_module, "refresh_project", lambda root: (_ for _ in ()).throw(AssertionError("write")))
    def ancestor_probe(*args, **kwargs):
        assert kwargs["env"]["GIT_DISCOVERY_ACROSS_FILESYSTEM"] == "1"
        return subprocess.CompletedProcess(args[0], 0, str(tmp_path), "")

    monkeypatch.setattr(main_module.subprocess, "run", ancestor_probe)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", str(child)])
    assert main_module.main() == 1
    assert "own Git worktree root" in capsys.readouterr().err


def test_explicit_root_refuses_unverifiable_git_boundary(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: (_ for _ in ()).throw(AssertionError("ancestor search")))
    monkeypatch.setattr(main_module, "refresh_project", lambda root: (_ for _ in ()).throw(AssertionError("write")))
    monkeypatch.setattr(main_module.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 128, "", "unknown Git error"))
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", str(tmp_path)])
    assert main_module.main() == 1
    assert "could not be verified" in capsys.readouterr().err


def test_explicit_root_rejects_symlink_target(tmp_path, monkeypatch, capsys):
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("directory symlinks unavailable")
    monkeypatch.setattr(main_module, "refresh_project", lambda root: (_ for _ in ()).throw(AssertionError("write")))
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: (_ for _ in ()).throw(AssertionError("ancestor search")))
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", str(alias)])
    assert main_module.main() == 1
    assert "symlink or reparse" in capsys.readouterr().err


def test_explicit_root_rejects_git_environment_overrides(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_module, "refresh_project", lambda *a, **k: (_ for _ in ()).throw(AssertionError("write")))
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: (_ for _ in ()).throw(AssertionError("search")))
    for key in ("GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_DISCOVERY_ACROSS_FILESYSTEM"):
        monkeypatch.setenv(key, "synthetic")
        monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", str(tmp_path)])
        assert main_module.main() == 1
        assert "Git environment overrides" in capsys.readouterr().err
        monkeypatch.delenv(key)


def test_explicit_root_rejects_ambiguous_git_diagnostics(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_module, "refresh_project", lambda *a, **k: (_ for _ in ()).throw(AssertionError("write")))
    for code, stderr in ((1, "fatal: not a git repository (or any of the parent directories): .git"),
                         (128, "warning: not a git repository (or any of the parent directories): .git"),
                         (128, "fatal: not a git repository (or any of the parent directories): .git\nother"),
                         (128, "fatal: not a git repository (or any parent up to mount point /)\nStopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).\n")):
        monkeypatch.setattr(main_module.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], code, "", stderr))
        monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", str(tmp_path)])
        assert main_module.main() == 1
        assert "boundary could not be verified" in capsys.readouterr().err


def test_explicit_root_accepts_own_worktree_and_rejects_git_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: (_ for _ in ()).throw(AssertionError("search")))
    calls = []

    def fake_refresh(root, *, git_env):
        calls.append(root)
        assert git_env["LC_ALL"] == "C"
        assert git_env["GIT_DISCOVERY_ACROSS_FILESYSTEM"] == "1"
        return {"root": root.as_posix(), "overall": "fresh", "actions_applied": [],
                "actions_skipped": [], "preserved_custom": []}

    monkeypatch.setattr(main_module, "refresh_project", fake_refresh)
    monkeypatch.setattr(main_module.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, str(tmp_path), ""))
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", str(tmp_path)])
    assert main_module.main() == 0
    assert calls == [tmp_path.resolve()]
    capsys.readouterr()
    monkeypatch.setattr(main_module.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("git", 10)))
    assert main_module.main() == 1
    assert len(calls) == 1
    assert "could not be validated" in capsys.readouterr().err


def test_explicit_root_rejects_mocked_reparse_ancestor(tmp_path, monkeypatch, capsys):
    child = tmp_path / "child"
    child.mkdir()
    original = Path.lstat

    def fake_lstat(path):
        result = original(path)
        if path == tmp_path:
            class ReparseStat:
                st_file_attributes = 0x400
            return ReparseStat()
        return result

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    monkeypatch.setattr(main_module, "refresh_project", lambda *a, **k: (_ for _ in ()).throw(AssertionError("write")))
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "refresh", "--root", str(child)])
    assert main_module.main() == 1
    assert "symlink or reparse" in capsys.readouterr().err


def test_core_git_env_is_optional_and_forwarded_only_when_explicit(tmp_path, monkeypatch):
    from sybermem_core import project_refresh as core_refresh
    captured = []

    def fake_run(*args, **kwargs):
        captured.append(kwargs)
        return subprocess.CompletedProcess(args[0], 0, "true", "")

    monkeypatch.setattr(core_refresh.subprocess, "run", fake_run)
    assert core_refresh._git_worktree_available(tmp_path)
    assert "env" not in captured[-1]
    explicit_env = {"LC_ALL": "C", "LANG": "C"}
    assert core_refresh._git_worktree_available(tmp_path, git_env=explicit_env)
    assert captured[-1]["env"] == explicit_env
