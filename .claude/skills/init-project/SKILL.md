---
name: init-project
description: Initialize ADR record system for a project (auto-detects new or existing codebase)
---

# init-project Skill

Create ADR directory structure in a project. Auto-detects new project vs existing codebase.

## Usage

User runs `/init-project` in the target project directory.

## Flow

### Step 1: Check existing state

- If `ADR/` directory exists → prompt user, ask whether to reinitialize
- If not → continue

### Step 2: Determine project type

Check for code files (excluding node_modules, .git, etc.):

| Condition | Action |
|-----------|--------|
| Empty directory / no code files | New project → create basic structure |
| Code files exist | Existing project → create structure + scan & analyze |

### Step 3: Create directory structure

```
ADR/
├── INDEX.md
├── changes/
├── decisions/
├── requirements/
├── bugs/
└── templates/
    ├── change-template.md
    ├── decision-template.md
    ├── requirement-template.md
    └── bug-template.md
```

### Step 4: Generate INDEX.md

Use standard format, including:
- `## Key Conclusions` section + `<!-- add new conclusions here -->` placeholder (AI reads this section at session start for project context)
- 4 type tables + `<!-- add new records here -->` placeholder

### Step 5 (existing codebase only): Scan & analyze

1. **Identify tech stack** (via package.json / requirements.txt / go.mod etc.)
2. **Scan Git history** (last 20 commits)
3. **Detect special code** (TODO, FIXME, HACK, workaround)
4. Present findings to user, suggest creating corresponding records

### Step 5.1: Persist scan findings

Write key findings from Step 5 into `ADR/INDEX.md`'s `## Key Conclusions` section, format:

```
- [init] Tech stack: TypeScript + React + Vite, testing with Vitest (date)
- [init] Project uses monorepo structure, pnpm workspace (date)
- [init] Found 12 TODO/FIXME items, concentrated in src/auth/ and src/api/ (date)
```

Write principles:
- Tech stack is mandatory (language, framework, build tool, test framework)
- Project structure characteristics are mandatory (monorepo, microservices, monolith, etc.)
- TODO/FIXME hotspot areas are worth noting (helps future sessions locate problem areas)
- Major changes in Git history are worth noting (recent refactors, migrations, etc.)

### Step 5.2: Detect existing record files

Scan for common record/documentation files in the project:

| Target | Common paths |
|--------|-------------|
| Changelog | `CHANGELOG.md`, `CHANGES.md`, `HISTORY.md` |
| ADR/Decision records | `docs/adr/`, `docs/decisions/`, `adr/`, `doc/architecture/` |
| Requirements/Design docs | `docs/design/`, `docs/specs/`, `docs/rfcs/` |
| Bug tracking | `BUGS.md`, `KNOWN_ISSUES.md` |

**When found, use AskUserQuestion to ask the user**:

> Detected existing record files in the project:
> - `CHANGELOG.md` (47 entries)
> - `docs/adr/` (5 decision files)
>
> Would you like to organize these into the ADR system?
> 1. **Import and organize** — Split content by type into ADR/ directories, keep backups of original files
> 2. **Index only** — Don't move files, add links to original files in INDEX.md
> 3. **Skip** — Don't process, organize manually later

Processing rules:
- **Import and organize**: Parse existing records, classify as change/decision/requirement/bug, rewrite to ADR/ directories using templates, rename original files to `*.backup.md`
- **Index only**: Add `- [existing] Project's original CHANGELOG.md contains 47 change entries, see original file` to INDEX.md key conclusions section, add link rows to corresponding tables
- **Skip**: No action

### Step 6: Create CLAUDE.md / AGENTS.md (if not exists)

Create CLAUDE.md (Claude Code) and AGENTS.md (OpenCode) in project root with ADR workflow rules.
If one already exists, only create the missing one.

### Step 7: Output summary

```markdown
## ADR System Initialized

**Project type:** [New project / Existing codebase]

**Created:**
- ADR/ directory structure
- INDEX.md (with key conclusions)
- Template files
- CLAUDE.md / AGENTS.md

**Project context (existing projects):**
- Tech stack: [detection results]
- Existing records: [import/index/skip results]
- Attention areas: [TODO/FIXME hotspots]

**Next steps:**
- Use /record to create records after completing work
```

## Tech Stack Detection

| Config file | Tech stack |
|-------------|-----------|
| package.json | Node.js / JavaScript / TypeScript |
| requirements.txt / pyproject.toml | Python |
| go.mod | Go |
| Cargo.toml | Rust |
| pom.xml / build.gradle | Java |

## Key Principles

- **Don't modify user's existing files**: Only create new ADR/ directory
- **Scan but don't auto-create records for existing code**: Output suggestions, let user decide
- **Idempotent safety**: Repeated execution won't destroy existing records
