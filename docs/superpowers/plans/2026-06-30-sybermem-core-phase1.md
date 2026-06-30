# SyberMem Core Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the first real SyberMem Core/CLI foundation by introducing `packages/core/` and `packages/cli/`, then shipping a minimal but working cross-project pipeline: `sybermem project init`, `sybermem index build`, and `sybermem search`.

**Architecture:** Build a small Python core package (`sybermem_core`) and a thin CLI package (`sybermem_cli`). The core owns identity, project registry, record scanning, SQLite index creation, and search. Existing skills remain in place, but `/sybermem-search` will gain the option to delegate workspace search to the CLI in a later integration task.

**Tech Stack:** Python 3.10+, SQLite (stdlib `sqlite3`), YAML written/read via simple line-based parsing (no external dependency in v1)

---

### Task 1: Scaffold `packages/core/` and `packages/cli/`

**Files:**
- Create: `packages/core/pyproject.toml`
- Create: `packages/core/sybermem_core/__init__.py`
- Create: `packages/core/sybermem_core/identity.py`
- Create: `packages/core/sybermem_core/project.py`
- Create: `packages/core/sybermem_core/registry.py`
- Create: `packages/core/sybermem_core/records.py`
- Create: `packages/core/sybermem_core/index.py`
- Create: `packages/core/sybermem_core/search.py`
- Create: `packages/core/sybermem_core/storage.py`
- Create: `packages/core/sybermem_core/formats.py`
- Create: `packages/cli/pyproject.toml`
- Create: `packages/cli/sybermem_cli/__init__.py`
- Create: `packages/cli/sybermem_cli/main.py`
- Create: `schemas/project.yaml.example`
- Create: `schemas/projects.yaml.example`
- Create: `schemas/search-result.schema.json`

- [ ] **Step 1: Create `packages/core/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "sybermem-core"
version = "0.1.0"
description = "Core identity, registry, indexing, and search logic for SyberMem"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
where = ["."]
include = ["sybermem_core*"]
```

- [ ] **Step 2: Create `packages/cli/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "sybermem-cli"
version = "0.1.0"
description = "CLI for SyberMem core operations"
requires-python = ">=3.10"
dependencies = []

[project.scripts]
sybermem = "sybermem_cli.main:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["sybermem_cli*"]
```

- [ ] **Step 3: Create package markers**

Create these 4 files with minimal content:

`packages/core/sybermem_core/__init__.py`
```python
__all__ = []
```

`packages/cli/sybermem_cli/__init__.py`
```python
__all__ = []
```

`packages/core/sybermem_core/formats.py`
```python
from __future__ import annotations

import json
from typing import Any


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
```

`packages/core/sybermem_core/storage.py`
```python
from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Create schema examples**

`schemas/project.yaml.example`
```yaml
schema_version: 1
project_id: prj_01JEXAMPLE0001
slug: example-project
name: example-project
repository:
  remote: github.com/example/example-project
  default_branch: main
created_at: 2026-06-30T10:00:00+08:00
```

`schemas/projects.yaml.example`
```yaml
schema_version: 1
projects:
  - project_id: prj_01JEXAMPLE0001
    slug: example-project
    path: D:/workspace/example-project
    remote: github.com/example/example-project
    registered_at: 2026-06-30T10:00:00+08:00
```

`schemas/search-result.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "query": { "type": "string" },
    "scope": { "type": "string", "enum": ["project", "workspace"] },
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "project_id": { "type": "string" },
          "slug": { "type": "string" },
          "record_id": { "type": "string" },
          "type": { "type": "string" },
          "title": { "type": "string" },
          "path": { "type": "string" },
          "score": { "type": "number" }
        },
        "required": ["project_id", "slug", "record_id", "type", "title", "path"]
      }
    }
  },
  "required": ["query", "scope", "results"]
}
```

- [ ] **Step 5: Commit**

```bash
git add packages/core/ packages/cli/ schemas/
git commit -m "feat: scaffold sybermem core and CLI packages"
```

---

### Task 2: Implement `sybermem project init`

**Files:**
- Modify: `packages/core/sybermem_core/identity.py`
- Modify: `packages/core/sybermem_core/project.py`
- Modify: `packages/core/sybermem_core/registry.py`
- Modify: `packages/cli/sybermem_cli/main.py`

Once Phase 1.5 is done, users and skills should invoke this as:

```bash
sybermem project init --register --format json
```

- [ ] **Step 1: Implement `identity.py`**

```python
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import uuid


def generate_project_id() -> str:
    return f"prj_{uuid.uuid4().hex[:16]}"


def derive_slug(root: Path) -> str:
    remote = git_remote(root)
    if remote:
        slug = remote.rstrip("/").split("/")[-1]
        if slug.endswith(".git"):
            slug = slug[:-4]
        return slug
    return root.name


def git_remote(root: Path) -> str:
    try:
        r = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def git_default_branch(root: Path) -> str:
    try:
        r = subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def now_iso() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat(timespec="seconds")


def render_project_yaml(project_id: str, slug: str, root: Path) -> str:
    return (
        f"schema_version: 1\n"
        f"project_id: {project_id}\n"
        f"slug: {slug}\n"
        f"name: {slug}\n"
        f"repository:\n"
        f"  remote: {git_remote(root)}\n"
        f"  default_branch: {git_default_branch(root)}\n"
        f"created_at: {now_iso()}\n"
    )
```

- [ ] **Step 2: Implement `project.py`**

```python
from __future__ import annotations

from pathlib import Path
from .identity import derive_slug, generate_project_id, render_project_yaml


def resolve_project_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / ".sybermem").is_dir() and (current / ".claude" / "settings.json").is_file():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def ensure_project_yaml(root: Path) -> tuple[str, str, str]:
    proj = root / ".sybermem" / "project.yaml"
    if proj.is_file():
        text = proj.read_text(encoding="utf-8")
        project_id = next((l.split(":",1)[1].strip() for l in text.splitlines() if l.startswith("project_id:")), "")
        slug = next((l.split(":",1)[1].strip() for l in text.splitlines() if l.startswith("slug:")), root.name)
        return ("existing", project_id, slug)
    project_id = generate_project_id()
    slug = derive_slug(root)
    proj.write_text(render_project_yaml(project_id, slug, root), encoding="utf-8")
    return ("created", project_id, slug)
```

- [ ] **Step 3: Implement `registry.py`**

```python
from __future__ import annotations

from pathlib import Path
from .identity import git_remote, now_iso
from .storage import ensure_dir


def hub_registry_path() -> Path:
    return Path.home() / ".sybermem" / "projects.yaml"


def register_project(project_id: str, slug: str, root: Path) -> None:
    path = hub_registry_path()
    ensure_dir(path.parent)
    projects: list[dict[str, str]] = []
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
        current: dict[str, str] | None = None
        for line in lines:
            if line.startswith("  - project_id:"):
                if current:
                    projects.append(current)
                current = {"project_id": line.split(":",1)[1].strip()}
            elif current is not None and line.startswith("    slug:"):
                current["slug"] = line.split(":",1)[1].strip()
            elif current is not None and line.startswith("    path:"):
                current["path"] = line.split(":",1)[1].strip()
            elif current is not None and line.startswith("    remote:"):
                current["remote"] = line.split(":",1)[1].strip()
            elif current is not None and line.startswith("    registered_at:"):
                current["registered_at"] = line.split(":",1)[1].strip()
        if current:
            projects.append(current)

    updated = False
    for p in projects:
        if p.get("project_id") == project_id:
            p["path"] = str(root).replace('\\', '/')
            p["slug"] = slug
            p["remote"] = git_remote(root)
            updated = True
            break
    if not updated:
        projects.append({
            "project_id": project_id,
            "slug": slug,
            "path": str(root).replace('\\', '/'),
            "remote": git_remote(root),
            "registered_at": now_iso(),
        })

    lines = ["schema_version: 1", "projects:"]
    for p in projects:
        lines.extend([
            f"  - project_id: {p['project_id']}",
            f"    slug: {p['slug']}",
            f"    path: {p['path']}",
            f"    remote: {p.get('remote', '')}",
            f"    registered_at: {p.get('registered_at', now_iso())}",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Implement `main.py` with `project init` command**

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sybermem_core.formats import dump_json
from sybermem_core.project import resolve_project_root, ensure_project_yaml
from sybermem_core.registry import register_project
from sybermem_core.identity import git_remote


def cmd_project_init(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found. Run /sybermem-init-project first.", file=sys.stderr)
        return 1
    status, project_id, slug = ensure_project_yaml(root)
    if args.register:
        register_project(project_id, slug, root)
    payload = {
        "status": status,
        "project_id": project_id,
        "slug": slug,
        "path": str(root).replace('\\', '/'),
        "remote": git_remote(root),
    }
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"{status}: {slug} ({project_id}) @ {payload['path']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="sybermem")
    sub = parser.add_subparsers(dest="command", required=True)

    project = sub.add_parser("project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    init = project_sub.add_parser("init")
    init.add_argument("--register", action="store_true")
    init.add_argument("--format", choices=["text", "json"], default="text")
    init.set_defaults(func=cmd_project_init)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Verify command works**

Run:
```bash
python -m sybermem_cli.main project init --register --format json
```
Expected: JSON with `status`, `project_id`, `slug`, `path`, `remote`.

- [ ] **Step 6: Commit**

```bash
git add packages/core/sybermem_core/identity.py packages/core/sybermem_core/project.py packages/core/sybermem_core/registry.py packages/cli/sybermem_cli/main.py
git commit -m "feat: add sybermem project init command and hub registry support"
```

---

### Task 3: Implement `sybermem index build`

**Files:**
- Modify: `packages/core/sybermem_core/records.py`
- Modify: `packages/core/sybermem_core/index.py`
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Implement `records.py` scanning helpers**

```python
from __future__ import annotations

from pathlib import Path
import re


def parse_project_yaml(root: Path) -> dict[str, str]:
    proj = root / ".sybermem" / "project.yaml"
    if not proj.is_file():
        return {}
    out: dict[str, str] = {}
    for line in proj.read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.startswith("  "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def iter_record_files(root: Path) -> list[Path]:
    syb = root / ".sybermem"
    files: list[Path] = []
    for sub in ["changes", "decisions", "requirements", "bugs"]:
        d = syb / sub
        if d.is_dir():
            files.extend(sorted(d.glob("*.md")))
    return files


def parse_record_file(path: Path, project_id: str, slug: str) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    title = ""
    rtype = ""
    date = ""
    topics: list[str] = []
    record_id = ""
    for line in text.splitlines():
        if line.startswith("type:"):
            rtype = line.split(":", 1)[1].strip()
        elif line.startswith("date:"):
            date = line.split(":", 1)[1].strip()
        elif line.startswith("title:"):
            title = line.split(":", 1)[1].strip()
    # infer record_id from filename
    m = re.match(r"\d{4}-\d{2}-\d{2}-(\d{3})-", path.name)
    if m and rtype:
        record_id = f"{rtype}-{m.group(1)}"
    # topics from Key Conclusion tags are not in the record file; leave blank for now
    return {
        "project_id": project_id,
        "slug": slug,
        "record_id": record_id,
        "type": rtype,
        "title": title,
        "content": text,
        "topics": ",".join(topics),
        "path": str(path).replace('\\', '/'),
        "created_at": date,
    }
```

- [ ] **Step 2: Implement `index.py`**

```python
from __future__ import annotations

from pathlib import Path
import sqlite3

from .storage import ensure_dir
from .records import parse_project_yaml, iter_record_files, parse_record_file
from .registry import hub_registry_path


def index_db_path() -> Path:
    return Path.home() / ".sybermem" / "index" / "sybermem.db"


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS records;
        DROP TABLE IF EXISTS projects;
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            slug TEXT,
            path TEXT,
            remote TEXT
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
            created_at TEXT
        );
        CREATE VIRTUAL TABLE records_fts USING fts5(record_id, title, content, topics, slug, content='');
        """
    )


def load_registry() -> list[dict[str, str]]:
    path = hub_registry_path()
    if not path.is_file():
        return []
    projects: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  - project_id:"):
            if current:
                projects.append(current)
            current = {"project_id": line.split(":",1)[1].strip()}
        elif current is not None and line.startswith("    slug:"):
            current["slug"] = line.split(":",1)[1].strip()
        elif current is not None and line.startswith("    path:"):
            current["path"] = line.split(":",1)[1].strip()
        elif current is not None and line.startswith("    remote:"):
            current["remote"] = line.split(":",1)[1].strip()
    if current:
        projects.append(current)
    return projects


def rebuild_index(project_filter: str | None = None) -> dict[str, int]:
    db = index_db_path()
    ensure_dir(db.parent)
    conn = sqlite3.connect(db)
    init_schema(conn)

    projects = load_registry()
    indexed_projects = 0
    indexed_records = 0

    for p in projects:
        if project_filter and p.get("slug") != project_filter:
            continue
        root = Path(p["path"])
        if not (root / ".sybermem" / "INDEX.md").is_file():
            continue
        conn.execute(
            "INSERT INTO projects(project_id, slug, path, remote) VALUES (?, ?, ?, ?)",
            (p["project_id"], p.get("slug", ""), p["path"], p.get("remote", ""))
        )
        proj_meta = parse_project_yaml(root)
        slug = proj_meta.get("slug") or p.get("slug", "")
        for rf in iter_record_files(root):
            row = parse_record_file(rf, p["project_id"], slug)
            conn.execute(
                "INSERT INTO records(project_id, slug, record_id, type, title, content, topics, path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["project_id"], row["slug"], row["record_id"], row["type"], row["title"], row["content"], row["topics"], row["path"], row["created_at"])
            )
            conn.execute(
                "INSERT INTO records_fts(rowid, record_id, title, content, topics, slug) VALUES (last_insert_rowid(), ?, ?, ?, ?, ?)",
                (row["record_id"], row["title"], row["content"], row["topics"], row["slug"])
            )
            indexed_records += 1
        indexed_projects += 1

    conn.commit()
    conn.close()
    return {"projects": indexed_projects, "records": indexed_records}
```

- [ ] **Step 3: Extend CLI with `index build`**

In `packages/cli/sybermem_cli/main.py`, add imports:

```python
from sybermem_core.index import rebuild_index
```

Add command handler:

```python
def cmd_index_build(args: argparse.Namespace) -> int:
    result = rebuild_index(args.project)
    if args.format == "json":
        print(dump_json(result))
    else:
        print(f"indexed {result['projects']} projects, {result['records']} records")
    return 0
```

Add parser wiring in `main()`:

```python
    index = sub.add_parser("index")
    index_sub = index.add_subparsers(dest="index_command", required=True)
    build = index_sub.add_parser("build")
    build.add_argument("--project")
    build.add_argument("--format", choices=["text", "json"], default="text")
    build.set_defaults(func=cmd_index_build)
```

- [ ] **Step 4: Verify**

Run:
```bash
python -m sybermem_cli.main index build --format json
```
Expected: JSON like `{"projects": 1, "records": <n>}` and `~/.sybermem/index/sybermem.db` exists.

- [ ] **Step 5: Commit**

```bash
git add packages/core/sybermem_core/records.py packages/core/sybermem_core/index.py packages/cli/sybermem_cli/main.py
git commit -m "feat: add sybermem index build command and SQLite workspace index"
```

---

### Task 4: Implement `sybermem search`

**Files:**
- Modify: `packages/core/sybermem_core/search.py`
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Implement `search.py`**

```python
from __future__ import annotations

from pathlib import Path
import sqlite3

from .index import index_db_path
from .project import resolve_project_root
from .records import iter_record_files, parse_project_yaml, parse_record_file


def search_project(query: str) -> list[dict[str, str]]:
    root = resolve_project_root()
    if root is None:
        return []
    meta = parse_project_yaml(root)
    project_id = meta.get("project_id", "")
    slug = meta.get("slug", root.name)
    results: list[dict[str, str]] = []
    q = query.lower()
    for rf in iter_record_files(root):
        row = parse_record_file(rf, project_id, slug)
        haystack = f"{row['record_id']} {row['title']} {row['content']} {row['topics']}".lower()
        if q in haystack:
            row['score'] = 1.0
            results.append(row)
    return results


def search_workspace(query: str) -> list[dict[str, str]]:
    db = index_db_path()
    if not db.is_file():
        raise FileNotFoundError("workspace index not built; run `sybermem index build`")
    conn = sqlite3.connect(db)
    q = f'%{query}%'
    rows = conn.execute(
        "SELECT project_id, slug, record_id, type, title, path, created_at FROM records WHERE title LIKE ? OR content LIKE ? OR record_id LIKE ? OR topics LIKE ? ORDER BY slug, created_at DESC",
        (q, q, q, q)
    ).fetchall()
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

- [ ] **Step 2: Extend CLI with `search` command**

In `packages/cli/sybermem_cli/main.py`, add imports:

```python
from sybermem_core.search import search_project, search_workspace
```

Add command handler:

```python
def cmd_search(args: argparse.Namespace) -> int:
    if args.scope == "workspace":
        try:
            results = search_workspace(args.query)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        results = search_project(args.query)

    payload = {"query": args.query, "scope": args.scope, "results": results}
    if args.format == "json":
        print(dump_json(payload))
    else:
        current_project = None
        for row in results:
            if row["slug"] != current_project:
                current_project = row["slug"]
                print(f"[{current_project}]")
            print(f"- {row['record_id']} {row['title']}")
        if not results:
            print("No matches.")
    return 0
```

Add parser wiring in `main()`:

```python
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--scope", choices=["project", "workspace"], default="project")
    search.add_argument("--format", choices=["text", "json"], default="text")
    search.set_defaults(func=cmd_search)
```

- [ ] **Step 3: Verify search end-to-end**

Run:
```bash
python -m sybermem_cli.main search hooks --scope workspace --format json
```
Expected: JSON result set containing at least the `sybermem` project with matching records (`change-003`, `change-005`, `bug-001`, `change-008`, etc.).

Also run:
```bash
python -m sybermem_cli.main search hooks --scope project
```
Expected: text output grouped under `[sybermem]`.

- [ ] **Step 4: Commit**

```bash
git add packages/core/sybermem_core/search.py packages/cli/sybermem_cli/main.py
git commit -m "feat: add sybermem search command with project and workspace scopes"
```

---

### Task 5: Wire the existing skill docs to the Phase 1 reality and verify

**Files:**
- Modify: `packages/claude-skills/sybermem-search/SKILL.md`
- Modify: `skills/` (generated by sync)

- [ ] **Step 1: Update `sybermem-search` skill to prefer the CLI for workspace scope**

In `packages/claude-skills/sybermem-search/SKILL.md`, in the `When --scope workspace is specified:` subsection, replace the current project-iteration bullets with:

```markdown
   **When `--scope workspace` is specified:**
   - Prefer running `sybermem search <query> --scope workspace --format json`.
   - If the CLI reports that the workspace index is missing, tell the user to run `sybermem index build` first.
   - Use the returned JSON as the source of truth, then explain or group the results for the user.
```

Leave project-scope behavior unchanged.

- [ ] **Step 2: Sync plugin tree**

Run: `python scripts/sync-plugin-skills.py`
Expected: exits 0.

- [ ] **Step 3: Verify plugin copy contains the CLI-preference text**

Run: `python -c "
for f in ['packages/claude-skills/sybermem-search/SKILL.md', 'skills/sybermem-search/SKILL.md']:
    t = open(f, encoding='utf-8').read()
    assert 'sybermem search <query> --scope workspace --format json' in t
    print(f, 'OK')
"`
Expected: both files OK.

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-search/SKILL.md skills/
git commit -m "docs: point workspace search skill path at the Phase 1 CLI"
```
