# SyberMem Natural-Language Record Intent Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the reminder-first loop by turning explicit natural-language record intent (e.g. “这轮结束提醒我记录”) into a real `.record-intent.json` state that the stop hook can consume later.

**Architecture:** Add a lightweight `UserPromptSubmit` hook that scans user prompts for clear record-intent phrases and writes `.sybermem/.record-intent.json`. Keep the stop hook as the consumer and `/sybermem-record` as the closer that clears the state once a record is actually written. This keeps language understanding in the conversation layer and reminder execution in the stop-hook layer.

**Tech Stack:** Python 3.10+, Claude Code `UserPromptSubmit` + `Stop` hooks, project-local `.sybermem/` state files

---

### Task 1: Add a prompt-side record-intent detector hook

**Files:**
- Create: `.sybermem/hooks/detect_record_intent.py`
- Create: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/detect_record_intent.py`

- [ ] **Step 1: Create the project hook script**

Create `.sybermem/hooks/detect_record_intent.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess


def resolve_sybermem_root() -> Path:
    current = Path.cwd().resolve()
    git_root = None
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
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
    return Path.cwd()


INTENT_PATTERNS = [
    re.compile(r"这轮.*提醒我.*记录"),
    re.compile(r"这次.*要记.*record", re.IGNORECASE),
    re.compile(r"做完.*提醒我.*/sybermem-record"),
    re.compile(r"这轮工作.*记录到.*sybermem", re.IGNORECASE),
]


def now_iso() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat(timespec="seconds")


def main() -> int:
    root = resolve_sybermem_root()
    intent_path = root / ".sybermem" / ".record-intent.json"

    payload = json.load(__import__("sys").stdin)
    user_text = payload.get("prompt", "") or payload.get("userPrompt", "") or ""

    matched = next((p.pattern for p in INTENT_PATTERNS if p.search(user_text)), None)
    if not matched:
        return 0

    intent_path.write_text(json.dumps({
        "record_intent": True,
        "source": "user-declared",
        "created_at": now_iso(),
        "phrase": user_text,
        "matched_pattern": matched,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Mirror it into the init-project template**

Copy the same file to:

```text
packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/detect_record_intent.py
```

- [ ] **Step 3: Verify the detector works standalone**

Run:
```bash
echo '{"prompt":"这轮结束提醒我记录"}' | python .sybermem/hooks/detect_record_intent.py
```

Expected:
- `.sybermem/.record-intent.json` is created
- it contains `record_intent: true`
- it preserves the original phrase

- [ ] **Step 4: Commit**

```bash
git add .sybermem/hooks/detect_record_intent.py packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/detect_record_intent.py
git commit -m "feat: add natural-language record intent detector hook"
```

---

### Task 2: Wire the detector into project settings and health checks

**Files:**
- Modify: `.claude/settings.json`
- Modify: `.sybermem/hooks/check_project_health.py`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`

- [ ] **Step 1: Add a `UserPromptSubmit` hook entry to project settings**

In `.claude/settings.json`, extend `hooks` with:

```json
"UserPromptSubmit": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python .sybermem/hooks/detect_record_intent.py",
        "timeout": 10,
        "statusMessage": "SyberMem checking whether this round should be recorded..."
      }
    ]
  }
]
```

Merge it into the existing hooks object without disturbing SessionStart/Stop.

- [ ] **Step 2: Update the init-project template settings**

Add the same `UserPromptSubmit` hook to:

```text
packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json
```

- [ ] **Step 3: Extend the health check**

In `.sybermem/hooks/check_project_health.py`, update `check_settings_json()` so it also checks for the UserPromptSubmit hook by looking for `detect_record_intent.py` in the settings content.

Add a `has_record_intent_hook` field and include it in the freshness calculation.

Also add:

```python
files[".sybermem/hooks/detect_record_intent.py"] = check_file_exists(root / ".sybermem" / "hooks" / "detect_record_intent.py")
```

and ensure `generate_actions()` creates it when missing.

Mirror the updated health check into:

```text
packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py
```

- [ ] **Step 4: Verify the hook is visible in health status**

Run:
```bash
python .sybermem/hooks/check_project_health.py
```

Expected:
- `.claude/settings.json.has_record_intent_hook = true`
- `.sybermem/hooks/detect_record_intent.py = fresh`

- [ ] **Step 5: Commit**

```bash
git add .claude/settings.json .sybermem/hooks/check_project_health.py packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py
git commit -m "feat: wire natural-language record intent detection into project hooks"
```

---

### Task 3: Clear record intent after `/sybermem-record`

**Files:**
- Modify: `packages/claude-skills/sybermem-record/SKILL.md`
- Modify: `skills/sybermem-record/SKILL.md`

- [ ] **Step 1: Add a cleanup step near the end of the record skill**

In `packages/claude-skills/sybermem-record/SKILL.md`, after the record file / INDEX / Key Conclusion work is complete and before final output, add a step that says:

- if `.sybermem/.record-intent.json` exists, delete it
- explain that a successful manual record completes the earlier reminder loop

Keep this as explicit skill behavior rather than hidden model magic.

- [ ] **Step 2: Mirror the updated record skill**

Copy the same change into:

```text
skills/sybermem-record/SKILL.md
```

- [ ] **Step 3: Verify the skill docs match**

Run:
```bash
python -c "from pathlib import Path; a = Path('packages/claude-skills/sybermem-record/SKILL.md').read_text(encoding='utf-8'); b = Path('skills/sybermem-record/SKILL.md').read_text(encoding='utf-8'); assert a == b; print('record skill cleanup OK')"
```

Expected: `record skill cleanup OK`

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-record/SKILL.md skills/sybermem-record/SKILL.md
git commit -m "feat: clear record intent after successful manual record"
```

---

### Task 4: End-to-end dogfood and docs note

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: End-to-end dogfood the natural-language flow**

Simulate the path:
1. Feed an explicit phrase into the new detector hook
2. Confirm `.record-intent.json` appears
3. Run the stop hook once in `remind` mode with changed files present
4. Confirm the reminder references the earlier intent
5. Confirm the intent file is cleared

- [ ] **Step 2: Add a short note to README docs**

Chinese:
```markdown
- **记录提醒闭环**：如果你在对话里明确说“这轮结束提醒我记录”，SyberMem 会记住这轮记录意图，并在合适时机提醒你运行 `/sybermem-record`
```

English:
```markdown
- **Record-intent loop**: if you explicitly say something like “remind me to record this round when it’s done”, SyberMem will remember that intent and remind you to run `/sybermem-record` at the right time
```

- [ ] **Step 3: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: note natural-language record-intent reminder loop"
```
