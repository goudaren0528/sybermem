from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]


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
        "skills": ["sybermem-team-summary"],
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
