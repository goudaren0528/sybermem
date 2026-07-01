# SyberMem Team MVP Phase A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the first real Team storage foundation by adding `sybermem team init`, `team.yaml`, and a Team Git repository directory skeleton with remote binding.

**Architecture:** Extend the existing Phase 1 Core/CLI with a new `team.py` core module and a `team init` CLI subcommand. This command initializes a local Team repo skeleton, validates or attaches a Git remote, and writes a stable `team.yaml`. It intentionally stops short of `publish`, `sync`, or `review`.

**Tech Stack:** Python 3.10+, Git CLI, YAML-style line rendering (no external YAML dependency)

---

### Task 1: Add Team schema and core module

**Files:**
- Create: `schemas/team.yaml.example`
- Create: `packages/core/sybermem_core/team.py`

- [ ] **Step 1: Create `schemas/team.yaml.example`**

```yaml
schema_version: 1
team_id: team_rental_platform
name: Rental Platform
repository:
  remote: https://github.com/example/sybermem-team.git
created_at: 2026-06-30T10:00:00+08:00
```

- [ ] **Step 2: Create `packages/core/sybermem_core/team.py`**

```python
from __future__ import annotations

from pathlib import Path
import subprocess

from .identity import now_iso
from .storage import ensure_dir


def render_team_yaml(team_id: str, name: str, remote: str) -> str:
    return (
        f"schema_version: 1\n"
        f"team_id: {team_id}\n"
        f"name: {name}\n"
        f"repository:\n"
        f"  remote: {remote}\n"
        f"created_at: {now_iso()}\n"
    )


def git_remote(root: Path) -> str:
    try:
        r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def init_team_repo(path: Path, team_id: str, name: str, remote: str) -> dict[str, str]:
    if path.exists() and not path.is_dir():
        raise ValueError(f"Path exists but is not a directory: {path}")

    created = False
    if not path.exists():
        ensure_dir(path)
        created = True

    git_dir = path / ".git"
    if not git_dir.exists():
        # If the directory already existed but is not a git repo, refuse.
        if not created and any(path.iterdir()):
            raise ValueError(f"Path exists but is not a git repository: {path}")
        subprocess.run(["git", "init"], cwd=path, check=True)

    current_remote = git_remote(path)
    if current_remote:
        if current_remote != remote:
            raise ValueError(f"Existing origin remote differs: {current_remote}")
    else:
        subprocess.run(["git", "remote", "add", "origin", remote], cwd=path, check=True)

    # Create Team directory skeleton
    for sub in [
        "projects",
        "lessons/candidates",
        "lessons/accepted",
        "lessons/rejected",
        "lessons/deprecated",
        "standards",
        "architecture",
        "publications",
        "dashboards",
    ]:
        ensure_dir(path / sub)

    team_yaml = path / "team.yaml"
    if not team_yaml.exists():
        team_yaml.write_text(render_team_yaml(team_id, name, remote), encoding="utf-8")
        status = "created"
    else:
        status = "existing"

    return {
        "status": status,
        "team_id": team_id,
        "name": name,
        "path": str(path).replace('\\', '/'),
        "remote": remote,
    }
```

- [ ] **Step 3: Verify the core module imports cleanly**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "from sybermem_core.team import render_team_yaml, init_team_repo; print('team.py OK')"
```

Expected: `team.py OK`

- [ ] **Step 4: Commit**

```bash
git add schemas/team.yaml.example packages/core/sybermem_core/team.py
git commit -m "feat: add Team repo schema and core init logic"
```

---

### Task 2: Wire `team init` into the CLI

**Files:**
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Add the import**

Add to the imports:

```python
from sybermem_core.team import init_team_repo
```

- [ ] **Step 2: Add the command handler**

Insert this function above `main()`:

```python
def cmd_team_init(args: argparse.Namespace) -> int:
    try:
        payload = init_team_repo(Path(args.path), args.team_id, args.name, args.remote)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.format == "json":
        print(dump_json(payload))
    else:
        print("Initialized team repo:")
        print(f"- team_id: {payload['team_id']}")
        print(f"- name: {payload['name']}")
        print(f"- path: {payload['path']}")
        print(f"- remote: {payload['remote']}")
    return 0
```

- [ ] **Step 3: Add parser wiring**

In `main()`, add a new top-level `team` command:

```python
    team = sub.add_parser("team")
    team_sub = team.add_subparsers(dest="team_command", required=True)
    team_init = team_sub.add_parser("init")
    team_init.add_argument("--path", required=True)
    team_init.add_argument("--team-id", required=True)
    team_init.add_argument("--name", required=True)
    team_init.add_argument("--remote", required=True)
    team_init.add_argument("--format", choices=["text", "json"], default="text")
    team_init.set_defaults(func=cmd_team_init)
```

- [ ] **Step 4: Verify CLI help shows the team command**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main --help
```

Expected: top-level choices include `team`.

- [ ] **Step 5: Commit**

```bash
git add packages/cli/sybermem_cli/main.py
git commit -m "feat: add sybermem team init CLI command"
```

---

### Task 3: Dogfood `sybermem team init` against a real local Team repo path

**Files:**
- No repo-file changes required by default (verification only)

- [ ] **Step 1: Pick a local Team repo path and initialize it**

Run a real dogfood command such as:

```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main team init --path D:/team-memory --team-id team_rental_platform --name "Rental Platform" --remote https://github.com/example/sybermem-team.git --format json
```

Expected: JSON with `status`, `team_id`, `name`, `path`, `remote`.

- [ ] **Step 2: Verify the Team directory skeleton exists**

Check for:
- `D:/team-memory/team.yaml`
- `D:/team-memory/projects/`
- `D:/team-memory/lessons/candidates/`
- `D:/team-memory/lessons/accepted/`
- `D:/team-memory/lessons/rejected/`
- `D:/team-memory/lessons/deprecated/`
- `D:/team-memory/standards/`
- `D:/team-memory/architecture/`
- `D:/team-memory/publications/`
- `D:/team-memory/dashboards/`
- `D:/team-memory/.git/`

Use a PowerShell or Python existence check.

- [ ] **Step 3: Verify the Git remote binding**

Run in `D:/team-memory`:

```bash
git remote get-url origin
```

Expected: `https://github.com/example/sybermem-team.git`

- [ ] **Step 4: No commit needed** (verification only)

---

### Task 4: Add minimal docs for Team Phase A and sync plugin tree if needed

**Files:**
- Modify: `docs/superpowers/specs/2026-06-30-sybermem-team-mvp-phaseA-design.md` (only if dogfood reveals a behavior mismatch)
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Add a short note to README.md**

Add a brief subsection under the platform / roadmap area:

```markdown
## Team MVP（进行中）

SyberMem 已经开始进入 Team MVP 路线。当前第一步是 `sybermem team init`：
- 创建 team repo 骨架
- 写 `team.yaml`
- 绑定远程 Git

后续 `publish status` / `team sync` / `team review` 会在此基础上叠加。
```

- [ ] **Step 2: Add the same note to README.en.md**

```markdown
## Team MVP (in progress)

SyberMem has started the Team MVP track. The first step is `sybermem team init`, which:
- creates the team repo skeleton
- writes `team.yaml`
- binds the Git remote

`publish status`, `team sync`, and `team review` will build on top of that foundation.
```

- [ ] **Step 3: Only update the spec if dogfood contradicted it**

If the real `team init` command required a design adjustment, patch the spec; otherwise leave it untouched.

- [ ] **Step 4: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: note Team MVP Phase A team init entrypoint"
```
