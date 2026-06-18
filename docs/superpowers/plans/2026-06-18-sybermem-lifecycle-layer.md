# SyberMem Lifecycle Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Embed SyberMem into the Claude Code / OpenCode session lifecycle so that project memory loads automatically at startup, nudges at the right moments on stop/idle, survives compaction, and deduplicates across platforms.

**Architecture:** A new `session_start_context.py` hook script reads Key Conclusions, Topic Index, and phase-index at session start and outputs structured `additionalContext`. The existing Stop hook gains commit-gap detection and auto-trail dedup. Both platforms converge on a single `.nudge-state.json`. The OpenCode plugin gets stale-signal detection and compaction length limits. Install/update scripts distribute the new global launcher.

**Tech Stack:** Python 3.10+ (hooks), TypeScript (OpenCode plugin), Bash/PowerShell (install scripts), JSON (settings/state)

**Spec:** `docs/superpowers/specs/2026-06-18-sybermem-lifecycle-layer-design.md`

---

### Task 1: Create session_start_context.py (project-level hook)

The core new file. Reads SyberMem state and outputs structured JSON for Claude Code's SessionStart hook.

**Files:**
- Create: `.sybermem/hooks/session_start_context.py`

- [ ] **Step 1: Create the session start context script**

```python
#!/usr/bin/env python3
"""SyberMem SessionStart hook — injects project memory context into Claude Code sessions.

Reads Key Conclusions, Topic Index, phase-index status, and stale signals.
Outputs structured JSON with hookSpecificOutput.additionalContext.
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


def run_git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd or Path.cwd(),
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def parse_conclusions(index_text: str) -> list[str]:
    match = re.search(
        r"## Key Conclusions\s*\n([\s\S]*?)(?=\n---|\n## )", index_text
    )
    if not match:
        return []
    return [
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith("- [")
    ]


def parse_topic_index(index_text: str) -> dict[str, list[str]]:
    match = re.search(
        r"## Topic Index\s*\n([\s\S]*?)(?=\n---|\n## |$)", index_text
    )
    if not match:
        return {}
    topics: dict[str, list[str]] = {}
    for line in match.group(1).splitlines():
        m = re.match(r"^- (\S+):\s*(.+)", line)
        if m:
            topics[m.group(1)] = [s.strip() for s in m.group(2).split(",")]
    return topics


def parse_phase_index(root: Path) -> dict:
    """Return phase-index metadata: status, last_git_boundary, active_phase, confirmed_count."""
    phase_path = root / ".sybermem" / "analysis" / "phase-index.md"
    if not phase_path.is_file():
        return {"exists": False}

    content = phase_path.read_text(encoding="utf-8")
    status_match = re.search(r"^- status:\s*(.+)", content, re.MULTILINE)
    boundary_match = re.search(r"^- last_git_boundary:\s*(\S+)", content, re.MULTILINE)
    phases = re.findall(r"### Phase: (.+)", content)

    return {
        "exists": True,
        "status": status_match.group(1).strip() if status_match else "unknown",
        "last_git_boundary": boundary_match.group(1).strip() if boundary_match else None,
        "active_phase": phases[-1] if phases else None,
        "confirmed_count": len(phases),
    }


def detect_stale_signal(root: Path, boundary_commit: str | None) -> dict:
    """Compare phase-index boundary to current HEAD."""
    if not boundary_commit:
        return {"stale": False, "commits_ahead": 0}

    head = run_git("rev-parse", "HEAD", cwd=root)
    if not head or head == boundary_commit:
        return {"stale": False, "commits_ahead": 0}

    count_str = run_git(
        "rev-list", "--count", f"{boundary_commit}..HEAD", cwd=root
    )
    try:
        count = int(count_str)
    except (ValueError, TypeError):
        count = 0

    return {
        "stale": count >= 3,
        "commits_ahead": count,
        "boundary": boundary_commit,
        "head": head[:7],
    }


def build_context(root: Path) -> str:
    """Build the additionalContext string for Claude Code."""
    index_path = root / ".sybermem" / "INDEX.md"
    if not index_path.is_file():
        return "SyberMem startup context:\nNo .sybermem/INDEX.md found. Run /sybermem-init-project to initialize."

    index_text = index_path.read_text(encoding="utf-8")
    conclusions = parse_conclusions(index_text)
    topics = parse_topic_index(index_text)
    phase_info = parse_phase_index(root)

    lines: list[str] = ["SyberMem startup context:"]
    lines.append(f"Loaded {len(conclusions)} key conclusions from SyberMem.")

    if topics:
        topic_names = ", ".join(sorted(topics.keys()))
        lines.append(f"Relevant topics: {topic_names}.")

    if phase_info["exists"]:
        lines.append(
            f"Phase index: {phase_info['status']}. "
            f"{phase_info['confirmed_count']} confirmed phases."
        )
        if phase_info["active_phase"]:
            lines.append(f"Active phase: {phase_info['active_phase']}.")

        stale = detect_stale_signal(root, phase_info.get("last_git_boundary"))
        if stale["stale"]:
            lines.append(
                f"Stale signal: phase-index last git boundary is {stale['boundary']}, "
                f"current HEAD is {stale['head']} ({stale['commits_ahead']} commits ahead)."
            )
    else:
        lines.append("Phase index: not found. Run /sybermem-phase-analyze to create it.")

    if conclusions:
        lines.append("")
        lines.append("Key Conclusions:")
        for c in conclusions:
            lines.append(c)

    if topics:
        lines.append("")
        lines.append("Topic Index:")
        for topic, records in sorted(topics.items()):
            lines.append(f"- {topic}: {', '.join(records)}")

    return "\n".join(lines)


def main() -> int:
    root = resolve_sybermem_root()
    if root is None:
        return 0

    context = build_context(root)

    output = json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    })
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify the script runs without errors**

Run: `python .sybermem/hooks/session_start_context.py`

Expected: JSON output containing `hookSpecificOutput.additionalContext` with conclusions, topics, phase info.

- [ ] **Step 3: Commit**

```bash
git add .sybermem/hooks/session_start_context.py
git commit -m "feat: add session_start_context.py hook for startup memory injection"
```

---

### Task 2: Create global-session-start-launcher.py

Mirrors the existing `global-stop-hook-launcher.py` pattern — resolves root then delegates to the project-level script.

**Files:**
- Create: `scripts/global-session-start-launcher.py`

- [ ] **Step 1: Create the launcher script**

```python
#!/usr/bin/env python3
"""Global launcher for SyberMem SessionStart hook.

Resolves the SyberMem project root from the current working directory,
then delegates to the project-level session_start_context.py script.
Mirrors the pattern of global-stop-hook-launcher.py.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def resolve_sybermem_root() -> Path | None:
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


def main() -> int:
    root = resolve_sybermem_root()
    if root is None:
        return 0

    target = root / ".sybermem" / "hooks" / "session_start_context.py"
    if not target.is_file():
        return 0

    result = subprocess.run([sys.executable, str(target)], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify the launcher works end-to-end**

Run: `python scripts/global-session-start-launcher.py`

Expected: Same JSON output as running the project-level script directly.

- [ ] **Step 3: Commit**

```bash
git add scripts/global-session-start-launcher.py
git commit -m "feat: add global session start launcher for Claude Code SessionStart hook"
```

---

### Task 3: Update .claude/settings.json — add SessionStart hook

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1: Add the SessionStart hook entry**

The current file is:

```json
{
  "env": {
    "SYBERMEM_RECORD_MODE": "auto"
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/69046/.claude/sybermem/launch_record_change_on_stop.py",
            "timeout": 60,
            "statusMessage": "SyberMem checking whether to record a change..."
          }
        ]
      }
    ]
  }
}
```

Replace the entire file with:

```json
{
  "env": {
    "SYBERMEM_RECORD_MODE": "auto"
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/69046/.claude/sybermem/launch_session_start_context.py",
            "timeout": 15,
            "statusMessage": "SyberMem loading project memory..."
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/69046/.claude/sybermem/launch_record_change_on_stop.py",
            "timeout": 60,
            "statusMessage": "SyberMem checking whether to record a change..."
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Validate JSON syntax**

Run: `python -c "import json; json.load(open('.claude/settings.json'))" && echo OK`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .claude/settings.json
git commit -m "feat: add SessionStart hook to .claude/settings.json for startup memory injection"
```

---

### Task 4: Update init-project template settings.json

New projects initialized with `/sybermem-init-project` should also get the SessionStart hook.

**Files:**
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json`

- [ ] **Step 1: Update the template to include SessionStart hook**

The current template is:

```json
{
  "env": {
    "SYBERMEM_RECORD_MODE": "auto"
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/69046/.claude/sybermem/launch_record_change_on_stop.py",
            "timeout": 60,
            "statusMessage": "SyberMem checking whether to record a change..."
          }
        ]
      }
    ]
  }
}
```

Replace the entire file with:

```json
{
  "env": {
    "SYBERMEM_RECORD_MODE": "auto"
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/69046/.claude/sybermem/launch_session_start_context.py",
            "timeout": 15,
            "statusMessage": "SyberMem loading project memory..."
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/69046/.claude/sybermem/launch_record_change_on_stop.py",
            "timeout": 60,
            "statusMessage": "SyberMem checking whether to record a change..."
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json
git commit -m "feat: add SessionStart hook to init-project template settings.json"
```

---

### Task 5: Add session_start_context.py to init-project template

So that `/sybermem-init-project` provisions it to new projects.

**Files:**
- Create: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py`

- [ ] **Step 1: Copy the session_start_context.py from Task 1**

Create the file with the exact same content as `.sybermem/hooks/session_start_context.py` from Task 1.

- [ ] **Step 2: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py
git commit -m "feat: add session_start_context.py to init-project template"
```

---

### Task 6: Update init-project SKILL.md to install SessionStart hook

**Files:**
- Modify: `packages/claude-skills/sybermem-init-project/SKILL.md`

- [ ] **Step 1: Add SessionStart hook to the managed files list**

In the SKILL.md, find the Step 7 section ("Create or refresh project instruction files"). After the bullet about ensuring the global launcher exists, add:

```markdown
- Create missing `.sybermem/hooks/session_start_context.py` from the template file when startup context injection is being installed.
- Ensure the global session start launcher `~/.claude/sybermem/launch_session_start_context.py` exists; if not, instruct the user to refresh global skills first or run `/sybermem-update`.
```

Also update the settings.json description to mention SessionStart:

Find:
```markdown
- The generated `.claude/settings.json` must set `SYBERMEM_RECORD_MODE` and install the default Stop hook for automatic `change` records only.
```

Replace with:
```markdown
- The generated `.claude/settings.json` must set `SYBERMEM_RECORD_MODE`, install the default SessionStart hook for startup context injection, and install the default Stop hook for automatic `change` records.
```

In Step 8 (Output summary), add to the "Created or updated" list:

```markdown
- `.sybermem/hooks/session_start_context.py` when startup context injection is installed
- managed SessionStart hook command updated to the launcher form when needed
```

- [ ] **Step 2: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/SKILL.md
git commit -m "feat: update init-project skill to install SessionStart hook"
```

---

### Task 7: Enhance Stop hook — commit-gap detection + auto-trail dedup + unified nudge state

This is the largest existing-file modification. Carefully patch `record_change_on_stop.py`.

**Files:**
- Modify: `.sybermem/hooks/record_change_on_stop.py`

- [ ] **Step 1: Change NUDGE_STATE_PATH to use unified `.nudge-state.json`**

Find:
```python
NUDGE_STATE_PATH = SYBERMEM_DIR / ".auto-nudge-state.json"
```

Replace with:
```python
NUDGE_STATE_PATH = SYBERMEM_DIR / ".nudge-state.json"
LEGACY_NUDGE_STATE_PATH = SYBERMEM_DIR / ".auto-nudge-state.json"
```

- [ ] **Step 2: Add nudge state migration logic**

Find the `load_nudge_state()` function:

```python
def load_nudge_state() -> dict:
    if not NUDGE_STATE_PATH.exists():
        return {}
    try:
        return json.loads(NUDGE_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
```

Replace with:

```python
def load_nudge_state() -> dict:
    """Load unified nudge state, migrating from legacy files if needed."""
    if NUDGE_STATE_PATH.exists():
        try:
            return json.loads(NUDGE_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Migrate from legacy .auto-nudge-state.json if it exists
    if LEGACY_NUDGE_STATE_PATH.exists():
        try:
            data = json.loads(LEGACY_NUDGE_STATE_PATH.read_text(encoding="utf-8"))
            # Save to new path; leave legacy file on disk (cleaned by /sybermem-update)
            save_nudge_state(data)
            return data
        except Exception:
            pass
    return {}
```

- [ ] **Step 3: Add commit-gap detection function**

After the `detect_high_level_areas` function, add:

```python
COMMIT_GAP_THRESHOLD = 10


def count_commits_since_last_record() -> int:
    """Count commits since the most recent record file date across all record directories."""
    latest_date: str = ""
    for subdir in ("changes", "decisions", "requirements", "bugs"):
        record_dir = SYBERMEM_DIR / subdir
        if not record_dir.is_dir():
            continue
        for path in record_dir.glob("*.md"):
            match = re.match(r"(\d{4}-\d{2}-\d{2})-", path.name)
            if match and match.group(1) > latest_date:
                latest_date = match.group(1)
    if not latest_date:
        return 0
    count_str = run_git("rev-list", "--count", f"--since={latest_date}", "HEAD")
    try:
        return int(count_str)
    except (ValueError, TypeError):
        return 0
```

- [ ] **Step 4: Add auto-trail dedup function**

After `count_commits_since_last_record`, add:

```python
AUTO_TRAIL_DEDUP_WINDOW = 3
AUTO_TRAIL_OVERLAP_THRESHOLD = 0.8


def overlaps_recent_auto_trails(files: list[str]) -> bool:
    """Check if the current file set overlaps >80% with any of the last 3 auto trails."""
    if not CHANGES_DIR.is_dir():
        return False
    trails = sorted(CHANGES_DIR.glob("*.md"), key=lambda p: p.name, reverse=True)
    current_set = set(files)
    checked = 0
    for trail_path in trails:
        if checked >= AUTO_TRAIL_DEDUP_WINDOW:
            break
        try:
            content = trail_path.read_text(encoding="utf-8")
        except Exception:
            continue
        # Only check auto-generated trails (they have the "Auto-generated" marker)
        if "Auto-generated from workspace changes" not in content:
            continue
        checked += 1
        # Extract related_files from frontmatter
        fm_match = re.search(r"^related_files:\s*(.+)$", content, re.MULTILINE)
        if not fm_match:
            continue
        trail_files = {f.strip() for f in fm_match.group(1).split(",")}
        if not trail_files or not current_set:
            continue
        overlap = len(current_set & trail_files) / max(len(current_set), len(trail_files))
        if overlap >= AUTO_TRAIL_OVERLAP_THRESHOLD:
            return True
    return False
```

- [ ] **Step 5: Integrate commit-gap into classify_followup**

Find the `classify_followup` function. After the existing digest check block and before the record nudge block, add commit-gap as an additional record nudge signal.

Find:
```python
    cross_area = len(areas) >= 2
    strong_signal = bool(high_signal_hits)
    large_change = file_count >= RECORD_FILE_THRESHOLD
    if (strong_signal or cross_area or large_change) and not (last_type == "record" and last_theme == theme_key):
        return "record", theme_key, "SyberMem note: this change looks important enough for a manual /sybermem-record so the reason and impact are preserved more clearly."
```

Replace with:
```python
    cross_area = len(areas) >= 2
    strong_signal = bool(high_signal_hits)
    large_change = file_count >= RECORD_FILE_THRESHOLD
    commit_gap = count_commits_since_last_record() >= COMMIT_GAP_THRESHOLD
    if (strong_signal or cross_area or large_change or commit_gap) and not (last_type == "record" and last_theme == theme_key):
        gap_note = f" ({count_commits_since_last_record()} commits since last record)" if commit_gap else ""
        return "record", theme_key, f"SyberMem note: this change looks important enough for a manual /sybermem-record so the reason and impact are preserved more clearly.{gap_note}"
```

- [ ] **Step 6: Integrate auto-trail dedup into main()**

Find in `main()`, the section right after the fingerprint check:

```python
    fingerprint = json.dumps(files, ensure_ascii=False)
    state = load_state()
    if state.get("last_fingerprint") == fingerprint:
        return 0
```

After that block, add:

```python
    # Auto-trail dedup: skip if >80% overlap with recent auto trails
    if overlaps_recent_auto_trails(files):
        save_state({"last_fingerprint": fingerprint, "last_record": state.get("last_record", "")})
        if nudge_message:
            print(nudge_message)
        return 0
```

- [ ] **Step 7: Add platform field to saved nudge state**

In the two `save_nudge_state` calls in `main()`, add `"platform": "claude-code"` to the dict. Find the first one (soft-skip-only branch):

```python
        save_nudge_state({
            **nudge_state,
            "last_theme": theme_key,
            "last_nudge_type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
            "digest_nudged_at_window_len": digest_nudged_at,
        })
```

Replace with:
```python
        save_nudge_state({
            **nudge_state,
            "last_nudge": {
                "platform": "claude-code",
                "type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
                "theme": theme_key,
                "date": date.today().isoformat(),
            },
            "last_theme": theme_key,
            "last_nudge_type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
            "digest_nudged_at_window_len": digest_nudged_at,
        })
```

Find the second `save_nudge_state` call (normal record branch):
```python
    save_nudge_state({
        **nudge_state,
        "last_theme": theme_key,
        "last_nudge_type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
        "last_record": record_path.name,
        "digest_nudged_at_window_len": digest_nudged_at,
    })
```

Replace with:
```python
    save_nudge_state({
        **nudge_state,
        "last_nudge": {
            "platform": "claude-code",
            "type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
            "theme": theme_key,
            "date": date.today().isoformat(),
        },
        "last_theme": theme_key,
        "last_nudge_type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
        "last_record": record_path.name,
        "digest_nudged_at_window_len": digest_nudged_at,
    })
```

- [ ] **Step 8: Verify the Stop hook still works**

Run: `python .sybermem/hooks/record_change_on_stop.py`

Expected: exits 0, no errors. If there are uncommitted changes in the workspace it may write an auto trail record or emit a nudge — both are correct.

- [ ] **Step 9: Commit**

```bash
git add .sybermem/hooks/record_change_on_stop.py
git commit -m "feat: add commit-gap detection, auto-trail dedup, and unified nudge state to Stop hook"
```

---

### Task 8: Update init-project template Stop hook to match

The template version in `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py` must stay in sync with the project copy.

**Files:**
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py`

- [ ] **Step 1: Copy the updated record_change_on_stop.py**

Copy the full contents of `.sybermem/hooks/record_change_on_stop.py` (as modified in Task 7) to `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py`, replacing the entire file.

- [ ] **Step 2: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/record_change_on_stop.py
git commit -m "feat: sync init-project template Stop hook with lifecycle layer enhancements"
```

---

### Task 9: Update OpenCode plugin — unified nudge state + stale detection + compaction limit

**Files:**
- Modify: `packages/opencode-plugin/sybermem.ts`

- [ ] **Step 1: Update nudge state path to unified `.nudge-state.json`**

Find:
```typescript
function loadNudgeState(root: string): NudgeState {
  const p = join(root, ".sybermem", ".opencode-nudge-state.json")
  if (!existsSync(p)) return {}
  try {
    return JSON.parse(readFileSync(p, "utf-8"))
  } catch {
    return {}
  }
}

function saveNudgeState(root: string, state: NudgeState) {
  const p = join(root, ".sybermem", ".opencode-nudge-state.json")
  writeFileSync(p, JSON.stringify(state, null, 2) + "\n", "utf-8")
}
```

Replace with:
```typescript
const NUDGE_STATE_FILE = ".nudge-state.json"
const LEGACY_NUDGE_STATE_FILE = ".opencode-nudge-state.json"

function loadNudgeState(root: string): NudgeState {
  const p = join(root, ".sybermem", NUDGE_STATE_FILE)
  if (existsSync(p)) {
    try {
      return JSON.parse(readFileSync(p, "utf-8"))
    } catch {
      // fall through to legacy
    }
  }
  // Migrate from legacy file if it exists
  const legacy = join(root, ".sybermem", LEGACY_NUDGE_STATE_FILE)
  if (existsSync(legacy)) {
    try {
      const data = JSON.parse(readFileSync(legacy, "utf-8"))
      saveNudgeState(root, data)
      return data
    } catch {
      // fall through
    }
  }
  return {}
}

function saveNudgeState(root: string, state: NudgeState) {
  const p = join(root, ".sybermem", NUDGE_STATE_FILE)
  writeFileSync(p, JSON.stringify(state, null, 2) + "\n", "utf-8")
}
```

- [ ] **Step 2: Add phase-index stale detection function**

After the `getActivePhase` function, add:

```typescript
interface StaleSignal {
  stale: boolean
  commitsAhead: number
  boundary?: string
  head?: string
}

async function detectStaleSignal(
  $: any,
  root: string
): Promise<StaleSignal> {
  const phasePath = join(root, ".sybermem", "analysis", "phase-index.md")
  if (!existsSync(phasePath)) return { stale: false, commitsAhead: 0 }
  const content = readFileSync(phasePath, "utf-8")
  const boundaryMatch = content.match(/^- last_git_boundary:\s*(\S+)/m)
  if (!boundaryMatch) return { stale: false, commitsAhead: 0 }
  const boundary = boundaryMatch[1]

  try {
    const head = (await $`git rev-parse HEAD`.cwd(root).text()).trim()
    if (head === boundary) return { stale: false, commitsAhead: 0 }
    const countStr = (
      await $`git rev-list --count ${boundary}..HEAD`.cwd(root).text()
    ).trim()
    const count = parseInt(countStr, 10) || 0
    return {
      stale: count >= 3,
      commitsAhead: count,
      boundary,
      head: head.substring(0, 7),
    }
  } catch {
    return { stale: false, commitsAhead: 0 }
  }
}
```

- [ ] **Step 3: Enhance session.created to include stale signal**

Find:
```typescript
    event: async ({ event }) => {
      if (event.type === "session.created" && root) {
        const parsed = parseIndex(root)
        if (parsed && parsed.conclusions.length > 0) {
          return {
            "tui.toast.show": {
              message: `SyberMem: loaded ${parsed.conclusions.length} key conclusions`,
              level: "info",
            },
          }
        }
      }
```

Replace with:
```typescript
    event: async ({ event }) => {
      if (event.type === "session.created" && root) {
        const parsed = parseIndex(root)
        if (parsed && parsed.conclusions.length > 0) {
          const stale = await detectStaleSignal($, root)
          const staleNote = stale.stale
            ? ` (phase-index ${stale.commitsAhead} commits behind)`
            : ""
          return {
            "tui.toast.show": {
              message: `SyberMem: loaded ${parsed.conclusions.length} key conclusions${staleNote}`,
              level: "info",
            },
          }
        }
      }
```

- [ ] **Step 4: Add platform field to nudge state writes**

In the `session.idle` handler, find:
```typescript
          saveNudgeState(root, { lastFingerprint: fingerprint, lastNudgeCommitCount: commitsSince })
```

Replace with:
```typescript
          saveNudgeState(root, {
            lastFingerprint: fingerprint,
            lastNudgeCommitCount: commitsSince,
            last_nudge: {
              platform: "opencode",
              type: "record",
              theme: "idle-detect",
              date: new Date().toISOString().split("T")[0],
            },
          })
```

- [ ] **Step 5: Add stale signal to compaction context and enforce length limit**

Find the compaction handler:
```typescript
    "experimental.session.compacting": async (_input, output) => {
      if (!root) return

      const parsed = parseIndex(root)
      if (!parsed || parsed.conclusions.length === 0) return

      const activePhase = getActivePhase(root)

      let context = "## SyberMem Project Memory\n\n"
      context += "### Key Conclusions\n"
      for (const c of parsed.conclusions) {
        context += c + "\n"
      }

      if (activePhase) {
        context += `\n### Active Phase: ${activePhase}\n`
      }

      if (Object.keys(parsed.topicIndex).length > 0) {
        context += "\n### Topic Index\n"
        for (const [topic, records] of Object.entries(parsed.topicIndex)) {
          context += `- ${topic}: ${records.join(", ")}\n`
        }
      }

      context += "\n### SyberMem Commands\n"
      context +=
        "- /sybermem-record — create a record after meaningful work\n"
      context +=
        "- /sybermem-summary — view current phase status\n"
      context +=
        "- /sybermem-digest — create durable phase digest\n"

      output.context.push(context)
    },
```

Replace with:
```typescript
    "experimental.session.compacting": async (_input, output) => {
      if (!root) return

      const parsed = parseIndex(root)
      if (!parsed || parsed.conclusions.length === 0) return

      const activePhase = getActivePhase(root)
      const stale = await detectStaleSignal($, root)

      let context = "## SyberMem Project Memory\n\n"
      context += "### Key Conclusions\n"
      for (const c of parsed.conclusions) {
        context += c + "\n"
      }

      if (activePhase) {
        context += `\n### Active Phase: ${activePhase}\n`
      }

      if (stale.stale) {
        context += `\n### Stale Signal\nPhase-index last git boundary: ${stale.boundary}, current HEAD: ${stale.head} (${stale.commitsAhead} commits ahead).\n`
      }

      if (Object.keys(parsed.topicIndex).length > 0) {
        context += "\n### Topic Index\n"
        for (const [topic, records] of Object.entries(parsed.topicIndex)) {
          context += `- ${topic}: ${records.join(", ")}\n`
        }
      }

      context += "\n### SyberMem Commands\n"
      context +=
        "- /sybermem-record — create a record after meaningful work\n"
      context +=
        "- /sybermem-summary — view current phase status\n"
      context +=
        "- /sybermem-digest — create durable phase digest\n"

      // Enforce 3000-char limit to avoid compaction noise
      if (context.length > 3000) {
        context = context.substring(0, 2997) + "..."
      }

      output.context.push(context)
    },
```

- [ ] **Step 6: Update NudgeState interface**

Find:
```typescript
interface NudgeState {
  lastFingerprint?: string
  lastNudgeCommitCount?: number
}
```

Replace with:
```typescript
interface NudgeState {
  lastFingerprint?: string
  lastNudgeCommitCount?: number
  last_nudge?: {
    platform: string
    type: string
    theme: string
    date: string
  }
  // Cross-platform fields (shared with Python Stop hook)
  theme_recent_stops?: Record<string, string[]>
  digest_nudged_at_window_len?: Record<string, number>
  last_theme?: string
  last_nudge_type?: string
}
```

- [ ] **Step 7: Commit**

```bash
git add packages/opencode-plugin/sybermem.ts
git commit -m "feat: unified nudge state, stale detection, and compaction limit in OpenCode plugin"
```

---

### Task 10: Update install scripts — distribute session start launcher

**Files:**
- Modify: `scripts/install.sh`
- Modify: `scripts/install.ps1`
- Modify: `scripts/install-remote.sh`
- Modify: `scripts/install-remote.ps1`
- Modify: `scripts/update.sh`
- Modify: `scripts/update.ps1`

- [ ] **Step 1: Update install.sh**

Add a variable at the top, after the existing `LAUNCHER_SOURCE` line:

Find:
```bash
LAUNCHER_SOURCE="$ADR_PATH/scripts/global-stop-hook-launcher.py"
```

After it, add:
```bash
SESSION_LAUNCHER_SOURCE="$ADR_PATH/scripts/global-session-start-launcher.py"
SESSION_LAUNCHER_PATH="$LAUNCHER_DIR/launch_session_start_context.py"
```

After the block that installs the stop hook launcher (after `echo "  [Claude Code] 已安装 stop hook launcher: $LAUNCHER_PATH"`), add:

```bash
    cp "$SESSION_LAUNCHER_SOURCE" "$SESSION_LAUNCHER_PATH"
    chmod +x "$SESSION_LAUNCHER_PATH"
    echo "  [Claude Code] 已安装 session start launcher: $SESSION_LAUNCHER_PATH"
```

- [ ] **Step 2: Update install.ps1**

Add variables at the top, after the existing `$LauncherSource` line:

Find:
```powershell
$LauncherSource = Join-Path $AdrPath "scripts\global-stop-hook-launcher.py"
```

After it, add:
```powershell
$SessionLauncherSource = Join-Path $AdrPath "scripts\global-session-start-launcher.py"
$SessionLauncherPath = Join-Path $LauncherDir "launch_session_start_context.py"
```

After the block `Copy-Item -Path $LauncherSource -Destination $LauncherPath -Force`, add:

```powershell
    Copy-Item -Path $SessionLauncherSource -Destination $SessionLauncherPath -Force
    Write-Host "  [Claude Code] 已安装 session start launcher: $SessionLauncherPath"
```

- [ ] **Step 3: Update install-remote.sh**

After the line:
```bash
LAUNCHER_PATH="$LAUNCHER_DIR/launch_record_change_on_stop.py"
```

Add:
```bash
SESSION_LAUNCHER_PATH="$LAUNCHER_DIR/launch_session_start_context.py"
```

After the line:
```bash
LAUNCHER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/global-stop-hook-launcher.py"
```

Add:
```bash
SESSION_LAUNCHER_SOURCE="$TMPDIR/$ARCHIVE_PREFIX/scripts/global-session-start-launcher.py"
```

After the existing stop hook launcher install block, add:

```bash
    if [ -f "$SESSION_LAUNCHER_SOURCE" ]; then
        cp "$SESSION_LAUNCHER_SOURCE" "$SESSION_LAUNCHER_PATH"
        chmod +x "$SESSION_LAUNCHER_PATH"
        echo "  [Claude Code] installed session start launcher: $SESSION_LAUNCHER_PATH"
    fi
```

- [ ] **Step 4: Update install-remote.ps1**

After the line:
```powershell
$LauncherPath = Join-Path $LauncherDir "launch_record_change_on_stop.py"
```

Add:
```powershell
$SessionLauncherPath = Join-Path $LauncherDir "launch_session_start_context.py"
```

After the line:
```powershell
$LauncherSource = Join-Path $TmpDir "$ArchivePrefix\scripts\global-stop-hook-launcher.py"
```

Add:
```powershell
$SessionLauncherSource = Join-Path $TmpDir "$ArchivePrefix\scripts\global-session-start-launcher.py"
```

After the stop hook launcher Copy-Item block, add:

```powershell
        if (Test-Path $SessionLauncherSource) {
            Copy-Item -Path $SessionLauncherSource -Destination $SessionLauncherPath -Force
            Write-Host "  [Claude Code] installed session start launcher: $SessionLauncherPath"
        }
```

- [ ] **Step 5: Update update.sh**

After the line:
```bash
LAUNCHER_SOURCE="$ADR_PATH/scripts/global-stop-hook-launcher.py"
```

Add:
```bash
SESSION_LAUNCHER_SOURCE="$ADR_PATH/scripts/global-session-start-launcher.py"
SESSION_LAUNCHER_PATH="$LAUNCHER_DIR/launch_session_start_context.py"
```

After the stop hook launcher cp block:
```bash
cp "$LAUNCHER_SOURCE" "$LAUNCHER_PATH"
chmod +x "$LAUNCHER_PATH"
echo "  [Global] 已安装 stop hook launcher: $LAUNCHER_PATH"
```

Add:
```bash
cp "$SESSION_LAUNCHER_SOURCE" "$SESSION_LAUNCHER_PATH"
chmod +x "$SESSION_LAUNCHER_PATH"
echo "  [Global] 已安装 session start launcher: $SESSION_LAUNCHER_PATH"
```

- [ ] **Step 6: Update update.ps1**

After the line:
```powershell
$LauncherSource = Join-Path $AdrPath "scripts\global-stop-hook-launcher.py"
```

Add:
```powershell
$SessionLauncherSource = Join-Path $AdrPath "scripts\global-session-start-launcher.py"
$SessionLauncherPath = Join-Path $LauncherDir "launch_session_start_context.py"
```

After the stop hook launcher Copy-Item block, add:

```powershell
Copy-Item -Path $SessionLauncherSource -Destination $SessionLauncherPath -Force
Write-Host "  [Global] 已安装 session start launcher: $SessionLauncherPath"
```

- [ ] **Step 7: Commit**

```bash
git add scripts/install.sh scripts/install.ps1 scripts/install-remote.sh scripts/install-remote.ps1 scripts/update.sh scripts/update.ps1
git commit -m "feat: distribute session start launcher in all install and update scripts"
```

---

### Task 11: Install the session start launcher locally

Run the actual install so this dev machine has the launcher in place.

**Files:**
- No repo file changes (installs to `~/.claude/sybermem/`)

- [ ] **Step 1: Copy the launcher to the global location**

Run:
```powershell
Copy-Item -Path "scripts\global-session-start-launcher.py" -Destination "$env:USERPROFILE\.claude\sybermem\launch_session_start_context.py" -Force
```

Expected: file exists at `C:\Users\69046\.claude\sybermem\launch_session_start_context.py`

- [ ] **Step 2: Verify end-to-end SessionStart hook**

Run:
```powershell
python "$env:USERPROFILE\.claude\sybermem\launch_session_start_context.py"
```

Expected: JSON output with `hookSpecificOutput.additionalContext` containing conclusions, topics, and phase info.

- [ ] **Step 3: No commit needed** (local install, not a repo change)

---

### Task 12: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add lifecycle layer section**

After the existing "## 工作流程" section, add a new section:

```markdown
## 生命周期层（Lifecycle Layer）

SyberMem 嵌入 Claude Code / OpenCode 的会话生命周期，让项目记忆无感地跟随工作流：

| 生命周期 | Claude Code | OpenCode |
|---|---|---|
| 会话开始 | `SessionStart` hook 自动注入 Key Conclusions、Topic Index、phase 状态 | `session.created` toast 通知 |
| 工作中 | 模型根据 Topic Index 关联历史记录 | 同上 |
| 压缩前 | `SessionStart` compact 后重新注入 | `session.compacting` 注入 Key Conclusions + phase |
| 会话结束 | `Stop` hook 写轻量 change trail + nudge | `session.idle` 检测变更 + toast |

两个平台共享 `.sybermem/.nudge-state.json`，交替使用时不重复提示。
```

- [ ] **Step 2: Update the "在你的项目中会创建什么" section**

In the directory tree, add `session_start_context.py` next to the existing hook:

Find:
```
├── hooks/
│   └── record_change_on_stop.py   # 默认自动 change hook helper
```

Replace with:
```
├── hooks/
│   ├── record_change_on_stop.py   # 默认自动 change hook helper
│   └── session_start_context.py   # SessionStart 上下文注入脚本
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add lifecycle layer section and session_start_context.py to README"
```

---

### Task 13: Final end-to-end verification

- [ ] **Step 1: Verify SessionStart hook fires**

Run:
```powershell
python "$env:USERPROFILE\.claude\sybermem\launch_session_start_context.py"
```

Expected: Valid JSON output with key conclusions, topic index, phase info, and stale signal.

- [ ] **Step 2: Verify Stop hook still works**

Run:
```powershell
python "$env:USERPROFILE\.claude\sybermem\launch_record_change_on_stop.py"
```

Expected: Exits 0. If workspace has changes, may write auto trail or emit nudge.

- [ ] **Step 3: Verify settings.json is valid**

Run:
```powershell
python -c "import json; json.load(open('.claude/settings.json')); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Verify unified nudge state path**

Check that `.sybermem/.nudge-state.json` would be the path used by both platforms:

Run:
```powershell
python -c "from pathlib import Path; print(Path('.sybermem/.nudge-state.json').resolve())"
```

Expected: Absolute path to the unified nudge state file.

- [ ] **Step 5: Verify OpenCode plugin has no TypeScript syntax errors**

Run:
```powershell
python -c "
content = open('packages/opencode-plugin/sybermem.ts').read()
# Basic checks: balanced braces, no stray Python
assert content.count('{') == content.count('}'), 'Unbalanced braces'
assert 'def ' not in content, 'Python def leaked into TS'
print('OK')
"
```

Expected: `OK`

- [ ] **Step 6: No commit needed** (verification only)
