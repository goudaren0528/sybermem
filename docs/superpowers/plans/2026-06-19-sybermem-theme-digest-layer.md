# SyberMem Theme Digest Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new Theme Digest Layer above phase digests, so a topic (e.g. `hooks`, `plugin`, `memory`) can be compressed across multiple phases into one durable artifact.

**Architecture:** A new `/sybermem-theme-digest` skill writes `.sybermem/theme-digests/YYYY-MM-DD-NNN-topic.md` using a new `theme-digest-template.md`. It reads topic-tagged records from Topic Index / Key Conclusions, enriches them with phase coverage from `phase-index.md`, prefers existing phase digests as source material when available, and falls back to raw records to fill gaps. `INDEX.md` gets a new `## Theme Digests` section, and `init-project` provisions the new directory/template/INDEX section for new or upgraded projects.

**Tech Stack:** Markdown (SKILL.md + templates + INDEX sections)

**Spec:** `docs/superpowers/specs/2026-06-19-sybermem-theme-digest-layer-design.md`

**Global Constraints:**
- `/sybermem-digest` keeps its existing meaning: phase digest only. Theme digest is a NEW skill, `/sybermem-theme-digest`.
- First version supports one topic slug only — no multi-topic, no time-based aggregation.
- Theme digests are durable files under `.sybermem/theme-digests/`.
- `source_phases`, `source_digests`, and `source_records` must be explicit and deduplicated.
- Coverage strategy must be `phase-digests-first-then-records`.
- No hierarchy, no meta-meta-digest, no summary theme mode in this phase.
- Zero new dependencies.

---

### Task 1: Add the theme digest template and directory support to init-project templates

Provision the storage layout first so the new skill has a place to write.

**Files:**
- Create: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/templates/theme-digest-template.md`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md`
- Modify: `packages/claude-skills/sybermem-init-project/SKILL.md`

- [ ] **Step 1: Create the theme digest template**

Create `packages/claude-skills/sybermem-init-project/project-files/.sybermem/templates/theme-digest-template.md` with this exact content:

```markdown
---
type: theme-digest
date: {{date}}
number: {{number}}
theme: {{theme}}
status: {{status}}
source_topics:
{{source_topics}}
source_phases:
{{source_phases}}
source_digests:
{{source_digests}}
source_records:
{{source_records}}
coverage_strategy: phase-digests-first-then-records
---

# Theme Digest: {{theme}}

## Theme
{{theme_summary}}

## Why This Theme Matters
{{why_this_theme_matters}}

## What Stabilized
{{what_stabilized}}

## Cross-Phase Evolution
{{cross_phase_evolution}}

## Current Reusable Conclusions
{{current_reusable_conclusions}}

## Open Edges
{{open_edges}}

## Source Coverage
{{source_coverage}}
```

- [ ] **Step 2: Add Theme Digests section to the init-project INDEX template**

Open `packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md`. It currently has:

```markdown
## Stage Digests

| Number | Date | Title | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
| 001 | 2026-06-05 | sybermem v1 digest design phase | completed | 3 records | [link](digests/2026-06-05-001-sybermem-v1-digest-design-phase.md) |
<!-- add new digest records here -->

---

## Feature Changes
```

Insert immediately after the Stage Digests section and before `## Feature Changes`:

```markdown
## Theme Digests

| Number | Date | Theme | Status | Coverage | Link |
|--------|------|-------|--------|----------|------|
<!-- add new theme digest records here -->

---
```

- [ ] **Step 3: Update init-project SKILL.md to provision theme-digests support**

Open `packages/claude-skills/sybermem-init-project/SKILL.md` and make these exact changes:

1. In the "Use these template files..." list (Step 1.1), add:
```markdown
- `project-files/.sybermem/templates/theme-digest-template.md`
```

2. Add a new capability check subsection after Step 1.3 (analysis) and before Step 2:

```markdown
### Step 1.4: Enable theme-digest capability if missing

For projects that already have `.sybermem/INDEX.md`, check whether theme-digest support is present:

- `.sybermem/theme-digests/`
- `.sybermem/templates/theme-digest-template.md`
- `## Theme Digests` section in `.sybermem/INDEX.md`

If any are missing:
- create the missing `theme-digests/` directory
- create the missing `theme-digest-template.md` from `project-files/.sybermem/templates/theme-digest-template.md`
- insert the missing `## Theme Digests` section into `INDEX.md`

Do this idempotently. Never duplicate the section and never overwrite an existing theme digest template without asking.
```

3. In Step 8 output summary, after the digest lines, add:
```markdown
- `.sybermem/theme-digests/` and theme digest template when theme-digest support is enabled
- `INDEX.md` theme digest navigation when missing
```

- [ ] **Step 4: Verify template files**

Run: `python -c "import pathlib; assert pathlib.Path('packages/claude-skills/sybermem-init-project/project-files/.sybermem/templates/theme-digest-template.md').is_file(); t = pathlib.Path('packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md').read_text(encoding='utf-8'); assert '## Theme Digests' in t; s = pathlib.Path('packages/claude-skills/sybermem-init-project/SKILL.md').read_text(encoding='utf-8'); assert 'Step 1.4: Enable theme-digest capability if missing' in s; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add packages/claude-skills/sybermem-init-project/project-files/.sybermem/templates/theme-digest-template.md packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md packages/claude-skills/sybermem-init-project/SKILL.md
git commit -m "feat: provision theme digest layer in init-project templates"
```

---

### Task 2: Add the new /sybermem-theme-digest skill

This is the core feature. It must be separate from `/sybermem-digest`.

**Files:**
- Create: `packages/claude-skills/sybermem-theme-digest/SKILL.md`

- [ ] **Step 1: Write the skill file**

Create `packages/claude-skills/sybermem-theme-digest/SKILL.md` with this exact content:

```markdown
---
name: sybermem-theme-digest
description: Use when creating a durable topic-based digest that compresses multiple related phases or records into one theme-level conclusion.
---

# sybermem-theme-digest Skill

**Announce at start:** "I'm using the sybermem-theme-digest skill to create a durable topic-level digest."

Create a durable theme digest in `.sybermem/theme-digests/` so future project understanding does not require re-reading every phase digest or all raw records for one topic.

## Core Invariants

- **No theme digest without explicit source coverage.**
- **Theme digests are topic-based. First version supports one topic slug only.**
- **Coverage strategy is phase-digests-first-then-records.**

<HARD-GATE>
Do NOT create a theme digest unless ALL of the following are true:
1. A single topic slug has been identified
2. `source_phases`, `source_digests`, and `source_records` have been explicitly built and deduplicated
3. The output path, INDEX row, and theme digest file can all be written consistently

If any of these is false, STOP. Do not write the theme digest file.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Preconditions

Before creating a theme digest, verify all of the following:
- `.sybermem/theme-digests/` exists
- `.sybermem/templates/theme-digest-template.md` exists
- `.sybermem/INDEX.md` contains a `## Theme Digests` section
- `.sybermem/INDEX.md` contains the exact insertion anchor `<!-- add new theme digest records here -->` within that section

If any are missing, explain that theme-digest capability has not been enabled in this project yet and ask the user to run `/sybermem-update`.

## Usage

```text
/sybermem-theme-digest hooks
```

First version supports one topic slug only.

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply directory resolution rules above.
2. **Verify preconditions** — `.sybermem/theme-digests/` exists, `theme-digest-template.md` exists, `INDEX.md` has `## Theme Digests` with `<!-- add new theme digest records here -->`. If any missing, ask the user to run `/sybermem-update`.
3. **Identify the topic scope** — the user provides one topic slug (e.g. `hooks`). Do not merge topics in this first version.
4. **Collect candidate records** — read `## Topic Index` in `.sybermem/INDEX.md` for that topic. If the topic is missing, refuse and explain.
5. **Enrich with phase coverage** — read `.sybermem/analysis/phase-index.md` coverage map and determine which confirmed phases cover those records.
6. **Prefer phase digests first** — if any of those phases already have digests listed in `## Stage Digests`, use them as primary compressed sources.
7. **Fill gaps with raw records** — for records not covered by any existing phase digest, include the raw record file as a direct source.
8. **Deduplicate** — deduplicate `source_phases`, `source_digests`, and `source_records` by ID or path.
9. **Write the theme digest file** — path: `.sybermem/theme-digests/{YYYY-MM-DD}-{NNN}-{topic}.md`. Use `.sybermem/templates/theme-digest-template.md`. Set `coverage_strategy: phase-digests-first-then-records`.
10. **Update INDEX.md** — insert a row above `<!-- add new theme digest records here -->` in `## Theme Digests`: `| NNN | YYYY-MM-DD | topic | completed | X phases, Y digests, Z records | [link](theme-digests/file.md) |`

## Output Shape

```md
# Theme Digest: hooks

## Theme
- hooks

## Why This Theme Matters
- ...

## What Stabilized
- ...

## Cross-Phase Evolution
- phase-001: ...
- phase-004: ...

## Current Reusable Conclusions
- ...

## Open Edges
- ...

## Source Coverage
- Digests used: digest-001
- Raw records used: change-003, bug-001
```

## Error Handling

- Topic not found in Topic Index → stop and explain.
- Theme-digest capability missing → ask user to run `/sybermem-update`.
- No records for topic → stop and explain.
- Exact duplicate source coverage with an existing theme digest → do not create a second one; point to the existing file.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Merging multiple topic slugs into one theme digest
- Creating a theme digest without explicit source lists
- Repeating raw records already covered by a phase digest without a reason
- Treating a theme digest as a current-state summary instead of a durable conclusion

**All of these mean: go back to the relevant step and re-verify source coverage.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll just summarize all related topics together" | First version is one topic only. Keep the scope explicit. |
| "Those phase digests probably cover everything" | Verify. Use raw records to fill actual gaps. |
| "This is basically the same as /sybermem-digest" | No. Phase digest summarizes one phase; theme digest summarizes one topic across phases. |

## Terminal State

This skill is complete when:
- the theme digest file is written to `.sybermem/theme-digests/`
- the `INDEX.md` Theme Digests table has a new row
- `source_phases`, `source_digests`, and `source_records` are explicitly listed
- the user has been shown the theme digest path and coverage

## Integration

**Related skills:**
- **sybermem-digest** — phase digests are preferred source material
- **sybermem-summary** — current-state panel remains separate from durable theme conclusions
- **sybermem-update** — enables theme-digest support in older projects
```

- [ ] **Step 2: Verify the new skill**

Run: `python -c "import pathlib; t = pathlib.Path('packages/claude-skills/sybermem-theme-digest/SKILL.md').read_text(encoding='utf-8'); assert 'name: sybermem-theme-digest' in t; assert 'coverage_strategy: phase-digests-first-then-records' in t; assert '## Theme Digests' in t; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add packages/claude-skills/sybermem-theme-digest/SKILL.md
git commit -m "feat: add sybermem-theme-digest skill"
```

---

### Task 3: Wire the new skill into instruction files and plugin skill sync

Make the new skill visible and available everywhere.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md`
- Modify: `packages/claude-skills/sybermem-init-project/project-files/AGENTS.md`
- Modify: `README.md`
- Modify: `skills/` (generated by sync)

- [ ] **Step 1: Add /sybermem-theme-digest to root instruction files**

In both `CLAUDE.md` and `AGENTS.md`, find the `## Available Skills` list and add after the existing `/sybermem-digest` line:

```markdown
- `/sybermem-theme-digest` — Create a durable topic-level digest that compresses one theme across multiple related phases or records
```

- [ ] **Step 2: Add /sybermem-theme-digest to init-project template instruction files**

Make the same insertion in:
- `packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md`
- `packages/claude-skills/sybermem-init-project/project-files/AGENTS.md`

- [ ] **Step 3: Update README Skills table**

In `README.md`, find the Skills table and add a row after `/sybermem-digest`:

```markdown
| `/sybermem-theme-digest` | 为单个 topic 创建跨多个 phase 的持久化高阶摘要（Theme Digest） |
```

Also add a short subsection after the Skills table:

```markdown
## Theme Digest Layer

除了 phase digest (`/sybermem-digest`), SyberMem 现在还支持 theme digest (`/sybermem-theme-digest`)：

- phase digest = 某个阶段最终沉淀了什么
- theme digest = 某个主题跨多个阶段最终沉淀了什么

Theme digest 目录为 `.sybermem/theme-digests/`。第一版按单个 topic 聚合,优先使用已有 phase digests,再用 raw records 补缺。
```

- [ ] **Step 4: Sync plugin-facing skills tree**

Run: `python scripts/sync-plugin-skills.py`
Expected: exits 0 (no output)

- [ ] **Step 5: Verify plugin tree contains the new skill**

Run: `python -c "import pathlib; assert pathlib.Path('skills/sybermem-theme-digest/SKILL.md').is_file(); print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md AGENTS.md packages/claude-skills/sybermem-init-project/project-files/CLAUDE.md packages/claude-skills/sybermem-init-project/project-files/AGENTS.md README.md skills/
git commit -m "docs: wire sybermem-theme-digest into instruction catalogs and plugin tree"
```

---

### Task 4: Verify end-to-end provisioning and runtime surface

Verify that the new capability is visible and that init-project templates contain the new theme-digest support.

**Files:**
- No file changes

- [ ] **Step 1: Verify plugin package still validates**

Run: `python scripts/check-plugin-package.py`
Expected: `OK (static checks + claude plugins validate)`

- [ ] **Step 2: Verify the template INDEX.md contains Theme Digests**

Run: `python -c "import pathlib; t = pathlib.Path('packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md').read_text(encoding='utf-8'); assert '## Theme Digests' in t; assert '<!-- add new theme digest records here -->' in t; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Verify the runtime surface sees the skill**

Run: `claude --plugin-dir . -p "/sybermem:using-sybermem"`
Expected: the startup context and skill catalog should be present, and the skill catalogs on disk now include `/sybermem-theme-digest`.

(We are not yet smoke-testing `/sybermem:sybermem-theme-digest` against a real theme because no `.sybermem/theme-digests/` directory exists in the current project until `/sybermem-update` provisions it. This task is verifying that the new capability is wired and provisionable.)

- [ ] **Step 4: No commit needed** (verification only)
