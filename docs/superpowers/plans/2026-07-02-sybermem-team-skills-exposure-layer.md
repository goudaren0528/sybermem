# SyberMem Team Skills Exposure Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the current Team CLI capabilities as user-facing SyberMem skills so Team workflows feel consistent with the existing slash-command-based project workflows.

**Architecture:** Keep the CLI as the execution layer, and add two new wrapper skills: `/sybermem-team-publish` and `/sybermem-team-summary`. Each skill should call the existing CLI surface, format the result for users, and route cleanly when Team prerequisites are missing. Update `/using-sybermem` so it can mention Team state and recommend the new Team skills.

**Tech Stack:** Markdown skill definitions, existing `sybermem` CLI, project-local `project.yaml` Team association

---

### Task 1: Add `/sybermem-team-publish` skill

**Files:**
- Create: `packages/claude-skills/sybermem-team-publish/SKILL.md`
- Create: `skills/sybermem-team-publish/SKILL.md` (plugin-facing tree)

- [ ] **Step 1: Create the source skill definition**

Write `packages/claude-skills/sybermem-team-publish/SKILL.md` with content like:

```markdown
# sybermem-team-publish Skill

**Announce at start:** "I'm using the sybermem-team-publish skill to publish this project into Team memory."

Publish the current project into the configured Team repo using the existing CLI publish pipeline.

## Flow

1. Resolve the current project root.
2. Check whether `.sybermem/project.yaml` already contains a `team:` block.
3. If a Team association exists, run:

```bash
sybermem publish status --format json
```

4. If no Team association exists, explain that the project is not yet linked to Team memory and ask for a Team repo path. Then run:

```bash
sybermem publish status --team-path <path> --format json
```

5. Report:
- team ID
- project slug
- files updated
- whether push succeeded

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

- [ ] **Step 2: Copy it into the plugin-facing skills tree**

Copy the same content to:

```text
skills/sybermem-team-publish/SKILL.md
```

- [ ] **Step 3: Verify the skill file exists in both locations**

Check that both paths exist and match.

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-team-publish/SKILL.md skills/sybermem-team-publish/SKILL.md
git commit -m "feat: add sybermem-team-publish skill"
```

---

### Task 2: Add `/sybermem-team-summary` skill

**Files:**
- Create: `packages/claude-skills/sybermem-team-summary/SKILL.md`
- Create: `skills/sybermem-team-summary/SKILL.md`

- [ ] **Step 1: Create the source skill definition**

Write `packages/claude-skills/sybermem-team-summary/SKILL.md` with content like:

```markdown
# sybermem-team-summary Skill

**Announce at start:** "I'm using the sybermem-team-summary skill to generate a Team management summary."

Generate the management-consumption layer summary for the current project's Team repo.

## Flow

1. Resolve the current project root.
2. Read `.sybermem/project.yaml` and check for `team.team_path`.
3. If found, run:

```bash
sybermem team summary --team-path <team-path> --format json
```

4. If not found, ask the user for a Team repo path.
5. Report:
- team ID
- generated markdown path
- generated JSON path
- baseline state path
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

- [ ] **Step 2: Copy it into the plugin-facing skills tree**

Copy the same content to:

```text
skills/sybermem-team-summary/SKILL.md
```

- [ ] **Step 3: Verify the skill file exists in both locations**

Check that both paths exist and match.

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/sybermem-team-summary/SKILL.md skills/sybermem-team-summary/SKILL.md
git commit -m "feat: add sybermem-team-summary skill"
```

---

### Task 3: Teach `/using-sybermem` to report Team state and recommend Team skills

**Files:**
- Modify: `packages/claude-skills/using-sybermem/SKILL.md`
- Modify: `skills/using-sybermem/SKILL.md`

- [ ] **Step 1: Add Team state reporting to the skill instructions**

In `packages/claude-skills/using-sybermem/SKILL.md`, extend the diagnostic section so it also reports:
- whether `project.yaml` has a `team:` block
- whether the Team path is accessible
- whether the current Team repo appears to have published content

- [ ] **Step 2: Add Team routing explanations**

Also extend the routing section with:
- `/sybermem-team-publish` → publish current project into Team memory
- `/sybermem-team-summary` → generate Team management summary

- [ ] **Step 3: Mirror the updated content to `skills/using-sybermem/SKILL.md`**

Copy the same Team-aware wording into the plugin-facing `skills/using-sybermem/SKILL.md`.

- [ ] **Step 4: Commit**

```bash
git add packages/claude-skills/using-sybermem/SKILL.md skills/using-sybermem/SKILL.md
git commit -m "feat: add Team-aware routing to using-sybermem"
```

---

### Task 4: Dogfood the new Team skills via the real Team repo and update README

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Verify `/sybermem-team-publish` wraps the current Team publish flow correctly**

Use the skill on the current project and confirm it would route to the Team repo already stored in `project.yaml`, publishing without needing a manual CLI path.

- [ ] **Step 2: Verify `/sybermem-team-summary` wraps the Team management summary flow correctly**

Use the skill on the current project and confirm it would route to the Team repo already stored in `project.yaml`, producing `latest-management-summary.md/.json`.

- [ ] **Step 3: Update README Team workflow section**

Add a short note to both READMEs that Team workflows now have skill entrypoints:

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
