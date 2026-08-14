from __future__ import annotations

import re
import os
import tempfile
from pathlib import Path
from typing import Final, TypedDict

from .project import ensure_project_yaml
from .project_refresh_settings import merge_settings_file


PROTOCOL_START: Final = "<!-- SYBERMEM_SESSION_PROTOCOL:START -->"
PROTOCOL_END: Final = "<!-- SYBERMEM_SESSION_PROTOCOL:END -->"
PROTOCOL_BLOCK_RE: Final = re.compile(
    rf"{re.escape(PROTOCOL_START)}.*?{re.escape(PROTOCOL_END)}",
    re.DOTALL,
)
INSTRUCTION_FILES: Final = frozenset(("CLAUDE.md", "AGENTS.md"))
REPLACEABLE_PREFIXES: Final = (".sybermem/hooks/", ".sybermem/templates/")
KNOWN_DIRS: Final = (
    ".sybermem",
    ".sybermem/digests",
    ".sybermem/theme-digests",
    ".sybermem/analysis",
    ".sybermem/hooks",
    ".sybermem/templates",
)
GLOBAL_TEMPLATE_PROJECT_FILES: Final = (
    Path.home() / ".claude" / "skills" / "sybermem-init-project" / "project-files",
    Path.home() / ".config" / "opencode" / "skills" / "sybermem-init-project" / "project-files",
    Path.home() / ".agents" / "skills" / "sybermem-init-project" / "project-files",
)


class FileRefresh(TypedDict, total=False):
    status: str
    action: str
    backup: str


class ProjectRefreshReport(TypedDict):
    root: str
    overall: str
    files: dict[str, FileRefresh]
    actions_needed: list[str]
    actions_applied: list[str]
    actions_skipped: list[str]
    preserved_custom: list[str]


def discover_template_roots() -> tuple[Path, ...]:
    repo_root = Path(__file__).resolve().parents[3]
    candidates = (
        repo_root / "packages" / "claude-skills" / "sybermem-init-project" / "project-files",
        repo_root / "skills" / "sybermem-init-project" / "project-files",
        *GLOBAL_TEMPLATE_PROJECT_FILES,
    )
    return tuple(path for path in candidates if path.is_dir())


def refresh_project(root: Path, template_roots: tuple[Path, ...] | None = None) -> ProjectRefreshReport:
    resolved_root = root.resolve()
    roots = template_roots if template_roots is not None else discover_template_roots()
    templates = _load_templates(roots)
    files: dict[str, FileRefresh] = {}
    actions_needed: list[str] = []
    actions_applied: list[str] = []
    actions_skipped: list[str] = []
    preserved_custom: list[str] = []

    _ensure_known_dirs(resolved_root)
    for rel_path, template_text in templates.items():
        if rel_path in INSTRUCTION_FILES:
            outcome = _refresh_instruction_file(resolved_root, rel_path, template_text)
        elif rel_path == ".claude/settings.json":
            outcome = _refresh_settings_file(resolved_root, template_text)
        else:
            outcome = _refresh_managed_file(resolved_root, rel_path, template_text)
        files[rel_path] = outcome
        _collect_actions(outcome, actions_needed, actions_applied, actions_skipped)
        if outcome["status"] in ("custom_preserved", "fresh_custom"):
            preserved_custom.append(rel_path)

    yaml_status, _project_id, _slug = ensure_project_yaml(resolved_root)
    yaml_action = "create .sybermem/project.yaml with project identity"
    if yaml_status == "created":
        files[".sybermem/project.yaml"] = {"status": "created", "action": yaml_action}
        actions_needed.append(yaml_action)
        actions_applied.append(yaml_action)
    else:
        files[".sybermem/project.yaml"] = {"status": "fresh"}

    overall = "fresh" if not actions_applied and not actions_skipped else "updated"
    return {
        "root": str(resolved_root).replace("\\", "/"),
        "overall": overall,
        "files": files,
        "actions_needed": actions_needed,
        "actions_applied": actions_applied,
        "actions_skipped": actions_skipped,
        "preserved_custom": preserved_custom,
    }


def _load_templates(template_roots: tuple[Path, ...]) -> dict[str, str]:
    templates: dict[str, str] = {}
    for root in template_roots:
        if not root.is_dir():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            rel_path = path.relative_to(root).as_posix()
            if rel_path not in templates:
                templates[rel_path] = path.read_text(encoding="utf-8")
    return templates


def _ensure_known_dirs(root: Path) -> None:
    for rel_path in KNOWN_DIRS:
        path = _guard_project_path(root, rel_path)
        path.mkdir(parents=True, exist_ok=True)


def _refresh_managed_file(root: Path, rel_path: str, template_text: str) -> FileRefresh:
    target = _guard_project_path(root, rel_path)
    action_create = f"create {rel_path} from template"
    if not target.exists():
        _write_text(target, template_text)
        return {"status": "created", "action": action_create}

    current_text = target.read_text(encoding="utf-8")
    if current_text == template_text:
        return {"status": "fresh"}
    if rel_path.startswith(REPLACEABLE_PREFIXES):
        backup = _backup_file(target)
        _write_text(target, template_text)
        return {
            "status": "replaced",
            "action": f"replace {rel_path} from template",
            "backup": str(backup).replace("\\", "/"),
        }
    return {"status": "custom_preserved", "action": f"preserve custom {rel_path}"}


def _refresh_settings_file(root: Path, template_text: str) -> FileRefresh:
    target = _guard_project_path(root, ".claude/settings.json")
    existed = target.exists()
    changed = merge_settings_file(root, template_text)
    if not changed:
        return {"status": "fresh"}
    if existed:
        return {"status": "updated", "action": "merge .claude/settings.json from template"}
    return {"status": "created", "action": "create .claude/settings.json from template"}


def _refresh_instruction_file(root: Path, rel_path: str, template_text: str) -> FileRefresh:
    target = _guard_project_path(root, rel_path)
    if not target.exists():
        _write_text(target, template_text)
        return {"status": "created", "action": f"create {rel_path} from template"}

    current_text = target.read_text(encoding="utf-8")
    if current_text == template_text:
        return {"status": "fresh"}

    if _is_sybermem_only_instruction(current_text, template_text):
        backup = _backup_file(target)
        _write_text(target, template_text)
        return {
            "status": "replaced",
            "action": f"replace {rel_path} from template",
            "backup": str(backup).replace("\\", "/"),
        }

    protocol_block = _template_protocol_block(template_text)
    if protocol_block == "":
        return {"status": "custom_preserved", "action": f"preserve custom {rel_path}"}

    refreshed_text = _upsert_protocol_block(current_text, protocol_block)
    if refreshed_text == current_text:
        return {"status": "fresh_custom"}
    _write_text(target, refreshed_text)
    action = _instruction_action(rel_path, current_text)
    return {"status": "custom_preserved", "action": action}


def _is_sybermem_only_instruction(current_text: str, template_text: str) -> bool:
    stripped_current = PROTOCOL_BLOCK_RE.sub("", current_text).strip()
    stripped_template = PROTOCOL_BLOCK_RE.sub("", template_text).strip()
    return stripped_current == stripped_template


def _template_protocol_block(template_text: str) -> str:
    match = PROTOCOL_BLOCK_RE.search(template_text)
    return "" if match is None else match.group(0).strip()


def _upsert_protocol_block(current_text: str, protocol_block: str) -> str:
    if PROTOCOL_BLOCK_RE.search(current_text):
        return PROTOCOL_BLOCK_RE.sub(protocol_block, current_text, count=1)
    prefix = current_text.rstrip()
    if prefix == "":
        return f"{protocol_block}\n"
    return f"{prefix}\n\n{protocol_block}\n"


def _instruction_action(rel_path: str, current_text: str) -> str:
    if PROTOCOL_BLOCK_RE.search(current_text):
        return f"replace protocol block in {rel_path} (preserve content outside block)"
    return f"insert protocol block into {rel_path} (preserve existing content)"


def _backup_file(path: Path) -> Path:
    base = path.with_suffix(f"{path.suffix}.bak")
    backup = base
    counter = 1
    while backup.exists() or backup.is_symlink():
        backup = path.with_suffix(f"{path.suffix}.bak.{counter}")
        counter += 1
    with backup.open("x", encoding="utf-8") as handle:
        handle.write(path.read_text(encoding="utf-8"))
    return backup


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        tmp_path = Path(handle.name)
    os.replace(tmp_path, path)


def _guard_project_path(root: Path, rel_path: str) -> Path:
    relative = Path(rel_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"managed path escapes project root: {rel_path}")
    target = root / relative
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError(f"managed path parent is a symlink: {current}")
    if target.exists() and target.is_symlink():
        raise ValueError(f"managed path is a symlink: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target_parent = target.parent.resolve()
    root_resolved = root.resolve()
    try:
        target_parent.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"managed path escapes project root: {rel_path}") from exc
    return target


def _collect_actions(
    outcome: FileRefresh,
    actions_needed: list[str],
    actions_applied: list[str],
    actions_skipped: list[str],
) -> None:
    action = outcome.get("action")
    if action is None:
        return
    actions_needed.append(action)
    if outcome["status"] == "custom_preserved" and action.startswith("preserve custom "):
        actions_skipped.append(action)
    else:
        actions_applied.append(action)
