# SyberMem Team MVP Phase C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Team memory automatically regenerate a stable team-wide overview (`dashboards/current-overview.md`) every time a project publishes its status, so management agents have a single entrypoint into the Team repo.

**Architecture:** Extend the Team publish path so `sybermem publish status` not only writes per-project files (`project.md`, `current-status.md`, `meta.json`) but also rebuilds `dashboards/current-overview.md` from all published project summaries already in the Team repo. This is a full-rebuild generated view, not a hand-maintained file.

**Tech Stack:** Python 3.10+, Markdown, Team Git repo local filesystem

---

### Task 1: Add Team overview generation core logic

**Files:**
- Modify: `packages/core/sybermem_core/publish.py`

- [ ] **Step 1: Add a parser for published project summaries**

In `packages/core/sybermem_core/publish.py`, add helper functions above `publish_status()`:

```python
def parse_published_status(project_dir: Path) -> dict[str, str | list[str]]:
    status_md = project_dir / "current-status.md"
    meta_json = project_dir / "meta.json"
    if not status_md.is_file() or not meta_json.is_file():
        return {}

    import json as _json
    meta = _json.loads(meta_json.read_text(encoding="utf-8"))
    text = status_md.read_text(encoding="utf-8")

    phase_line = ""
    for line in text.splitlines():
        if line.startswith("- phase-") or line.startswith("- (no phase)"):
            phase_line = line[2:].strip()
            break

    open_bugs = []
    open_requirements = []
    section = None
    for line in text.splitlines():
        if line.startswith("## Open Bugs"):
            section = "bugs"
            continue
        if line.startswith("## Open Requirements"):
            section = "reqs"
            continue
        if line.startswith("## "):
            section = None
            continue
        if section == "bugs" and line.startswith("- ") and line.strip() != "- none":
            open_bugs.append(line[2:].strip())
        if section == "reqs" and line.startswith("- ") and line.strip() != "- none":
            open_requirements.append(line[2:].strip())

    return {
        "slug": project_dir.name,
        "published_at": meta.get("published_at", ""),
        "phase_line": phase_line,
        "open_bugs": open_bugs,
        "open_requirements": open_requirements,
        "source_phase_digest": meta.get("source_phase_digest", ""),
        "source_theme_digest": meta.get("source_theme_digest", ""),
    }
```

- [ ] **Step 2: Add the Team overview renderer**

Still in `packages/core/sybermem_core/publish.py`, add:

```python
def render_team_overview(team_id: str, summaries: list[dict]) -> str:
    active = []
    stale = []
    attention = []
    sources = []

    summaries = sorted(summaries, key=lambda s: s.get("published_at", ""), reverse=True)

    for s in summaries:
        slug = s["slug"]
        phase_line = s.get("phase_line", "")
        published_at = s.get("published_at", "")
        source_phase = bool(s.get("source_phase_digest"))
        source_theme = bool(s.get("source_theme_digest"))

        if phase_line and phase_line != "(no phase)":
            active.append(f"- {slug} → {phase_line}")
        else:
            attention.append(f"- {slug} — no active phase")

        if published_at:
            stale.append(f"- {slug} — {published_at[:10]}")

        if s.get("open_bugs"):
            attention.append(f"- {slug} — open bugs: {len(s['open_bugs'])}")
        if s.get("open_requirements"):
            attention.append(f"- {slug} — open requirements: {len(s['open_requirements'])}")

        if source_phase and source_theme:
            sources.append(f"- {slug} → phase digest available, theme digest available")
        elif source_phase:
            sources.append(f"- {slug} → phase digest available")
        elif source_theme:
            sources.append(f"- {slug} → theme digest available")
        else:
            sources.append(f"- {slug} → no digest published")

    lines = [
        "# Team Overview",
        "",
        f"- Updated at: {summaries[0]['published_at'] if summaries else ''}",
        f"- Team: {team_id}",
        "",
        "## Active Projects",
    ]
    lines.extend(active or ["- none"])
    lines.extend(["", "## Recently Updated"])
    lines.extend(stale or ["- none"])
    lines.extend(["", "## Needs Attention"])
    lines.extend(attention or ["- none"])
    lines.extend(["", "## Published Sources"])
    lines.extend(sources or ["- none"])
    return "\n".join(lines) + "\n"
```

- [ ] **Step 3: Add Team overview rebuild into `publish_status()`**

At the end of `publish_status()` — after writing `project.md`, `current-status.md`, and `meta.json` — add:

```python
    # Rebuild team-wide overview from all published project summaries
    dashboards_dir = team_root / "dashboards"
    dashboards_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    projects_root = team_root / "projects"
    for child in sorted(projects_root.iterdir()):
        if child.is_dir():
            parsed = parse_published_status(child)
            if parsed:
                summaries.append(parsed)
    overview = dashboards_dir / "current-overview.md"
    overview.write_text(render_team_overview(team_id, summaries), encoding="utf-8")
```

Also extend the returned payload `files` list to include:

```python
            str(overview).replace('\\', '/'),
```

- [ ] **Step 4: Verify the core module still imports**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "from sybermem_core.publish import publish_status, render_team_overview; print('publish.py overview OK')"
```

Expected: `publish.py overview OK`

- [ ] **Step 5: Commit**

```bash
git add packages/core/sybermem_core/publish.py
git commit -m "feat: rebuild Team current-overview after publish status"
```

---

### Task 2: Dogfood the Team overview rebuild with real published project data

**Files:**
- No repo-file changes required by default

- [ ] **Step 1: Re-run publish status for `sybermem`**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --team-path D:/team-memory --format json
```

Expected:
- payload `files` now includes `D:/team-memory/dashboards/current-overview.md`

- [ ] **Step 2: Verify `current-overview.md` exists and has all 4 sections**

Check for:
- `# Team Overview`
- `## Active Projects`
- `## Recently Updated`
- `## Needs Attention`
- `## Published Sources`

- [ ] **Step 3: Confirm it includes `sybermem` and uses digest source awareness**

`current-overview.md` should mention:
- `sybermem`
- its active phase
- whether phase digest / theme digest are available

- [ ] **Step 4: No commit needed** (dogfood verification only)

---

### Task 3: Update Team MVP documentation to mention automatic overview rebuild

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseC-design.md`

- [ ] **Step 1: Update README.md Team MVP note**

In the Team MVP section, add one bullet after the Phase B line:

```markdown
- **Phase C**：每次 `publish status` 后自动重建 `dashboards/current-overview.md`，作为团队统一总览入口
```

- [ ] **Step 2: Update README.en.md Team MVP note**

Add the matching bullet:

```markdown
- **Phase C**: after each `publish status`, automatically rebuild `dashboards/current-overview.md` as the team-wide overview entrypoint
```

- [ ] **Step 3: Update the Phase C spec to mention the exact file path in output examples**

In `docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseC-design.md`, ensure the examples and success criteria explicitly mention:

```text
<team-repo>/dashboards/current-overview.md
```

If already present, no change needed.

- [ ] **Step 4: Commit**

```bash
git add README.md README.en.md docs/superpowers/specs/2026-07-01-sybermem-team-mvp-phaseC-design.md
git commit -m "docs: note automatic Team overview rebuild after publish status"
```
