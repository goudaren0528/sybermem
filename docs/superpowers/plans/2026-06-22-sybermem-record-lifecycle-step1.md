# SyberMem Record Lifecycle Governance Step 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Key Conclusions Active/Archived split and Phase lifecycle field so SessionStart injects less noise and summary/digest know which phases are active vs completed.

**Architecture:** INDEX.md gets a new `## Archived Conclusions` section; SessionStart hook's regex stops before it; phase-index blocks get a `lifecycle` field; 6 skills get filtering logic updates. All changes are markdown structure + one Python regex tweak.

**Tech Stack:** Python 3.10+ (hooks), Markdown (skills + INDEX)

**Spec:** `docs/superpowers/specs/2026-06-22-sybermem-record-lifecycle-step1-design.md`

**Global Constraints:**
- `## Key Conclusions` stays the active section; `## Archived Conclusions` is the new archive section.
- SessionStart hook must NOT inject archived conclusions.
- Phase `lifecycle` field values: `active` (default), `completed`, `archived`. Missing field = `active`.
- No record file format changes. Archiving only moves INDEX.md conclusion lines.
- Zero new dependencies.
- Non-destructive: all existing projects without the new section/field continue to work unchanged.

---

### Task 1: Add Archived Conclusions section to INDEX.md (project + template)

**Files:**
- Modify: `.sybermem/INDEX.md`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md`

- [ ] **Step 1: Add Archived Conclusions to this project's INDEX.md**

In `.sybermem/INDEX.md`, find:

```markdown
<!-- add new conclusions here -->

---

## Stage Digests
```

Replace with:

```markdown
<!-- add new conclusions here -->

---

## Archived Conclusions

<!-- Not injected at session start; findable via /sybermem-search -->
<!-- Suffix each line with: [superseded by <id>] or [compressed in <id>] or [archived] -->
<!-- add new archived conclusions here -->

---

## Stage Digests
```

- [ ] **Step 2: Add Archived Conclusions to the init-project INDEX template**

In `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md`, find the same pattern (`<!-- add new conclusions here -->` followed by `---` followed by `## Stage Digests`) and make the same insertion.

- [ ] **Step 3: Verify**

Run: `python -c "for f in ['.sybermem/INDEX.md', 'packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md']: t=open(f,encoding='utf-8').read(); assert '## Archived Conclusions' in t; assert '<!-- add new archived conclusions here -->' in t; print(f, 'OK')"`
Expected: both files OK.

- [ ] **Step 4: Commit**

```bash
git add .sybermem/INDEX.md packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md
git commit -m "feat: add Archived Conclusions section to INDEX.md and init-project template"
```

---

### Task 2: Update SessionStart hook to stop before Archived Conclusions

**Files:**
- Modify: `.sybermem/hooks/session_start_context.py`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py`

- [ ] **Step 1: Update parse_conclusions regex in project hook**

In `.sybermem/hooks/session_start_context.py`, find:

```python
def parse_conclusions(index_text: str) -> list[str]:
    match = re.search(
        r"## Key Conclusions\s*\n([\s\S]*?)(?=\n---|\n## )", index_text
    )
```

The current regex `(?=\n---|\n## )` stops at any `---` or any `## `. This already works correctly because `## Archived Conclusions` starts with `## `, so the regex will stop before it. **No code change needed for the regex itself.**

However, verify this is true by running the hook and checking the output does not include archived lines. Since we haven't archived anything yet, we need to add a test archived line temporarily.

- [ ] **Step 2: Verify the regex boundary works**

Run: `python -c "
import re
text = '''## Key Conclusions
- [change-010] active conclusion (2026-06-22)
<!-- add new conclusions here -->

---

## Archived Conclusions
- [requirement-001] old conclusion (2026-05-08) [archived]
'''
match = re.search(r'## Key Conclusions\s*\n([\s\S]*?)(?=\n---|\n## )', text)
lines = [l.strip() for l in match.group(1).splitlines() if l.strip().startswith('- [')]
assert len(lines) == 1, f'Expected 1, got {len(lines)}: {lines}'
assert 'change-010' in lines[0]
assert 'requirement-001' not in str(lines)
print('OK: regex stops before Archived Conclusions')
"`
Expected: `OK: regex stops before Archived Conclusions`

- [ ] **Step 3: Copy the project hook to the template**

The hook files should stay in sync. Copy `.sybermem/hooks/session_start_context.py` to `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py`.

(Since no code change was needed, this is a no-op if files are already identical. Verify and skip if so.)

- [ ] **Step 4: Commit** (only if files changed)

```bash
git add .sybermem/hooks/session_start_context.py packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/session_start_context.py
git commit -m "verify: SessionStart hook regex already stops before Archived Conclusions"
```

If no files changed, skip the commit and note "no code change needed — regex boundary already works."

---

### Task 3: Update health check to detect Archived Conclusions section

**Files:**
- Modify: `.sybermem/hooks/check_project_health.py`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`

- [ ] **Step 1: Add archived conclusions detection to check_index_md**

In `.sybermem/hooks/check_project_health.py`, find the `check_index_md` function. After the line:

```python
    has_theme_digest_anchor = "<!-- add new theme digest records here -->" in content
```

Add:

```python
    has_archived_conclusions = "## Archived Conclusions" in content
    has_archived_anchor = "<!-- add new archived conclusions here -->" in content
```

Then update the `all_present` line to include the new checks:

Find:
```python
    all_present = has_conclusions and has_digest and has_records and has_topic_index and has_theme_digests and has_theme_digest_anchor
```

Replace with:
```python
    all_present = has_conclusions and has_digest and has_records and has_topic_index and has_theme_digests and has_theme_digest_anchor and has_archived_conclusions and has_archived_anchor
```

Add the new fields to the return dict, after the `has_theme_digest_anchor` line:

```python
        "has_archived_conclusions": has_archived_conclusions,
        "has_archived_anchor": has_archived_anchor,
```

- [ ] **Step 2: Add archived conclusions action to generate_actions**

In the same file, in `generate_actions`, find the INDEX.md stale section:

```python
    # INDEX.md — insert missing sections only
    idx = files.get(".sybermem/INDEX.md", {})
    if idx.get("status") == "stale":
```

After the existing theme digests action line, add:

```python
        if not idx.get("has_archived_conclusions") or not idx.get("has_archived_anchor"):
            actions.append("insert Archived Conclusions section into INDEX.md (preserve existing content)")
```

- [ ] **Step 3: Copy to template**

Copy the updated `.sybermem/hooks/check_project_health.py` to `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py`.

- [ ] **Step 4: Verify health check detects new section**

Run: `python .sybermem/hooks/check_project_health.py | python -c "import json,sys; r=json.load(sys.stdin); idx=r['files']['.sybermem/INDEX.md']; print('archived_conclusions:', idx.get('has_archived_conclusions')); print('archived_anchor:', idx.get('has_archived_anchor')); print('overall:', r['overall'])"`
Expected: `has_archived_conclusions: True`, `has_archived_anchor: True`, `overall: fresh`

- [ ] **Step 5: Commit**

```bash
git add .sybermem/hooks/check_project_health.py packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py
git commit -m "feat: detect Archived Conclusions section in health check"
```

---

### Task 4: Add lifecycle field to phase-index and update this project's phases

**Files:**
- Modify: `.sybermem/analysis/phase-index.md`
- Modify: `packages/claude-skills/sybermem-phase-analyze/SKILL.md`
- Modify: `packages/claude-skills/sybermem-phase-confirm/SKILL.md`

- [ ] **Step 1: Add lifecycle field to all confirmed phases in this project**

In `.sybermem/analysis/phase-index.md`, add `- lifecycle: completed` to phases 001-009 (all past work) and `- lifecycle: active` to phase-010 (current work). Insert the line after `- status: confirmed` in each block.

For phases 001-009, also add `- completed_at: 2026-06-22` after the lifecycle line.

For phase-010, do NOT add `completed_at` (it's still active).

Example for phase-001:
```markdown
### Phase: Global skill distribution and project refresh
- phase_id: phase-001
- source_candidate_id: candidate-phase-001
- status: confirmed
- lifecycle: completed
- completed_at: 2026-06-22
- covered_records:
```

Example for phase-010:
```markdown
### Phase: Search, relations, and theme digest
- phase_id: phase-010
- source_candidate_id: candidate-phase-010
- status: confirmed
- lifecycle: active
- covered_records: []
```

- [ ] **Step 2: Update phase-analyze SKILL.md — default lifecycle: active**

In `packages/claude-skills/sybermem-phase-analyze/SKILL.md`, find the canonical confirmed phase block shape (around line 74):

```md
### Phase: <phase_title>
- phase_id: phase-<NNN>
- source_candidate_id: candidate-phase-<NNN>
- status: confirmed
- covered_records:
```

Add `- lifecycle: active` after `- status: confirmed`:

```md
### Phase: <phase_title>
- phase_id: phase-<NNN>
- source_candidate_id: candidate-phase-<NNN>
- status: confirmed
- lifecycle: active
- covered_records:
```

- [ ] **Step 3: Update phase-confirm SKILL.md — support lifecycle changes**

In `packages/claude-skills/sybermem-phase-confirm/SKILL.md`, find the canonical confirmed phase block shape and add `- lifecycle: active` to it (same as above).

Then, after the existing Step 2 section ("Ask the user which candidate to act on"), add guidance for lifecycle changes:

Find the text after the confirmed phase block shape. After the closing ` ``` ` of the confirmed phase code block, add:

```markdown
**Lifecycle management:** Users can also change a confirmed phase's lifecycle:
- `lifecycle: active` — current work (default for new phases)
- `lifecycle: completed` — work is done; add `completed_at: YYYY-MM-DD`
- `lifecycle: archived` — digested and no longer active

When changing lifecycle to `completed`, always add the `completed_at` date field.
```

- [ ] **Step 4: Verify phase-index**

Run: `python -c "
t = open('.sybermem/analysis/phase-index.md', encoding='utf-8').read()
import re
phases = re.findall(r'### Phase:', t)
lifecycles = re.findall(r'- lifecycle: (active|completed|archived)', t)
assert len(phases) == 10, f'Expected 10 phases, got {len(phases)}'
assert len(lifecycles) == 10, f'Expected 10 lifecycle fields, got {len(lifecycles)}'
assert lifecycles.count('completed') == 9
assert lifecycles.count('active') == 1
print('OK: 9 completed + 1 active')
"`
Expected: `OK: 9 completed + 1 active`

- [ ] **Step 5: Commit**

```bash
git add .sybermem/analysis/phase-index.md packages/claude-skills/sybermem-phase-analyze/SKILL.md packages/claude-skills/sybermem-phase-confirm/SKILL.md
git commit -m "feat: add lifecycle field to phase-index and update analyze/confirm skills"
```

---

### Task 5: Update summary, digest, search, and record skills

**Files:**
- Modify: `packages/claude-skills/sybermem-summary/SKILL.md`
- Modify: `packages/claude-skills/sybermem-digest/SKILL.md`
- Modify: `packages/claude-skills/sybermem-search/SKILL.md`
- Modify: `packages/claude-skills/sybermem-record/SKILL.md`

- [ ] **Step 1: Update summary skill — default to lifecycle: active**

In `packages/claude-skills/sybermem-summary/SKILL.md`, find in the Flow section (around line 39):

```markdown
   - If phase-index exists with at least one confirmed phase → use the most recently active confirmed phase as the default summary target
```

Replace with:

```markdown
   - If phase-index exists with at least one confirmed phase → use the most recently active confirmed phase with `lifecycle: active` as the default summary target. If no phase has `lifecycle: active`, fall back to the most recent confirmed phase regardless of lifecycle. Phases missing a `lifecycle` field are treated as `active`.
```

- [ ] **Step 2: Update digest skill — prefer lifecycle: completed**

In `packages/claude-skills/sybermem-digest/SKILL.md`, find in the batch mode section (around line 58):

```markdown
When multiple confirmed phases exist and no explicit source records were provided, create a digest for **each** confirmed phase that does not already have an existing digest with the same source coverage. Process them in chronological order by phase coverage dates. Skip any phase whose raw source records are incomplete or missing.
```

Replace with:

```markdown
When multiple confirmed phases exist and no explicit source records were provided, create a digest for **each** confirmed phase that does not already have an existing digest with the same source coverage. Prefer phases with `lifecycle: completed` first, then `lifecycle: active` if no completed phases remain undigested. Skip phases with `lifecycle: archived` (they already have digests). Process in chronological order by phase coverage dates. Skip any phase whose raw source records are incomplete or missing. Phases missing a `lifecycle` field are treated as `active`.
```

- [ ] **Step 3: Update search skill — mark archived conclusions**

In `packages/claude-skills/sybermem-search/SKILL.md`, find in the Flow section, step 3 under free keyword:

```markdown
   - **free keyword** → Grep `## Key Conclusions` first, then Grep record bodies under `.sybermem/{changes,decisions,requirements,bugs}/`.
```

Replace with:

```markdown
   - **free keyword** → Grep `## Key Conclusions` first, then Grep `## Archived Conclusions`, then Grep record bodies under `.sybermem/{changes,decisions,requirements,bugs}/`. Results from `## Archived Conclusions` are marked with their archive reason (e.g. `[superseded by ...]`, `[archived]`).
```

- [ ] **Step 4: Update record skill — clarify active section**

In `packages/claude-skills/sybermem-record/SKILL.md`, find step 8 (around line 63):

```markdown
8. **Write back key conclusion** — insert a one-line core conclusion above `<!-- add new conclusions here -->` in `## Key Conclusions`.
```

Replace with:

```markdown
8. **Write back key conclusion** — insert a one-line core conclusion above `<!-- add new conclusions here -->` in `## Key Conclusions` (the active section). Never write new conclusions to `## Archived Conclusions`.
```

- [ ] **Step 5: Verify all four skills**

Run: `python -c "
checks = [
    ('packages/claude-skills/sybermem-summary/SKILL.md', 'lifecycle: active'),
    ('packages/claude-skills/sybermem-digest/SKILL.md', 'lifecycle: completed'),
    ('packages/claude-skills/sybermem-search/SKILL.md', 'Archived Conclusions'),
    ('packages/claude-skills/sybermem-record/SKILL.md', 'active section'),
]
for f, marker in checks:
    assert marker in open(f, encoding='utf-8').read(), f'{f} missing {marker}'
    print(f, 'OK')
"`
Expected: four OKs.

- [ ] **Step 6: Commit**

```bash
git add packages/claude-skills/sybermem-summary/SKILL.md packages/claude-skills/sybermem-digest/SKILL.md packages/claude-skills/sybermem-search/SKILL.md packages/claude-skills/sybermem-record/SKILL.md
git commit -m "feat: add lifecycle-aware filtering to summary, digest, search, and record skills"
```

---

### Task 6: Update init-project, sync plugin tree, and verify end-to-end

**Files:**
- Modify: `packages/claude-skills/sybermem-init-project/SKILL.md`
- Modify: `skills/` (generated by sync)

- [ ] **Step 1: Update init-project SKILL.md health check section**

In `packages/claude-skills/sybermem-init-project/SKILL.md`, find the existing capability check for theme-digest (the subsection about `## Theme Digests`). After it, add:

```markdown
For projects that already have `.sybermem/INDEX.md`, check whether the Archived Conclusions section is present:

- `## Archived Conclusions` in `.sybermem/INDEX.md`
- `<!-- add new archived conclusions here -->` anchor

If missing, insert the section between `## Key Conclusions` (after its closing `---`) and `## Stage Digests`. Do this idempotently.
```

- [ ] **Step 2: Sync plugin skills tree**

Run: `python scripts/sync-plugin-skills.py`
Expected: exits 0.

- [ ] **Step 3: Verify end-to-end**

Run: `python .sybermem/hooks/check_project_health.py | python -c "import json,sys; r=json.load(sys.stdin); print('overall:', r['overall']); print('actions:', r['actions_needed'])"`
Expected: `overall: fresh`, `actions: []`

Run: `python .sybermem/hooks/session_start_context.py | python -c "import json,sys; d=json.load(sys.stdin); ctx=d['hookSpecificOutput']['additionalContext']; assert 'Archived' not in ctx; print('OK: no archived conclusions in startup context')"`
Expected: `OK: no archived conclusions in startup context`

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/SKILL.md skills/
git commit -m "feat: add archived conclusions provisioning to init-project and sync plugin tree"
```
