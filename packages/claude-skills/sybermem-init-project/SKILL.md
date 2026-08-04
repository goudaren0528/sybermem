---
name: sybermem-init-project
description: Use when initializing SyberMem project records for a new or existing codebase, or when an older project still uses ADR storage or stale SyberMem instruction files.
---

# sybermem-init-project Skill

**Announce at start:** "I'm using the sybermem-init-project skill to initialize or refresh the SyberMem system in this project."

Initialize or refresh the SyberMem project record system in the current project. `.sybermem/` is the canonical project data directory.

## Core Invariants

- **No file classification without file-system verification.**
- **No nested `.sybermem/` without explicit user approval.**
- **No stale SyberMem-managed file may remain classified as fresh if it is missing newly required managed behavior.**
- **No protocol update should rewrite more than the bounded `using-sybermem` block when the markers already exist.**

<HARD-GATE>
Do NOT classify any file without first verifying its existence on disk with a file-system tool. Do NOT infer existence from settings.json references, previous tool output, or conversation context. If the tool confirms the file does not exist, classify it as `missing` regardless of what other signals suggest.

Do NOT create `.sybermem/` in a subdirectory when a parent SyberMem root already exists above cwd. Inform the user and ask before creating a nested project.
</HARD-GATE>

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

### Step 0.5: Fast-path health check (existing projects only)

**First, update the health check script itself.** Copy `project-files/.sybermem/hooks/check_project_health.py` from the installed skill template to the project's `.sybermem/hooks/check_project_health.py`, replacing the existing file unconditionally. This is safe because the script is SyberMem-owned and contains no user content. This ensures the health check always knows about the latest managed-file requirements, even when the project was initialized with an older version of SyberMem.

Then run it:

```bash
python .sybermem/hooks/check_project_health.py
```

Parse the JSON output and branch:

**If `overall == "fresh"`:**
- Output: "SyberMem project is up to date. No changes needed."
- Skip all subsequent steps. Skill is complete.

**If `overall == "needs_update"`:**
- Process only the `actions_needed` list. Each action specifies its update method:
  - `"create ..."` → create the file from the init-project template
  - `"insert ..."` → non-destructive partial update (see `file-classification-rules.md` Non-Destructive Update Rules)
  - `"replace ..."` → full replacement (only for SyberMem-owned files like hooks and templates)
  - `"add ..."` → surgical JSON patch (only for settings.json hook entries)
- After processing all actions, output a summary of what was changed and skip remaining steps.

**If `overall == "not_initialized"` or the script does not exist:**
- Proceed with the full initialization flow starting at Step 1.

### Step 1: Resolve existing state

- Apply the directory resolution rules above.
- If `.sybermem/INDEX.md` already exists after resolution, treat the project as already initialized.
- Before scanning code or regenerating files, inspect project-root `AGENTS.md` and `CLAUDE.md`.

Read `file-classification-rules.md` for the complete file classification logic, protocol-block handling rules, and non-destructive update rules.

Read `capability-checks.md` for the digest, analysis, theme-digest, and archived-conclusions capability checks.

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

Read `codebase-scan-rules.md` for the existing codebase scan and record detection logic.

### Step 7: Create or refresh project instruction files

- Create missing `CLAUDE.md` / `AGENTS.md` from the template files.
- Create missing project-level `.claude/settings.json` from the template file when the project does not already define its own hook settings.
- Create missing `.sybermem/hooks/record_change_on_stop.py` from the template file when automatic mode is being installed.
- Create missing `.sybermem/hooks/detect_record_intent.py` from the template file when reminder-first record-intent capture is being installed.
- Create missing `.sybermem/hooks/task_recall.py` from the template file when read-only task recall is being installed for prompt-time hook support.
- Ensure the global launcher `~/.claude/sybermem/launch_record_change_on_stop.py` exists; if not, instruct the user to refresh global skills first or run `/sybermem-update`.
- Create missing `.sybermem/hooks/session_start_context.py` from the template file when startup context injection is being installed.
- Create missing `.sybermem/hooks/check_project_health.py` from the template file to enable fast-path updates on subsequent runs.
- Create missing `.sybermem/project.yaml` with project identity. Generate `project_id` as a ULID or UUID4 (once, never changes). Derive `slug` from `git remote get-url origin` (last path segment without `.git`) or fall back to the current directory name. Set `schema_version: 1`, `name` equal to `slug`, `repository.remote` and `repository.default_branch` from git (leave empty if unavailable), and `created_at` as current ISO8601 timestamp. If `project.yaml` already exists, do not overwrite it.
- After generating or confirming `project.yaml`, register the project in the user's Hub registry at `~/.sybermem/projects.yaml`. Read the existing registry (create the file and `~/.sybermem/` directory if missing). Look up the current `project_id`: if found, update its `path` to the current project root; if not found, append a new entry with `project_id`, `slug`, `path`, `remote`, and `registered_at`. Write the file back.
- Ensure the global session start launcher `~/.claude/sybermem/launch_session_start_context.py` exists; if not, instruct the user to refresh global skills first or run `/sybermem-update`.
- Create missing `.sybermem/hooks/launch_record_change_on_stop.py` from the template file.
- If the project uses the SyberMem-managed Stop hook entry, rewrite `.claude/settings.json` to call the global absolute launcher path instead of any project-local relative hook path.
- Even if `.claude/settings.json` is otherwise custom, if the Stop hook contains a recognized old SyberMem hook command, replace just that command with the global launcher path and leave the rest of the file unchanged.
- If `.claude/settings.json` is otherwise custom, patch only the recognized SyberMem-managed `UserPromptSubmit`, `SessionStart`, and `Stop` hook entries that are missing or stale. Do not overwrite unrelated custom hooks, env, or instructions.
- The generated `.claude/settings.json` must set `SYBERMEM_RECORD_MODE`, install the default SessionStart hook for startup context injection, install the default `UserPromptSubmit` hook for both natural-language record-intent capture and read-only task recall, and install the default Stop hook for automatic `change` records / reminder-first nudges.
- If the user approved a refresh in Step 1.1, back up and overwrite the stale SyberMem-managed files.
- Treat an existing `.claude/settings.json` as custom unless it clearly matches the SyberMem-managed template. Do not overwrite unrelated custom hook settings automatically.
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
- `.sybermem/theme-digests/` and theme digest template when theme-digest support is enabled
- `INDEX.md` theme digest navigation when missing
- `INDEX.md` archived conclusions section when missing
- `.sybermem/hooks/record_change_on_stop.py` when auto mode is installed
- `.sybermem/hooks/detect_record_intent.py` when reminder-first record-intent capture is installed
- `.sybermem/hooks/task_recall.py` when read-only task recall support is installed
- `.sybermem/hooks/launch_record_change_on_stop.py` when root-resolving launcher support is installed
- managed Stop hook command updated to the launcher form when needed
- `.sybermem/hooks/session_start_context.py` when startup context injection is installed
- `.sybermem/hooks/check_project_health.py` for fast-path update detection
- managed `UserPromptSubmit` hook entries repaired when missing or stale, without overwriting unrelated custom hooks, env, or instructions
- `.sybermem/project.yaml` project identity when missing
- `~/.sybermem/projects.yaml` user Hub registry entry
- managed SessionStart hook command updated to the launcher form when needed
- `using-sybermem` session protocol block inserted or refreshed in `CLAUDE.md` / `AGENTS.md` when applicable
- `CLAUDE.md` / `AGENTS.md` / project-level `.claude/settings.json`

**Next steps:**
- Use `/sybermem-record` after meaningful work
- Use `/sybermem-summary` for weekly or monthly progress reports
- If this project belongs in Team memory, use `/sybermem-team-publish`
- If the project is already linked to Team memory, use `/sybermem-team-summary` to generate a Team management summary
- Use `/sybermem-update` later to refresh global skills and re-check this project
```

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:

- Classifying a file as `fresh` or `custom` without first verifying it exists on disk with a filesystem tool
- Creating `.sybermem/` in a subdirectory when a parent SyberMem root already exists
- Reporting "kept local version" for a file that does not actually exist
- Skipping the launcher file creation because "the hook file already exists"
- Treating a pre-digest or pre-analysis managed file as `fresh` when it is missing newly required behavior
- Repairing a stale `UserPromptSubmit` hook by overwriting the whole `.claude/settings.json` file instead of patching only the recognized SyberMem-managed entry

**All of these mean: go back to Step 1.1, re-verify with filesystem tools, and re-classify.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "This file looks fresh, I don't need to check" | Without filesystem verification, you're guessing. HARD-GATE requires tool-verified classification. |
| "The project was just initialized, everything must be fine" | New features may have been added since initialization. Always verify against current templates. |
| "I'll skip the backup, the old file wasn't important" | The user may have custom content. Always backup stale files before replacing. |
| "This settings.json is custom, I'll overwrite it with the template" | Only replace SyberMem-owned entries. Preserve all other user configuration. |
| "The new task recall hook needs a full settings rewrite" | It does not. Repair only the recognized SyberMem-managed `UserPromptSubmit` entry and preserve unrelated custom hooks, env, and instructions. |

## Terminal State

This skill is complete when:
- the project root is resolved and all managed files are classified
- missing files are created, stale files are refreshed (with backup), and custom files are preserved
- the output summary has been shown to the user
- the user knows which commands are available next

## Key Principles

- **`.sybermem/` is canonical**: New writes always go to `.sybermem/`
- **Legacy compatibility**: Old `ADR/` directories are auto-migrated on first use; users should not rename them manually
- **Instruction refresh is explicit**: stale SyberMem-managed project files should be refreshed with backups, custom files only with user approval
- **Scan but don't auto-create records for existing code**: output suggestions and let the user decide
- **Idempotent safety**: repeated execution should not destroy valid `.sybermem/` records or custom project instructions

## Integration

**Related skills:**
- **sybermem-update** — Calls this skill as its Step 2
- **sybermem-record** — Available after initialization
- **sybermem-summary** — Available after initialization
