# SyberMem Team Digest History Publication Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Team publication pipeline so the Team repo retains the full phase digest and theme digest history for each project, while still publishing current status and management views.

**Architecture:** Build this into the existing `publish status` flow. After generating `project.md`, `current-status.md`, and `meta.json`, the publisher will incrementally sync `.sybermem/digests/` → `projects/<slug>/phase-digests/` and `.sybermem/theme-digests/` → `projects/<slug>/theme-digests/`, skipping unchanged files and preserving Team repo history. `meta.json` gains latest-digest references and counts.

**Tech Stack:** Python 3.10+, Markdown files, Team Git repo local filesystem

---

### Task 1: Add digest-history sync core logic to `publish.py`

**Files:**
- Modify: `packages/core/sybermem_core/publish.py`

- [ ] **Step 1: Add a file-sync helper above `publish_status()`**

In `packages/core/sybermem_core/publish.py`, add:

```python
def sync_markdown_history(src_dir: Path, dst_dir: Path) -> tuple[int, list[str]]:
    """Sync markdown files from src to dst.

    Returns:
      (count, paths) where count is number of files present in src,
      and paths are the files that were created/updated in dst.
    """
    if not src_dir.is_dir():
        return 0, []

    dst_dir.mkdir(parents=True, exist_ok=True)
    changed = []
    files = sorted(src_dir.glob("*.md"))
    for src in files:
        dst = dst_dir / src.name
        src_text = src.read_text(encoding="utf-8")
        dst_text = dst.read_text(encoding="utf-8") if dst.is_file() else None
        if dst_text != src_text:
            dst.write_text(src_text, encoding="utf-8")
            changed.append(str(dst).replace('\\', '/'))
    return len(files), changed
```

- [ ] **Step 2: Sync both digest history directories inside `publish_status()`**

After writing `project.md`, `current-status.md`, and `meta.json`, add:

```python
    phase_digests_dir = project_dir / "phase-digests"
    theme_digests_dir = project_dir / "theme-digests"

    phase_count, phase_changed = sync_markdown_history(root / ".sybermem" / "digests", phase_digests_dir)
    theme_count, theme_changed = sync_markdown_history(root / ".sybermem" / "theme-digests", theme_digests_dir)
```

- [ ] **Step 3: Upgrade `meta.json` output**

Replace the existing `meta_json.write_text(...)` payload with:

```python
    meta_json.write_text(_json.dumps({
        "status": "published",
        "team_id": team_id,
        "project_id": project_meta["project_id"],
        "slug": slug,
        "published_at": status["as_of"],
        "source_commit": source_commit,
        "source_phase_digest": phase_digest,
        "source_theme_digest": theme_digest,
        "latest_phase_digest": phase_changed[-1] if phase_changed else (str(phase_digests_dir / Path(phase_digest).name).replace('\\', '/') if phase_digest else ""),
        "latest_theme_digest": theme_changed[-1] if theme_changed else (str(theme_digests_dir / Path(theme_digest).name).replace('\\', '/') if theme_digest else ""),
        "phase_digest_count": phase_count,
        "theme_digest_count": theme_count,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Extend git add files list**

Replace the current Team repo add call:

```python
["git", "add", f"projects/{slug}/", "dashboards/"]
```

with the same path (keep it broad):

```python
["git", "add", f"projects/{slug}/", "dashboards/"]
```

No code change required if the existing broad add already stages the new digest-history directories. Just verify that it does.

- [ ] **Step 5: Verify the module still imports**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -c "from sybermem_core.publish import sync_markdown_history, publish_status; print('digest history sync OK')"
```

Expected: `digest history sync OK`

- [ ] **Step 6: Commit**

```bash
git add packages/core/sybermem_core/publish.py
git commit -m "feat: sync digest history into Team repo during publish"
```

---

### Task 2: Dogfood the full digest-history sync against the real Team repo

**Files:**
- No repo-file changes required by default

- [ ] **Step 1: Re-publish `sybermem`**

Run:
```bash
$env:PYTHONPATH = 'packages/core;packages/cli'; python -m sybermem_cli.main publish status --format json
```

Expected:
- publish succeeds using the remembered Team association
- Team repo receives digest-history directories

- [ ] **Step 2: Verify Team repo directories now exist**

Check for:
- `D:/team-memory/projects/sybermem/phase-digests/`
- `D:/team-memory/projects/sybermem/theme-digests/`

- [ ] **Step 3: Verify real digest files were copied**

Check that Team repo contains at least:
- one phase digest file under `phase-digests/`
- one theme digest file under `theme-digests/`

- [ ] **Step 4: Verify `meta.json` carries counts and latest paths**

`D:/team-memory/projects/sybermem/meta.json` should now include:
- `latest_phase_digest`
- `latest_theme_digest`
- `phase_digest_count`
- `theme_digest_count`

- [ ] **Step 5: Re-run publish to confirm idempotent sync**

Run the same publish command a second time.

Expected:
- no duplicate digest files
- no unwanted delete behavior
- Team repo still stays clean except for legitimate timestamp/content changes from the summary files

- [ ] **Step 6: No commit needed** (dogfood verification only)

---

### Task 3: Update docs to reflect the full digest-history layer

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/superpowers/specs/2026-07-02-sybermem-team-digest-history-publication-layer-design.md` (only if implementation wording differs)

- [ ] **Step 1: Add a Phase F bullet to `README.md`**

Add under the Team MVP bullets:

```markdown
- **Phase F**：发布时同步完整的 phase/theme digest 历史到 Team repo，形成“概括看 status、详细看 digest”的团队工程记忆层
```

- [ ] **Step 2: Add the matching bullet to `README.en.md`**

```markdown
- **Phase F**: publish now syncs the full phase/theme digest history into the Team repo, so you can skim status and then drill into digest history for detail
```

- [ ] **Step 3: Patch the spec only if the implemented field names differ**

If the final `meta.json` field names differ from the spec, align the spec wording. Otherwise leave it unchanged.

- [ ] **Step 4: Commit**

```bash
git add README.md README.en.md docs/superpowers/specs/2026-07-02-sybermem-team-digest-history-publication-layer-design.md
git commit -m "docs: note Team digest history publication layer"
```
