---
name: init-project
description: Use when initializing SyberMem project records for a new or existing codebase, or when an older project still uses ADR/ storage.
---

# init-project Skill

Initialize the SyberMem project record system in a target project. Generated user projects use `.sybermem/` as the canonical project data directory.

## Usage

User runs `/init-project` in the target project directory.

## Directory Resolution Rules

Resolve the project data directory before doing any other work:

1. If `.sybermem/` exists, use it.
2. If only `ADR/` exists, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If both `.sybermem/` and `ADR/` exist, use `.sybermem/`, warn that `ADR/` was ignored, and do not auto-merge them.
4. If neither exists, create `.sybermem/`.

## Flow

### Step 1: Resolve existing state

- Apply the directory resolution rules above.
- If `.sybermem/INDEX.md` already exists after resolution, treat the project as already initialized and ask whether the user wants to refresh templates / instruction files.
- If initialization has not happened yet, continue.

### Step 2: Determine project type

Check for code files (excluding node_modules, .git, etc.):

| Condition | Action |
|-----------|--------|
| Empty directory / no code files | New project → create basic structure |
| Code files exist | Existing project → create structure + scan & analyze |

### Step 3: Create directory structure

```
.sybermem/
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

Use the standard format, including:
- `## Key Conclusions` section + `<!-- add new conclusions here -->` placeholder (AI reads this section at session start for project context)
- 4 type tables + `<!-- add new records here -->` placeholder

### Step 5 (existing codebase only): Scan & analyze

1. **Identify tech stack** (via package.json / requirements.txt / go.mod etc.)
2. **Scan Git history** (last 20 commits)
3. **Detect special code** (TODO, FIXME, HACK, workaround)
4. Present findings to the user, suggest creating corresponding records

### Step 5.1: Persist scan findings

Write key findings from Step 5 into `.sybermem/INDEX.md`'s `## Key Conclusions` section, format:

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
| ADR/decision records | `docs/adr/`, `docs/decisions/`, `adr/`, `doc/architecture/` |
| Requirements/design docs | `docs/design/`, `docs/specs/`, `docs/rfcs/` |
| Bug tracking | `BUGS.md`, `KNOWN_ISSUES.md` |

**When found, use AskUserQuestion to ask the user**:

> Detected existing record files in the project:
> - `CHANGELOG.md` (47 entries)
> - `docs/adr/` (5 decision files)
>
> Would you like to organize these into the SyberMem system?
> 1. **Import and organize** — Split content by type into `.sybermem/` directories, keep backups of original files
> 2. **Index only** — Don't move files, add links to original files in `.sybermem/INDEX.md`
> 3. **Skip** — Don't process, organize manually later

Processing rules:
- **Import and organize**: Parse existing records, classify as change/decision/requirement/bug, rewrite to `.sybermem/` directories using templates, rename original files to `*.backup.md`
- **Index only**: Add `- [existing] Project's original CHANGELOG.md contains 47 change entries, see original file` to the key conclusions section, add link rows to corresponding tables
- **Skip**: No action

### Step 6: Create CLAUDE.md / AGENTS.md (if not exists)

Create `CLAUDE.md` (Claude Code) and `AGENTS.md` (OpenCode) in the project root with SyberMem workflow rules.
If one already exists, only create the missing one.

### Step 7: Output summary

```markdown
## SyberMem System Initialized

**Project type:** [New project / Existing codebase]

**Storage directory:** [.sybermem/ created / ADR/ auto-migrated to .sybermem/ / Existing .sybermem/ reused]

**Created or updated:**
- `.sybermem/` directory structure
- `INDEX.md` (with key conclusions)
- Template files
- `CLAUDE.md` / `AGENTS.md`

**Project context (existing projects):**
- Tech stack: [detection results]
- Existing records: [import/index/skip results]
- Attention areas: [TODO/FIXME hotspots]

**Next steps:**
- Use `/record` to create records after completing work
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

- **`.sybermem/` is canonical**: New writes always go to `.sybermem/`
- **Legacy compatibility**: Old `ADR/` directories are auto-migrated on first use; users should not rename them manually
- **Warn on split state**: If both `.sybermem/` and `ADR/` exist, use `.sybermem/` and warn that `ADR/` was ignored
- **Scan but don't auto-create records for existing code**: Output suggestions, let the user decide
- **Idempotent safety**: Repeated execution won't destroy existing `.sybermem/` records
