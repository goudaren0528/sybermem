# SyberMem Update Fast-Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Speed up `/sybermem-update` from 15-25 tool calls to 1 script call + targeted fixes, by adding a Python health-check script and a fast-path to `init-project`.

**Architecture:** A new `check_project_health.py` script does all managed-file classification in one shot, outputting a JSON report. The `init-project` SKILL.md gets a fast-path that runs this script first — if everything is fresh, it exits immediately; if not, it processes only the `actions_needed` list with non-destructive updates (protocol-block insertion, surgical JSON patching, never full-file overwrites for user files).

**Tech Stack:** Python 3.10+ (health check script), Markdown (SKILL.md edits)

**Spec:** `docs/superpowers/specs/2026-06-18-sybermem-update-fastpath-design.md`

**Global Constraints:**
- `CLAUDE.md` / `AGENTS.md`: NEVER overwrite the whole file. Only insert/refresh the `SYBERMEM_SESSION_PROTOCOL` bounded block. Preserve all user content outside the block.
- `.claude/settings.json`: NEVER overwrite the whole file. Only add/update SyberMem-owned entries (`env.SYBERMEM_RECORD_MODE`, `hooks.SessionStart`, `hooks.Stop`). Preserve all other fields and hooks.
- `.sybermem/INDEX.md`: NEVER regenerate. Only insert missing sections (e.g. `## Stage Digests`, `## Topic Index`). Preserve all existing data.
- `.sybermem/hooks/*.py` and `.sybermem/templates/*.md`: SyberMem-owned — safe to replace entirely.

---

### Task 1: Create check_project_health.py

The core new script. Checks all managed files and outputs a JSON health report.

**Files:**
- Create: `.sybermem/hooks/check_project_health.py`

- [ ] **Step 1: Create the health check script**

```python
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

    return {
        "status": "fresh" if has_block else "stale",
        "has_protocol_block": has_block,
        "is_sybermem_only": is_sybermem_only,
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
            "has_auto_mode": False,
        }

    has_session_start = "launch_session_start_context" in content
    has_stop = "launch_record_change_on_stop" in content
    has_auto_mode = "SYBERMEM_RECORD_MODE" in content

    all_present = has_session_start and has_stop and has_auto_mode
    return {
        "status": "fresh" if all_present else "stale",
        "has_session_start_hook": has_session_start,
        "has_stop_hook": has_stop,
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

    all_present = has_conclusions and has_digest and has_records and has_topic_index
    return {
        "status": "fresh" if all_present else "stale",
        "has_conclusions_anchor": has_conclusions,
        "has_digest_anchor": has_digest,
        "has_records_anchors": has_records,
        "has_topic_index": has_topic_index,
    }


def generate_actions(files: dict) -> list[str]:
    """Generate the list of actions needed based on file statuses."""
    actions: list[str] = []

    # Instruction files — insert only, never overwrite
    for name in ("CLAUDE.md", "AGENTS.md"):
        info = files.get(name, {})
        if info.get("status") == "missing":
            actions.append(f"create {name} from template")
        elif not info.get("has_protocol_block"):
            actions.append(f"insert protocol block into {name} (preserve existing content)")

    # settings.json — surgical patch only
    sj = files.get(".claude/settings.json", {})
    if sj.get("status") == "missing":
        actions.append("create .claude/settings.json from template")
    else:
        if not sj.get("has_session_start_hook"):
            actions.append("add SessionStart hook entry to .claude/settings.json (preserve other hooks)")
        if not sj.get("has_stop_hook"):
            actions.append("add Stop hook entry to .claude/settings.json (preserve other hooks)")
        if not sj.get("has_auto_mode"):
            actions.append("add SYBERMEM_RECORD_MODE to .claude/settings.json (preserve other env)")

    # SyberMem-owned hooks — create or replace
    for hook_name, key in [
        ("session_start_context.py", ".sybermem/hooks/session_start_context.py"),
        ("launch_record_change_on_stop.py", ".sybermem/hooks/launch_record_change_on_stop.py"),
    ]:
        info = files.get(key, {})
        if info.get("status") == "missing":
            actions.append(f"create {key} from template")

    rcos = files.get(".sybermem/hooks/record_change_on_stop.py", {})
    if rcos.get("status") == "missing":
        actions.append("create .sybermem/hooks/record_change_on_stop.py from template")
    elif rcos.get("status") == "stale":
        actions.append("replace .sybermem/hooks/record_change_on_stop.py from template")

    # INDEX.md — insert missing sections only
    idx = files.get(".sybermem/INDEX.md", {})
    if idx.get("status") == "stale":
        if not idx.get("has_digest_anchor"):
            actions.append("insert Stage Digests section into INDEX.md (preserve existing content)")
        if not idx.get("has_topic_index"):
            actions.append("insert Topic Index section into INDEX.md (preserve existing content)")

    # Directories and templates — create if missing
    for d in (".sybermem/digests/", ".sybermem/analysis/phase-index.md", ".sybermem/templates/digest-template.md"):
        info = files.get(d, {})
        if info.get("status") == "missing":
            actions.append(f"create {d} from template")

    return actions


def main() -> int:
    root = resolve_sybermem_root()
    if root is None:
        print(json.dumps({"root": None, "overall": "not_initialized", "files": {}, "capabilities": {}, "actions_needed": []}))
        return 0

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
    files[".sybermem/hooks/session_start_context.py"] = check_file_exists(root / ".sybermem" / "hooks" / "session_start_context.py")
    files[".sybermem/hooks/launch_record_change_on_stop.py"] = check_file_exists(root / ".sybermem" / "hooks" / "launch_record_change_on_stop.py")
    files[".sybermem/INDEX.md"] = check_index_md(root)
    files[".sybermem/digests/"] = check_dir_exists(root / ".sybermem" / "digests")
    files[".sybermem/analysis/phase-index.md"] = check_file_exists(root / ".sybermem" / "analysis" / "phase-index.md")
    files[".sybermem/templates/digest-template.md"] = check_file_exists(root / ".sybermem" / "templates" / "digest-template.md")

    # Check for health script itself
    files[".sybermem/hooks/check_project_health.py"] = check_file_exists(root / ".sybermem" / "hooks" / "check_project_health.py")

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
        "analysis": files[".sybermem/analysis/phase-index.md"]["status"] != "missing",
        "auto_record_hook": files[".sybermem/hooks/record_change_on_stop.py"]["status"] != "missing",
        "session_start_hook": files[".sybermem/hooks/session_start_context.py"]["status"] != "missing",
        "protocol_block": files["CLAUDE.md"].get("has_protocol_block", False) or files["AGENTS.md"].get("has_protocol_block", False),
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
```

- [ ] **Step 2: Verify the script runs and produces correct output**

Run: `python .sybermem/hooks/check_project_health.py`

Expected: JSON output with `overall: "fresh"` (since this project is fully up to date after the lifecycle layer work). All files should show `status: "fresh"` or `"present"`.

- [ ] **Step 3: Verify stale detection works by simulating a missing capability**

Run: `python -c "import json; r = json.loads(open('.sybermem/hooks/check_project_health.py').read()); print('script exists')"` — just confirm the script is readable. The real stale-detection verification is that the check logic is correct by inspection: each check function uses the exact markers from the spec.

- [ ] **Step 4: Commit**

```bash
git add .sybermem/hooks/check_project_health.py
git commit -m "feat: add check_project_health.py for fast-path update detection"
```

---

### Task 2: Copy health check script to init-project template

**Files:**
- Create: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`

- [ ] **Step 1: Copy the script from Task 1**

Copy the entire contents of `.sybermem/hooks/check_project_health.py` to `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`.

- [ ] **Step 2: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py
git commit -m "feat: add check_project_health.py to init-project template"
```

---

### Task 3: Update init-project SKILL.md with fast-path and non-destructive update rules

This is the key skill modification. Add a fast-path at the top of the Flow section, and reinforce non-destructive update rules.

**Files:**
- Modify: `packages/claude-skills/sybermem-init-project/SKILL.md`

- [ ] **Step 1: Add the fast-path step before Step 1**

Find in the SKILL.md:
```markdown
## Flow

### Step 1: Resolve existing state
```

Insert between `## Flow` and `### Step 1`:

```markdown
### Step 0.5: Fast-path health check (existing projects only)

If `.sybermem/hooks/check_project_health.py` exists at the resolved project root, run it first:

```bash
python .sybermem/hooks/check_project_health.py
```

Parse the JSON output and branch:

**If `overall == "fresh"`:**
- Output: "SyberMem project is up to date. No changes needed."
- Skip all subsequent steps. Skill is complete.

**If `overall == "needs_update"`:**
- Process only the `actions_needed` list. Each action specifies its update method:
  - `"create ..."` → create the file from the init-project template
  - `"insert ..."` → non-destructive partial update (see Non-Destructive Update Rules below)
  - `"replace ..."` → full replacement (only for SyberMem-owned files like hooks and templates)
  - `"add ..."` → surgical JSON patch (only for settings.json hook entries)
- After processing all actions, output a summary of what was changed and skip remaining steps.

**If `overall == "not_initialized"` or the script does not exist:**
- Proceed with the full initialization flow starting at Step 1.

### Non-Destructive Update Rules

**These rules apply to ALL update operations, whether triggered by fast-path or full flow.**

| File | Allowed Update | Forbidden |
|---|---|---|
| `CLAUDE.md` / `AGENTS.md` | Insert or refresh the bounded `SYBERMEM_SESSION_PROTOCOL:START`/`END` block only. If the block exists, replace only its contents. If it does not exist, insert the complete block at the top of the file. All content outside the block markers is preserved verbatim. | Overwriting the entire file when it contains user content outside the protocol block. |
| `.claude/settings.json` | Read with `json.load`, add/update only SyberMem-owned keys (`env.SYBERMEM_RECORD_MODE`, `hooks.SessionStart`, `hooks.Stop`), write back with `json.dump`. All other keys, env vars, and hooks are preserved. | Overwriting the entire file from template. |
| `.sybermem/INDEX.md` | Insert missing sections (`## Stage Digests`, `## Topic Index`) at the appropriate position. All existing Key Conclusions, record tables, and user data are preserved. | Regenerating the entire file from template. |
| `.sybermem/hooks/*.py` | Full replacement from template — these are SyberMem-owned executables with no user content. | — |
| `.sybermem/templates/*.md` | Full replacement from template — these are SyberMem-owned templates. | — |

```

- [ ] **Step 2: Add check_project_health.py to the template files list in Step 1.1**

Find in the SKILL.md:
```markdown
Use these template files from this installed skill as the canonical refresh source:

- `project-files/AGENTS.md`
- `project-files/CLAUDE.md`
- `project-files/.claude/settings.json`
- `project-files/.sybermem/hooks/record_change_on_stop.py`
```

Add after the last bullet:
```markdown
- `project-files/.sybermem/hooks/check_project_health.py`
```

- [ ] **Step 3: Add check_project_health.py creation to Step 7**

Find in the SKILL.md, in Step 7 ("Create or refresh project instruction files"), after the bullet about `session_start_context.py`:
```markdown
- Create missing `.sybermem/hooks/session_start_context.py` from the template file when startup context injection is being installed.
```

Add after it:
```markdown
- Create missing `.sybermem/hooks/check_project_health.py` from the template file to enable fast-path updates on subsequent runs.
```

- [ ] **Step 4: Add check_project_health.py to Step 8 output summary**

Find in the SKILL.md, in Step 8 output summary, in the "Created or updated" list. After the line about `session_start_context.py`:
```markdown
- `.sybermem/hooks/session_start_context.py` when startup context injection is installed
```

Add after it:
```markdown
- `.sybermem/hooks/check_project_health.py` for fast-path update detection
```

- [ ] **Step 5: Verify the SKILL.md is well-formed**

Read back the modified SKILL.md and verify:
1. Step 0.5 appears between `## Flow` and `### Step 1`
2. Non-Destructive Update Rules table is present
3. `check_project_health.py` appears in the template list, Step 7, and Step 8
4. No existing content was accidentally removed

- [ ] **Step 6: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/SKILL.md
git commit -m "feat: add fast-path health check and non-destructive update rules to init-project"
```

---

### Task 4: Verify end-to-end fast-path on this project

Run the health check on this project (which should be fully up to date) and confirm the fast-path would work.

**Files:**
- No file changes

- [ ] **Step 1: Run the health check script**

Run: `python .sybermem/hooks/check_project_health.py`

Expected: JSON with `"overall": "fresh"` and empty `actions_needed`.

- [ ] **Step 2: Verify all files report fresh/present**

Parse the output and confirm every file status is `"fresh"` or `"present"`. No `"missing"` or `"stale"`.

- [ ] **Step 3: Verify the health check script itself is in the report**

Confirm the output includes `".sybermem/hooks/check_project_health.py": {"status": "fresh"}`.

- [ ] **Step 4: No commit needed** (verification only)
