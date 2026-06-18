# Codebase Scan Rules

This file contains the existing codebase scan and record detection logic for the `sybermem-init-project` skill.

## Step 5: Scan and analyze existing codebases

For existing codebases only:

1. Identify the tech stack (package.json / requirements.txt / go.mod etc.)
2. Scan recent Git history (last 20 commits)
3. Detect special code markers (TODO, FIXME, HACK, workaround)
4. Present findings to the user and suggest creating corresponding records

Write key findings into `.sybermem/INDEX.md` `## Key Conclusions` in concise bullet form.

## Step 6: Detect existing record files

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
