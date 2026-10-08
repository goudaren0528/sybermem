from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[3]
POSIX_FD = os.name != "nt" and hasattr(os, "O_DIRECTORY")


def _module():
    path = ROOT / "scripts" / "safe-managed-remove.py"
    spec = importlib.util.spec_from_file_location("safe_managed_remove", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_remove_child_removes_only_direct_managed_child(tmp_path: Path) -> None:
    module = _module()
    root = tmp_path / "skills"
    target = root / "sybermem-test"
    target.mkdir(parents=True)
    (target / "file.txt").write_text("managed\n", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("preserve\n", encoding="utf-8")

    module.remove_child(root, "sybermem-test")

    assert not target.exists()
    assert outside.read_text(encoding="utf-8") == "preserve\n"


def test_remove_child_rejects_path_traversal(tmp_path: Path) -> None:
    module = _module()
    root = tmp_path / "skills"
    root.mkdir()
    with pytest.raises(RuntimeError, match="invalid managed child name"):
        module.remove_child(root, "../outside")


def test_remove_child_unlinks_symlink_without_deleting_target(tmp_path: Path) -> None:
    module = _module()
    root = tmp_path / "skills"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel.txt").write_text("preserve\n", encoding="utf-8")
    link = root / "sybermem-link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    module.remove_child(root, "sybermem-link")

    assert not link.exists()
    assert (outside / "sentinel.txt").read_text(encoding="utf-8") == "preserve\n"


def test_remove_child_rejects_linked_ancestor(tmp_path: Path) -> None:
    module = _module()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel.txt").write_text("preserve\n", encoding="utf-8")
    linked_ancestor = tmp_path / "config"
    try:
        linked_ancestor.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    # root resolves under a symlinked ancestor -> deletion would escape the home tree.
    root = linked_ancestor / "skills"
    root.mkdir()
    (root / "sybermem-test").write_text("managed\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="linked ancestor"):
        module.remove_child(root, "sybermem-test")

    assert (outside / "sentinel.txt").read_text(encoding="utf-8") == "preserve\n"


def test_uninstall_rejects_tampered_opencode_plugin(tmp_path: Path) -> None:
    module = _module()
    home = tmp_path / "home"
    home.mkdir()
    sentinel = tmp_path / "victim.ts"
    sentinel.write_text("preserve\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "skills": [],
        "runtime_dirs": [],
        "runtime_files": [],
        "codex_hook_files": [],
        "opencode_plugin": "../../victim.ts",
    }
    manifest_path = tmp_path / "managed-install.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(RuntimeError, match="invalid OpenCode plugin path"):
        module.uninstall(home, manifest_path)


def test_uninstall_cleans_retired_skill_from_all_roots(tmp_path: Path) -> None:
    # A retired skill (e.g. the removed Team skills) must be cleaned from every
    # managed skills root on uninstall, including the Codex ~/.agents/skills root.
    module = _module()
    home = tmp_path / "home"
    home.mkdir()
    roots = [
        home / ".claude" / "skills",
        home / ".config" / "opencode" / "skills",
        home / ".agents" / "skills",
    ]
    for root in roots:
        skill_dir = root / "sybermem-team-summary"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("retired\n", encoding="utf-8")
    (home / ".claude" / "sybermem").mkdir(parents=True)

    manifest = {
        "schema_version": 1,
        "skills": [],
        "retired_skills": ["sybermem-team-summary"],
        "runtime_dirs": [],
        "runtime_files": ["managed-install.json", "safe-managed-remove.py"],
        "codex_hook_files": [],
        "opencode_plugin": ".config/opencode/plugins/sybermem.ts",
    }
    manifest_path = tmp_path / "managed-install.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    module.uninstall(home, manifest_path)

    for root in roots:
        assert not (root / "sybermem-team-summary").exists()


def test_remove_missing_child_and_root_are_idempotent(tmp_path: Path) -> None:
    module = _module()
    module.remove_child(tmp_path / "missing", "sybermem-test")
    module.remove_child(tmp_path, "sybermem-test")
    assert list(tmp_path.iterdir()) == []


@pytest.fixture
def legacy_remover(monkeypatch):
    if not POSIX_FD:
        pytest.skip("POSIX descriptor-relative removal required")
    # Load against the actual old public signature, not just a forced flag.
    def old_rmtree(path, ignore_errors=False, onerror=None):
        raise AssertionError("legacy rmtree must not be used for fd removal")

    monkeypatch.setattr(shutil, "rmtree", old_rmtree)
    module = _module()
    assert not module._RMTREE_HAS_DIR_FD
    return module


def test_legacy_signature_removes_tree_and_preserves_nested_link_targets(legacy_remover, tmp_path):
    root = tmp_path / "skills"
    nested = root / "sybermem-test" / "nested"
    nested.mkdir(parents=True)
    (nested / "managed").write_text("remove", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_text("preserve", encoding="utf-8")
    (nested / "dir-link").symlink_to(outside, target_is_directory=True)
    (nested / "file-link").symlink_to(outside / "sentinel")
    (nested / "dangling-link").symlink_to(tmp_path / "missing")

    legacy_remover.remove_child(root, "sybermem-test")
    legacy_remover.remove_child(root, "sybermem-test")

    assert list(root.iterdir()) == []
    assert (outside / "sentinel").read_text(encoding="utf-8") == "preserve"


@pytest.mark.parametrize("replacement", ["directory", "symlink"])
def test_legacy_removal_refuses_swap_before_open(legacy_remover, tmp_path, monkeypatch, replacement):
    root = tmp_path / "root"
    target = root / "managed"
    target.mkdir(parents=True)
    saved = root / "saved"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_text("preserve", encoding="utf-8")
    original_open = os.open
    captured = []

    def swapping_open(path, flags, *args, **kwargs):
        if path == "managed":
            target.rename(saved)
            if replacement == "symlink":
                target.symlink_to(outside, target_is_directory=True)
            else:
                target.mkdir()
                (target / "sentinel").write_text("preserve", encoding="utf-8")
        fd = original_open(path, flags, *args, **kwargs)
        if path == "managed":
            captured.append(fd)
        return fd

    parent_fd = original_open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        monkeypatch.setattr(os, "open", swapping_open)
        with pytest.raises((RuntimeError, OSError)):
            legacy_remover._rmtree_at(parent_fd, "managed")
        for fd in captured:
            with pytest.raises(OSError):
                os.fstat(fd)
    finally:
        os.close(parent_fd)
    assert saved.is_dir()
    assert (outside / "sentinel").read_text(encoding="utf-8") == "preserve"
    if replacement == "directory":
        assert (target / "sentinel").read_text(encoding="utf-8") == "preserve"


def test_legacy_removal_refuses_swap_after_scan(legacy_remover, tmp_path, monkeypatch):
    root = tmp_path / "root"
    target = root / "managed"
    target.mkdir(parents=True)
    saved = root / "saved"
    original_scandir = os.scandir

    def swapping_scandir(fd):
        target.rename(saved)
        target.mkdir()
        return original_scandir(fd)

    parent_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        monkeypatch.setattr(os, "scandir", swapping_scandir)
        with pytest.raises(RuntimeError, match="directory changed"):
            legacy_remover._rmtree_at(parent_fd, "managed")
    finally:
        os.close(parent_fd)
    assert target.is_dir() and saved.is_dir()


def test_legacy_removal_propagates_permission_error_and_closes_fd(legacy_remover, tmp_path, monkeypatch):
    root = tmp_path / "root"
    target = root / "managed"
    target.mkdir(parents=True)
    (target / "file").write_text("preserve", encoding="utf-8")
    original_open = os.open
    captured = []

    def recording_open(*args, **kwargs):
        fd = original_open(*args, **kwargs)
        captured.append(fd)
        return fd

    def denied(*args, **kwargs):
        raise PermissionError("synthetic denial")

    parent_fd = original_open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        monkeypatch.setattr(os, "open", recording_open)
        monkeypatch.setattr(os, "unlink", denied)
        with pytest.raises(PermissionError, match="synthetic denial"):
            legacy_remover._rmtree_at(parent_fd, "managed")
        for fd in captured:
            with pytest.raises(OSError):
                os.fstat(fd)
    finally:
        os.close(parent_fd)
    assert (target / "file").read_text(encoding="utf-8") == "preserve"


def test_legacy_removal_missing_entry(legacy_remover, tmp_path):
    parent_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        legacy_remover._rmtree_at(parent_fd, "missing")
    finally:
        os.close(parent_fd)
