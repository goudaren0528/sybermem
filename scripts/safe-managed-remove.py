from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import sys
from uuid import uuid4


def _is_link_or_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & reparse)


def _remove_link(path: Path) -> None:
    if path.is_dir():
        os.rmdir(path)
    else:
        path.unlink()


def _assert_direct_child(root: Path, target: Path) -> None:
    root = root.absolute()
    target = target.absolute()
    if target.parent != root:
        raise RuntimeError(f"refusing path outside managed root: {target}")
    if _is_link_or_reparse(root):
        raise RuntimeError(f"refusing linked managed root: {root}")


def _identity(path: Path) -> tuple[int, int]:
    info = path.stat(follow_symlinks=False)
    return info.st_dev, info.st_ino


def remove_child(root: Path, name: str) -> None:
    if Path(name).name != name or name in {"", ".", ".."}:
        raise RuntimeError(f"invalid managed child name: {name}")
    target = root / name
    if not target.exists() and not _is_link_or_reparse(target):
        return
    _assert_direct_child(root, target)
    if os.name != "nt" and hasattr(os, "O_DIRECTORY"):
        flags = os.O_RDONLY | os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        root_fd = os.open(root, flags)
        quarantine_name = f".sybermem-remove-{uuid4().hex}"
        try:
            info = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                os.unlink(name, dir_fd=root_fd)
                return
            os.rename(name, quarantine_name, src_dir_fd=root_fd, dst_dir_fd=root_fd)
            moved = os.stat(quarantine_name, dir_fd=root_fd, follow_symlinks=False)
            if stat.S_ISDIR(moved.st_mode):
                shutil.rmtree(quarantine_name, dir_fd=root_fd)
            else:
                os.unlink(quarantine_name, dir_fd=root_fd)
        finally:
            os.close(root_fd)
        return

    # Windows stdlib has no dir_fd deletion API. Revalidate root identity immediately
    # around an atomic rename, then delete only the randomized quarantine entry.
    root_identity = _identity(root)
    if _is_link_or_reparse(target):
        _remove_link(target)
        return
    quarantine = root / f".sybermem-remove-{uuid4().hex}"
    if _identity(root) != root_identity:
        raise RuntimeError(f"managed root changed during removal: {root}")
    os.replace(target, quarantine)
    if _identity(root) != root_identity:
        raise RuntimeError(f"managed root changed after quarantine rename: {root}")
    mode = quarantine.lstat().st_mode
    if _is_link_or_reparse(quarantine):
        _remove_link(quarantine)
    elif stat.S_ISDIR(mode):
        shutil.rmtree(quarantine, ignore_errors=False)
    else:
        quarantine.unlink()


def _remove_codex_handlers(hooks_json: Path, managed: set[str]) -> None:
    if not hooks_json.is_file():
        return
    if hooks_json.is_symlink() or hooks_json.parent.is_symlink():
        raise RuntimeError(f"refusing linked Codex hooks path: {hooks_json}")
    data = json.loads(hooks_json.read_text(encoding="utf-8-sig"))
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return
    for event, groups in list(hooks.items()):
        if not isinstance(groups, list):
            continue
        kept = []
        for group in groups:
            encoded = json.dumps(group, ensure_ascii=False)
            if not any(name in encoded for name in managed):
                kept.append(group)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    temporary = hooks_json.with_name(f".{hooks_json.name}.sybermem-{uuid4().hex}.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, hooks_json)


def uninstall(home: Path, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise RuntimeError("unsupported managed-install manifest version")
    for root in (home / ".claude" / "skills", home / ".config" / "opencode" / "skills", home / ".agents" / "skills"):
        for name in manifest["skills"]:
            remove_child(root, name)
    runtime = home / ".claude" / "sybermem"
    for name in manifest["runtime_dirs"]:
        remove_child(runtime, name)
    # Remove the helper and manifest last so this process can finish from installed files.
    runtime_files = [name for name in manifest["runtime_files"] if name not in {"managed-install.json", "safe-managed-remove.py"}]
    for name in runtime_files:
        remove_child(runtime, name)
    plugin = home / manifest["opencode_plugin"]
    remove_child(plugin.parent, plugin.name)
    codex_hooks = home / ".codex" / "hooks"
    for name in manifest["codex_hook_files"]:
        remove_child(codex_hooks, name)
    _remove_codex_handlers(home / ".codex" / "hooks.json", set(manifest["codex_hook_files"]))
    for name in ("managed-install.json", "safe-managed-remove.py"):
        remove_child(runtime, name)
    try:
        runtime.rmdir()
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    child = sub.add_parser("child")
    child.add_argument("--root", required=True)
    child.add_argument("--name", required=True)
    remove = sub.add_parser("uninstall")
    remove.add_argument("--home", required=True)
    remove.add_argument("--manifest", required=True)
    args = parser.parse_args()
    if args.command == "child":
        remove_child(Path(args.root), args.name)
    else:
        uninstall(Path(args.home), Path(args.manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
