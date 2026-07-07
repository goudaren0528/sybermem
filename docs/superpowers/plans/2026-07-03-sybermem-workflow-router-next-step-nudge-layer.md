# SyberMem Workflow Router / Next-Step Nudge Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Help users decide the *one* best next SyberMem action after a round of work by adding a lightweight router/nudge layer that chooses between `/sybermem-record`, `/sybermem-digest`, and `/sybermem-team-publish`.

**Architecture:** Add a small routing helper that inspects current project state (recent record quality, digest readiness, Team publish staleness) and returns the single highest-priority next step using the fixed priority order `record > digest > team-publish`. Surface it through `/using-sybermem`, the reminder-first stop hook, and lightweight post-publish/post-summary suggestions.

**Tech Stack:** Python 3.10+, existing SyberMem hooks, project.yaml Team association, Team repo overview/summary files

---

### Task 1: Add a reusable next-step router helper

**Files:**
- Create: `packages/core/sybermem_core/next_step_router.py`

- [ ] **Step 1: Create `next_step_router.py`**

```python
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json

from .project import read_team_from_project_yaml
from .status import project_status, publication_readiness
from .publish import latest_phase_digest, latest_theme_digest


def recommend_next_step(root: Path) -> dict[str, str]:
    status = project_status(root)
    readiness = publication_readiness(root)
    team = read_team_from_project_yaml(root)

    phase_digest = latest_phase_digest(root)
    theme_digest = latest_theme_digest(root)

    # 1) record > digest > team-publish
    if readiness["record_count"] >= 1 and not phase_digest and not theme_digest:
        return {
            "action": "/sybermem-record",
            "reason": "This round has meaningful project changes, but no durable manual record exists yet."
        }

    if readiness["enough_material"] and not phase_digest:
        return {
            "action": "/sybermem-digest",
            "reason": "The current project has enough material for a phase digest, but no digest exists yet."
        }

    if team.get("team_path"):
        team_root = Path(team["team_path"])
        meta_path = team_root / "projects" / status["slug"] / "meta.json"
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            published_at = meta.get("published_at", "")
            if published_at:
                try:
                    published_dt = datetime.fromisoformat(published_at)
                    if datetime.fromisoformat(status["as_of"]) - published_dt > timedelta(days=2):
                        return {
                            "action": "/sybermem-team-publish",
                            "reason": "This project has a Team association but has not been published to Team memory recently."
                        }
                except Exception:
                    pass
        else:
            return {
                "action": "/sybermem-team-publish",
                "reason": "This project is linked to Team memory but has not been published there yet."
            }

    return {
        "action": "/sybermem-summary",
        "reason": "Project memory is in a healthy state; review the current summary for context."
    }
```

- [ ] **Step 2: Verify the helper imports cleanly**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "from pathlib import Path; from sybermem_core.next_step_router import recommend_next_step; print(recommend_next_step(Path('.')))"
```

Expected: prints a dict with `action` and `reason`.

- [ ] **Step 3: Commit**

```bash
git add packages/core/sybermem_core/next_step_router.py
git commit -m "feat: add SyberMem next-step router helper"
```

---

### Task 2: Surface the router in `/using-sybermem` and the stop hook

**Files:**
- Modify: `packages/claude-skills/using-sybermem/SKILL.md`
- Modify: `skills/using-sybermem/SKILL.md`
- Modify: `.sybermem/hooks/record_change_on_stop.py`

- [ ] **Step 1: Update `using-sybermem` to explicitly use the router logic**

In both `packages/claude-skills/using-sybermem/SKILL.md` and `skills/using-sybermem/SKILL.md`, update the “Recommend the next command” section so it references the Team-aware priority order:

```text
record > digest > team-publish
```

And add examples such as:
- if important work exists without a durable record → recommend `/sybermem-record`
- if material has accumulated but no digest exists → recommend `/sybermem-digest`
- if Team association exists and Team memory is stale → recommend `/sybermem-team-publish`

- [ ] **Step 2: Add a lightweight router call to the stop hook**

In `.sybermem/hooks/record_change_on_stop.py`, import and use the new helper *only* to improve reminder wording. Near the existing reminder output, add:

```python
try:
    from sybermem_core.next_step_router import recommend_next_step
    router_hint = recommend_next_step(ROOT)
except Exception:
    router_hint = None
```

Then where the stop hook emits a generic reminder, prefer:

```python
if router_hint:
    print(f"Recommended next step: {router_hint['action']} — {router_hint['reason']}")
elif nudge_message:
    print(nudge_message)
```

Do not let router failures break the hook.

- [ ] **Step 3: Verify stop-hook reminder output**

Using a controlled change set, run the stop hook manually and confirm the output now names one concrete next step instead of a generic nudge when the router succeeds.

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/using-sybermem/SKILL.md skills/using-sybermem/SKILL.md .sybermem/hooks/record_change_on_stop.py
git commit -m "feat: route SyberMem reminders through next-step priority logic"
```

---

### Task 3: Add Team-aware post-publish and post-summary suggestions

**Files:**
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Add a post-publish suggestion**

In `cmd_publish_status()`, after the existing output, add:

```python
        print("- suggested follow-up: /sybermem-team-summary")
```

- [ ] **Step 2: Add a post-summary suggestion for thin projects**

In `cmd_team_summary()`, after generating the result, if `payload["deep_review_candidates"]` is non-empty, print a soft follow-up suggestion in text mode such as:

```python
        if payload.get("deep_review_candidates"):
            print("- suggested deeper review: inspect the projects listed under Worth Deeper Review")
```

- [ ] **Step 3: Verify both suggestions appear in the real CLI**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --format json
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main team summary --team-path D:/team-memory
```

Expected:
- text-mode publish mentions `/sybermem-team-summary`
- text-mode team summary mentions deeper review when candidates exist

- [ ] **Step 4: Commit**

```bash
git add packages/cli/sybermem_cli/main.py
git commit -m "feat: add next-step suggestions after Team publish and summary"
```

---

### Task 4: End-to-end dogfood and README note

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Dogfood the end-to-end routing logic**

Verify a realistic sequence:
- a project with new work but no fresh digest should recommend `/sybermem-digest`
- a Team-linked project stale for >2 days should recommend `/sybermem-team-publish`
- otherwise the fallback should be `/sybermem-summary`

Use real project state plus one controlled temporary scenario if necessary.

- [ ] **Step 2: Add a short README note**

Chinese:
```markdown
- **Workflow Router**：SyberMem 现在会优先按 `record > digest > team-publish` 的顺序推荐下一步动作，避免在一轮工作结束后犹豫先做哪个
```

English:
```markdown
- **Workflow Router**: SyberMem now recommends the next step using the priority order `record > digest > team-publish`, reducing the “what should I do next?” friction after a round of work
```

- [ ] **Step 3: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: note workflow router next-step guidance"
```
