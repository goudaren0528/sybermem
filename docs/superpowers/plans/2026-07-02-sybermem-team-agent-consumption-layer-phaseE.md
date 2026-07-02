# SyberMem Team Agent Consumption Layer（Phase E）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight Team management-consumption layer so management agents can generate a low-cost, incrementally computed team summary from the real Team repo.

**Architecture:** Build a new Team-summary core module that reads only Team repo outputs (`current-overview.md`, `projects/*/current-status.md`, `projects/*/meta.json`), tracks a baseline in `.summary-state.json`, and emits both a markdown summary and a machine-readable JSON summary. Expose it as `sybermem team summary`.

**Tech Stack:** Python 3.10+, Markdown, JSON, Team Git repo local filesystem

---

### Task 1: Add Team summary generation core logic

**Files:**
- Create: `packages/core/sybermem_core/team_summary.py`

- [ ] **Step 1: Create `team_summary.py`**

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json


def now_iso() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat(timespec="seconds")


def read_team_yaml(team_root: Path) -> str:
    team_yaml = team_root / "team.yaml"
    if not team_yaml.is_file():
        raise FileNotFoundError(f"Missing team.yaml in Team repo: {team_root}")
    for line in team_yaml.read_text(encoding="utf-8").splitlines():
        if line.startswith("team_id:"):
            return line.split(":", 1)[1].strip()
    return ""


def load_summary_state(dashboards_dir: Path) -> dict:
    state_path = dashboards_dir / ".summary-state.json"
    if not state_path.is_file():
        return {"last_generated_at": "", "last_seen_projects": {}}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_summary_state(dashboards_dir: Path, state: dict) -> Path:
    path = dashboards_dir / ".summary-state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_project_publications(team_root: Path) -> list[dict]:
    projects_root = team_root / "projects"
    items = []
    if not projects_root.is_dir():
        return items

    for child in sorted(projects_root.iterdir()):
        if not child.is_dir():
            continue
        meta_json = child / "meta.json"
        status_md = child / "current-status.md"
        if not meta_json.is_file() or not status_md.is_file():
            continue
        meta = json.loads(meta_json.read_text(encoding="utf-8"))
        status_text = status_md.read_text(encoding="utf-8")

        phase_line = ""
        for line in status_text.splitlines():
            if line.startswith("- phase-") or line.startswith("- (no phase)"):
                phase_line = line[2:].strip()
                break

        open_bugs = []
        open_requirements = []
        section = None
        for line in status_text.splitlines():
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

        items.append({
            "slug": child.name,
            "published_at": meta.get("published_at", ""),
            "phase_line": phase_line,
            "source_phase_digest": meta.get("source_phase_digest", ""),
            "source_theme_digest": meta.get("source_theme_digest", ""),
            "open_bugs": open_bugs,
            "open_requirements": open_requirements,
        })
    return items


def build_team_management_summary(team_root: Path) -> dict[str, Path | dict | str]:
    team_root = team_root.resolve()
    dashboards_dir = team_root / "dashboards"
    dashboards_dir.mkdir(parents=True, exist_ok=True)

    team_id = read_team_yaml(team_root)
    publications = load_project_publications(team_root)
    state = load_summary_state(dashboards_dir)
    previous_seen = state.get("last_seen_projects", {})

    generated_at = now_iso()
    recent_cutoff = datetime.fromisoformat(generated_at) - timedelta(hours=48)

    progress = []
    attention = []
    deep_review = []
    recent_updates = []
    next_seen = {}

    for p in publications:
        slug = p["slug"]
        published_at = p.get("published_at", "")
        next_seen[slug] = published_at

        if published_at and previous_seen.get(slug) != published_at:
            progress.append({
                "slug": slug,
                "change_type": "status_update",
                "published_at": published_at,
                "phase": p.get("phase_line", ""),
            })

        if published_at:
            try:
                published_dt = datetime.fromisoformat(published_at)
                if published_dt >= recent_cutoff:
                    recent_updates.append({"slug": slug, "published_at": published_at})
                else:
                    days_old = (datetime.fromisoformat(generated_at) - published_dt).days
                    if days_old > 3:
                        attention.append({"slug": slug, "reason": "stale", "count": days_old})
            except Exception:
                pass

        if not p.get("phase_line") or p.get("phase_line") == "(no phase)":
            attention.append({"slug": slug, "reason": "no_active_phase", "count": 0})
        if p.get("open_bugs"):
            attention.append({"slug": slug, "reason": "open_bugs", "count": len(p["open_bugs"])})
        if p.get("open_requirements"):
            attention.append({"slug": slug, "reason": "open_requirements", "count": len(p["open_requirements"])})

        if p.get("source_phase_digest"):
            deep_review.append({"slug": slug, "reason": "new_phase_digest"})
        elif p.get("source_theme_digest"):
            deep_review.append({"slug": slug, "reason": "new_theme_digest"})
        elif p.get("open_bugs") and p.get("open_requirements"):
            deep_review.append({"slug": slug, "reason": "multiple_attention_signals"})

    md_lines = [
        "# Team Management Summary",
        "",
        f"- Generated at: {generated_at}",
        f"- Team: {team_id}",
        "- Baseline: since last summary",
        "- Recent window: last 48 hours",
        "",
        "## Progress Since Last Summary",
    ]
    if progress:
        for item in progress:
            phase = item.get("phase", "")
            phase_tail = f"; current phase {phase}" if phase else ""
            md_lines.append(f"- {item['slug']} — published a new update{phase_tail}")
    else:
        md_lines.append("- none")

    md_lines.extend(["", "## Attention Needed"])
    if attention:
        for item in attention:
            if item["reason"] == "stale":
                md_lines.append(f"- {item['slug']} — stale for {item['count']} days")
            elif item["reason"] == "no_active_phase":
                md_lines.append(f"- {item['slug']} — no active phase")
            elif item["reason"] == "open_bugs":
                md_lines.append(f"- {item['slug']} — open bugs: {item['count']}")
            elif item["reason"] == "open_requirements":
                md_lines.append(f"- {item['slug']} — open requirements: {item['count']}")
    else:
        md_lines.append("- none")

    md_lines.extend(["", "## Worth Deeper Review"])
    if deep_review:
        for item in deep_review:
            md_lines.append(f"- {item['slug']} — {item['reason']}")
    else:
        md_lines.append("- none")

    md_lines.extend(["", "## Recently Updated Projects"])
    if recent_updates:
        for item in recent_updates:
            md_lines.append(f"- {item['slug']} — {item['published_at'][:10]}")
    else:
        md_lines.append("- none")

    summary_md = dashboards_dir / "latest-management-summary.md"
    summary_json = dashboards_dir / "latest-management-summary.json"
    summary_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    payload = {
        "generated_at": generated_at,
        "team_id": team_id,
        "baseline": "since_last_summary",
        "recent_window_hours": 48,
        "progress": progress,
        "attention": attention,
        "deep_review_candidates": deep_review,
        "recent_updates": recent_updates,
    }
    summary_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state_path = save_summary_state(dashboards_dir, {
        "last_generated_at": generated_at,
        "last_seen_projects": next_seen,
    })

    return {
        "team_id": team_id,
        "team_path": str(team_root).replace('\\', '/'),
        "summary_markdown": summary_md,
        "summary_json": summary_json,
        "summary_state": state_path,
        "payload": payload,
    }
```

- [ ] **Step 2: Verify the module imports cleanly**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "from sybermem_core.team_summary import build_team_management_summary; print('team_summary.py OK')"
```

Expected: `team_summary.py OK`

- [ ] **Step 3: Commit**

```bash
git add packages/core/sybermem_core/team_summary.py
git commit -m "feat: add Team management summary core generator"
```

---

### Task 2: Add `sybermem team summary` CLI command

**Files:**
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Add the import**

Add:

```python
from sybermem_core.team_summary import build_team_management_summary
```

- [ ] **Step 2: Add the command handler**

Insert above `main()`:

```python
def cmd_team_summary(args: argparse.Namespace) -> int:
    try:
        result = build_team_management_summary(Path(args.team_path))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = result["payload"]
    if args.format == "json":
        print(dump_json(payload))
    else:
        print("Generated Team management summary:")
        print(f"- team: {result['team_id']}")
        print(f"- markdown: {result['summary_markdown']}")
        print(f"- json: {result['summary_json']}")
        print(f"- baseline state: {result['summary_state']}")
    return 0
```

- [ ] **Step 3: Add parser wiring**

Under the existing `team` command, add a `summary` subcommand:

```python
    team_summary = team_sub.add_parser("summary")
    team_summary.add_argument("--team-path", required=True)
    team_summary.add_argument("--format", choices=["text", "json"], default="text")
    team_summary.set_defaults(func=cmd_team_summary)
```

- [ ] **Step 4: Verify CLI help**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main team --help
```

Expected: subcommands include `init` and `summary`.

- [ ] **Step 5: Commit**

```bash
git add packages/cli/sybermem_cli/main.py
git commit -m "feat: add sybermem team summary CLI command"
```

---

### Task 3: Dogfood management summary generation on the real Team repo

**Files:**
- No repo-file changes required by default

- [ ] **Step 1: Generate the summary**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main team summary --team-path D:/team-memory --format json
```

Expected: JSON payload with:
- `generated_at`
- `team_id`
- `progress`
- `attention`
- `deep_review_candidates`
- `recent_updates`

- [ ] **Step 2: Verify the three dashboard files exist**

Check:
- `D:/team-memory/dashboards/latest-management-summary.md`
- `D:/team-memory/dashboards/latest-management-summary.json`
- `D:/team-memory/dashboards/.summary-state.json`

- [ ] **Step 3: Verify markdown structure**

`latest-management-summary.md` must contain:
- `# Team Management Summary`
- `## Progress Since Last Summary`
- `## Attention Needed`
- `## Worth Deeper Review`
- `## Recently Updated Projects`

- [ ] **Step 4: Re-run to confirm incremental baseline works**

Run the same command twice in a row.

Expected:
- The second run still succeeds
- `.summary-state.json` updates `last_generated_at`
- `progress` should shrink or stabilize when no new publishes occurred

- [ ] **Step 5: No commit needed** (dogfood verification only)

---

### Task 4: Update README Team MVP notes for the new management-consumption layer

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Add a Phase E bullet to `README.md`**

Add under the existing Team MVP bullets:

```markdown
- **Phase E**：`sybermem team summary` —— 基于 Team repo 已发布内容生成低成本管理摘要（markdown + json），服务管理 agent 的日常消费
```

- [ ] **Step 2: Add the matching bullet to `README.en.md`**

```markdown
- **Phase E**: `sybermem team summary` — generate a low-cost management summary (markdown + json) from Team repo publications for management-agent consumption
```

- [ ] **Step 3: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: add Team Phase E management summary entrypoint"
```
