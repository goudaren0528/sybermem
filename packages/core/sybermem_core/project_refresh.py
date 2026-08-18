from __future__ import annotations

import re
import os
import tempfile
from pathlib import Path
from typing import Final, TypedDict

from .project import ensure_project_yaml
from .project_refresh_settings import merge_settings_file
from .version import get_installed_version


PROTOCOL_START: Final = "<!-- SYBERMEM_SESSION_PROTOCOL:START -->"
PROTOCOL_END: Final = "<!-- SYBERMEM_SESSION_PROTOCOL:END -->"
PROTOCOL_BLOCK_RE: Final = re.compile(
    rf"{re.escape(PROTOCOL_START)}.*?{re.escape(PROTOCOL_END)}",
    re.DOTALL,
)
INSTRUCTION_FILES: Final = frozenset(("CLAUDE.md", "AGENTS.md"))
REPLACEABLE_PREFIXES: Final = (".sybermem/hooks/", ".sybermem/templates/")
GITIGNORE_START: Final = "# >>> SyberMem >>>"
GITIGNORE_END: Final = "# <<< SyberMem <<<"
GITIGNORE_BLOCK_RE: Final = re.compile(
    rf"{re.escape(GITIGNORE_START)}.*?{re.escape(GITIGNORE_END)}\n?",
    re.DOTALL,
)
# Machine-local runtime state, hooks/scripts, and per-machine hook wiring. These
# are not shareable project memory, so they are ignored. Canonical records
# (changes/decisions/requirements/bugs), digests, analysis, templates, INDEX.md,
# and project.yaml are intentionally NOT ignored so teams can commit memory.
GITIGNORE_BODY: Final = "\n".join(
    (
        GITIGNORE_START,
        "# SyberMem machine-local runtime, scripts, and hook wiring (not shareable memory).",
        "/.sybermem/hooks/",
        "/.sybermem/.recall-debug.jsonl",
        "/.sybermem/.recall-outcomes.jsonl",
        "/.sybermem/.auto-trail.jsonl",
        "/.sybermem/.nudge-state.json",
        "/.sybermem/.opencode-nudge-state.json",
        "/.sybermem/.record-intent.json",
        "/.sybermem/.auto-change-state.json",
        "/.sybermem/.codex-compact-marker.json",
        "/.claude/settings.json",
        GITIGNORE_END,
    )
)
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
            # CLAUDE.md / AGENTS.md are no longer created or refreshed by SyberMem.
            # Legacy protocol blocks are removed by the migration below.
            continue
        if rel_path == ".claude/settings.json":
            outcome = _refresh_settings_file(resolved_root, template_text)
        else:
            outcome = _refresh_managed_file(resolved_root, rel_path, template_text)
        files[rel_path] = outcome
        _collect_actions(outcome, actions_needed, actions_applied, actions_skipped)
        if outcome["status"] in ("custom_preserved", "fresh_custom"):
            preserved_custom.append(rel_path)

    # Migration: remove legacy SyberMem protocol blocks from instruction files.
    # If a file is purely SyberMem-managed (only the protocol block), delete it.
    # If it carries user content outside the block, strip just the block and
    # preserve the rest. Files without a block are left untouched.
    for name in INSTRUCTION_FILES:
        outcome = _remove_instruction_protocol(resolved_root, name)
        files[name] = outcome
        _collect_actions(outcome, actions_needed, actions_applied, actions_skipped)

    yaml_status, _project_id, _slug = ensure_project_yaml(resolved_root)
    yaml_action = "create .sybermem/project.yaml with project identity"
    yaml_created = yaml_status == "created"
    if yaml_created:
        # New project.yaml already carries the current sybermem_version via
        # render_project_yaml, so no separate stamp is needed.
        files[".sybermem/project.yaml"] = {"status": "created", "action": yaml_action}
        actions_needed.append(yaml_action)
        actions_applied.append(yaml_action)

    # Ignore machine-local SyberMem runtime/scripts in the user's .gitignore.
    # Skipped for non-git projects. Keeps shareable memory (records/digests/INDEX)
    # committable while excluding hooks, runtime logs, and per-machine hook wiring.
    gitignore_outcome = _ensure_gitignore(resolved_root)
    files[".gitignore"] = gitignore_outcome
    _collect_actions(gitignore_outcome, actions_needed, actions_applied, actions_skipped)

    # Stamp the version LAST so it doubles as a completion marker: session-start
    # clears the /sybermem-update nudge only once every earlier migration step
    # (protocol-block removal, settings/hook refresh, gitignore) has succeeded.
    # If any earlier step raises, the stamp is not written and the next session
    # still nudges — the refresh is retry-safe.
    if not yaml_created:
        version_outcome = _stamp_project_version(resolved_root)
        files[".sybermem/project.yaml"] = version_outcome
        _collect_actions(version_outcome, actions_needed, actions_applied, actions_skipped)

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


def _stamp_project_version(root: Path) -> FileRefresh:
    """Upsert `sybermem_version: <installed>` into an existing project.yaml.

    New projects already get the field from render_project_yaml. This keeps an
    existing project's stamp current so session-start can detect a trailing
    project and nudge `/sybermem-update`. Idempotent when already current.
    """
    target = root / ".sybermem" / "project.yaml"
    if not target.is_file():
        return {"status": "fresh"}
    installed = get_installed_version()
    text = target.read_text(encoding="utf-8")
    lines = text.splitlines()
    stamped = f"sybermem_version: {installed}"
    for i, line in enumerate(lines):
        if line.startswith("sybermem_version:"):
            if line.strip() == stamped:
                return {"status": "fresh"}
            lines[i] = stamped
            _write_text(target, "\n".join(lines) + "\n")
            return {"status": "updated", "action": "update sybermem_version in .sybermem/project.yaml"}
    # Field absent (older project.yaml): append it.
    new_text = text.rstrip("\n") + f"\n{stamped}\n"
    _write_text(target, new_text)
    return {"status": "updated", "action": "add sybermem_version to .sybermem/project.yaml"}


def _ensure_gitignore(root: Path) -> FileRefresh:
    """Add a marker-bounded SyberMem ignore block to the project's .gitignore.

    - Non-git project (no `.git`): skip (fresh, no action).
    - Missing/absent block: append the block (creating .gitignore if needed).
    - Block present but stale: replace only the marker-bounded block.
    - Block present and current: leave untouched (fresh).
    Content outside the marker block is always preserved verbatim.
    """
    if not (root / ".git").exists():
        return {"status": "fresh"}

    target = _guard_project_path(root, ".gitignore")
    if not target.exists():
        _write_text(target, GITIGNORE_BODY + "\n")
        return {"status": "created", "action": "create .gitignore with SyberMem ignore block"}

    current = target.read_text(encoding="utf-8")
    match = GITIGNORE_BLOCK_RE.search(current)
    if match is None:
        prefix = current.rstrip("\n")
        updated = f"{prefix}\n\n{GITIGNORE_BODY}\n" if prefix else f"{GITIGNORE_BODY}\n"
        _write_text(target, updated)
        return {"status": "updated", "action": "add SyberMem ignore block to .gitignore (preserve existing content)"}

    if match.group(0).strip() == GITIGNORE_BODY:
        return {"status": "fresh"}

    updated = GITIGNORE_BLOCK_RE.sub(GITIGNORE_BODY + "\n", current, count=1)
    _write_text(target, updated)
    return {"status": "updated", "action": "refresh SyberMem ignore block in .gitignore (preserve content outside block)"}


def _remove_instruction_protocol(root: Path, rel_path: str) -> FileRefresh:
    """Remove a legacy SyberMem protocol block from an instruction file.

    - No file / no block: leave untouched (fresh).
    - File is purely SyberMem-managed (only the protocol block, or only known
      SyberMem template sections with no user content): delete the file.
    - File has user content outside the block: strip only the block, preserve the rest.
    """
    target = _guard_project_path(root, rel_path)
    if not target.exists():
        return {"status": "fresh"}

    current_text = target.read_text(encoding="utf-8")
    if not PROTOCOL_BLOCK_RE.search(current_text):
        return {"status": "fresh"}

    stripped = PROTOCOL_BLOCK_RE.sub("", current_text).strip()
    if _is_sybermem_only_instruction(stripped):
        backup = _backup_file(target)
        target.unlink()
        return {
            "status": "removed",
            "action": f"remove {rel_path} (purely SyberMem-managed)",
            "backup": str(backup).replace("\\", "/"),
        }

    _write_text(target, stripped + "\n")
    return {
        "status": "updated",
        "action": f"remove protocol block from {rel_path} (preserve content outside block)",
    }


# The exact body of the SyberMem instruction template with the protocol block
# removed. A file whose content outside the protocol block matches this (or an
# old heavy SyberMem template) is purely SyberMem-managed and safe to delete.
_SYBERMEM_TEMPLATE_BODY: Final = (
    "# SyberMem Project Record System\n"
    "\n"
    "## Core Rule\n"
    "\n"
    "After completing meaningful work, run `/sybermem-record` to create a record.\n"
    "\n"
    "## Directories\n"
    "\n"
    "- `.sybermem/changes/` — Feature changes\n"
    "- `.sybermem/decisions/` — Technical decisions\n"
    "- `.sybermem/requirements/` — Requirements / discussions\n"
    "- `.sybermem/bugs/` — Bug fixes\n"
    "- `.sybermem/INDEX.md` — Master index\n"
    "\n"
    "## No Record Needed\n"
    "\n"
    "Formatting adjustments, comment edits, config tweaks with no functional impact."
)


def _is_sybermem_only_instruction(stripped_text: str) -> bool:
    """Return True when the stripped text is only known SyberMem template content.

    A file is purely SyberMem-managed when its content outside the protocol block
    is empty, matches the current SyberMem template body, or is an old heavy
    SyberMem template (recognized by its distinctive section headings). Any other
    content means user content, so we must preserve the file and strip only the
    protocol block. Blank-line count is ignored because removing the block can
    leave extra blank lines.
    """
    if _normalize_blank_lines(stripped_text) == "":
        return True
    if _normalize_blank_lines(stripped_text) == _normalize_blank_lines(_SYBERMEM_TEMPLATE_BODY):
        return True
    # Old heavy SyberMem templates shipped extra sections. Require the SyberMem H1
    # heading to co-occur so a user file that merely has a "## Workflow" section is
    # NOT misclassified as purely SyberMem-managed and deleted.
    if "# SyberMem Project Record System" not in stripped_text:
        return False
    return (
        "## Available Skills" in stripped_text
        or "## Workflow" in stripped_text
        or ("## Directory Resolution" in stripped_text and "## Core Rule" in stripped_text)
    )


def _normalize_blank_lines(text: str) -> str:
    """Collapse runs of blank lines to a single blank line and strip edges."""
    lines = [line.rstrip() for line in text.splitlines()]
    out: list[str] = []
    prev_blank = False
    for line in lines:
        blank = line.strip() == ""
        if blank and prev_blank:
            continue
        out.append(line)
        prev_blank = blank
    return "\n".join(out).strip()


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
