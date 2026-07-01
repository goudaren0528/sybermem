# SyberMem Hub MVP Phase 2.1 — Portfolio Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `sybermem portfolio` from a just-connected command into a genuinely useful Hub homepage by polishing its text output and validating it against real registered projects.

**Architecture:** The command is already wired into `main.py`. This phase refines `portfolio.py` and `main.py` text rendering so output is grouped by `active / stale / missing` instead of a flat list. JSON output stays stable. Then we run a real dogfood cycle against `sybermem` and `teamspark`.

**Tech Stack:** Python 3.10+, Markdown skill docs (optional note only)

---

### Task 1: Improve `portfolio.py` data shape for grouped text output

**Files:**
- Modify: `packages/core/sybermem_core/portfolio.py`

- [ ] **Step 1: Replace `build_portfolio()` with a richer structure**

Replace the current file with:

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
                "phase": {"id": "", "name": "", "lifecycle": ""},
                "reason": "path not accessible",
            })
            continue

        if (path / ".sybermem" / "INDEX.md").is_file():
            status = project_status(path)
            projects.append({
                "project_id": entry["project_id"],
                "slug": entry["slug"],
                "status": entry.get("status", "active"),
                "phase": status["phase"],
                "reason": "",
            })

    return {"projects": projects}
```

- [ ] **Step 2: Verify JSON shape stays valid**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "
from sybermem_core.portfolio import build_portfolio
payload = build_portfolio()
assert 'projects' in payload
assert isinstance(payload['projects'], list)
for p in payload['projects']:
    assert 'status' in p and 'phase' in p and 'reason' in p
print('portfolio.py OK')
"
```

Expected: `portfolio.py OK`

- [ ] **Step 3: Commit**

```bash
git add packages/core/sybermem_core/portfolio.py
git commit -m "feat: enrich portfolio payload with phase object and reason field"
```

---

### Task 2: Polish `sybermem portfolio` text output in `main.py`

**Files:**
- Modify: `packages/cli/sybermem_cli/main.py`

- [ ] **Step 1: Replace the current flat text renderer**

Find:

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

Replace with:

```python
def cmd_portfolio(args: argparse.Namespace) -> int:
    payload = build_portfolio()
    if args.format == "json":
        print(dump_json(payload))
    else:
        buckets = {"active": [], "stale": [], "missing": []}
        for p in payload["projects"]:
            buckets.setdefault(p["status"], []).append(p)

        for status_key in ["active", "stale", "missing"]:
            items = buckets.get(status_key, [])
            if not items:
                continue
            print(f"[{status_key}]")
            for p in items:
                if status_key == "missing":
                    print(f"- {p['slug']} → {p['reason']}")
                else:
                    phase = p["phase"]
                    phase_label = phase.get("id") or phase.get("name") or "(no phase)"
                    phase_name = phase.get("name", "")
                    if phase_name and phase.get("id"):
                        print(f"- {p['slug']} → {phase_label} {phase_name}")
                    else:
                        print(f"- {p['slug']} → {phase_label}")
            print("")
    return 0
```

- [ ] **Step 2: Verify the command now groups output**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main portfolio
```

Expected:
- Output contains an `[active]` header
- Output lists `sybermem` and `teamspark` under `[active]`
- No `invalid choice: 'portfolio'` error

- [ ] **Step 3: Commit**

```bash
git add packages/cli/sybermem_cli/main.py
git commit -m "feat: group portfolio text output by project status"
```

---

### Task 3: Real Hub MVP dogfood validation with `teamspark`

**Files:**
- No code changes

- [ ] **Step 1: Rebuild the workspace index after the code changes**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main index build --format json
```

Expected: JSON with `projects` / `records`.

- [ ] **Step 2: Run the portfolio command**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main portfolio --format json
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main portfolio
```

Expected:
- JSON includes both `sybermem` and `teamspark`
- Text output has an `[active]` section listing both projects

- [ ] **Step 3: Run one real workspace search against `teamspark`**

Use a term likely to exist in teamspark's records (choose one based on its existing `.sybermem/` content — for example a domain topic, product term, or recurring requirement term). Run:

```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main search <real-teamspark-term> --scope workspace --project teamspark --format json
```

Expected:
- JSON results contain only `slug = teamspark`
- At least one matching record returned

- [ ] **Step 4: No commit needed** (verification only)
