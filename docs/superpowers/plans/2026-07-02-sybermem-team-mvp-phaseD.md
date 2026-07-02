# SyberMem Team MVP Phase D — Onboarding Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Team init first-push, make projects remember their Team association, and let `publish status` auto-read the default team path from `project.yaml`.

**Architecture:** Patch 5 existing files: `team.py` for init improvements, `identity.py` + `project.py` for project.yaml team field, `publish.py` for default team resolution + writeback, `main.py` for optional `--team-path`. Then update `check_project_health.py` for Team awareness.

**Tech Stack:** Python 3.10+, Git CLI, YAML line-based parsing

---

### Task 1: Fix `team init` first-push flow

**Files:**
- Modify: `packages/core/sybermem_core/team.py`

- [ ] **Step 1: Add `git branch -M main` after `git init`**

In `init_team_repo()`, after:

```python
subprocess.run(["git", "init"], cwd=path, check=True)
```

Add:

```python
subprocess.run(["git", "branch", "-M", "main"], cwd=path, check=False)
```

- [ ] **Step 2: Add initial commit + push after skeleton creation**

At the end of `init_team_repo()`, after writing `team.yaml` and before the `return`, add:

```python
    # Initial commit and push for new repos
    if status == "created":
        subprocess.run(["git", "add", "."], cwd=path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init: team repo skeleton"],
            cwd=path, check=True,
        )
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=path, capture_output=True, text=True, check=False,
        )
        if push_result.returncode != 0:
            import sys
            print(f"Warning: initial push failed. Check that the remote repo exists and is accessible.", file=sys.stderr)
```

- [ ] **Step 3: Verify team init on a fresh temp directory**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "
from sybermem_core.team import init_team_repo
from pathlib import Path
import tempfile, shutil
tmp = Path(tempfile.mkdtemp()) / 'test-team'
try:
    r = init_team_repo(tmp, 'test_team', 'Test', 'https://github.com/example/nonexistent.git')
    print(r)
    import subprocess
    branch = subprocess.run(['git', 'branch', '--show-current'], cwd=tmp, capture_output=True, text=True).stdout.strip()
    print(f'branch: {branch}')
    log = subprocess.run(['git', 'log', '--oneline'], cwd=tmp, capture_output=True, text=True).stdout.strip()
    print(f'log: {log}')
    assert branch == 'main'
    assert 'init: team repo skeleton' in log
    print('team init fix OK')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
"
```

Expected: `branch: main`, log contains initial commit, `team init fix OK`.

- [ ] **Step 4: Commit**

```bash
git add packages/core/sybermem_core/team.py
git commit -m "fix: team init uses main branch with initial commit and push attempt"
```

---

### Task 2: Add `team` field to `project.yaml` and teach `publish status` to use it

**Files:**
- Modify: `packages/core/sybermem_core/project.py`
- Modify: `packages/core/sybermem_core/publish.py`
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Add a helper to read/write team fields in `project.py`**

Append to `packages/core/sybermem_core/project.py`:

```python

def read_team_from_project_yaml(root: Path) -> dict[str, str]:
    yaml_path = root / ".sybermem" / "project.yaml"
    if not yaml_path.is_file():
        return {}
    team_id = ""
    team_path = ""
    in_team = False
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        if line.rstrip() == "team:":
            in_team = True
            continue
        if in_team and line.startswith("  team_id:"):
            team_id = line.split(":", 1)[1].strip()
        elif in_team and line.startswith("  team_path:"):
            team_path = line.split(":", 1)[1].strip()
        elif not line.startswith(" ") and not line.startswith("\t"):
            in_team = False
    return {"team_id": team_id, "team_path": team_path}


def write_team_to_project_yaml(root: Path, team_id: str, team_path: str) -> None:
    yaml_path = root / ".sybermem" / "project.yaml"
    if not yaml_path.is_file():
        return
    text = yaml_path.read_text(encoding="utf-8")

    # Remove existing team block if present
    lines = text.splitlines()
    new_lines = []
    skip = False
    for line in lines:
        if line.rstrip() == "team:":
            skip = True
            continue
        if skip and (line.startswith("  ") or line.startswith("\t")):
            continue
        skip = False
        new_lines.append(line)

    # Append team block
    new_lines.append("team:")
    new_lines.append(f"  team_id: {team_id}")
    new_lines.append(f"  team_path: {team_path}")

    yaml_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
```

- [ ] **Step 2: Teach `publish_status()` to resolve team path from project.yaml and write back**

In `packages/core/sybermem_core/publish.py`, add import:

```python
from .project import resolve_project_root, read_team_from_project_yaml, write_team_to_project_yaml
```

Replace the first line of `publish_status()`:

```python
def publish_status(team_path: Path | None = None) -> dict[str, object]:
    root = resolve_project_root()
    if root is None:
        raise ValueError("No SyberMem project root found.")

    # Resolve team path: explicit arg > project.yaml > error
    if team_path is None:
        saved = read_team_from_project_yaml(root)
        if saved.get("team_path"):
            team_path = Path(saved["team_path"])
        else:
            raise ValueError(
                "No --team-path provided and no team association found in project.yaml. "
                "Run `sybermem publish status --team-path <path>` to set it, "
                "or `sybermem team init` to create a Team repo first."
            )

    team_root = team_path.resolve()
```

And at the end, before the `return`, add the writeback:

```python
    # Persist team association in project.yaml
    write_team_to_project_yaml(root, team_id, str(team_root).replace('\\', '/'))
```

Also update the existing import line to remove the duplicate `resolve_project_root`:

```python
from .project import resolve_project_root, read_team_from_project_yaml, write_team_to_project_yaml
```

(Remove the old `from .project import resolve_project_root` line.)

- [ ] **Step 3: Make `--team-path` optional in CLI**

In `packages/cli/sybermem_cli/main.py`, change:

```python
    publish_status_cmd.add_argument("--team-path", required=True)
```

to:

```python
    publish_status_cmd.add_argument("--team-path", default=None)
```

And update `cmd_publish_status` to pass `None` when not provided:

```python
def cmd_publish_status(args: argparse.Namespace) -> int:
    try:
        tp = Path(args.team_path) if args.team_path else None
        payload = publish_status(tp)
    except Exception as exc:
```

- [ ] **Step 4: Verify the full flow**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --team-path D:/team-memory --format json
```

Expected: `pushed: true` and `project.yaml` now contains `team:` block.

Then verify default resolution:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --format json
```

Expected: same result without `--team-path` (reads from `project.yaml`).

- [ ] **Step 5: Commit**

```bash
git add packages/core/sybermem_core/project.py packages/core/sybermem_core/publish.py packages/cli/sybermem_cli/main.py
git commit -m "feat: persist team association in project.yaml and auto-resolve team path"
```

---

### Task 3: Update `check_project_health.py` with Team awareness

**Files:**
- Modify: `.sybermem/hooks/check_project_health.py`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`

- [ ] **Step 1: Add Team status check to the health script**

In the health check script, after the existing checks and before the final JSON output, add a `team` block:

```python
    # Team association check
    team_info = {"has_team_link": False, "team_path": "", "team_path_accessible": False}
    yaml_path = root / ".sybermem" / "project.yaml"
    if yaml_path.is_file():
        in_team = False
        for line in yaml_path.read_text(encoding="utf-8").splitlines():
            if line.rstrip() == "team:":
                in_team = True
                continue
            if in_team and line.startswith("  team_path:"):
                tp = line.split(":", 1)[1].strip()
                if tp:
                    team_info["has_team_link"] = True
                    team_info["team_path"] = tp
                    team_info["team_path_accessible"] = Path(tp).is_dir()
            if in_team and not line.startswith(" "):
                in_team = False
```

Include `"team": team_info` in the final JSON output dict.

- [ ] **Step 2: Copy the updated script to both locations**

Ensure both `.sybermem/hooks/check_project_health.py` and `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py` have the same content.

- [ ] **Step 3: Verify**

Run:
```bash
python .sybermem/hooks/check_project_health.py
```

Expected: JSON output includes `"team": {"has_team_link": true, "team_path": "D:/team-memory", "team_path_accessible": true}`.

- [ ] **Step 4: Commit**

```bash
git add .sybermem/hooks/check_project_health.py packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py
git commit -m "feat: add Team awareness to project health check"
```

---

### Task 4: Dogfood the full improved flow and update docs

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Verify end-to-end: publish without --team-path**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --format json
```

Expected: succeeds, reads team_path from project.yaml, auto-commit + push to remote.

- [ ] **Step 2: Update README Team MVP notes**

Add a Phase D bullet to both READMEs:

Chinese:
```markdown
- **Phase D**：`publish status` 自动记住团队关联，无需每次传 `--team-path`；`team init` 自动首次提交并推送
```

English:
```markdown
- **Phase D**: `publish status` remembers the team association automatically — no need to pass `--team-path` every time; `team init` auto-commits and pushes on first run
```

- [ ] **Step 3: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: note Team MVP Phase D onboarding polish improvements"
```
