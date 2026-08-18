# File Classification Rules

This file contains the complete file classification logic, protocol-block handling rules, and non-destructive update rules for the `sybermem-init-project` skill.

## Step 1.1: Inspect project instruction files

Use these template files from this installed skill as the canonical refresh source:

- `project-files/.claude/settings.json`
- `project-files/.sybermem/hooks/record_change_on_stop.py`
- `project-files/.sybermem/hooks/check_project_health.py`

**MANDATORY: Before classifying any file, you MUST verify its existence using a file-system tool. Do NOT infer existence from settings.json references, previous tool output, or conversation context. If the tool confirms the file does not exist, classify it as `missing` regardless of what other signals suggest.**

Classify each project file as one of:

- **missing** — file does not exist on disk (verified by file-system tool)
- **fresh** — file exists on disk and matches the current SyberMem-managed behavior set for this release, including the current analysis-aware command set and workflow guidance
- **stale SyberMem-managed** — file exists on disk and is recognizably SyberMem-managed, but is missing newly required behavior or wording for this release (for example pre-digest or pre-analysis managed content)
- **custom** — file exists on disk but no longer clearly behaves like a SyberMem-managed instruction file or template-derived file structure for this release.

Refresh rules:

1. **missing** → create it from the matching template file.
2. **fresh** → leave it unchanged.
3. **stale SyberMem-managed** → ask the user whether to refresh it. Before overwriting, create a same-directory backup (e.g. `.sybermem/hooks/<name>.py.bak`), then replace it with the current template. This applies to SyberMem-owned files (hooks, templates, `.claude/settings.json`); `CLAUDE.md` / `AGENTS.md` are NEVER replaced from a template — they are handled by protocol-block removal only (see below).
4. **custom** → do not overwrite automatically. Explain why it appears custom and ask before replacing it.

## Protocol-block removal

For `CLAUDE.md` and `AGENTS.md`, SyberMem no longer injects or refreshes a session-entry protocol block. Legacy projects may still carry a marker-bounded `SYBERMEM_SESSION_PROTOCOL:START`/`END` block from older versions; init/update must remove it.

- If the file contains `SYBERMEM_SESSION_PROTOCOL:START` and `SYBERMEM_SESSION_PROTOCOL:END`, remove only the contents inside that block.
- If the file is purely SyberMem-managed (only the protocol block, or an old heavy SyberMem template with no user content), delete the whole file.
- If the file has user content outside the block, strip only the block and preserve the rest verbatim.
- If the file has no block, leave it untouched.

The visible `/using-sybermem` skill is the manual entrypoint; no instruction-file injection is needed.

If the project was already initialized and only instruction-file protocol-block removal is needed, you may skip the codebase scan and go directly to the summary.

## Non-Destructive Update Rules

**These rules apply to ALL update operations, whether triggered by fast-path or full flow.**

| File | Allowed Update | Forbidden |
|---|---|---|
| `CLAUDE.md` / `AGENTS.md` | Remove the bounded `SYBERMEM_SESSION_PROTOCOL:START`/`END` block only. If the block exists, remove only its contents. If the file is purely SyberMem-managed, delete the whole file. All content outside the block markers is preserved verbatim. | Injecting or refreshing a protocol block; overwriting the entire file when it contains user content outside the protocol block. |
| `.gitignore` (git projects only) | Insert or refresh the bounded `# >>> SyberMem >>>` / `# <<< SyberMem <<<` block that ignores machine-local runtime/scripts (`.sybermem/hooks/`, `.sybermem/` runtime dotfiles, `.claude/settings.json`). If the block exists, replace only its contents. All content outside the markers is preserved verbatim. Skip entirely for non-git projects. | Ignoring shareable memory (records/digests/analysis/templates/`INDEX.md`/`project.yaml`); creating `.gitignore` in a non-git project; overwriting unrelated ignore rules. |
| `.claude/settings.json` | Read with `json.load`, add/update only SyberMem-owned keys (`env.SYBERMEM_RECORD_MODE`, `hooks.SessionStart`, `hooks.Stop`), write back with `json.dump`. All other keys, env vars, and hooks are preserved. | Overwriting the entire file from template. |
| `.sybermem/INDEX.md` | Insert missing sections (`## Phase Digests`, `## Topic Index`) at the appropriate position. All existing Key Conclusions, record tables, and user data are preserved. | Regenerating the entire file from template. |
| `.sybermem/hooks/*.py` | Full replacement from template — these are SyberMem-owned executables with no user content. | — |
| `.sybermem/templates/*.md` | Full replacement from template — these are SyberMem-owned templates. | — |
