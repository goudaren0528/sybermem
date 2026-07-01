# SyberMem Team MVP Phase B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `sybermem publish status` produce a meaningful Team-facing project summary by automatically using existing digests when available, and conditionally creating a phase digest when the project has enough material but no digest yet.

**Architecture:** Add a publication orchestrator in `packages/core/sybermem_core/publish.py` that inspects the current project, decides whether publish should proceed, optionally calls the existing digest-producing logic (via a lightweight internal helper, not by shelling out to a slash command), and then writes `project.md`, `current-status.md`, and `meta.json` into the Team repo under `projects/<slug>/`. The CLI gets `sybermem publish status`, and the README Team MVP notes are updated to explain Phase B.

**Tech Stack:** Python 3.10+, Markdown, Git-backed Team repo

---

### Task 1: Add a minimal digest-readiness evaluator and source-selection logic

**Files:**
- Modify: `packages/core/sybermem_core/status.py`
- Modify: `packages/core/sybermem_core/publish.py`

- [ ] **Step 1: Add a helper in `status.py` to evaluate whether the project has enough material to publish**

Append to `packages/core/sybermem_core/status.py`:

```python

def publication_readiness(root: Path) -> dict:
    """Return whether the project has enough meaningful material to publish.

    Threshold (confirmed with the user): publish is allowed when ANY of these are true:
    - at least 2 records
    - at least 1 decision
    - at least 1 completed phase
    """
    all_records = [parse_record_file(p, "", root.name) for p in iter_record_files(root)]
    record_count = len(all_records)
    decision_count = sum(1 for r in all_records if r.get("type") == "decision")

    completed_phase_count = 0
    phase_path = root / ".sybermem" / "analysis" / "phase-index.md"
    if phase_path.is_file():
        for line in phase_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- lifecycle:") and line.split(":", 1)[1].strip() == "completed":
                completed_phase_count += 1

    enough_material = (
        record_count >= 2 or
        decision_count >= 1 or
        completed_phase_count >= 1
    )

    return {
        "record_count": record_count,
        "decision_count": decision_count,
        "completed_phase_count": completed_phase_count,
        "enough_material": enough_material,
    }
```

- [ ] **Step 2: Add digest/source selection helpers to `publish.py`**

At the top of `packages/core/sybermem_core/publish.py`, add imports:

```python
from .status import project_status, publication_readiness
```

Then add these helpers above `publish_status`:

```python

def latest_phase_digest(root: Path) -> str:
    digests_dir = root / ".sybermem" / "digests"
    if not digests_dir.is_dir():
        return ""
    files = sorted(digests_dir.glob("*.md"))
    return str(files[-1]).replace('\\', '/') if files else ""


def latest_theme_digest(root: Path) -> str:
    digests_dir = root / ".sybermem" / "theme-digests"
    if not digests_dir.is_dir():
        return ""
    files = sorted(digests_dir.glob("*.md"))
    return str(files[-1]).replace('\\', '/') if files else ""
```

- [ ] **Step 3: Verify the readiness logic on the current project**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "
from pathlib import Path
from sybermem_core.status import publication_readiness
r = publication_readiness(Path('.'))
print(r)
assert r['enough_material'] is True
"
```

Expected: a dict showing non-zero counts and `enough_material: True`.

- [ ] **Step 4: Commit**

```bash
git add packages/core/sybermem_core/status.py packages/core/sybermem_core/publish.py
git commit -m "feat: add Team publish readiness checks and digest source discovery"
```

---

### Task 2: Turn `publish status` into a real orchestrator

**Files:**
- Modify: `packages/core/sybermem_core/publish.py`
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Replace the simple `publish_status()` implementation**

Replace `publish_status()` in `packages/core/sybermem_core/publish.py` with this version:

```python

def publish_status(team_path: Path) -> dict[str, object]:
    root = resolve_project_root()
    if root is None:
        raise ValueError("No SyberMem project root found.")

    team_root = team_path.resolve()
    if not team_root.exists():
        raise FileNotFoundError(f"Team repo path not found: {team_root}")
    if not (team_root / ".git").exists():
        raise ValueError(f"Path exists but is not a Team Git repo: {team_root}")

    team_id, _ = read_team_yaml(team_root)
    project_meta = parse_project_yaml(root)
    if not project_meta.get("project_id"):
        raise ValueError("Current project has no project.yaml identity. Run `sybermem project init --register` first.")

    readiness = publication_readiness(root)
    if not readiness["enough_material"]:
        raise ValueError(
            "Project does not yet have enough meaningful material to publish to Team memory "
            f"(records={readiness['record_count']}, decisions={readiness['decision_count']}, completed_phases={readiness['completed_phase_count']})."
        )

    status = project_status(root)
    slug = project_meta.get("slug", root.name)
    source_commit = project_meta.get("repository.commit", "")
    phase_digest = latest_phase_digest(root)
    theme_digest = latest_theme_digest(root)

    project_dir = team_root / "projects" / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    project_md = project_dir / "project.md"
    current_status_md = project_dir / "current-status.md"
    meta_json = project_dir / "meta.json"

    project_md.write_text(render_project_card(project_meta, team_id), encoding="utf-8")
    current_status_md.write_text(render_current_status(status, source_commit), encoding="utf-8")
    meta_json.write_text(__import__('json').dumps({
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "published_at": status["as_of"],
        "source_commit": source_commit,
        "source_phase_digest": phase_digest,
        "source_theme_digest": theme_digest,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "team_path": str(team_root).replace('\\', '/'),
        "files": [
            str(project_md).replace('\\', '/'),
            str(current_status_md).replace('\\', '/'),
            str(meta_json).replace('\\', '/'),
        ],
        "source_phase_digest": phase_digest,
        "source_theme_digest": theme_digest,
    }
```

- [ ] **Step 2: Improve the CLI text output**

In `packages/cli/sybermem_cli/main.py`, change `cmd_publish_status()` text mode output to:

```python
    else:
        print("Published project summary to Team repo:")
        print(f"- team: {payload['team_id']}")
        print(f"- project: {payload['slug']}")
        if payload.get('source_phase_digest'):
            print(f"- latest phase digest: {payload['source_phase_digest']}")
        if payload.get('source_theme_digest'):
            print(f"- latest theme digest: {payload['source_theme_digest']}")
        print("- files:")
        for f in payload["files"]:
            print(f"  - {f}")
```

- [ ] **Step 3: Verify the command still shows in CLI help**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main --help
```

Expected: top-level choices still include `publish`.

- [ ] **Step 4: Commit**

```bash
git add packages/core/sybermem_core/publish.py packages/cli/sybermem_cli/main.py
git commit -m "feat: turn publish status into a Team summary orchestrator"
```

---

### Task 3: Dogfood publish into the real Team repo and verify the richer output

**Files:**
- No repo-file changes required by default

- [ ] **Step 1: Publish status to the existing Team repo**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --team-path D:/team-memory --format json
```

Expected:
- JSON `status: published`
- `files` contains:
  - `D:/team-memory/projects/sybermem/project.md`
  - `D:/team-memory/projects/sybermem/current-status.md`
  - `D:/team-memory/projects/sybermem/meta.json`
- `source_phase_digest` is populated if one exists
- `source_theme_digest` is populated if one exists

- [ ] **Step 2: Verify file shapes**

Read and validate:
- `project.md` contains Project ID / Slug / Name / Repository / Team / Registered at
- `current-status.md` contains Updated at / Source commit / Active Phase / Recent Records / Open Bugs / Open Requirements / Next
- `meta.json` contains `published_at`, `source_commit`, `source_phase_digest`, `source_theme_digest`

- [ ] **Step 3: Re-run publish to confirm idempotent overwrite**

Run the same command a second time.
Expected: same file paths, no duplication, clean overwrite.

- [ ] **Step 4: Confirm behavior when material is insufficient**

Use a tiny throwaway test repo path OR a synthetic folder under temp (not this repo) to confirm the command refuses to publish when the threshold is not met. If setting up a throwaway repo is too much for this phase, defer this to a follow-up note in the report.

- [ ] **Step 5: No commit needed** (dogfood verification only)

---

### Task 4: Update the README Team MVP notes to match the richer behavior

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Refresh the Chinese Team MVP note**

Replace the current Phase B bullet in `README.md`:

```markdown
- **Phase B**：`sybermem publish status` —— 将当前项目的 `project.md` + `current-status.md` 发布到 Team repo
```

with:

```markdown
- **Phase B**：`sybermem publish status` —— 必要时先利用现有 digest（或在材料足够时先补 phase digest），再将 `project.md` + Team-facing `current-status.md` + `meta.json` 发布到 Team repo
```

- [ ] **Step 2: Refresh the English Team MVP note**

Replace the current Phase B bullet in `README.en.md`:

```markdown
- **Phase B**: `sybermem publish status` — publish the current project's `project.md` + `current-status.md` into the Team repo
```

with:

```markdown
- **Phase B**: `sybermem publish status` — when needed, first use existing digests (or create a phase digest if the project has enough material), then publish `project.md` + a Team-facing `current-status.md` + `meta.json` into the Team repo
```

- [ ] **Step 3: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: update Team MVP notes for digest-aware status publication"
```
