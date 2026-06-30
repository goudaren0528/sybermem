# SyberMem Hub MVP Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current cross-project search bridge into a real Hub MVP by strengthening the project registry, adding commit-based incremental indexing, expanding workspace search filters, and introducing `sybermem project status` plus `sybermem portfolio`.

**Architecture:** Build on the existing Phase 1 Core/CLI. `registry.py` becomes the authoritative Hub registry reader/writer. `index.py` gains a persisted `index-state.json` and per-project incremental rebuild based on git HEAD. `search.py` gains workspace filters. New `status.py` computes a project status snapshot from `.sybermem/analysis/phase-index.md` and recent records. New `portfolio.py` aggregates project statuses across the registry. CLI wiring in `main.py` exposes all of this.

**Tech Stack:** Python 3.10+, SQLite (stdlib `sqlite3`), YAML-style line parsing, JSON output

---

### Task 1: Strengthen the Hub registry schema and code

**Files:**
- Modify: `packages/core/sybermem_core/registry.py`
- Modify: `schemas/projects.yaml.example`

- [ ] **Step 1: Expand `projects.yaml.example` to the Phase 2 shape**

Replace the current `schemas/projects.yaml.example`:

```yaml
schema_version: 1
projects:
  - project_id: prj_01JEXAMPLE0001
    slug: example-project
    path: D:/workspace/example-project
    remote: github.com/example/example-project
    registered_at: 2026-06-30T10:00:00+08:00
```

with:

```yaml
schema_version: 1
projects:
  - project_id: prj_01JEXAMPLE0001
    slug: example-project
    name: example-project
    path: D:/workspace/example-project
    remote: github.com/example/example-project
    registered_at: 2026-06-30T10:00:00+08:00
    last_indexed_at: 2026-06-30T10:05:00+08:00
    last_seen_commit: abc1234
    status: active
```

- [ ] **Step 2: Replace `registry.py` with a richer registry implementation**

Replace the entire file `packages/core/sybermem_core/registry.py` with:

```python
from __future__ import annotations

from pathlib import Path
from .identity import git_remote, now_iso
from .storage import ensure_dir


RegistryEntry = dict[str, str]


def hub_registry_path() -> Path:
    return Path.home() / ".sybermem" / "projects.yaml"


def load_registry() -> list[RegistryEntry]:
    path = hub_registry_path()
    if not path.is_file():
        return []

    projects: list[RegistryEntry] = []
    current: RegistryEntry | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  - project_id:"):
            if current:
                projects.append(current)
            current = {"project_id": line.split(":", 1)[1].strip()}
        elif current is not None and line.startswith("    slug:"):
            current["slug"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    name:"):
            current["name"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    path:"):
            current["path"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    remote:"):
            current["remote"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    registered_at:"):
            current["registered_at"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    last_indexed_at:"):
            current["last_indexed_at"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    last_seen_commit:"):
            current["last_seen_commit"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("    status:"):
            current["status"] = line.split(":", 1)[1].strip()
    if current:
        projects.append(current)
    return projects


def save_registry(projects: list[RegistryEntry]) -> None:
    path = hub_registry_path()
    ensure_dir(path.parent)
    lines = ["schema_version: 1", "projects:"]
    for p in projects:
        lines.extend([
            f"  - project_id: {p['project_id']}",
            f"    slug: {p['slug']}",
            f"    name: {p.get('name', p['slug'])}",
            f"    path: {p['path']}",
            f"    remote: {p.get('remote', '')}",
            f"    registered_at: {p.get('registered_at', now_iso())}",
            f"    last_indexed_at: {p.get('last_indexed_at', '')}",
            f"    last_seen_commit: {p.get('last_seen_commit', '')}",
            f"    status: {p.get('status', 'active')}",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def register_project(project_id: str, slug: str, root: Path) -> None:
    projects = load_registry()
    updated = False
    for p in projects:
        if p.get("project_id") == project_id:
            p["slug"] = slug
            p["name"] = slug
            p["path"] = str(root).replace('\\', '/')
            p["remote"] = git_remote(root)
            p["status"] = "active"
            updated = True
            break
    if not updated:
        projects.append({
            "project_id": project_id,
            "slug": slug,
            "name": slug,
            "path": str(root).replace('\\', '/'),
            "remote": git_remote(root),
            "registered_at": now_iso(),
            "last_indexed_at": "",
            "last_seen_commit": "",
            "status": "active",
        })
    save_registry(projects)


def update_registry_index_metadata(project_id: str, *, commit: str, indexed_at: str, status: str) -> None:
    projects = load_registry()
    for p in projects:
        if p.get("project_id") == project_id:
            p["last_seen_commit"] = commit
            p["last_indexed_at"] = indexed_at
            p["status"] = status
            break
    save_registry(projects)
```

- [ ] **Step 3: Add a tiny registry regression check**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "
from pathlib import Path
from sybermem_core.registry import load_registry, save_registry, hub_registry_path
p = hub_registry_path()
projects = load_registry()
assert isinstance(projects, list)
print('registry entries:', len(projects))
save_registry(projects)
print('save_registry OK')
"
```

Expected: prints current registry entry count and `save_registry OK`.

- [ ] **Step 4: Commit**

```bash
git add packages/core/sybermem_core/registry.py schemas/projects.yaml.example
git commit -m "feat: strengthen Hub registry schema for Phase 2"
```

---

### Task 2: Add incremental indexing state and project-status metadata to the SQLite index

**Files:**
- Modify: `packages/core/sybermem_core/index.py`
- Modify: `packages/core/sybermem_core/records.py`
- Create: `packages/core/sybermem_core/status.py`

- [ ] **Step 1: Add record parsing fields in `records.py`**

Extend `parse_record_file()` to also extract:
- `superseded_by`
- `status` (reuse the existing `status:` frontmatter value if present)

Append these keys to the returned dict:

```python
        "status": status,
        "superseded_by": superseded_by,
```

Use this implementation for the extra parsing inside the loop:

```python
    status = ""
    superseded_by = ""
    for line in text.splitlines():
        if line.startswith("type:"):
            rtype = line.split(":", 1)[1].strip()
        elif line.startswith("date:"):
            date = line.split(":", 1)[1].strip()
        elif line.startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.startswith("status:"):
            status = line.split(":", 1)[1].strip()
        elif line.startswith("superseded_by:"):
            superseded_by = line.split(":", 1)[1].strip()
```

- [ ] **Step 2: Add `status.py` to compute a minimal project snapshot**

Create `packages/core/sybermem_core/status.py` with:

```python
from __future__ import annotations

from pathlib import Path
import re
from .records import parse_project_yaml, iter_record_files, parse_record_file
from .identity import now_iso


def project_status(root: Path) -> dict:
    meta = parse_project_yaml(root)
    phase_path = root / ".sybermem" / "analysis" / "phase-index.md"
    phase_id = ""
    phase_name = ""
    lifecycle = ""
    if phase_path.is_file():
        lines = phase_path.read_text(encoding="utf-8").splitlines()
        current_name = ""
        current_id = ""
        current_lifecycle = ""
        for line in lines:
            if line.startswith("### Phase: "):
                current_name = line.replace("### Phase: ", "").strip()
                current_id = ""
                current_lifecycle = ""
            elif line.startswith("- phase_id:"):
                current_id = line.split(":", 1)[1].strip()
            elif line.startswith("- lifecycle:"):
                current_lifecycle = line.split(":", 1)[1].strip()
                if current_lifecycle == "active":
                    phase_name = current_name
                    phase_id = current_id
                    lifecycle = current_lifecycle
        if not phase_name:
            # fallback: pick last phase heading
            text = phase_path.read_text(encoding="utf-8")
            phases = re.findall(r"### Phase: (.+)", text)
            if phases:
                phase_name = phases[-1]

    recent_records: list[str] = []
    all_records = [parse_record_file(p, meta.get("project_id", ""), meta.get("slug", root.name)) for p in iter_record_files(root)]
    all_records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    recent_records = [r["record_id"] for r in all_records[:3] if r.get("record_id")]
    open_bugs = [r["record_id"] for r in all_records if r.get("type") == "bug"]
    open_requirements = [r["record_id"] for r in all_records if r.get("type") == "requirement"]

    return {
        "project_id": meta.get("project_id", ""),
        "slug": meta.get("slug", root.name),
        "as_of": now_iso(),
        "phase": {
            "id": phase_id,
            "name": phase_name,
            "lifecycle": lifecycle or "active",
        },
        "recent_records": recent_records,
        "open_bugs": open_bugs,
        "open_requirements": open_requirements,
        "next": [],
    }
```

- [ ] **Step 3: Replace `index.py` with incremental rebuild behavior**

Replace the current `packages/core/sybermem_core/index.py` with a version that:
1. Adds `index-state.json` path
2. Extends the `projects` table with `status`, `last_seen_commit`, `last_indexed_at`
3. Extends the `records` table with `status`, `superseded_by`
4. On each project, compares current git HEAD with registry `last_seen_commit`
5. Skips unchanged projects
6. Deletes + rebuilds rows only for changed projects
7. Updates registry metadata via `update_registry_index_metadata()`

Use this exact top-level structure:

```python
from __future__ import annotations

from pathlib import Path
import json
import sqlite3
import subprocess

from .storage import ensure_dir
from .records import parse_project_yaml, iter_record_files, parse_record_file
from .registry import load_registry, update_registry_index_metadata
from .identity import now_iso


def index_db_path() -> Path:
    return Path.home() / ".sybermem" / "index" / "sybermem.db"


def index_state_path() -> Path:
    return Path.home() / ".sybermem" / "index" / "index-state.json"


def current_head(root: Path) -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""
```

Schema changes:

```sql
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    slug TEXT,
    name TEXT,
    path TEXT,
    remote TEXT,
    status TEXT,
    last_seen_commit TEXT,
    last_indexed_at TEXT
);

CREATE TABLE records (
    project_id TEXT,
    slug TEXT,
    record_id TEXT,
    type TEXT,
    title TEXT,
    content TEXT,
    topics TEXT,
    path TEXT,
    created_at TEXT,
    status TEXT,
    superseded_by TEXT
);
```

Inside `rebuild_index()`:
- For each project, compute `head = current_head(root)`
- If `head` exists and equals registry `last_seen_commit`, skip the project and leave counts unchanged
- Else:
  - `DELETE FROM records WHERE project_id = ?`
  - `DELETE FROM projects WHERE project_id = ?`
  - rebuild rows for that project
  - call `update_registry_index_metadata(project_id, commit=head, indexed_at=now_iso(), status='active')`

Write `index-state.json` at the end with a minimal payload:

```json
{
  "schema_version": 1,
  "last_built_at": "...",
  "projects_indexed": 3,
  "records_indexed": 42
}
```

- [ ] **Step 4: Verify incremental behavior**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main index build --format json
```
Expected: JSON with at least `projects` and `records`. Then run it a second time immediately; expect the counts to remain stable and no errors.

- [ ] **Step 5: Commit**

```bash
git add packages/core/sybermem_core/records.py packages/core/sybermem_core/status.py packages/core/sybermem_core/index.py
git commit -m "feat: add incremental Hub indexing and project status snapshot support"
```

---

### Task 3: Add richer workspace search filters and wire `project status` / `portfolio` into the CLI

**Files:**
- Modify: `packages/core/sybermem_core/search.py`
- Create: `packages/core/sybermem_core/portfolio.py`
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Extend `search.py` filters**

Replace `search_workspace()` in `packages/core/sybermem_core/search.py` with:

```python
def search_workspace(query: str, *, project: str | None = None, type_: str | None = None, project_status: str | None = None) -> list[dict[str, str]]:
    db = index_db_path()
    if not db.is_file():
        raise FileNotFoundError("workspace index not built; run `sybermem index build`")
    conn = sqlite3.connect(db)
    q = f'%{query}%'
    sql = """
        SELECT r.project_id, r.slug, r.record_id, r.type, r.title, r.path, r.created_at
        FROM records r
        JOIN projects p ON p.project_id = r.project_id
        WHERE (r.title LIKE ? OR r.content LIKE ? OR r.record_id LIKE ? OR r.topics LIKE ?)
    """
    params: list[str] = [q, q, q, q]
    if project:
        sql += " AND r.slug = ?"
        params.append(project)
    if type_:
        sql += " AND r.type = ?"
        params.append(type_)
    if project_status:
        sql += " AND p.status = ?"
        params.append(project_status)
    sql += " ORDER BY r.slug, r.created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [
        {
            "project_id": r[0],
            "slug": r[1],
            "record_id": r[2],
            "type": r[3],
            "title": r[4],
            "path": r[5],
            "created_at": r[6],
            "score": 1.0,
        }
        for r in rows
    ]
```

- [ ] **Step 2: Create `portfolio.py`**

```python
from __future__ import annotations

from pathlib import Path
from .registry import load_registry
from .status import project_status


def build_portfolio() -> dict:
    projects = []
    for entry in load_registry():
        path = Path(entry["path"])
        if not path.exists():
            projects.append({
                "project_id": entry["project_id"],
                "slug": entry["slug"],
                "status": "missing",
                "phase": "",
            })
            continue
        if (path / ".sybermem" / "INDEX.md").is_file():
            status = project_status(path)
            projects.append({
                "project_id": entry["project_id"],
                "slug": entry["slug"],
                "status": entry.get("status", "active"),
                "phase": status["phase"]["id"] or status["phase"]["name"],
            })
    return {"projects": projects}
```

- [ ] **Step 3: Extend `main.py` with `search` filters, `project status`, and `portfolio`**

In `packages/cli/sybermem_cli/main.py`:

1. Add imports:
```python
from pathlib import Path
from sybermem_core.status import project_status
from sybermem_core.portfolio import build_portfolio
```

2. Replace `cmd_search()` with a version that passes filters:

```python
def cmd_search(args: argparse.Namespace) -> int:
    if args.scope == "workspace":
        try:
            results = search_workspace(args.query, project=args.project, type_=args.type, project_status=args.project_status)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        results = search_project(args.query)

    payload = {
        "query": args.query,
        "scope": args.scope,
        "filters": {
            "project": args.project,
            "type": args.type,
            "project_status": args.project_status,
        },
        "results": results,
    }
```

(Keep the rest of the text/json output behavior the same.)

3. Add `cmd_project_status()`:

```python
def cmd_project_status(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    payload = project_status(root)
    if args.format == "json":
        print(dump_json(payload))
    else:
        phase = payload["phase"]
        print(f"[{payload['slug']}] {phase['id'] or phase['name']}")
    return 0
```

4. Add `cmd_portfolio()`:

```python
def cmd_portfolio(args: argparse.Namespace) -> int:
    payload = build_portfolio()
    if args.format == "json":
        print(dump_json(payload))
    else:
        for p in payload["projects"]:
            print(f"- {p['slug']} → {p['status']} {p['phase']}")
    return 0
```

5. Add parser wiring:

```python
    status_cmd = project_sub.add_parser("status")
    status_cmd.add_argument("--format", choices=["text", "json"], default="text")
    status_cmd.set_defaults(func=cmd_project_status)

    search.add_argument("--project")
    search.add_argument("--type")
    search.add_argument("--project-status")

    portfolio = sub.add_parser("portfolio")
    portfolio.add_argument("--format", choices=["text", "json"], default="text")
    portfolio.set_defaults(func=cmd_portfolio)
```

- [ ] **Step 4: Verify Hub MVP CLI**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main project status --format json
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main portfolio --format json
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main search hooks --scope workspace --project sybermem --type change --project-status active --format json
```

Expected:
- `project status` returns JSON with `project_id`, `slug`, `phase`, `recent_records`
- `portfolio` returns JSON with at least one project entry (`sybermem`)
- filtered workspace search still returns `change-*` records from the `sybermem` project only

- [ ] **Step 5: Commit**

```bash
git add packages/core/sybermem_core/search.py packages/core/sybermem_core/portfolio.py packages/cli/sybermem_cli/main.py
git commit -m "feat: add Hub project status, portfolio, and filtered workspace search"
```

---

### Task 4: Sync plugin tree and refresh the search skill docs to match Hub MVP

**Files:**
- Modify: `packages/claude-skills/sybermem-search/SKILL.md`
- Modify: `skills/` (generated by sync)

- [ ] **Step 1: Update `sybermem-search` Skill for the richer workspace path**

In `packages/claude-skills/sybermem-search/SKILL.md`, in the `When --scope workspace is specified:` subsection, replace:

```markdown
   - Prefer running `sybermem search <query> --scope workspace --format json`.
   - If the CLI reports that the workspace index is missing, tell the user to run `sybermem index build` first.
   - Use the returned JSON as the source of truth, then explain or group the results for the user.
```

with:

```markdown
   - Prefer running `sybermem search <query> --scope workspace --format json`.
   - Optional filters may be added: `--project <slug>`, `--type <change|decision|requirement|bug>`, `--project-status <active|missing|stale>`.
   - If the CLI reports that the workspace index is missing, tell the user to run `sybermem index build` first.
   - Use the returned JSON as the source of truth, then explain or group the results for the user.
```

- [ ] **Step 2: Sync plugin tree**

Run: `python scripts/sync-plugin-skills.py`
Expected: exits 0.

- [ ] **Step 3: Verify plugin copy updated**

Run: `python -c "
for f in ['packages/claude-skills/sybermem-search/SKILL.md', 'skills/sybermem-search/SKILL.md']:
    t = open(f, encoding='utf-8').read()
    assert '--project <slug>' in t
    assert '--project-status <active|missing|stale>' in t
    print(f, 'OK')
"`
Expected: both OK.

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-search/SKILL.md skills/
git commit -m "docs: extend workspace search skill docs for Hub MVP filters"
```
