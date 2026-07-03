# SyberMem Team Skills Exposure Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Team workflows feel native to SyberMem by exposing the existing Team CLI capabilities as first-class slash skills.

**Architecture:** Keep the CLI as the execution layer (`sybermem publish status`, `sybermem team summary`) and add two thin wrapper skills — `/sybermem-team-publish` and `/sybermem-team-summary` — that explain, route, and invoke the existing Team pipeline. Extend `/using-sybermem` so Team state and Team routes are discoverable from the main diagnostic entrypoint.

**Tech Stack:** Markdown skill definitions, existing `sybermem` CLI, current Team repo publication pipeline

---

### Task 1: Add `/sybermem-team-publish` skill in both source and plugin-facing trees

**Files:**
- Create: `packages/claude-skills/sybermem-team-publish/SKILL.md`
- Create: `skills/sybermem-team-publish/SKILL.md`

- [ ] **Step 1: Create the source skill**

Write `packages/claude-skills/sybermem-team-publish/SKILL.md`:

```markdown
---
name: sybermem-team-publish
description: Publish the current project into Team memory using the remembered Team association or a one-time Team path.
---

# sybermem-team-publish Skill

**Announce at start:** "I'm using the sybermem-team-publish skill to publish this project into Team memory."

Use the existing Team publication pipeline through the `sybermem` CLI.

## Flow

1. Resolve the current project root.
2. Check `.sybermem/project.yaml` for a `team:` block.
3. If the project is already linked to Team memory, run:

```bash
sybermem publish status --format json
```

4. If the project is not yet linked to Team memory, ask the user for a Team repo path, then run:

```bash
sybermem publish status --team-path <path> --format json
```

5. Report:
- team ID
- project slug
- files updated
- whether Team push succeeded

## Output Style

```md
## Team Publish
- Team: ...
- Project: ...
- Files updated:
  - ...
- Push: success / failed
```
```

- [ ] **Step 2: Mirror the same file into the plugin-facing skill tree**

Create the same content at:

```text
skills/sybermem-team-publish/SKILL.md
```

- [ ] **Step 3: Verify both files exist and match**

Run:
```bash
python -c "from pathlib import Path; a = Path('packages/claude-skills/sybermem-team-publish/SKILL.md').read_text(encoding='utf-8'); b = Path('skills/sybermem-team-publish/SKILL.md').read_text(encoding='utf-8'); assert a == b; print('team-publish skill OK')"
```

Expected: `team-publish skill OK`

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-team-publish/SKILL.md skills/sybermem-team-publish/SKILL.md
git commit -m "feat: add sybermem-team-publish skill"
```

---

### Task 2: Add `/sybermem-team-summary` skill in both source and plugin-facing trees

**Files:**
- Create: `packages/claude-skills/sybermem-team-summary/SKILL.md`
- Create: `skills/sybermem-team-summary/SKILL.md`

- [ ] **Step 1: Create the source skill**

Write `packages/claude-skills/sybermem-team-summary/SKILL.md`:

```markdown
---
name: sybermem-team-summary
description: Generate the Team management summary from the current project's remembered Team repo or a one-time Team path.
---

# sybermem-team-summary Skill

**Announce at start:** "I'm using the sybermem-team-summary skill to generate a Team management summary."

Use the existing Team summary CLI surface to generate management-consumption outputs.

## Flow

1. Resolve the current project root.
2. Check `.sybermem/project.yaml` for `team.team_path`.
3. If present, run:

```bash
sybermem team summary --team-path <team-path> --format json
```

4. If not present, ask the user for a Team repo path.
5. Report:
- team ID
- summary markdown path
- summary JSON path
- summary-state path
- recommend reading `latest-management-summary.md`

## Output Style

```md
## Team Summary Generated
- Team: ...
- Markdown: ...
- JSON: ...
- Baseline state: ...
- Recommended reading: ...
```
```

- [ ] **Step 2: Mirror the same file into the plugin-facing skill tree**

Create the same content at:

```text
skills/sybermem-team-summary/SKILL.md
```

- [ ] **Step 3: Verify both files exist and match**

Run:
```bash
python -c "from pathlib import Path; a = Path('packages/claude-skills/sybermem-team-summary/SKILL.md').read_text(encoding='utf-8'); b = Path('skills/sybermem-team-summary/SKILL.md').read_text(encoding='utf-8'); assert a == b; print('team-summary skill OK')"
```

Expected: `team-summary skill OK`

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-team-summary/SKILL.md skills/sybermem-team-summary/SKILL.md
git commit -m "feat: add sybermem-team-summary skill"
```

---

### Task 3: Extend `/using-sybermem` to report Team state and route to the new Team skills

**Files:**
- Modify: `packages/claude-skills/using-sybermem/SKILL.md`
- Modify: `skills/using-sybermem/SKILL.md`

- [ ] **Step 1: Add Team-state reporting to the source skill**

In `packages/claude-skills/using-sybermem/SKILL.md`, extend the health-check/reporting section so it also reports:
- whether `project.yaml` contains a `team:` block
- whether the Team path is accessible
- whether the current project appears Team-publishable

- [ ] **Step 2: Add Team-routing explanations**

Also extend the routing section so the skill now explains what would happen if the user runs:
- `/sybermem-team-publish`
- `/sybermem-team-summary`

And allow the recommendation logic to suggest one of these when the project already has a Team association.

- [ ] **Step 3: Mirror the updated content to `skills/using-sybermem/SKILL.md`**

After editing the source skill, copy the same content into the plugin-facing skill tree.

- [ ] **Step 4: Verify both files still match**

Run:
```bash
python -c "from pathlib import Path; a = Path('packages/claude-skills/using-sybermem/SKILL.md').read_text(encoding='utf-8'); b = Path('skills/using-sybermem/SKILL.md').read_text(encoding='utf-8'); assert a == b; print('using-sybermem Team routing OK')"
```

Expected: `using-sybermem Team routing OK`

- [ ] **Step 5: Commit**

```bash
git add packages/claude-skills/using-sybermem/SKILL.md skills/using-sybermem/SKILL.md
git commit -m "feat: add Team-aware routing to using-sybermem"
```

---

### Task 4: Dogfood the Team skill layer and document it

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Verify `/sybermem-team-publish` wraps the real Team publish path correctly**

Use the new skill on the current project and confirm it resolves the Team association from `project.yaml` and would produce the same Team publication result as the CLI path.

- [ ] **Step 2: Verify `/sybermem-team-summary` wraps the real Team summary path correctly**

Use the new skill on the current project and confirm it resolves the Team association from `project.yaml` and would produce the same management-summary outputs as the CLI path.

- [ ] **Step 3: Update README Team workflow notes**

Add a short note to both READMEs:

Chinese:
```markdown
- **Team Skills**：`/sybermem-team-publish` 与 `/sybermem-team-summary` 提供与项目级 slash workflow 一致的 Team 入口
```

English:
```markdown
- **Team Skills**: `/sybermem-team-publish` and `/sybermem-team-summary` provide Team entrypoints consistent with the project-level slash workflow
```

- [ ] **Step 4: Commit**

```bash
git add README.md README.en.md
git commit -m "docs: add Team skill entrypoints to README"
```
