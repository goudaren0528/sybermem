# SyberMem Team Push Bootstrap Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `sybermem publish status` into a Team push bootstrap flow that can automatically fill in low-risk prerequisites (project identity, registry entry, team association write-back, digest/status preparation) while only pausing for high-impact actions.

**Architecture:** Keep the user-facing entrypoint unchanged (`sybermem publish status`). Add a small bootstrap/orchestration layer that resolves project initialization state, project identity, team association, Team repo availability, and publish readiness before delegating to the existing publish pipeline. Do not create a parallel `team push` command.

**Tech Stack:** Python 3.10+, existing SyberMem core/CLI modules, Markdown Team publication pipeline

---

### Task 1: Add a Team publish bootstrap orchestrator in core

**Files:**
- Create: `packages/core/sybermem_core/publish_bootstrap.py`
- Modify: `packages/core/sybermem_core/project.py`
- Modify: `packages/core/sybermem_core/team.py`

- [ ] **Step 1: Add a Team repo validity checker to `team.py`**

Append to `packages/core/sybermem_core/team.py`:

```python

def is_valid_team_repo(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists() and (path / "team.yaml").is_file()
```

- [ ] **Step 2: Add a project-initialization probe to `project.py`**

Append to `packages/core/sybermem_core/project.py`:

```python

def is_sybermem_project(root: Path) -> bool:
    return (root / ".sybermem").is_dir()
```

- [ ] **Step 3: Create `publish_bootstrap.py`**

Create `packages/core/sybermem_core/publish_bootstrap.py`:

```python
from __future__ import annotations

from pathlib import Path

from .project import resolve_project_root, ensure_project_yaml, is_sybermem_project, read_team_from_project_yaml
from .registry import register_project
from .team import init_team_repo, is_valid_team_repo
from .publish import publish_status


def bootstrap_publish_status(team_path: Path | None = None) -> dict[str, object]:
    root = resolve_project_root()
    if root is None:
        raise ValueError(
            "Current directory is not initialized for SyberMem. "
            "Run `/sybermem-init-project` first so the project can be published to Team memory."
        )

    if not is_sybermem_project(root):
        raise ValueError(
            "Current project has no `.sybermem/` directory. "
            "Run `/sybermem-init-project` first so the project can be published to Team memory."
        )

    status, project_id, slug = ensure_project_yaml(root)
    if status == "created":
        register_project(project_id, slug, root)

    saved_team = read_team_from_project_yaml(root)
    if team_path is None and saved_team.get("team_path"):
        team_path = Path(saved_team["team_path"])

    if team_path is None:
        raise ValueError(
            "No Team association found for this project. "
            "Run `sybermem publish status --team-path <path>` once to set it, "
            "or initialize a Team repo with `sybermem team init`."
        )

    team_root = team_path.resolve()
    if not team_root.exists():
        raise ValueError(
            f"Team repo path does not exist: {team_root}. "
            "Initialize it first with `sybermem team init` or provide a valid existing Team repo path."
        )

    if not is_valid_team_repo(team_root):
        raise ValueError(
            f"Path exists but is not a valid Team repo: {team_root}. "
            "A valid Team repo needs both `.git/` and `team.yaml`."
        )

    return publish_status(team_root)
```

- [ ] **Step 4: Verify the new module imports cleanly**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "from sybermem_core.publish_bootstrap import bootstrap_publish_status; print('publish_bootstrap.py OK')"
```

Expected: `publish_bootstrap.py OK`

- [ ] **Step 5: Commit**

```bash
git add packages/core/sybermem_core/team.py packages/core/sybermem_core/project.py packages/core/sybermem_core/publish_bootstrap.py
git commit -m "feat: add Team publish bootstrap orchestrator"
```

---

### Task 2: Wire the bootstrap flow into `sybermem publish status`

**Files:**
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Add the import**

Add:

```python
from sybermem_core.publish_bootstrap import bootstrap_publish_status
```

- [ ] **Step 2: Route `cmd_publish_status()` through the bootstrap layer**

Replace:

```python
        tp = Path(args.team_path) if args.team_path else None
        payload = publish_status(tp)
```

with:

```python
        tp = Path(args.team_path) if args.team_path else None
        payload = bootstrap_publish_status(tp)
```

- [ ] **Step 3: Improve error wording to stay goal-oriented**

Keep the existing exception print, but verify the surfaced error text now talks about completing publish rather than missing low-level primitives.

- [ ] **Step 4: Verify the CLI command still works**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --format json
```

Expected:
- If current project already has a Team association, publish succeeds.
- If not, the error should clearly say how to complete the Team publish flow.

- [ ] **Step 5: Commit**

```bash
git add packages/cli/sybermem_cli/main.py
git commit -m "feat: route publish status through Team bootstrap flow"
```

---

### Task 3: Dogfood bootstrap behavior across the main branches

**Files:**
- No repo-file changes required by default

- [ ] **Step 1: Happy path — current project with remembered Team association**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --format json
```

Expected: publish succeeds and still pushes to the real Team repo.

- [ ] **Step 2: First-time Teamspark-style path with explicit Team repo**

From `D:/teamspark`, run:

```bash
$env:PYTHONPATH = 'D:/adr-project/packages/core;D:/adr-project/packages/cli'; python -m sybermem_cli.main publish status --team-path D:/team-memory --format json
```

Expected: publish succeeds and writes/updates the Team association in `D:/teamspark/.sybermem/project.yaml`.

- [ ] **Step 3: Missing Team association without `--team-path` should fail clearly**

Use a local temp/synthetic project config or remove the `team:` block temporarily in a controlled local copy to confirm the error says:
- no Team association found
- run publish once with `--team-path`
- or initialize Team repo first

Do not mutate the real project irreversibly.

- [ ] **Step 4: Invalid Team repo path should fail clearly**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --team-path D:/not-a-team-repo --format json
```

Expected: a clear Team repo path error, not a low-level stack trace.

- [ ] **Step 5: No commit needed** (verification only)

---

### Task 4: Update docs to explain that `publish status` is the single Team publication entrypoint

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/superpowers/specs/2026-07-02-sybermem-team-push-bootstrap-flow-design.md` (only if wording drifted)

- [ ] **Step 1: Add a note to `README.md`**

Add under the Team MVP bullets or nearby explanatory text:

```markdown
> `sybermem publish status` 是 Team 发布的唯一入口。不要再记多个 team push / bootstrap 命令；系统会在 publish 流程中自动补齐低风险前置条件，并在高影响动作前提示你确认。
```

- [ ] **Step 2: Add the matching note to `README.en.md`**

```markdown
> `sybermem publish status` is the single Team publication entrypoint. You do not need separate team-push/bootstrap commands; the system fills in low-risk prerequisites during publish and asks for confirmation before high-impact actions.
```

- [ ] **Step 3: Commit**

```bash
git add README.md README.en.md docs/superpowers/specs/2026-07-02-sybermem-team-push-bootstrap-flow-design.md
git commit -m "docs: describe publish status as the single Team bootstrap entrypoint"
```
