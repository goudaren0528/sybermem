# SyberMem Team Project Summary Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Team repo single-project `current-status.md` from a thin status snapshot into a readable Team Project Summary that answers what the project is doing, what changed recently, what needs attention, and what comes next.

**Architecture:** Keep the Team repo file path unchanged (`projects/<slug>/current-status.md`) but replace its rendering logic in `publish.py`. The new content will prefer digest-derived/high-signal project information where available, fall back to recent records when needed, and demote raw status fields into a `Supporting Signals` section.

**Tech Stack:** Python 3.10+, Markdown, Team repo publication pipeline

---

### Task 1: Replace the Team project summary renderer in `publish.py`

**Files:**
- Modify: `packages/core/sybermem_core/publish.py`

- [ ] **Step 1: Replace `render_current_status()` with a Team Project Summary version**

In `packages/core/sybermem_core/publish.py`, replace the current `render_current_status()` function with:

```python
def render_current_status(status: dict, source_commit: str) -> str:
    phase = status["phase"]
    phase_label = phase["id"] or "(no phase)"
    phase_name = phase.get("name", "")
    digest_tail = []
    if phase["id"]:
        digest_tail.append(f"Current phase remains {phase['id']}")
    if phase_name:
        digest_tail.append(phase_name)

    progress = []
    if status["recent_records"]:
        progress.append(f"Recent records published: {', '.join(status['recent_records'][:3])}")
    if phase["id"]:
        progress.append(f"Active phase is {phase['id']}{(' — ' + phase_name) if phase_name else ''}")

    focus = []
    if phase_name:
        focus.append(f"Current work is centered on {phase_name.lower()}")
    elif phase["id"]:
        focus.append(f"Current work is centered on {phase['id']}")
    else:
        focus.append("Current work is still too early to resolve into an active phase")

    risks = []
    if status["open_bugs"]:
        risks.append(f"Open bugs still need attention ({len(status['open_bugs'])})")
    if status["open_requirements"]:
        risks.append(f"Open requirements remain unresolved ({len(status['open_requirements'])})")
    if not risks:
        risks.append("No major risks surfaced from the current project status snapshot")

    next_items = status["next"][:] if status["next"] else []
    if not next_items:
        if status["open_bugs"] or status["open_requirements"]:
            next_items.append("Resolve the open bugs and requirements before the next publication cycle")
        elif phase_name:
            next_items.append(f"Continue advancing the current {phase_name.lower()} phase")
        else:
            next_items.append("Continue gathering enough material to clarify the active phase and next milestone")

    lines = [
        f"# {status['slug']} — Team Project Summary",
        "",
        f"- Updated at: {status['as_of']}",
        f"- Source commit: {source_commit}",
        "",
        "## Current Focus",
    ]
    lines.extend([f"- {item}" for item in focus])

    lines.extend(["", "## Recent Progress"])
    lines.extend([f"- {item}" for item in progress] if progress else ["- No significant recent progress detected"])

    lines.extend(["", "## Risks / Attention"])
    lines.extend([f"- {item}" for item in risks])

    lines.extend(["", "## Next"])
    lines.extend([f"- {item}" for item in next_items])

    lines.extend(["", "## Supporting Signals"])
    lines.append(f"- Active Phase: {phase_label}{(' — ' + phase_name) if phase_name else ''}")
    lines.append(f"- Open Bugs: {len(status['open_bugs'])}")
    lines.append(f"- Open Requirements: {len(status['open_requirements'])}")
    if digest_tail:
        lines.append(f"- Context: {'; '.join(digest_tail)}")

    return "\n".join(lines) + "\n"
```

- [ ] **Step 2: Verify the module still imports**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "from sybermem_core.publish import render_current_status; print('team project summary renderer OK')"
```

Expected: `team project summary renderer OK`

- [ ] **Step 3: Commit**

```bash
git add packages/core/sybermem_core/publish.py
git commit -m "feat: render Team project summaries instead of thin status snapshots"
```

---

### Task 2: Dogfood the refactor against the real Team repo

**Files:**
- No repo-file changes required by default (verification only)

- [ ] **Step 1: Re-publish `sybermem` to regenerate its Team project summary**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --format json
```

Expected: publish succeeds using the remembered Team association from `project.yaml`.

- [ ] **Step 2: Read the generated Team repo file**

Inspect:

```text
D:/team-memory/projects/sybermem/current-status.md
```

Expected sections:
- `# sybermem — Team Project Summary`
- `## Current Focus`
- `## Recent Progress`
- `## Risks / Attention`
- `## Next`
- `## Supporting Signals`

- [ ] **Step 3: Confirm the file no longer leads with raw record IDs as the main story**

Expected:
- main sections are narrative bullets
- raw IDs may still appear in supporting phrasing, but not as the top-level primary structure like the old `## Recent Records` block

- [ ] **Step 4: No commit needed** (dogfood verification only)

---

### Task 3: Update docs to reflect the Team Project Summary wording

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/superpowers/specs/2026-07-02-sybermem-team-project-summary-refactor-design.md` (only if implementation wording differs)

- [ ] **Step 1: Update the Team Phase B bullet in `README.md`**

Change the wording from:

```markdown
- **Phase B**：`sybermem publish status` —— 必要时先利用现有 digest（或在材料足够时先补 phase digest），再将 `project.md` + Team-facing `current-status.md` + `meta.json` 发布到 Team repo
```

to:

```markdown
- **Phase B**：`sybermem publish status` —— 必要时先利用现有 digest（或在材料足够时先补 phase digest），再将 `project.md` + Team Project Summary 风格的 `current-status.md` + `meta.json` 发布到 Team repo
```

- [ ] **Step 2: Update the Team Phase B bullet in `README.en.md`**

Change the wording to:

```markdown
- **Phase B**: `sybermem publish status` — when needed, first use existing digests (or create a phase digest if the project has enough material), then publish `project.md` + a Team Project Summary style `current-status.md` + `meta.json` into the Team repo
```

- [ ] **Step 3: Only patch the spec if the final section names changed**

If the implemented headings differ from the Phase B refactor spec, align the spec wording; otherwise leave it unchanged.

- [ ] **Step 4: Commit**

```bash
git add README.md README.en.md docs/superpowers/specs/2026-07-02-sybermem-team-project-summary-refactor-design.md
git commit -m "docs: describe Team project summary publication wording"
```
