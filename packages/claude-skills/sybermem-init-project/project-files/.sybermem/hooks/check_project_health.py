#!/usr/bin/env python3
"""SyberMem project health check — classifies all managed files in one pass.

Outputs a JSON report to stdout with file statuses, capabilities, and actions needed.
Used by init-project fast-path to skip unnecessary work.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Final, TypedDict


class FileStatus(TypedDict):
    status: str


RECORD_TEMPLATE_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "record_id:",
    "key_conclusion:",
    "topics:",
)
LEGACY_RECORD_TEMPLATE_MARKERS: Final[tuple[str, ...]] = ("number:",)
GLOBAL_TEMPLATE_PROJECT_FILES: Final[tuple[Path, ...]] = (
    Path.home() / ".claude" / "skills" / "sybermem-init-project" / "project-files",
    Path.home() / ".config" / "opencode" / "skills" / "sybermem-init-project" / "project-files",
    Path.home() / ".agents" / "skills" / "sybermem-init-project" / "project-files",
)


def resolve_sybermem_root() -> Path | None:
    """Walk up from cwd to find the nearest SyberMem project root."""
    current = Path.cwd().resolve()
    git_root = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip()).resolve()
    except Exception:
        pass

    while True:
        has_sybermem = (current / ".sybermem").is_dir()
        has_settings = (current / ".claude" / "settings.json").is_file()
        has_index = (current / ".sybermem" / "INDEX.md").is_file()
        if has_sybermem and (has_settings or has_index):
            return current
        if git_root and current == git_root:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def read_text(path: Path) -> str | None:
    """Read file contents, return None if not found."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check_instruction_file(root: Path, name: str, template_content: str) -> dict:
    """Check CLAUDE.md or AGENTS.md for a legacy SyberMem protocol block to remove.

    SyberMem no longer injects into instruction files. A file is only actionable
    when it still carries a legacy `SYBERMEM_SESSION_PROTOCOL` block; the migration
    removes the block (or the whole file when it is purely SyberMem-managed).
    """
    path = root / name
    content = read_text(path)
    if content is None:
        return {"status": "missing", "has_protocol_block": False, "is_sybermem_only": False}

    has_block = "SYBERMEM_SESSION_PROTOCOL:START" in content and "SYBERMEM_SESSION_PROTOCOL:END" in content

    # Check if file is purely SyberMem-managed (no user custom content).
    # Strip the protocol block and compare against the known SyberMem template body
    # (blank-line count ignored because removing the block can leave extra blanks).
    block_pattern = re.compile(
        r"<!-- SYBERMEM_SESSION_PROTOCOL:START -->.*?<!-- SYBERMEM_SESSION_PROTOCOL:END -->",
        re.DOTALL,
    )
    file_stripped = block_pattern.sub("", content).strip()
    is_sybermem_only = _is_sybermem_only_instruction(file_stripped)

    # A file is actionable only when it still carries a legacy protocol block.
    status = "stale" if has_block else "fresh"
    return {
        "status": status,
        "has_protocol_block": has_block,
        "is_sybermem_only": is_sybermem_only,
    }


# The exact body of the SyberMem instruction template with the protocol block
# removed. A file whose content outside the protocol block matches this (or an
# old heavy SyberMem template) is purely SyberMem-managed and safe to delete.
_SYBERMEM_TEMPLATE_BODY = (
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


def _is_sybermem_only_instruction(stripped_text: str) -> bool:
    """Return True when the stripped text is only known SyberMem template content.

    A file is purely SyberMem-managed when its content outside the protocol block
    is empty, matches the current SyberMem template body, or is an old heavy
    SyberMem template (recognized by its distinctive section headings). Any other
    content means user content, so we must preserve the file and strip only the
    protocol block.
    """
    if _normalize_blank_lines(stripped_text) == "":
        return True
    if _normalize_blank_lines(stripped_text) == _normalize_blank_lines(_SYBERMEM_TEMPLATE_BODY):
        return True
    # Old heavy SyberMem templates shipped sections that are not user content.
    return (
        "## Available Skills" in stripped_text
        or "## Workflow" in stripped_text
        or ("## Directory Resolution" in stripped_text and "## Core Rule" in stripped_text)
    )


def check_settings_json(root: Path) -> dict:
    """Check .claude/settings.json status."""
    path = root / ".claude" / "settings.json"
    content = read_text(path)
    if content is None:
        return {
            "status": "missing",
            "has_session_start_hook": False,
            "has_stop_hook": False,
            "has_relative_session_start_hook": False,
            "has_relative_stop_hook": False,
            "has_user_prompt_hook": False,
            "has_record_intent_hook": False,
            "has_task_recall_hook": False,
            "has_auto_mode": False,
        }

    # Operational target state: SessionStart/Stop call the machine-specific global
    # launcher (launch_*). The shipped template ships a portable *relative* seed
    # (.sybermem/hooks/session_start_context.py) that init/update must rewrite to the
    # launcher path — so a relative-only settings.json is a valid seed but NOT fresh,
    # because Python opens the relative hook path against the cwd before any root
    # resolution runs and can fail when Claude invokes the hook from a subdirectory.
    has_session_start = "launch_session_start_context" in content
    has_stop = "launch_record_change_on_stop" in content
    has_relative_session_start = ".sybermem/hooks/session_start_context.py" in content
    has_relative_stop = ".sybermem/hooks/record_change_on_stop.py" in content
    # Merged UserPromptSubmit hook (batch A): a single user_prompt.py entry is the
    # target state. The legacy detect_record_intent.py + task_recall.py pair is
    # still recognized so we can offer a non-destructive migration.
    has_user_prompt_hook = "user_prompt.py" in content
    has_record_intent_hook = "detect_record_intent.py" in content
    has_task_recall_hook = "task_recall.py" in content
    has_auto_mode = "SYBERMEM_RECORD_MODE" in content

    all_present = has_session_start and has_stop and has_user_prompt_hook and has_auto_mode
    return {
        "status": "fresh" if all_present else "stale",
        "has_session_start_hook": has_session_start,
        "has_stop_hook": has_stop,
        "has_relative_session_start_hook": has_relative_session_start,
        "has_relative_stop_hook": has_relative_stop,
        "has_user_prompt_hook": has_user_prompt_hook,
        "has_record_intent_hook": has_record_intent_hook,
        "has_task_recall_hook": has_task_recall_hook,
        "has_auto_mode": has_auto_mode,
    }


def check_stop_hook(root: Path) -> dict:
    """Check record_change_on_stop.py status."""
    path = root / ".sybermem" / "hooks" / "record_change_on_stop.py"
    content = read_text(path)
    if content is None:
        return {"status": "missing"}
    # Check for unified nudge state path (lifecycle layer feature)
    has_unified_nudge = '".nudge-state.json"' in content
    return {"status": "fresh" if has_unified_nudge else "stale"}


def check_session_start_hook(root: Path) -> dict:
    """Check session_start_context.py status — detect stale versions that over-inject."""
    path = root / ".sybermem" / "hooks" / "session_start_context.py"
    content = read_text(path)
    if content is None:
        return {"status": "missing"}
    # Stale if it still injects full Topic Index or skill list into output
    has_topic_dump = "Topic Index:" in content and "for topic, records" in content
    has_skill_list = "SyberMem skills available:" in content
    # Also stale if it predates digest governance or latest-digest injection:
    # content-check, not just existence, so these capabilities actually propagate
    # to older projects via /sybermem-update.
    missing_digest_heads_up = "detect_stale_digests" not in content
    missing_latest_digest_injection = "latest_digest_section" not in content
    is_stale = has_topic_dump or has_skill_list or missing_digest_heads_up or missing_latest_digest_injection
    return {"status": "stale" if is_stale else "fresh"}


def check_task_recall_hook(root: Path) -> dict:
    """Check task_recall.py status — detect stale copies missing task recall output contract."""
    path = root / ".sybermem" / "hooks" / "task_recall.py"
    content = read_text(path)
    if content is None:
        return {"status": "missing"}
    has_task_context_banner = "SyberMem retrieval hints for this task (maximum 3):" in content
    has_user_prompt_submit_contract = '"hookEventName": "UserPromptSubmit"' in content
    # Content-check the newer capabilities so they propagate to existing projects:
    # the aha/visible marker layer and the UTF-8 byte-buffer output that keeps
    # non-ASCII hints from silently failing on locales like GBK.
    has_aha_layer = "_is_aha_row" in content
    has_visible_marker_layer = "_has_high_signal_score" in content and "💡" in content
    has_utf8_output = "sys.stdout.buffer.write" in content
    is_fresh = (
        has_task_context_banner
        and has_user_prompt_submit_contract
        and has_aha_layer
        and has_visible_marker_layer
        and has_utf8_output
    )
    return {"status": "fresh" if is_fresh else "stale"}


def check_user_prompt_hook(root: Path) -> dict:
    """Check user_prompt.py status — the merged record-intent + task-recall hook (batch A)."""
    path = root / ".sybermem" / "hooks" / "user_prompt.py"
    content = read_text(path)
    if content is None:
        return {"status": "missing"}
    # Fresh copies orchestrate both legacy modules in one process.
    has_merged_contract = "Merged UserPromptSubmit hook" in content or (
        "detect_record_intent" in content and "task_recall" in content
    )
    # Content-check the UTF-8 byte-buffer output so the fix (non-ASCII aha markers /
    # CJK titles no longer crash this wired hook on GBK consoles) reaches old projects.
    has_utf8_output = "sys.stdout.buffer.write" in content
    return {"status": "fresh" if has_merged_contract and has_utf8_output else "stale"}


def check_file_exists(path: Path) -> dict:
    """Simple existence check for files that are either present or missing."""
    return {"status": "fresh" if path.is_file() else "missing"}


def check_record_template(path: Path) -> FileStatus:
    """Check whether a record template is missing, stale, or fresh."""
    content = read_text(path)
    if content is None:
        return {"status": "missing"}

    has_canonical_fields = all(
        field in content for field in RECORD_TEMPLATE_REQUIRED_FIELDS
    )
    has_legacy_numbering = any(
        marker in content for marker in LEGACY_RECORD_TEMPLATE_MARKERS
    )
    return {
        "status": (
            "fresh" if has_canonical_fields and not has_legacy_numbering else "stale"
        )
    }


def check_digest_template(path: Path) -> FileStatus:
    """Check the phase-digest template: missing, stale (pre coverage_hash), or fresh.

    coverage_hash is the field that enables mechanical stale-digest detection. A digest
    template that predates it (still carries the never-computed `fingerprint` field, or
    simply lacks `coverage_hash`) is stale and must be replaced by /sybermem-update so
    existing projects gain the capability, not just fresh installs.
    """
    content = read_text(path)
    if content is None:
        return {"status": "missing"}
    return {"status": "fresh" if "coverage_hash:" in content else "stale"}


def check_dir_exists(path: Path) -> dict:
    """Simple existence check for directories."""
    return {"status": "present" if path.is_dir() else "missing"}


def check_gitignore(root: Path) -> dict:
    """Check whether the SyberMem ignore block is present in a git project's .gitignore.

    Non-git projects are out of scope (fresh, no action). For git projects, a
    missing or stale SyberMem marker block is actionable so runtime/scripts stay
    out of version control while shareable records remain committable.
    """
    if not (root / ".git").exists():
        return {"status": "fresh", "applicable": False}
    content = read_text(root / ".gitignore")
    if content is None:
        return {"status": "missing", "applicable": True}
    has_block = "# >>> SyberMem >>>" in content and "# <<< SyberMem <<<" in content
    if not has_block:
        return {"status": "missing", "applicable": True}
    # Content-check a couple of load-bearing lines so old blocks get refreshed.
    is_current = "/.sybermem/hooks/" in content and "/.claude/settings.json" in content
    return {"status": "fresh" if is_current else "stale", "applicable": True}


def check_index_md(root: Path) -> dict:
    """Check .sybermem/INDEX.md status."""
    path = root / ".sybermem" / "INDEX.md"
    content = read_text(path)
    if content is None:
        return {
            "status": "missing",
            "has_conclusions_anchor": False,
            "has_digest_anchor": False,
            "has_records_anchors": False,
            "has_topic_index": False,
        }

    has_conclusions = "<!-- add new conclusions here -->" in content
    has_digest = "<!-- add new digest records here -->" in content
    has_records = "<!-- add new records here -->" in content
    has_topic_index = "## Topic Index" in content
    has_theme_digests = "## Theme Digests" in content
    has_theme_digest_anchor = "<!-- add new theme digest records here -->" in content
    has_archived_conclusions = "## Archived Conclusions" in content
    has_archived_anchor = "<!-- add new archived conclusions here -->" in content

    all_present = has_conclusions and has_digest and has_records and has_topic_index and has_theme_digests and has_theme_digest_anchor and has_archived_conclusions and has_archived_anchor
    return {
        "status": "fresh" if all_present else "stale",
        "has_conclusions_anchor": has_conclusions,
        "has_digest_anchor": has_digest,
        "has_records_anchors": has_records,
        "has_topic_index": has_topic_index,
        "has_theme_digests": has_theme_digests,
        "has_theme_digest_anchor": has_theme_digest_anchor,
        "has_archived_conclusions": has_archived_conclusions,
        "has_archived_anchor": has_archived_anchor,
    }


def generate_actions(files: dict) -> list[str]:
    """Generate the list of actions needed based on file statuses."""
    actions: list[str] = []

    # .gitignore — add/refresh the SyberMem ignore block only for git projects
    gi = files.get(".gitignore", {})
    if gi.get("applicable"):
        if gi.get("status") == "missing":
            actions.append("add SyberMem ignore block to .gitignore (preserve existing content)")
        elif gi.get("status") == "stale":
            actions.append("refresh SyberMem ignore block in .gitignore (preserve content outside block)")

    # Instruction files — remove legacy protocol blocks, never touch user content
    for name in ("CLAUDE.md", "AGENTS.md"):
        info = files.get(name, {})
        if info.get("status") == "missing":
            continue
        if info.get("has_protocol_block"):
            if info.get("is_sybermem_only"):
                actions.append(f"remove {name} (purely SyberMem-managed)")
            else:
                actions.append(f"remove protocol block from {name} (preserve content outside block)")

    # settings.json — surgical patch only
    sj = files.get(".claude/settings.json", {})
    if sj.get("status") == "missing":
        actions.append("create .claude/settings.json from template")
    else:
        if not sj.get("has_session_start_hook"):
            if sj.get("has_relative_session_start_hook"):
                actions.append("migrate SessionStart hook to the global launcher path in .claude/settings.json (replace the relative .sybermem/hooks/session_start_context.py command; preserve other hooks)")
            else:
                actions.append("add SessionStart hook entry to .claude/settings.json (preserve other hooks)")
        if not sj.get("has_stop_hook"):
            if sj.get("has_relative_stop_hook"):
                actions.append("migrate Stop hook to the global launcher path in .claude/settings.json (replace the relative .sybermem/hooks/record_change_on_stop.py command; preserve other hooks)")
            else:
                actions.append("add Stop hook entry to .claude/settings.json (preserve other hooks)")
        if not sj.get("has_user_prompt_hook"):
            if sj.get("has_record_intent_hook") or sj.get("has_task_recall_hook"):
                actions.append("migrate UserPromptSubmit to the merged user_prompt.py hook in .claude/settings.json (replace the detect_record_intent + task_recall entries with a single user_prompt.py entry; preserve other hooks)")
            else:
                actions.append("wire UserPromptSubmit to .sybermem/hooks/user_prompt.py in .claude/settings.json (preserve other hooks)")
        if not sj.get("has_auto_mode"):
            actions.append("add SYBERMEM_RECORD_MODE to .claude/settings.json (preserve other env)")

    # SyberMem-owned hooks — create if missing, replace if stale
    for hook_name, key in [
        ("session_start_context.py", ".sybermem/hooks/session_start_context.py"),
        ("launch_record_change_on_stop.py", ".sybermem/hooks/launch_record_change_on_stop.py"),
        ("detect_record_intent.py", ".sybermem/hooks/detect_record_intent.py"),
    ]:
        info = files.get(key, {})
        if info.get("status") == "missing":
            actions.append(f"create {key} from template")
        elif info.get("status") == "stale":
            actions.append(f"replace {key} from template")

    rcos = files.get(".sybermem/hooks/record_change_on_stop.py", {})
    if rcos.get("status") == "missing":
        actions.append("create .sybermem/hooks/record_change_on_stop.py from template")
    elif rcos.get("status") == "stale":
        actions.append("replace .sybermem/hooks/record_change_on_stop.py from template")

    trh = files.get(".sybermem/hooks/task_recall.py", {})
    if trh.get("status") == "missing":
        actions.append("create .sybermem/hooks/task_recall.py from template")
    elif trh.get("status") == "stale":
        actions.append("replace .sybermem/hooks/task_recall.py from template")

    uph = files.get(".sybermem/hooks/user_prompt.py", {})
    if uph.get("status") == "missing":
        actions.append("create .sybermem/hooks/user_prompt.py from template")
    elif uph.get("status") == "stale":
        actions.append("replace .sybermem/hooks/user_prompt.py from template")

    # INDEX.md — insert missing sections only
    idx = files.get(".sybermem/INDEX.md", {})
    if idx.get("status") == "stale":
        if not idx.get("has_digest_anchor"):
            actions.append("insert Phase Digests section into INDEX.md (preserve existing content)")
        if not idx.get("has_theme_digests") or not idx.get("has_theme_digest_anchor"):
            actions.append("insert Theme Digests section into INDEX.md (preserve existing content)")
        if not idx.get("has_archived_conclusions") or not idx.get("has_archived_anchor"):
            actions.append("insert Archived Conclusions section into INDEX.md (preserve existing content)")
        if not idx.get("has_topic_index"):
            actions.append("insert Topic Index section into INDEX.md (preserve existing content)")

    # Record templates — create if missing, replace if stale
    for template_path in (
        ".sybermem/templates/change-template.md",
        ".sybermem/templates/decision-template.md",
        ".sybermem/templates/requirement-template.md",
        ".sybermem/templates/bug-template.md",
    ):
        info = files.get(template_path, {})
        if info.get("status") == "missing":
            actions.append(f"create {template_path} from template")
        elif info.get("status") == "stale":
            actions.append(f"replace {template_path} from template")

    # Directories and non-record templates — create if missing
    for d in (
        ".sybermem/digests/",
        ".sybermem/theme-digests/",
        ".sybermem/analysis/phase-index.md",
        ".sybermem/templates/theme-digest-template.md",
    ):
        info = files.get(d, {})
        if info.get("status") == "missing":
            actions.append(f"create {d} from template")

    # Phase-digest template — create if missing, replace if stale so the coverage_hash
    # capability (mechanical stale-digest detection) propagates to existing projects.
    dgt = files.get(".sybermem/templates/digest-template.md", {})
    if dgt.get("status") == "missing":
        actions.append("create .sybermem/templates/digest-template.md from template")
    elif dgt.get("status") == "stale":
        actions.append("replace .sybermem/templates/digest-template.md from template")

    # Project identity
    proj = files.get(".sybermem/project.yaml", {})
    if proj.get("status") == "missing":
        actions.append("create .sybermem/project.yaml with project identity")

    return actions


def main() -> int:
    root = resolve_sybermem_root()
    if root is None:
        print(json.dumps({"root": None, "overall": "not_initialized", "files": {}, "capabilities": {}, "actions_needed": []}))
        return 0

    # Self-update: if the globally installed template is newer, replace ourselves and re-exec.
    # This ensures the health check always knows about the latest managed-file requirements,
    # even when the project was initialized with an older version of SyberMem.
    me = Path(__file__).resolve()
    for project_files in GLOBAL_TEMPLATE_PROJECT_FILES:
        skill_base = project_files / ".sybermem" / "hooks"
        template_health = skill_base / "check_project_health.py"
        if template_health.is_file():
            template_text = template_health.read_text(encoding="utf-8")
            my_text = me.read_text(encoding="utf-8")
            if template_text != my_text:
                me.write_text(template_text, encoding="utf-8")
                import sys
                result = subprocess.run([sys.executable, str(me)], cwd=Path.cwd())
                raise SystemExit(result.returncode)
            break

    files: dict = {}
    files["CLAUDE.md"] = check_instruction_file(root, "CLAUDE.md", "")
    files["AGENTS.md"] = check_instruction_file(root, "AGENTS.md", "")
    files[".claude/settings.json"] = check_settings_json(root)
    files[".sybermem/hooks/record_change_on_stop.py"] = check_stop_hook(root)
    files[".sybermem/hooks/session_start_context.py"] = check_session_start_hook(root)
    files[".sybermem/hooks/task_recall.py"] = check_task_recall_hook(root)
    files[".sybermem/hooks/user_prompt.py"] = check_user_prompt_hook(root)
    files[".sybermem/hooks/launch_record_change_on_stop.py"] = check_file_exists(root / ".sybermem" / "hooks" / "launch_record_change_on_stop.py")
    files[".sybermem/INDEX.md"] = check_index_md(root)
    files[".sybermem/digests/"] = check_dir_exists(root / ".sybermem" / "digests")
    files[".sybermem/theme-digests/"] = check_dir_exists(root / ".sybermem" / "theme-digests")
    files[".sybermem/analysis/phase-index.md"] = check_file_exists(root / ".sybermem" / "analysis" / "phase-index.md")
    files[".sybermem/templates/change-template.md"] = check_record_template(root / ".sybermem" / "templates" / "change-template.md")
    files[".sybermem/templates/decision-template.md"] = check_record_template(root / ".sybermem" / "templates" / "decision-template.md")
    files[".sybermem/templates/requirement-template.md"] = check_record_template(root / ".sybermem" / "templates" / "requirement-template.md")
    files[".sybermem/templates/bug-template.md"] = check_record_template(root / ".sybermem" / "templates" / "bug-template.md")
    files[".sybermem/templates/digest-template.md"] = check_digest_template(root / ".sybermem" / "templates" / "digest-template.md")
    files[".sybermem/templates/theme-digest-template.md"] = check_file_exists(root / ".sybermem" / "templates" / "theme-digest-template.md")

    # Check for health script itself
    files[".sybermem/hooks/check_project_health.py"] = check_file_exists(root / ".sybermem" / "hooks" / "check_project_health.py")
    files[".sybermem/hooks/detect_record_intent.py"] = check_file_exists(root / ".sybermem" / "hooks" / "detect_record_intent.py")

    # Project identity
    files[".sybermem/project.yaml"] = check_file_exists(root / ".sybermem" / "project.yaml")

    # .gitignore ignore block (git projects only)
    files[".gitignore"] = check_gitignore(root)

    # Determine overall status
    index_status = files[".sybermem/INDEX.md"]["status"]
    if index_status == "missing":
        overall = "not_initialized"
    elif all(
        f.get("status") in ("fresh", "present")
        for f in files.values()
    ):
        overall = "fresh"
    else:
        overall = "needs_update"

    # Capabilities
    capabilities = {
        "digest": files[".sybermem/digests/"]["status"] == "present",
        "theme_digest": files[".sybermem/theme-digests/"]["status"] == "present",
        "analysis": files[".sybermem/analysis/phase-index.md"]["status"] != "missing",
        "auto_record_hook": files[".sybermem/hooks/record_change_on_stop.py"]["status"] != "missing",
        "session_start_hook": files[".sybermem/hooks/session_start_context.py"]["status"] != "missing",
    }

    actions = generate_actions(files) if overall == "needs_update" else []

    report = {
        "root": str(root),
        "overall": overall,
        "files": files,
        "capabilities": capabilities,
        "actions_needed": actions,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
