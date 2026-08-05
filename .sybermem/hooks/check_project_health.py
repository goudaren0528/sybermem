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
    """Check CLAUDE.md or AGENTS.md status."""
    path = root / name
    content = read_text(path)
    if content is None:
        return {"status": "missing", "has_protocol_block": False, "is_sybermem_only": False}

    has_block = "SYBERMEM_SESSION_PROTOCOL:START" in content and "SYBERMEM_SESSION_PROTOCOL:END" in content

    # Check if file is purely SyberMem-managed (no user custom content)
    # Strip the protocol block from both template and file, compare the rest
    block_pattern = re.compile(
        r"<!-- SYBERMEM_SESSION_PROTOCOL:START -->.*?<!-- SYBERMEM_SESSION_PROTOCOL:END -->",
        re.DOTALL,
    )
    file_stripped = block_pattern.sub("", content).strip()
    template_stripped = block_pattern.sub("", template_content).strip()
    is_sybermem_only = file_stripped == template_stripped

    # Detect old SyberMem templates that have heavy sections outside the protocol block.
    # These are NOT user custom content — they are leftover from older SyberMem versions.
    has_old_sybermem_sections = (
        "## Available Skills" in content
        or "## Workflow" in content
        or ("## Directory Resolution" in content and "## Core Rule" in content)
    )
    if has_old_sybermem_sections:
        is_sybermem_only = True

    # Even if protocol block exists, check if its content matches the template
    # (detects stale/over-heavy protocol blocks from older versions)
    block_is_current = True
    if has_block and template_content:
        file_block_m = block_pattern.search(content)
        template_block_m = block_pattern.search(template_content)
        if file_block_m and template_block_m:
            file_block = file_block_m.group(0).strip()
            template_block = template_block_m.group(0).strip()
            block_is_current = file_block == template_block

    # If file is entirely SyberMem-managed (including old heavy templates),
    # compare the whole file to the current template
    content_is_current = True
    if is_sybermem_only and template_content:
        content_is_current = content.strip() == template_content.strip()

    status = "fresh" if (has_block and block_is_current and content_is_current) else "stale"
    return {
        "status": status,
        "has_protocol_block": has_block,
        "is_sybermem_only": is_sybermem_only,
        "block_is_current": block_is_current,
        "content_is_current": content_is_current,
    }


def check_settings_json(root: Path) -> dict:
    """Check .claude/settings.json status."""
    path = root / ".claude" / "settings.json"
    content = read_text(path)
    if content is None:
        return {
            "status": "missing",
            "has_session_start_hook": False,
            "has_stop_hook": False,
            "has_record_intent_hook": False,
            "has_task_recall_hook": False,
            "has_auto_mode": False,
        }

    has_session_start = "launch_session_start_context" in content
    has_stop = "launch_record_change_on_stop" in content
    has_record_intent_hook = "detect_record_intent.py" in content
    has_task_recall_hook = "task_recall.py" in content
    has_auto_mode = "SYBERMEM_RECORD_MODE" in content

    all_present = has_session_start and has_stop and has_record_intent_hook and has_task_recall_hook and has_auto_mode
    return {
        "status": "fresh" if all_present else "stale",
        "has_session_start_hook": has_session_start,
        "has_stop_hook": has_stop,
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
    is_stale = has_topic_dump or has_skill_list
    return {"status": "stale" if is_stale else "fresh"}


def check_task_recall_hook(root: Path) -> dict:
    """Check task_recall.py status — detect stale copies missing task recall output contract."""
    path = root / ".sybermem" / "hooks" / "task_recall.py"
    content = read_text(path)
    if content is None:
        return {"status": "missing"}
    has_task_context_banner = "SyberMem retrieval hints for this task (maximum 3):" in content
    has_user_prompt_submit_contract = '"hookEventName": "UserPromptSubmit"' in content
    return {"status": "fresh" if has_task_context_banner and has_user_prompt_submit_contract else "stale"}


def check_file_exists(path: Path) -> dict:
    """Simple existence check for files that are either present or missing."""
    return {"status": "fresh" if path.is_file() else "missing"}


def check_dir_exists(path: Path) -> dict:
    """Simple existence check for directories."""
    return {"status": "present" if path.is_dir() else "missing"}


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

    # Instruction files — insert or refresh protocol block, never overwrite user content
    for name in ("CLAUDE.md", "AGENTS.md"):
        info = files.get(name, {})
        if info.get("status") == "missing":
            actions.append(f"create {name} from template")
        elif info.get("is_sybermem_only") and not info.get("content_is_current", True):
            # File is entirely SyberMem-managed (or old heavy template) — safe to replace whole file
            actions.append(f"replace {name} from template")
        elif not info.get("has_protocol_block"):
            actions.append(f"insert protocol block into {name} (preserve existing content)")
        elif not info.get("block_is_current", True):
            actions.append(f"replace protocol block in {name} (preserve content outside block)")

    # settings.json — surgical patch only
    sj = files.get(".claude/settings.json", {})
    if sj.get("status") == "missing":
        actions.append("create .claude/settings.json from template")
    else:
        if not sj.get("has_session_start_hook"):
            actions.append("add SessionStart hook entry to .claude/settings.json (preserve other hooks)")
        if not sj.get("has_stop_hook"):
            actions.append("add Stop hook entry to .claude/settings.json (preserve other hooks)")
        if not sj.get("has_record_intent_hook"):
            actions.append("add UserPromptSubmit hook entry to .claude/settings.json (preserve other hooks)")
        if not sj.get("has_task_recall_hook"):
            actions.append("add task_recall UserPromptSubmit entry to .claude/settings.json (preserve other hooks)")
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

    # Directories and templates — create if missing
    for d in (
        ".sybermem/digests/",
        ".sybermem/theme-digests/",
        ".sybermem/analysis/phase-index.md",
        ".sybermem/templates/digest-template.md",
        ".sybermem/templates/theme-digest-template.md",
    ):
        info = files.get(d, {})
        if info.get("status") == "missing":
            actions.append(f"create {d} from template")

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
    for skill_base in (
        Path.home() / ".claude" / "skills" / "sybermem-init-project" / "project-files" / ".sybermem" / "hooks",
        Path.home() / ".config" / "opencode" / "skills" / "sybermem-init-project" / "project-files" / ".sybermem" / "hooks",
    ):
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

    # Load template content for comparison
    # Templates are in the installed skill's project-files directory
    # But this script runs from the project, so we read templates relative to the skill install
    # For is_sybermem_only check, we need the template CLAUDE.md/AGENTS.md content
    # Find the template by checking known global skill paths
    template_claude = ""
    template_agents = ""
    for skill_base in (
        Path.home() / ".claude" / "skills" / "sybermem-init-project" / "project-files",
        Path.home() / ".config" / "opencode" / "skills" / "sybermem-init-project" / "project-files",
    ):
        claude_path = skill_base / "CLAUDE.md"
        agents_path = skill_base / "AGENTS.md"
        if claude_path.is_file() and not template_claude:
            template_claude = read_text(claude_path) or ""
        if agents_path.is_file() and not template_agents:
            template_agents = read_text(agents_path) or ""

    files: dict = {}
    files["CLAUDE.md"] = check_instruction_file(root, "CLAUDE.md", template_claude)
    files["AGENTS.md"] = check_instruction_file(root, "AGENTS.md", template_agents)
    files[".claude/settings.json"] = check_settings_json(root)
    files[".sybermem/hooks/record_change_on_stop.py"] = check_stop_hook(root)
    files[".sybermem/hooks/session_start_context.py"] = check_session_start_hook(root)
    files[".sybermem/hooks/task_recall.py"] = check_task_recall_hook(root)
    files[".sybermem/hooks/launch_record_change_on_stop.py"] = check_file_exists(root / ".sybermem" / "hooks" / "launch_record_change_on_stop.py")
    files[".sybermem/INDEX.md"] = check_index_md(root)
    files[".sybermem/digests/"] = check_dir_exists(root / ".sybermem" / "digests")
    files[".sybermem/theme-digests/"] = check_dir_exists(root / ".sybermem" / "theme-digests")
    files[".sybermem/analysis/phase-index.md"] = check_file_exists(root / ".sybermem" / "analysis" / "phase-index.md")
    files[".sybermem/templates/digest-template.md"] = check_file_exists(root / ".sybermem" / "templates" / "digest-template.md")
    files[".sybermem/templates/theme-digest-template.md"] = check_file_exists(root / ".sybermem" / "templates" / "theme-digest-template.md")

    # Check for health script itself
    files[".sybermem/hooks/check_project_health.py"] = check_file_exists(root / ".sybermem" / "hooks" / "check_project_health.py")
    files[".sybermem/hooks/detect_record_intent.py"] = check_file_exists(root / ".sybermem" / "hooks" / "detect_record_intent.py")

    # Project identity
    files[".sybermem/project.yaml"] = check_file_exists(root / ".sybermem" / "project.yaml")

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
        "protocol_block": files["CLAUDE.md"].get("has_protocol_block", False) or files["AGENTS.md"].get("has_protocol_block", False),
    }

    actions = generate_actions(files) if overall == "needs_update" else []

    # Team association check
    team_info = {"has_team_link": False, "team_path": "", "team_path_accessible": False}
    yaml_path = root / ".sybermem" / "project.yaml"
    if yaml_path.is_file():
        in_team = False
        for line in yaml_path.read_text(encoding="utf-8").splitlines():
            if line.rstrip() == "team:":
                in_team = True
                continue
            if in_team and line.startswith("  team_path:"):
                tp = line.split(":", 1)[1].strip()
                if tp:
                    team_info["has_team_link"] = True
                    team_info["team_path"] = tp
                    team_info["team_path_accessible"] = Path(tp).is_dir()
            if in_team and not line.startswith(" "):
                in_team = False

    report = {
        "root": str(root),
        "overall": overall,
        "files": files,
        "capabilities": capabilities,
        "team": team_info,
        "actions_needed": actions,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
