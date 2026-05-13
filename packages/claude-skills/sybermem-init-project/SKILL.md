---
name: sybermem-init-project
description: Use when initializing SyberMem project records for a new or existing codebase, or when an older project still uses ADR storage or stale SyberMem instruction files.
---

# sybermem-init-project Skill

Initialize or refresh the SyberMem project record system in the current project. `.sybermem/` is the canonical project data directory.

## Usage

Run `/sybermem-init-project` in the target project directory.

## Directory Resolution Rules

Resolve the project data directory before doing any other work:

1. If `.sybermem/` exists, use it.
2. If only `ADR/` exists, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If both `.sybermem/` and `ADR/` exist, use `.sybermem/`, warn that `ADR/` was ignored, and do not auto-merge them.
4. If neither exists, create `.sybermem/`.

## Flow

### Step 1: Resolve existing state

- Apply the directory resolution rules above.
- If `.sybermem/INDEX.md` already exists after resolution, treat the project as already initialized.
- Before scanning code or regenerating files, inspect project-root `AGENTS.md` and `CLAUDE.md`.

### Step 1.1: Inspect project instruction files

Use these template files from this installed skill as the canonical refresh source:

- `.claude/skills/sybermem-init-project/project-files/AGENTS.md`
- `.claude/skills/sybermem-init-project/project-files/CLAUDE.md`

Classify each existing project file as one of:

- **missing** — file does not exist
- **fresh** — uses `.sybermem/` rules and references `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, and `/sybermem-update`
- **stale SyberMem-managed** — still references `/init-project`, `/record`, `/summary`, ADR-era wording, or is missing the new SyberMem-prefixed commands
- **custom** — exists but does not clearly look like a SyberMem-managed instruction file

Refresh rules:

1. **missing** → create it from the matching template file.
2. **fresh** → leave it unchanged.
3. **stale SyberMem-managed** → ask the user whether to refresh it. Before overwriting, create a same-directory backup such as `AGENTS.md.backup` or `CLAUDE.md.backup`, then replace it with the current template.
4. **custom** → do not overwrite automatically. Explain why it appears custom and ask before replacing it.

If the project was already initialized and only instruction files needed refresh, you may skip the codebase scan and go directly to the summary.

### Step 2: Determine project type

Only if initialization has not happened yet, check for code files (excluding node_modules, .git, etc.):

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
- `## Key Conclusions` section + `<!-- add new conclusions here -->` placeholder
- 4 type tables + `<!-- add new records here -->` placeholder

### Step 5: Scan and analyze existing codebases

For existing codebases only:

1. Identify the tech stack (package.json / requirements.txt / go.mod etc.)
2. Scan recent Git history (last 20 commits)
3. Detect special code markers (TODO, FIXME, HACK, workaround)
4. Present findings to the user and suggest creating corresponding records

Write key findings into `.sybermem/INDEX.md` `## Key Conclusions` in concise bullet form.

### Step 6: Detect existing record files

Scan for common record/documentation files:

| Target | Common paths |
|--------|-------------|
| Changelog | `CHANGELOG.md`, `CHANGES.md`, `HISTORY.md` |
| ADR/decision records | `docs/adr/`, `docs/decisions/`, `adr/`, `doc/architecture/` |
| Requirements/design docs | `docs/design/`, `docs/specs/`, `docs/rfcs/` |
| Bug tracking | `BUGS.md`, `KNOWN_ISSUES.md` |

When found, ask the user whether to:

1. **Import and organize** — rewrite content into `.sybermem/` records and keep backups
2. **Index only** — add links from `.sybermem/INDEX.md`
3. **Skip** — leave them untouched

### Step 7: Create or refresh project instruction files

- Create missing `CLAUDE.md` / `AGENTS.md` from the template files.
- If the user approved a refresh in Step 1.1, back up and overwrite the stale SyberMem-managed files.
- Keep custom files unless the user explicitly approves replacement.

### Step 8: Output summary

```markdown
## SyberMem System Initialized

**Project type:** [New project / Existing codebase / Existing project refreshed]

**Storage directory:** [.sybermem/ created / ADR/ auto-migrated to .sybermem/ / Existing .sybermem/ reused]

**Created or updated:**
- `.sybermem/` directory structure
- `INDEX.md` (with key conclusions)
- Template files
- `CLAUDE.md` / `AGENTS.md`

**Next steps:**
- Use `/sybermem-record` after meaningful work
- Use `/sybermem-summary` for weekly or monthly progress reports
- Use `/sybermem-update` later to refresh global skills and re-check this project
```

## Key Principles

- **`.sybermem/` is canonical**: New writes always go to `.sybermem/`
- **Legacy compatibility**: Old `ADR/` directories are auto-migrated on first use; users should not rename them manually
- **Instruction refresh is explicit**: stale SyberMem-managed project files should be refreshed with backups, custom files only with user approval
- **Scan but don't auto-create records for existing code**: output suggestions and let the user decide
- **Idempotent safety**: repeated execution should not destroy valid `.sybermem/` records or custom project instructions
