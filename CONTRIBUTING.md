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
- **Metadata only (entry manifests, not fully wired runtimes):** Gemini, Codex,
  Cursor, Kimi. When touching these, keep their manifests consistent but do not
  claim full runtime support.

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

## Key Conclusions governance (`.sybermem/INDEX.md`)

The `## Key Conclusions` section is injected at session start, so keep it high-signal:

- Record only **current operational truths and active constraints** — what matters now.
- Release history and implementation trivia belong in **archived conclusions** or a **phase/theme digest**, not in the active Key Conclusions list.
- Do not rewrite or reorder existing conclusions when adding a new one; append above the `<!-- add new conclusions here -->` marker.
- Auto-trail entries never go into Key Conclusions.

## Commit and PR style

- Keep changes focused and minimal.
- Match the existing code style and CLI patterns.
- Describe user-visible behavior changes clearly in the PR.
