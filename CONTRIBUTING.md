# Contributing to SyberMem

Thanks for your interest in improving SyberMem. This guide covers the repo-specific
workflows you need to know before opening a PR.

## Development setup

```bash
# Editable installs for local development
pip install -e packages/core
pip install -e packages/cli

# Run the test suites
pytest packages/core packages/cli
```

Python 3.10+ is required.

## Supported platforms

- **Fully supported (runtime + validation):** Claude Code, OpenCode.
- **Codex skills + habit reminders:** Codex installs user-level skills to `~/.agents/skills`
  and a bounded `UserPromptSubmit` hook to `~/.codex/hooks/` for User Habit
  Memory prompt reminders through `additionalContext`. Package checks verify both
  skill discoverability and hook distribution. Codex project recall, hidden
  auto-resume, prompt/agent handler runtimes, `.codex/config.toml`, and background
  automation remain unsupported.
- **Metadata only (entry manifests, not fully wired runtimes):** Gemini, Cursor,
  Kimi. When touching these, keep their manifests consistent but do not claim full
  runtime support.

## Skills are synced, not hand-edited in two places

The **source of truth for skills is `packages/claude-skills/`**. The `skills/`
tree is a generated mirror used by the plugin.

- Edit skills under `packages/claude-skills/<skill>/`.
- Run `python scripts/sync-plugin-skills.py` to regenerate `skills/`.
- Never hand-edit `skills/` directly — it will be overwritten.

## Hooks have three synchronized copies

The prompt/stop hooks live in three authoritative locations that MUST stay
byte-identical:

- `.sybermem/hooks/` (current project runtime)
- `packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/`
- `skills/sybermem-init-project/project-files/.sybermem/hooks/`

When you change a hook, update all three. Hooks must **fail open** (never raise,
never block a prompt).

## Versioning is single-sourced

The version lives in the root `VERSION` file. To bump it:

```bash
# 1. edit VERSION
# 2. propagate to all 8 manifests (2 pyprojects + 5 plugin manifests + gemini)
python scripts/sync-version.py
```

`scripts/check-plugin-package.py` fails if any manifest diverges from `VERSION`.

## Before opening a PR

Run the package integrity check (must print `OK`):

```bash
python scripts/check-plugin-package.py
```

Also ensure:

- `pytest packages/core packages/cli` is green.
- No cache artifacts committed (`__pycache__`, `.pytest_cache`, `dist/`).
- If you changed skills, you ran `sync-plugin-skills.py`.
- If you bumped the version, you ran `sync-version.py`.
- Dual-language docs (`README.md` / `README.en.md`) are kept in sync when you
  change user-facing behavior.

Codex distribution or habit-hook changes should also run the non-mutating smoke set:

```bash
python -m pytest packages/core/tests/test_package_integrity_scripts.py packages/core/tests/test_init_project_distribution.py -q
python scripts/check-plugin-package.py
```

## Project INDEX workflow (`.sybermem/INDEX.md`)

`.sybermem/INDEX.md` is a derived file, not a canonical source file for normal record work.

- Canonical record content lives in the record markdown files under `.sybermem/changes/`, `.sybermem/decisions/`, `.sybermem/requirements/`, and `.sybermem/bugs/`.
- New records should use generated UUID-backed `record_id` values. Legacy numeric records remain readable.
- Record creation is still handled by `/sybermem-record` skill orchestration. Do not document or add a separate record-creation CLI in PRs.
- In PRs, merge the canonical record files first, then rebuild the derived project index with `sybermem project index build` or verify it with `sybermem project index check`.
- Do not hand-edit `.sybermem/INDEX.md` as part of the normal record workflow.

## Commit and PR style

- Keep changes focused and minimal.
- Match the existing code style and CLI patterns.
- Describe user-visible behavior changes clearly in the PR.
