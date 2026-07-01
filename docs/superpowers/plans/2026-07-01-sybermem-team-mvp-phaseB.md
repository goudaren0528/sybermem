# SyberMem Team MVP Phase B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first real Team publication flow by shipping `sybermem publish status`, which writes `project.md` and `current-status.md` into a Team repo under `projects/<slug>/`.

**Architecture:** Build on the existing `team init` + `project status` work. Add a new core module `publish.py` that reads the current project's `project.yaml` and `project status` snapshot, validates a Team repo, and writes two Markdown files: a stable `project.md` identity card and a current `current-status.md` snapshot. Add a `publish status` CLI surface in `main.py`. No review/sync/history in this phase.

**Tech Stack:** Python 3.10+, Git repo local filesystem, Markdown

---

### Task 1: Implement Team status publication core logic

**Files:**
- Create: `packages/core/sybermem_core/publish.py`

- [ ] **Step 1: Create `publish.py`**

```python
from __future__ import annotations

from pathlib import Path

from .project import resolve_project_root
from .records import parse_project_yaml
from .status import project_status


def render_project_card(project_meta: dict[str, str], team_id: str) -> str:
    return (
        f"# {project_meta.get('slug', '')}\n\n"
        f"- Project ID: {project_meta.get('project_id', '')}\n"
        f"- Slug: {project_meta.get('slug', '')}\n"
        f"- Name: {project_meta.get('name', project_meta.get('slug', ''))}\n"
        f"- Repository: {project_meta.get('remote', '')}\n"
        f"- Team: {team_id}\n"
        f"- Registered at: {project_meta.get('created_at', '')}\n"
    )


def render_current_status(status: dict, source_commit: str) -> str:
    phase = status["phase"]
    lines = [
        f"# {status['slug']} — Current Status",
        "",
        f"- Updated at: {status['as_of']}",
        f"- Source commit: {source_commit}",
        "",
        "## Active Phase",
        f"- {phase['id'] or '(no phase)'}{(' — ' + phase['name']) if phase['name'] else ''}",
        "",
        "## Recent Records",
    ]
    if status["recent_records"]:
        lines.extend([f"- {r}" for r in status["recent_records"]])
    else:
        lines.append("- none")

    lines.extend(["", "## Open Bugs"])
    if status["open_bugs"]:
        lines.extend([f"- {r}" for r in status["open_bugs"]])
    else:
        lines.append("- none")

    lines.extend(["", "## Open Requirements"])
    if status["open_requirements"]:
        lines.extend([f"- {r}" for r in status["open_requirements"]])
    else:
        lines.append("- none")

    lines.extend(["", "## Next"])
    if status["next"]:
        lines.extend([f"- {n}" for n in status["next"]])
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def read_team_yaml(team_root: Path) -> tuple[str, str]:
    team_yaml = team_root / "team.yaml"
    if not team_yaml.is_file():
        raise FileNotFoundError(f"Missing team.yaml in Team repo: {team_root}")
    team_id = ""
    remote = ""
    for line in team_yaml.read_text(encoding="utf-8").splitlines():
        if line.startswith("team_id:"):
            team_id = line.split(":", 1)[1].strip()
        elif line.strip().startswith("remote:"):
            remote = line.split(":", 1)[1].strip()
    return team_id, remote


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

    status = project_status(root)
    slug = project_meta.get("slug", root.name)
    source_commit = project_meta.get("repository.commit", "")

    project_dir = team_root / "projects" / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    project_md = project_dir / "project.md"
    current_status_md = project_dir / "current-status.md"

    project_md.write_text(render_project_card(project_meta, team_id), encoding="utf-8")
    current_status_md.write_text(render_current_status(status, source_commit), encoding="utf-8")

    return {
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "team_path": str(team_root).replace('\\', '/'),
        "files": [
            str(project_md).replace('\\', '/'),
            str(current_status_md).replace('\\', '/'),
        ],
    }
```

- [ ] **Step 2: Verify the module imports cleanly**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "from sybermem_core.publish import publish_status; print('publish.py OK')"
```

Expected: `publish.py OK`

- [ ] **Step 3: Commit**

```bash
git add packages/core/sybermem_core/publish.py
git commit -m "feat: add Team status publication core logic"
```

---

### Task 2: Add `sybermem publish status` to the CLI

**Files:**
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Add the import**

Add:

```python
from sybermem_core.publish import publish_status
```

- [ ] **Step 2: Add the handler**

Insert above `main()`:

```python
def cmd_publish_status(args: argparse.Namespace) -> int:
    try:
        payload = publish_status(Path(args.team_path))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.format == "json":
        print(dump_json(payload))
    else:
        print("Published project status to Team repo:")
        print(f"- team: {payload['team_id']}")
        print(f"- project: {payload['slug']}")
        print("- files:")
        for f in payload["files"]:
            print(f"  - {f}")
    return 0
```

- [ ] **Step 3: Add parser wiring**

In `main()`, add a new top-level `publish` command with a `status` subcommand:

```python
    publish = sub.add_parser("publish")
    publish_sub = publish.add_subparsers(dest="publish_command", required=True)
    publish_status_cmd = publish_sub.add_parser("status")
    publish_status_cmd.add_argument("--team-path", required=True)
    publish_status_cmd.add_argument("--format", choices=["text", "json"], default="text")
    publish_status_cmd.set_defaults(func=cmd_publish_status)
```

- [ ] **Step 4: Verify the CLI surface**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main --help
```

Expected: top-level choices include `publish`.

- [ ] **Step 5: Commit**

```bash
git add packages/cli/sybermem_cli/main.py
git commit -m "feat: add sybermem publish status CLI command"
```

---

### Task 3: Dogfood `publish status` into the real Team repo

**Files:**
- No repo-file changes required by default (verification only)

- [ ] **Step 1: Use the Team repo created in Phase A**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --team-path D:/team-memory --format json
```

Expected: JSON like:

```json
{
  "status": "published",
  "team_id": "team_rental_platform",
  "project_id": "prj_01J6SYBERMEM0001",
  "slug": "sybermem",
  "team_path": "D:/team-memory",
  "files": [
    "D:/team-memory/projects/sybermem/project.md",
    "D:/team-memory/projects/sybermem/current-status.md"
  ]
}
```

- [ ] **Step 2: Verify the Team repo now has real content**

Check:
- `D:/team-memory/projects/sybermem/project.md`
- `D:/team-memory/projects/sybermem/current-status.md`

Both should exist.

- [ ] **Step 3: Read the generated files and verify content shape**

`project.md` should contain:
- Project ID
- Slug
- Name
- Repository
- Team
- Registered at

`current-status.md` should contain:
- Updated at
- Source commit
- Active Phase
- Recent Records
- Open Bugs
- Open Requirements
- Next

- [ ] **Step 4: Re-run publish to confirm idempotency**

Run the same command a second time.
Expected: still `status: published`; files are overwritten cleanly, not duplicated.

- [ ] **Step 5: No commit needed** (dogfood verification only)

---

### Task 4: Add a short Team Phase B note to README files

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Update the Team MVP note in `README.md`**

Replace the current Team MVP section (added in Phase A) with:

```markdown
## Team MVP（进行中）

SyberMem 正在进入 Team MVP 路线：

- **Phase A**：`sybermem team init` —— 创建 team repo 骨架、写 `team.yaml`、绑定远程 Git
- **Phase B**：`sybermem publish status` —— 将当前项目的 `project.md` + `current-status.md` 发布到 Team repo

后续 `team sync`、`team review`、digest/lesson 发布会在此基础上叠加。
```

- [ ] **Step 2: Update the Team MVP note in `README.en.md`**

Replace the current Team MVP section with:

```markdown
## Team MVP (in progress)

SyberMem is now moving into the Team MVP track:

- **Phase A**: `sybermem team init` — create the Team repo skeleton, write `team.yaml`, and bind the Git remote
- **Phase B**: `sybermem publish status` — publish the current project's `project.md` + `current-status.md` into the Team repo

`team sync`, `team review`, and digest/lesson publication will build on top of that foundation.
```

- [ ] **Step 3: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: update Team MVP notes for status publication phase"
```
