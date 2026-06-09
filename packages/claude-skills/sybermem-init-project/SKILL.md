---
name: sybermem-init-project
description: Use when initializing SyberMem project records for a new or existing codebase, or when an older project still uses ADR storage or stale SyberMem instruction files.
---

# sybermem-init-project Skill

Initialize or refresh the SyberMem project record system in the current project. `.sybermem/` is the canonical project data directory.

## Usage

Run `/sybermem-init-project` in the target project directory.

## Directory Resolution Rules

### Step 0: Resolve project root (with anti-nesting guard)

Before any other operation, walk up from the current working directory to find the nearest ancestor directory (including cwd itself) that contains **both** `.sybermem/` **and** `.claude/settings.json`.

**If a parent SyberMem root is found above cwd:**
- Do NOT create a new `.sybermem/` in the current subdirectory.
- Inform the user: "A SyberMem project root already exists at `<parent-path>`. Operating on that root instead."
- Ask whether they want to operate on the parent root (default) or create a separate nested project (rare).
- Only create a nested `.sybermem/` if the user explicitly confirms.

**If no SyberMem root is found:**
- Treat the current directory as the new project root and proceed with initialization.

**If cwd itself is the SyberMem root:**
- Proceed normally (this is the common case for existing projects).

After resolving the project root, apply legacy directory checks:
1. If the resolved root has `.sybermem/`, use it.
2. If the resolved root has only `ADR/`, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If the resolved root has both `.sybermem/` and `ADR/`, use `.sybermem/`, warn that `ADR/` was ignored.
4. If neither exists, create `.sybermem/`.

## Flow

### Step 1: Resolve existing state

- Apply the directory resolution rules above.
- If `.sybermem/INDEX.md` already exists after resolution, treat the project as already initialized.
- Before scanning code or regenerating files, inspect project-root `AGENTS.md` and `CLAUDE.md`.

### Step 1.1: Inspect project instruction files

Use these template files from this installed skill as the canonical refresh source:

- `project-files/AGENTS.md`
- `project-files/CLAUDE.md`
- `project-files/.claude/settings.json`
- `project-files/.sybermem/hooks/record_change_on_stop.py`

**MANDATORY: Before classifying any file, you MUST verify its existence using a file-system tool (Read, Glob, or equivalent). Do NOT infer existence from settings.json references, prior conversation context, or any other indirect evidence. If the tool confirms the file does not exist, classify it as `missing` regardless of what other signals suggest.**

Classify each project file as one of:

- **missing** — file does not exist on disk (verified by file-system tool)
- **fresh** — file exists on disk AND uses `.sybermem/` rules AND matches the current analysis-aware SyberMem-managed guidance, including `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, `/sybermem-digest`, `/sybermem-phase-analyze`, `/sybermem-phase-confirm`, and `/sybermem-update`
- **stale SyberMem-managed** — file exists on disk BUT still references `/init-project`, `/record`, `/summary`, ADR-era wording, is missing the new SyberMem-prefixed commands, or otherwise matches older SyberMem-managed wording such as a pre-digest or pre-analysis file
- **custom** — file exists on disk BUT does not clearly look like a SyberMem-managed instruction file

Refresh rules:

1. **missing** → create it from the matching template file.
2. **fresh** → leave it unchanged.
3. **stale SyberMem-managed** → ask the user whether to refresh it. Before overwriting, create a same-directory backup such as `AGENTS.md.backup` or `CLAUDE.md.backup`, then replace it with the current template.
4. **custom** → do not overwrite automatically. Explain why it appears custom and ask before replacing it.

If the project was already initialized and only instruction files needed refresh, you may skip the codebase scan and go directly to the summary.

### Step 1.2: Enable digest capability if missing

For projects that already have `.sybermem/INDEX.md`, check whether digest support is present:

- `.sybermem/digests/`
- `.sybermem/templates/digest-template.md`
- `## Stage Digests` section in `.sybermem/INDEX.md`

If any are missing:
- create the missing `digests/` directory
- create the missing `digest-template.md` from `project-files/.sybermem/templates/digest-template.md`
- insert the missing `## Stage Digests` section into `INDEX.md`

Do this idempotently. Never duplicate the section, never overwrite an existing digest template without asking, and never treat the absence of digest support as a reason to reinitialize the whole project.

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
├── digests/
├── hooks/
│   └── record_change_on_stop.py
└── templates/
    ├── change-template.md
    ├── decision-template.md
    ├── requirement-template.md
    ├── bug-template.md
    └── digest-template.md
```

### Step 4: Generate INDEX.md

Use the standard format, including:
- `## Key Conclusions` section + `<!-- add new conclusions here -->` placeholder
- `## Stage Digests` section + `<!-- add new digest records here -->` placeholder
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
- Create missing project-level `.claude/settings.json` from the template file when the project does not already define its own hook settings.
- Create missing `.sybermem/hooks/record_change_on_stop.py` from the template file when automatic mode is being installed.
- The generated `.claude/settings.json` must set `SYBERMEM_RECORD_MODE` and install the default Stop hook for automatic `change` records only.
- If the user approved a refresh in Step 1.1, back up and overwrite the stale SyberMem-managed files.
- Treat an existing `.claude/settings.json` as custom unless it clearly matches the SyberMem-managed template. Do not overwrite custom hook settings automatically.
- Keep custom files unless the user explicitly approves replacement.

### Step 8: Output summary

```markdown
## SyberMem System Initialized

**Project type:** [New project / Existing codebase / Existing project refreshed]

**Storage directory:** [.sybermem/ created / ADR/ auto-migrated to .sybermem/ / Existing .sybermem/ reused]

**Created or updated:**
- `.sybermem/` directory structure
- `INDEX.md` (with key conclusions)
- `INDEX.md` digest navigation when missing
- Template files
- `.sybermem/digests/` and digest template when digest support is enabled
- `.sybermem/hooks/record_change_on_stop.py` when auto mode is installed
- `CLAUDE.md` / `AGENTS.md` / project-level `.claude/settings.json`

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
