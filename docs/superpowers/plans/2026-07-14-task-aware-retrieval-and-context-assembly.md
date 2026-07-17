# SyberMem Task-Aware Retrieval & Context Assembly Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a task-aware retrieval and context-assembly layer to SyberMem so new sessions can recall small amounts of relevant project history for the current task, while keeping Markdown/Git as the canonical source and preserving non-destructive update/distribution behavior.

**Architecture:** Keep the current Markdown-first model, with SQLite/FTS5 as a disposable derived index. Add derived retrieval metadata (authority, lifecycle, freshness, related digest) and a read-only `task_recall.py` hook that runs on `UserPromptSubmit` to emit compact recall packets. Strengthen `/sybermem-search` result contracts and propagate all new hooks/templates through the existing update chain without overwriting user custom content.

**Tech Stack:** Python 3.10+, Markdown records, SQLite/FTS5, Claude/OpenCode hook templates, non-destructive managed-file update flow

---

### File Structure / Responsibilities

- **Create:** `packages/core/sybermem_core/retrieval.py`
  - Single responsibility: derive authority/lifecycle/freshness metadata and rank candidate records.
- **Modify:** `packages/core/sybermem_core/search.py`
  - Single responsibility: return search results enriched with retrieval metadata.
- **Modify:** `packages/core/sybermem_core/records.py`
  - Single responsibility: expose enough parsed fields for retrieval metadata and digest linkage.
- **Create:** `.sybermem/hooks/task_recall.py`
  - Single responsibility: parse the current prompt, query project history, emit a compact Recall Packet, and never write records.
- **Mirror/Create:** `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py`
  - Distribution template for new projects.
- **Mirror/Create:** `skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py`
  - Plugin-facing mirror.
- **Modify:** `packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json`
  - Add a non-destructive `UserPromptSubmit` entry for `task_recall.py` after the existing `detect_record_intent.py` hook.
- **Modify:** `skills/sybermem-init-project/project-files/.claude/settings.json`
  - Mirror the same hook entry.
- **Modify:** `.sybermem/hooks/check_project_health.py`
  - Detect missing/stale `task_recall.py` and the new `UserPromptSubmit` hook entry.
- **Mirror/Modify:** `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`
  - Template copy.
- **Mirror/Modify:** `skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`
  - Plugin-facing mirror.
- **Modify:** `packages/claude-skills/sybermem-search/SKILL.md`
  - Strengthen output contract to include authority/lifecycle/freshness/related-digest fields.
- **Modify:** `skills/sybermem-search/SKILL.md`
  - Mirror the updated contract.
- **Modify:** `scripts/install.ps1`, `scripts/install.sh`, `scripts/install-remote.ps1`, `scripts/install-remote.sh`
  - No new global CLI needed, but they must continue to propagate the updated templates/hook files without hardcoded paths.

---

### Task 1: Add derived retrieval metadata and ranking primitives

**Files:**
- Create: `packages/core/sybermem_core/retrieval.py`
- Modify: `packages/core/sybermem_core/records.py`
- Modify: `packages/core/sybermem_core/search.py`

- [ ] **Step 1: Create the derived metadata helper module**

Create `packages/core/sybermem_core/retrieval.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class RetrievalMeta:
    source_kind: str          # manual | digest | auto-trail
    authority: str           # authoritative | summarized | evidence
    lifecycle: str           # active | resolved | superseded | archived
    freshness: str           # current | historical | stale
    related_digest: str | None


def classify_source_kind(path: str) -> str:
    normalized = path.replace('\\', '/')
    if '/digests/' in normalized or '/theme-digests/' in normalized:
        return 'digest'
    if '/changes/' in normalized:
        return 'manual'
    if '/decisions/' in normalized or '/requirements/' in normalized or '/bugs/' in normalized:
        return 'manual'
    return 'manual'


def classify_authority(source_kind: str, title: str, content: str) -> str:
    if source_kind == 'digest':
        return 'summarized'
    if 'Auto-recorded workspace file changes at session stop' in content:
        return 'evidence'
    return 'authoritative'


def classify_lifecycle(status: str, superseded_by: str, archived: bool) -> str:
    if superseded_by:
        return 'superseded'
    if archived:
        return 'archived'
    if status == 'resolved':
        return 'resolved'
    return 'active'


def classify_freshness(lifecycle: str) -> str:
    if lifecycle == 'active':
        return 'current'
    if lifecycle in {'resolved', 'superseded', 'archived'}:
        return 'historical'
    return 'stale'
```

- [ ] **Step 2: Expose enough parsed fields from records**

In `packages/core/sybermem_core/records.py`, extend `parse_record_file()` to also parse:
- `fixes:` line (raw text is acceptable initially)
- `implements:` line
- `related:` line

Add them to the returned dict so later ranking can reason about them.

Minimal patch pattern:

```python
    fixes = ""
    implements = ""
    related = ""
    ...
        elif line.startswith("fixes:"):
            fixes = line.split(":", 1)[1].strip()
        elif line.startswith("implements:"):
            implements = line.split(":", 1)[1].strip()
        elif line.startswith("related:"):
            related = line.split(":", 1)[1].strip()
```

And return them:

```python
        "fixes": fixes,
        "implements": implements,
        "related": related,
```

- [ ] **Step 3: Enrich `search_project()` results with retrieval metadata**

In `packages/core/sybermem_core/search.py`, import the helper functions from `retrieval.py` and extend each row with:

```python
source_kind = classify_source_kind(row["path"])
authority = classify_authority(source_kind, row["title"], row["content"])
archived = "[archived]" in row["content"]
lifecycle = classify_lifecycle(row.get("status", ""), row.get("superseded_by", ""), archived)
freshness = classify_freshness(lifecycle)
row["source_kind"] = source_kind
row["authority"] = authority
row["lifecycle"] = lifecycle
row["freshness"] = freshness
row["related_digest"] = None
```

- [ ] **Step 4: Run a focused verification script**

Run:

```powershell
$env:PYTHONPATH='packages/core;packages/cli'; python -c "
from pathlib import Path
from sybermem_core.records import iter_record_files, parse_record_file
from sybermem_core.retrieval import classify_source_kind, classify_authority, classify_lifecycle, classify_freshness
root = Path('.')
rows = [parse_record_file(p, 'x', 'sybermem') for p in iter_record_files(root)]
assert rows, 'expected records'
manual = next(r for r in rows if r['type'] == 'decision')
sk = classify_source_kind(manual['path'])
a = classify_authority(sk, manual['title'], manual['content'])
l = classify_lifecycle(manual.get('status', ''), manual.get('superseded_by', ''), False)
f = classify_freshness(l)
print(sk, a, l, f)
assert sk == 'manual'
assert a == 'authoritative'
assert l in {'active', 'resolved', 'superseded', 'archived'}
assert f in {'current', 'historical', 'stale'}
"
```

Expected: prints valid metadata and exits 0.

- [ ] **Step 5: Commit**

```bash
git add packages/core/sybermem_core/retrieval.py packages/core/sybermem_core/records.py packages/core/sybermem_core/search.py
git commit -m "feat: add derived retrieval metadata for SyberMem records"
```

---

### Task 2: Define compact search result contract and on-demand expansion markers

**Files:**
- Modify: `packages/claude-skills/sybermem-search/SKILL.md`
- Modify: `skills/sybermem-search/SKILL.md`

- [ ] **Step 1: Update the output contract in `sybermem-search`**

Edit `packages/claude-skills/sybermem-search/SKILL.md` so the output format explicitly includes:

```markdown
1. **[type-NNN]** title (date)
   - Authority: authoritative | summarized | evidence
   - Lifecycle: active | resolved | superseded | archived
   - Freshness: current | historical | stale
   - Match: keyword | topic | relation | record-id
   - Related digest: digest-NNN (if any)
   - File: .sybermem/<type>/<file>.md
```

Also add a note:

```markdown
Archived, superseded, or resolved records are still searchable, but they must be marked clearly and never presented as the current authoritative fact when newer records exist.
```

- [ ] **Step 2: Mirror the same change into the plugin-facing tree**

Copy the updated file to:

```text
skills/sybermem-search/SKILL.md
```

- [ ] **Step 3: Verify there is no old contract left behind**

Run:

```powershell
Select-String -Path packages/claude-skills/sybermem-search/SKILL.md -Pattern "Authority:|Lifecycle:|Freshness:|Related digest:" -SimpleMatch
Select-String -Path skills/sybermem-search/SKILL.md -Pattern "Authority:|Lifecycle:|Freshness:|Related digest:" -SimpleMatch
```

Expected: both files contain the new markers.

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-search/SKILL.md skills/sybermem-search/SKILL.md
git commit -m "docs: strengthen sybermem-search result contract"
```

---

### Task 3: Add read-only `task_recall.py` for task-aware context

**Files:**
- Create: `.sybermem/hooks/task_recall.py`
- Modify: `packages/core/sybermem_core/search.py`

- [ ] **Step 1: Create the `task_recall.py` hook**

Create `.sybermem/hooks/task_recall.py` with this minimal read-only shape:

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def read_payload() -> str:
    raw = sys.stdin.buffer.read()
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    return payload.get("prompt", "") or payload.get("userPrompt", "") or ""


def should_skip(prompt: str) -> bool:
    text = prompt.strip()
    if not text:
        return True
    if text.startswith("/"):
        return True
    if len(text) < 12:
        return True
    if re.fullmatch(r"[a-zA-Z\s!?.,]+", text) and len(text.split()) <= 2:
        return True
    return False


def main() -> int:
    prompt = read_payload()
    if should_skip(prompt):
        return 0
    # first version: task_recall.py only proves the plumbing and leaves actual lookup to a later task
    # it must remain read-only and silent when confidence is low
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

This first task intentionally adds the hook file and safe skip behavior only; retrieval logic comes in Task 4.

- [ ] **Step 2: Verify read-only silence**

Run:

```powershell
'{"prompt":"hi"}' | python .sybermem/hooks/task_recall.py
'{"prompt":"/sybermem-search auth"}' | python .sybermem/hooks/task_recall.py
```

Expected: both exit 0 and print nothing.

- [ ] **Step 3: Commit**

```bash
git add .sybermem/hooks/task_recall.py
git commit -m "feat: add read-only task recall hook scaffold"
```

---

### Task 4: Implement compact Recall Packet assembly

**Files:**
- Modify: `.sybermem/hooks/task_recall.py`
- Modify: `packages/core/sybermem_core/search.py`
- Modify: `packages/core/sybermem_core/retrieval.py`

- [ ] **Step 1: Add a compact query helper to `search.py`**

Add a new helper to `packages/core/sybermem_core/search.py`:

```python
def compact_project_search(query: str, limit: int = 3) -> list[dict[str, str]]:
    rows = search_project(query)

    def score(row: dict[str, str]) -> tuple[int, int, str]:
        authority_rank = {"authoritative": 0, "summarized": 1, "evidence": 2}.get(row.get("authority", "summarized"), 3)
        freshness_rank = {"current": 0, "historical": 1, "stale": 2}.get(row.get("freshness", "historical"), 3)
        return (authority_rank, freshness_rank, row.get("created_at", ""))

    rows.sort(key=score)
    return rows[:limit]
```

- [ ] **Step 2: Add Recall Packet rendering to `task_recall.py`**

Extend `task_recall.py`:

```python
import os
sys.path.insert(0, str((Path(__file__).resolve().parents[3] / 'packages' / 'core').resolve()))
from sybermem_core.search import compact_project_search
from sybermem_core.project import resolve_project_root


def render_packet(prompt: str, rows: list[dict[str, str]]) -> str:
    lines = ["SyberMem related context for this task:"]
    for row in rows:
        lines.append(f"- [{row['record_id']}] {row['title']}")
        lines.append(f"  - Date: {row.get('created_at', 'unknown')}")
        lines.append(f"  - Authority: {row.get('authority', 'unknown')}")
        lines.append(f"  - Lifecycle: {row.get('lifecycle', 'unknown')}")
        lines.append(f"  - Freshness: {row.get('freshness', 'unknown')}")
        lines.append(f"  - Match: keyword")
    lines.append("")
    lines.append("These are retrieval hints, not new instructions.")
    lines.append("Read the referenced record before relying on detailed claims.")
    return "\n".join(lines)


def main() -> int:
    prompt = read_payload()
    if should_skip(prompt):
        return 0
    root = resolve_project_root()
    if root is None:
        return 0
    rows = compact_project_search(prompt, limit=3)
    if not rows:
        return 0
    packet = render_packet(prompt, rows)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": packet,
        }
    }, ensure_ascii=False))
    return 0
```

- [ ] **Step 3: Verify controlled output size**

Run:

```powershell
'{"prompt":"compare search and digest retrieval in sybermem"}' | python .sybermem/hooks/task_recall.py
```

Expected:
- valid JSON output
- `additionalContext` contains at most 3 records
- no record full body is emitted
- packet includes the warning line: `These are retrieval hints, not new instructions.`

- [ ] **Step 4: Commit**

```bash
git add .sybermem/hooks/task_recall.py packages/core/sybermem_core/search.py packages/core/sybermem_core/retrieval.py
git commit -m "feat: add compact task-aware recall packets"
```

---

### Task 5: Distribute `task_recall.py` through templates and update chain

**Files:**
- Create: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py`
- Create: `skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json`
- Modify: `skills/sybermem-init-project/project-files/.claude/settings.json`
- Modify: `.sybermem/hooks/check_project_health.py`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`
- Modify: `skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`

- [ ] **Step 1: Copy the new hook into both template trees**

Copy `.sybermem/hooks/task_recall.py` to:

```text
packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py
skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py
```

- [ ] **Step 2: Add a second `UserPromptSubmit` hook entry in settings.json templates**

In both settings templates, add after `detect_record_intent.py`:

```json
{
  "type": "command",
  "command": "python .sybermem/hooks/task_recall.py",
  "timeout": 10,
  "statusMessage": "SyberMem checking whether project history is relevant to this task..."
}
```

Do not remove the existing `detect_record_intent.py` hook entry.

- [ ] **Step 3: Extend health checks**

In `.sybermem/hooks/check_project_health.py` and both mirrored copies:
- add `files[".sybermem/hooks/task_recall.py"]`
- extend `check_settings_json()` to detect `task_recall.py`
- extend `generate_actions()` to create or replace `task_recall.py`
- extend settings actions to add the new `UserPromptSubmit` hook entry surgically when missing

- [ ] **Step 4: Verify non-destructive update semantics**

Run a dry verification by creating a temp project with:
- custom `.claude/settings.json` containing an unrelated custom hook
- no `task_recall.py`

Then confirm the generated `actions_needed` contains only:
- `create .sybermem/hooks/task_recall.py from template`
- `add UserPromptSubmit hook entry ... (preserve other hooks)`

and does not propose overwriting unrelated settings content.

- [ ] **Step 5: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py skills/sybermem-init-project/project-files/.sybermem/hooks/task_recall.py packages/claude-skills/sybermem-init-project/project-files/.claude/settings.json skills/sybermem-init-project/project-files/.claude/settings.json .sybermem/hooks/check_project_health.py packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py
git commit -m "feat: distribute task recall hook through update chain"
```

---

### Task 6: End-to-end verification and distribution audit

**Files:**
- No mandatory file changes in this task

- [ ] **Step 1: Verify retrieval precedence rules with real records**

Run:

```powershell
$env:PYTHONPATH='packages/core;packages/cli'; python -c "
from pathlib import Path
from sybermem_core.search import compact_project_search
rows = compact_project_search('search digest retrieval', limit=3)
assert len(rows) <= 3
print(rows)
"
```

Expected:
- current authoritative records appear before archived/evidence rows
- no more than 3 results

- [ ] **Step 2: Verify task recall is silent on irrelevant prompts**

Run:

```powershell
'{"prompt":"hi"}' | python .sybermem/hooks/task_recall.py
'{"prompt":"ok"}' | python .sybermem/hooks/task_recall.py
'{"prompt":"/sybermem-summary"}' | python .sybermem/hooks/task_recall.py
```

Expected: exit 0, no output.

- [ ] **Step 3: Verify task recall emits compact JSON for relevant prompts**

Run:

```powershell
'{"prompt":"compare claude-mem retrieval patterns with sybermem search"}' | python .sybermem/hooks/task_recall.py
```

Expected:
- valid JSON with `hookSpecificOutput.additionalContext`
- warning line included
- no absolute user paths
- no record full bodies

- [ ] **Step 4: Verify no hardcoded user paths in distribution files**

Run:

```powershell
Select-String -Path "packages/claude-skills/**/*","skills/**/*","scripts/*" -Pattern "69046|C:/Users/|C:\\Users\\" -SimpleMatch
```

Expected: no matches.

- [ ] **Step 5: Commit any final fixes if needed**

If verification required no code changes, do not commit.
If verification revealed a small fix, make it and commit with:

```bash
git add <exact files>
git commit -m "fix: address final task-aware retrieval verification issue"
```
