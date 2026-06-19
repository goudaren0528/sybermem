# SyberMem Search & Relations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add retrieval (`/sybermem-search`) and knowledge-relations (`/sybermem-link` + record cross-references) capabilities to SyberMem, keeping it zero-dependency and pure-markdown.

**Architecture:** Two new AI-driven skills plus enhancements to the record skill and templates. Relations are stored forward-only in record frontmatter (`implements`/`fixes`/`related`); reverse navigation is computed at query time by grepping. Search is fully AI-executed via file-system tools — no scripts, no index files. The plugin `skills/` tree is regenerated from `packages/claude-skills/` via the existing sync script.

**Tech Stack:** Markdown (SKILL.md + templates), Python (existing sync script, no new scripts)

**Spec:** `docs/superpowers/specs/2026-06-19-sybermem-search-and-relations-design.md`

**Global Constraints:**
- Zero new dependencies. No database, no index service, no full-text engine.
- Relations are forward-only. `/sybermem-link` and record creation write the SOURCE record's frontmatter only; never the target's.
- Relation fields are optional. Existing records without them must keep working.
- Relation values are arrays of existing record IDs (e.g. `requirement-002`). IDs must be validated to exist before writing.
- Search is AI-driven (Grep/Read), not script-driven.
- New skills must be picked up by `scripts/sync-plugin-skills.py` (it auto-discovers all top-level dirs under `packages/claude-skills/`).

---

### Task 1: Create the /sybermem-search skill

The retrieval skill. AI-driven, follows the existing SyberMem SKILL.md structure (Announce, Core Invariant, HARD-GATE, Flow, Red Flags, Terminal State, Integration).

**Files:**
- Create: `packages/claude-skills/sybermem-search/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Create `packages/claude-skills/sybermem-search/SKILL.md` with this exact content:

```markdown
---
name: sybermem-search
description: Use when searching or querying SyberMem project records by keyword, topic, phase range, date range, or record ID, including finding which records reference a given record.
---

# sybermem-search Skill

**Announce at start:** "I'm using the sybermem-search skill to query project records."

AI-driven retrieval over SyberMem records. Searches Key Conclusions, Topic Index, phase coverage, and record bodies using file-system tools. Zero dependencies, no index files.

## Core Invariant

- **Search is read-only. It never creates, modifies, or deletes records.**

<HARD-GATE>
Do NOT write any file to disk. Search is non-persistent output only.
Do NOT fabricate records or relations that are not present on disk.
Do NOT report a record without verifying it exists with a file-system tool.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Query Syntax

| Query form | Meaning |
|---|---|
| `auth` | free keyword search |
| `#hooks` | search by topic tag |
| `phase-002..phase-004` | phase range |
| `2026-05-01..2026-06-15` | date range |
| `requirement-002` | record ID lookup, including reverse references |

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply directory resolution rules above. If `.sybermem/INDEX.md` does not exist, tell the user to run `/sybermem-init-project` and stop.
2. **Parse the query type** — classify the query as topic (`#tag`), phase range (`phaseN..phaseM`), date range (`date..date`), record ID (`type-NNN`), or free keyword.
3. **Run the matching retrieval path:**
   - **topic** → read `## Topic Index` in `.sybermem/INDEX.md`, collect the record IDs listed for that topic.
   - **phase range** → read `.sybermem/analysis/phase-index.md` coverage map, collect records covered by phases in the range.
   - **date range** → list record files whose `YYYY-MM-DD` filename prefix falls in the range.
   - **record ID** → locate that record, AND reverse-scan all records' `implements`/`fixes`/`related` frontmatter fields for the ID (see Reverse references below).
   - **free keyword** → Grep `## Key Conclusions` first, then Grep record bodies under `.sybermem/{changes,decisions,requirements,bugs}/`.
4. **Enrich each hit** — for every matched record, look up its phase (from phase-index coverage map) and read its `implements`/`fixes`/`related` frontmatter fields.
5. **Rank** — keyword hits in Key Conclusions rank above body-only hits; newer dates rank higher within the same tier.
6. **Output** — render the result list (see Output Format). Do not write anything to disk.

## Reverse references

When the query is a record ID, also find which records point AT it:
- Grep all record frontmatter under `.sybermem/{changes,decisions,requirements,bugs}/` for the target ID appearing in `implements:`, `fixes:`, or `related:` fields.
- List those records under `Referenced by:` with the relation type.

This is computed live; no reverse index is stored.

## Output Format

```md
## SyberMem Search: "<query>"

Found N records:

1. **[type-NNN]** #topic1 #topic2 — one-line conclusion (date)
   - Phase: phase-00X (phase title)
   - File: .sybermem/<type>/<file>.md
   - Relations: implements requirement-002, related change-005
   - Referenced by: change-008 (implements)

2. ...
```

Omit `Relations:` or `Referenced by:` lines when there are none.

## Error Handling

- `.sybermem/INDEX.md` missing → prompt `/sybermem-init-project`, stop.
- No matches → say so plainly; do not invent results.
- Phase-index missing → skip phase enrichment, still return keyword/topic/date results.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Writing search output to a file
- Reporting a record without verifying it exists on disk
- Inventing a relation or phase that is not in the frontmatter / coverage map
- Returning results when the query clearly matched nothing

**All of these mean: go back to the relevant step and re-verify.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I roughly remember the records, I'll answer from memory" | Memory drifts. Grep the actual files. |
| "Close enough match, I'll report it as a hit" | Report what matched, with evidence. Don't pad results. |
| "Phase-index is missing, I'll guess the phase" | Skip phase enrichment. Never invent a phase. |

## Terminal State

This skill is complete when:
- the query has been parsed and the matching retrieval path run
- each hit is enriched with phase and relations where available
- the ranked result list has been output to the user
- no file was written

## Integration

**Related skills:**
- **sybermem-record** — creates the records this skill searches
- **sybermem-link** — adds the relations this skill surfaces
- **sybermem-phase-analyze** — produces the phase coverage used for enrichment
```

- [ ] **Step 2: Verify the skill file is well-formed**

Run: `python -c "import pathlib; t = pathlib.Path('packages/claude-skills/sybermem-search/SKILL.md').read_text(encoding='utf-8'); assert t.startswith('---'); assert 'name: sybermem-search' in t; assert 'Reverse references' in t; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add packages/claude-skills/sybermem-search/SKILL.md
git commit -m "feat: add sybermem-search retrieval skill"
```

---

### Task 2: Create the /sybermem-link skill

The relation-补充 skill. Forward-only writes.

**Files:**
- Create: `packages/claude-skills/sybermem-link/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Create `packages/claude-skills/sybermem-link/SKILL.md` with this exact content:

```markdown
---
name: sybermem-link
description: Use when establishing or adding a relationship between two existing SyberMem records, such as marking that a change implements a requirement or fixes a bug.
---

# sybermem-link Skill

**Announce at start:** "I'm using the sybermem-link skill to relate two project records."

Add a forward relation between two existing SyberMem records by editing the SOURCE record's frontmatter. Relations are forward-only.

## Core Invariant

- **Only the source record's frontmatter is modified. The target record is never touched.**

<HARD-GATE>
Do NOT modify the target record. Relations are stored forward-only on the source.
Do NOT create either record. Both must already exist; verify with a file-system tool.
Do NOT add a relation type other than implements, fixes, or related.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Usage

```
/sybermem-link <source-id> <relation> <target-id>
/sybermem-link change-008 implements requirement-002
/sybermem-link bug-001 related change-003
```

`<relation>` must be one of: `implements`, `fixes`, `related`.

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply directory resolution rules above.
2. **Parse arguments** — `<source-id> <relation> <target-id>`. If `<relation>` is not one of `implements`/`fixes`/`related`, stop and tell the user the valid relations.
3. **Verify both records exist** — use a file-system tool to find the source record file (`.sybermem/<type>/<date>-<NNN>-*.md` matching the source ID) and the target record file. If either does not exist, stop and report which one is missing.
4. **Read the source record** — load its frontmatter.
5. **Append the relation** — in the source record's frontmatter, add `<target-id>` to the `<relation>` field. If the field does not exist, create it as a list. If `<target-id>` is already present, skip (no duplicate).
6. **Write the source record only** — save the source file. Do NOT modify the target.
7. **Report** — tell the user which record and field were updated.

## Relation Semantics

| Relation | Meaning | Typical direction |
|---|---|---|
| `implements` | source implements the target requirement/decision | change → requirement / decision |
| `fixes` | source fixes the target bug | change / bug → bug |
| `related` | weak association, no clear causality | any → any |

## Error Handling

- Source or target record does not exist → stop, name the missing one.
- Invalid relation type → stop, list valid relations.
- Relation already present → report no-op, do not duplicate.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Editing the target record's frontmatter (relations are forward-only)
- Creating a record that does not exist instead of stopping
- Writing a relation type other than implements/fixes/related
- Duplicating a relation that is already present

**All of these mean: go back to the relevant step and re-verify.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll also add the reverse on the target for convenience" | Forward-only. Reverse is computed at query time by /sybermem-search. |
| "The target probably exists, I'll skip verification" | Verify with a file-system tool. A dangling relation is a defect. |
| "related is close enough for everything" | Use implements/fixes when the causality is clear. |

## Terminal State

This skill is complete when:
- both records were verified to exist
- the source record's relation field was updated (or confirmed already present)
- the target record was left untouched
- the user was told what changed

## Integration

**Related skills:**
- **sybermem-record** — also proposes relations at record-creation time
- **sybermem-search** — surfaces forward relations and computes reverse references
```

- [ ] **Step 2: Verify the skill file is well-formed**

Run: `python -c "import pathlib; t = pathlib.Path('packages/claude-skills/sybermem-link/SKILL.md').read_text(encoding='utf-8'); assert t.startswith('---'); assert 'name: sybermem-link' in t; assert 'forward-only' in t.lower(); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add packages/claude-skills/sybermem-link/SKILL.md
git commit -m "feat: add sybermem-link relation skill"
```

---

### Task 3: Add relation-inference step to the record skill

Enhance `/sybermem-record` to propose relations at creation time.

**Files:**
- Modify: `packages/claude-skills/sybermem-record/SKILL.md`

- [ ] **Step 1: Add a relation-inference step to the Flow**

In `packages/claude-skills/sybermem-record/SKILL.md`, find this Flow step (around line 54):

```markdown
5. **Create file** — path: `.sybermem/{type}/{YYYY-MM-DD}-{NNN}-{title}.md`. Use `templates/{type}.md` as the content template.
```

Insert a new step BEFORE it (so it becomes step 5, and the rest renumber):

```markdown
5. **Infer relations (propose, don't force)** — from the current session context, infer whether this record relates to an existing record. Look for:
   - a requirement or decision this change/work implements → propose `implements`
   - a bug this work fixes → propose `fixes`
   - a record discussed in the same session with no clear causality → propose `related`

   Propose to the user, e.g. "This change appears to implement requirement-002. Add `implements: [requirement-002]`?" Only write the relation field into the record's frontmatter if the user confirms or it is clearly correct. Relation values must be existing record IDs. If there is no clear relation, skip silently. This is a proposal — it never blocks the core record steps below.
```

Renumber the subsequent steps: "Create file" becomes 6, "Update INDEX.md table" becomes 7, "Write back key conclusion" becomes 8, "Update Topic Index" becomes 9.

- [ ] **Step 2: Update the Verification section to mention relations**

Find the `## Verification` section. After the existing numbered checks, add:

```markdown
5. **Relation validity:** If any `implements`/`fixes`/`related` field was written, does each referenced ID correspond to an existing record?
```

- [ ] **Step 3: Verify the edits**

Run: `python -c "import pathlib; t = pathlib.Path('packages/claude-skills/sybermem-record/SKILL.md').read_text(encoding='utf-8'); assert 'Infer relations' in t; assert 'Relation validity' in t; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-record/SKILL.md
git commit -m "feat: propose record relations at creation time in record skill"
```

---

### Task 4: Document relation fields in record templates

Add frontmatter comments documenting the optional relation fields so users editing records by hand know they exist.

**Files:**
- Modify: `packages/claude-skills/sybermem-record/templates/change.md`
- Modify: `packages/claude-skills/sybermem-record/templates/decision.md`
- Modify: `packages/claude-skills/sybermem-record/templates/requirement.md`
- Modify: `packages/claude-skills/sybermem-record/templates/bug.md`

- [ ] **Step 1: Update change.md template**

In `packages/claude-skills/sybermem-record/templates/change.md`, find:

```markdown
related_files: {{related_files}}
---
```

Replace with:

```markdown
related_files: {{related_files}}
# Optional relations (forward-only, values are existing record IDs):
# implements: [requirement-NNN]   # this change implements a requirement/decision
# fixes: [bug-NNN]                 # this change fixes a bug
# related: [type-NNN]              # weak association
---
```

- [ ] **Step 2: Update decision.md template**

Read `packages/claude-skills/sybermem-record/templates/decision.md`, find the closing `---` of its frontmatter (the line with `---` after the last frontmatter field). Insert the same comment block immediately before that closing `---`:

```markdown
# Optional relations (forward-only, values are existing record IDs):
# implements: [requirement-NNN]   # this decision implements a requirement
# fixes: [bug-NNN]                 # this decision addresses a bug
# related: [type-NNN]              # weak association
```

- [ ] **Step 3: Update requirement.md template**

Read `packages/claude-skills/sybermem-record/templates/requirement.md`, find the closing `---` of its frontmatter. Insert immediately before it:

```markdown
# Optional relations (forward-only, values are existing record IDs):
# related: [type-NNN]              # weak association with another record
```

- [ ] **Step 4: Update bug.md template**

In `packages/claude-skills/sybermem-record/templates/bug.md`, find:

```markdown
severity: {{severity}}
---
```

Replace with:

```markdown
severity: {{severity}}
# Optional relations (forward-only, values are existing record IDs):
# fixes: [bug-NNN]                 # this bug fix addresses another bug
# related: [type-NNN]              # weak association (e.g. caused by change-NNN)
---
```

- [ ] **Step 5: Verify all four templates**

Run: `python -c "import pathlib; [print(p, 'OK') for p in ['change','decision','requirement','bug'] if 'Optional relations' in pathlib.Path(f'packages/claude-skills/sybermem-record/templates/{p}.md').read_text(encoding='utf-8')]"`
Expected: four lines each ending `OK`

- [ ] **Step 6: Commit**

```bash
git add packages/claude-skills/sybermem-record/templates/
git commit -m "docs: document optional relation fields in record templates"
```

---

### Task 5: Add search/link to instruction-file skill lists

Update the managed CLAUDE.md/AGENTS.md skill catalogs (project root + init-project templates) to include the two new skills.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/AGENTS.md`

- [ ] **Step 1: Update project-root CLAUDE.md**

In `CLAUDE.md`, find the `## Available Skills` list. After the `/using-sybermem` line, add:

```markdown
- `/sybermem-search` — Search/query records by keyword, topic, phase range, date range, or record ID
- `/sybermem-link` — Add a forward relation between two existing records
```

- [ ] **Step 2: Update project-root AGENTS.md**

In `AGENTS.md`, find the `## Available Skills` list. After the `/using-sybermem` line, add the same two lines:

```markdown
- `/sybermem-search` — Search/query records by keyword, topic, phase range, date range, or record ID
- `/sybermem-link` — Add a forward relation between two existing records
```

- [ ] **Step 3: Update init-project template CLAUDE.md**

In `packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md`, find the `## Available Skills` list and add the same two lines after the `/using-sybermem` line.

- [ ] **Step 4: Update init-project template AGENTS.md**

In `packages/claude-skills/sybermem-init-project/project-files/AGENTS.md`, find the `## Available Skills` list and add the same two lines after the `/using-sybermem` line.

- [ ] **Step 5: Verify all four files**

Run: `python -c "import pathlib; files=['CLAUDE.md','AGENTS.md','packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md','packages/claude-skills/sybermem-init-project/project-files/AGENTS.md']; [print(f,'OK') for f in files if '/sybermem-search' in pathlib.Path(f).read_text(encoding='utf-8') and '/sybermem-link' in pathlib.Path(f).read_text(encoding='utf-8')]"`
Expected: four lines each ending `OK`

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md AGENTS.md packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md packages/claude-skills/sybermem-init-project/project-files/AGENTS.md
git commit -m "docs: add search and link skills to instruction-file skill catalogs"
```

---

### Task 6: Sync plugin skills tree and update README

Regenerate the plugin-facing `skills/` tree and document the new capabilities.

**Files:**
- Modify: `skills/` (generated)
- Modify: `README.md`

- [ ] **Step 1: Run the sync script**

Run: `python scripts/sync-plugin-skills.py`
Expected: exits 0 (no output)

- [ ] **Step 2: Verify the new skills appear in the plugin tree**

Run: `python -c "import pathlib; assert (pathlib.Path('skills/sybermem-search/SKILL.md')).is_file(); assert (pathlib.Path('skills/sybermem-link/SKILL.md')).is_file(); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Update README Skills table**

In `README.md`, find the Skills table (the `| Skill | 功能 |` table). Add two rows after the `/sybermem-update` row:

```markdown
| `/sybermem-search` | 按关键词、topic、phase 范围、日期范围或记录 ID 检索记录，并显示所属 phase 与关系 |
| `/sybermem-link` | 在两条已有记录间建立正向关系（implements / fixes / related） |
```

- [ ] **Step 4: Add a relations note to README**

In `README.md`, after the Skills table, add a short subsection:

```markdown
## 记录关系与检索

记录可以在 frontmatter 中声明可选的正向关系字段：

- `implements: [requirement-NNN]` — 实现某需求/决策
- `fixes: [bug-NNN]` — 修复某 bug
- `related: [type-NNN]` — 弱关联

关系只存正向。`/sybermem-search <record-id>` 在查询时实时扫描，反向列出所有引用该记录的记录（`Referenced by`）。`/sybermem-record` 创建记录时会尝试推断并提议关系；`/sybermem-link` 用于事后补充。
```

- [ ] **Step 5: Verify README**

Run: `python -c "import pathlib; t=pathlib.Path('README.md').read_text(encoding='utf-8'); assert '/sybermem-search' in t; assert '/sybermem-link' in t; assert '记录关系与检索' in t; print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add skills/ README.md
git commit -m "feat: sync search/link skills to plugin tree and document relations in README"
```

---

### Task 7: End-to-end verification

Verify the new capabilities work against the real project records.

**Files:**
- No file changes

- [ ] **Step 1: Verify plugin package still valid**

Run: `python scripts/check-plugin-package.py`
Expected: `OK` (static checks + claude plugins validate, or static-only if no CLI)

- [ ] **Step 2: Verify skill count increased**

Run: `python -c "import pathlib; dirs=[d for d in pathlib.Path('skills').iterdir() if d.is_dir()]; print(len(dirs), 'skills'); assert len(dirs) >= 10"`
Expected: `10 skills` (or more) — the 8 original plus search and link

- [ ] **Step 3: Real search smoke test via Claude CLI**

Run: `claude --plugin-dir . -p "/sybermem:sybermem-search hooks"`
Expected: A search result list mentioning records tagged `#hooks` (e.g. change-003, change-005, bug-001) with phase info. Captures real runtime behavior.

- [ ] **Step 4: Real reverse-reference smoke test**

Run: `claude --plugin-dir . -p "/sybermem:sybermem-search requirement-002"`
Expected: requirement-002 returned; if any record has `implements: [requirement-002]`, it appears under `Referenced by:`. (May be empty if no record links it yet — that is correct.)

- [ ] **Step 5: No commit needed** (verification only)
