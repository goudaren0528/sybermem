[中文](README.md) | **English**

# SyberMem

A set of Claude Code / OpenCode skills for tracking project development history. It records changes, decisions, requirements, and bugs as structured files, so AI can recall project context across sessions.

## How It Works

Install the skills, run `/sybermem-init-project` in your project, use `/sybermem-record` after meaningful work, use `/sybermem-phase-analyze` to build or refresh `.sybermem/analysis/phase-index.md` from project history, use `/sybermem-phase-confirm` to confirm or adjust candidate phases, use `/sybermem-summary` to view the current-state panel for the most recently active confirmed phase (falling back to the weekly/monthly dynamic report if the analysis layer does not exist yet), and use `/sybermem-digest` when a meaningful phase ends and you want a durable summary stored in `.sybermem/digests/`. The phase index is a persistent project analysis artifact, not a final digest. At session start, AI reads `.sybermem/INDEX.md` to recall key conclusions from past work. In `auto` mode, the stop hook still writes a lightweight `change` trail automatically, but it may also emit a non-blocking suggestion that a change is important enough for `/sybermem-record`, or that a recent cluster of work may be ready for `/sybermem-digest`.

`/sybermem-summary` answers “what is the current state of this phase?”, while `/sybermem-digest` records “what did this phase ultimately conclude?”

## Recommended upgrade path

For an existing project, run `/sybermem-update`:

1. Refresh the globally installed SyberMem skills
2. Continue in the current project with `/sybermem-init-project`
3. Migrate legacy `ADR/` if needed
4. Check whether local `AGENTS.md` / `CLAUDE.md` files are stale and offer a refresh

## Upgrading from ADR/

If your project already uses `ADR/`, do not rename anything manually. The first run of `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, `/sybermem-digest`, `/sybermem-phase-analyze`, or `/sybermem-phase-confirm` automatically migrates the old `ADR/` directory to `.sybermem/`.

If both `.sybermem/` and `ADR/` exist, the system uses `.sybermem/` and warns that `ADR/` was ignored.

Refreshing global skills alone does not automatically refresh project-local `AGENTS.md` / `CLAUDE.md`, so after upgrading you should run `/sybermem-update` inside each target project.

Updating global skills does not automatically enable digest support inside every project. To use `/sybermem-digest` in a project, run `/sybermem-update` in that project first. This creates only the missing digest-related structure and does not silently overwrite project-owned files.

Existing projects also receive `.sybermem/analysis/phase-index.md` project by project through `/sybermem-update`.

If an older project still contains project-local copies such as `.claude/skills/sybermem-*`, Claude may load both the local and global copies and show duplicates in the `/` list. If you have adopted the global-install model, you can safely delete those old local copies.

If you want an existing project to receive the refreshed stop-hook nudge behavior, you still need to enter that project and run `/sybermem-update` there. Global skills update once, but local hook/template/instruction refresh still applies project by project.

If you previously encountered stop hook errors (file not found) when working in a subdirectory, running `/sybermem-update` fixes the issue. The updated hook automatically walks up to find the nearest ancestor with both `.sybermem/` and `.claude/settings.json` as the project root.

The subdirectory stop-hook fix now uses a global launcher. Updated projects automatically migrate the Stop hook command to the global absolute path `python C:/Users/69046/.claude/sybermem/launch_record_change_on_stop.py`. That means the launcher can always start, find the real project root, and then invoke the project-local `record_change_on_stop.py`.

After `/sybermem-update`, existing projects should be auto-repaired this way. Even if `.claude/settings.json` is otherwise custom, SyberMem should still replace that one line when the old Stop hook command is clearly recognized as SyberMem-managed.

Many SyberMem behavior changes do not live only in the globally installed skill definitions. They also depend on project-local managed files such as `CLAUDE.md`, `AGENTS.md`, `.claude/settings.json`, and hook templates. For existing projects, you usually need to run `/sybermem-update` once after upgrading so the project actually receives the new local behavior.

`/sybermem-update` should create missing managed files, refresh stale SyberMem-managed files, and preserve custom local files without silently overwriting them.

SyberMem now uses a `using-sybermem` protocol block near the top of `CLAUDE.md` / `AGENTS.md` to establish session-entry rules. When an existing project runs `/sybermem-update`, managed instruction files should receive that block automatically; custom files should not be overwritten wholesale by default.

`using-sybermem` is now a dual-entry protocol: the bounded block at the top of `CLAUDE.md` / `AGENTS.md` applies automatically at session start, while `/using-sybermem` is the visible diagnostic entrypoint. When run manually, it reports the current SyberMem state, the routing behavior for summary/digest/analyze/record, and the recommended next command.

## Install

### Claude Code Plugin Install (Recommended)

For Claude Code users who want plugin-managed hooks and skills, the plugin installation flow is the preferred path.

#### Local development / testing

```bash
claude --plugin-dir .
```

This loads `.claude-plugin/` from the current repository, which is useful for validating plugin metadata, lifecycle hooks, and the plugin-facing `skills/` tree.

Once installed or updated, the CLI is available as a normal command:

```bash
sybermem project init --register
sybermem index build
sybermem search hooks --scope workspace
```

#### Current distribution status

SyberMem already includes `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Marketplace-style distribution is prepared, but the fully dogfooded runtime paths today are Claude Code and OpenCode.

### Claude Code / OpenCode Script Install (Compatibility Mode)

These commands remain as compatibility/direct install paths rather than the future default.

#### One-liner (requires public repo)

```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

#### Clone and install

```bash
# macOS / Linux
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem && ./scripts/install.sh

# Windows (PowerShell)
git clone https://github.com/goudaren0528/sybermem.git
cd sybermem; .\scripts\install.ps1
```

### OpenCode

OpenCode has a dedicated plugin runtime. See [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

### Initialize a project

After the global install, open your project and run:

```text
/sybermem-init-project
```

This creates or refreshes:
- `.sybermem/`
- `.sybermem/digests/` (phase digest directory)
- `.sybermem/analysis/phase-index.md` (persistent phase analysis artifact)
- `.sybermem/hooks/record_change_on_stop.py` (default auto-change hook helper)
- `CLAUDE.md`
- `AGENTS.md`
- `.claude/settings.json` (with the default SyberMem `auto` / `remind` mode)

It does not install another copy of the skills into the project.

See [INSTALL.md](INSTALL.md) for details.

## Skills

| Skill | What it does |
|-------|-------------|
| `/sybermem-init-project` | Create or refresh the `.sybermem/` structure in a project, refresh managed instruction files, and migrate legacy `ADR/` on first run |
| `/sybermem-record` | Create a structured change / decision / requirement / bug record from the current session context |
| `/sybermem-summary` | Show the current-state panel for the most relevant active phase, with weekly/monthly fallback |
| `/sybermem-digest` | Create a durable phase digest from existing records |
| `/sybermem-theme-digest` | Create a durable topic-level digest that compresses one theme across multiple phases or records |
| `/sybermem-phase-analyze` | Build or refresh `.sybermem/analysis/phase-index.md` from project history |
| `/sybermem-phase-confirm` | Adjust confirmed phases, names, and lifecycle state |
| `/using-sybermem` | Diagnose the current SyberMem state and recommend the right next command |
| `/sybermem-update` | Refresh globally installed SyberMem skills, then re-check the current project |
| `/sybermem-search` | Query records by keyword, topic, phase range, date range, or record ID, including relations |
| `/sybermem-link` | Add a forward relation between two existing records (`implements` / `fixes` / `related` / `superseded-by`) |

## Daily Workflow

A practical day-to-day path for using SyberMem:

```text
Look up history             → /sybermem-search <keyword|topic|record-id>
Check current state         → /sybermem-summary
Finish meaningful work      → /sybermem-record
Refresh stale phase index   → /sybermem-phase-analyze
Close a phase               → /sybermem-digest
Compress a topic across phases → /sybermem-theme-digest <topic>
Unsure what to do next      → /using-sybermem
```

## Theme Digest Layer

In addition to phase digests (`/sybermem-digest`), SyberMem now supports theme digests (`/sybermem-theme-digest`):

- phase digest = what one phase ultimately concluded
- theme digest = what one topic ultimately concluded across multiple phases

Theme digests live under `.sybermem/theme-digests/`. The first version is single-topic only, prefers existing phase digests when available, and fills gaps with raw records.

## Relations, Search, and Governance

Records can now declare forward-only relationship fields in frontmatter:

- `implements: [requirement-NNN]`
- `fixes: [bug-NNN]`
- `related: [type-NNN]`
- `superseded_by: <record-id>`

`/sybermem-search` can surface:
- phase membership
- forward relations
- reverse references
- supersession hints
- archived conclusion matches

Topic Index lines may also carry optional suffixes:
- `[active]`
- `[low]`
- `[deprecated → <new-topic>]`

## What gets created in your project

```
.sybermem/
├── INDEX.md                        # Master index — Active/Archived Conclusions, Digests, Topic Index
├── changes/                        # Feature additions, modifications, deletions
├── decisions/                      # Tech choices, architecture designs
├── requirements/                   # User requirements, discussion outcomes
├── bugs/                           # Bug analysis and fixes
├── digests/                        # Phase digests
├── theme-digests/                  # Theme digests (topic across multiple phases)
├── analysis/
│   └── phase-index.md              # Persistent project analysis artifact (includes lifecycle field)
├── hooks/
│   ├── record_change_on_stop.py    # Default auto-change hook helper
│   ├── session_start_context.py    # SessionStart context injection script
│   ├── check_project_health.py     # Update fast-path health check script
│   └── launch_record_change_on_stop.py # Root-resolving stop-hook launcher helper
└── templates/
    ├── change-template.md
    ├── decision-template.md
    ├── requirement-template.md
    ├── bug-template.md
    ├── digest-template.md
    └── theme-digest-template.md

CLAUDE.md             # Claude Code instructions (workflow rules)
AGENTS.md             # OpenCode instructions (same content)
.claude/settings.json # Project-level hook mode (SessionStart / Stop)
```

`INDEX.md` currently contains these core sections:
- `Key Conclusions` — Active conclusions, injected at session start
- `Archived Conclusions` — Archived conclusions, not injected at startup but still searchable
- `Stage Digests` — phase digest index
- `Theme Digests` — topic-level digest index
- `Topic Index` — topic → record IDs (supports `[active]` / `[low]` / `[deprecated → ...]` suffixes)

## Directory resolution rules

- `.sybermem/` is canonical.
- If `.sybermem/` already exists, use it.
- If only `ADR/` exists, the first run of `/sybermem-init-project`, `/sybermem-record`, `/sybermem-summary`, `/sybermem-digest`, `/sybermem-phase-analyze`, or `/sybermem-phase-confirm` automatically renames it to `.sybermem/`.
- If both `.sybermem/` and `ADR/` exist, use `.sybermem/` and warn that `ADR/` was ignored.

## Supported Platforms

| Platform | Current status | Notes |
|----------|----------------|-------|
| Claude Code | fully supported | Plugin install (recommended) and script install (compatibility mode) are both dogfooded |
| OpenCode | fully supported | TypeScript plugin implements `session.created`, `session.idle`, and `experimental.session.compacting` |
| Gemini CLI | entry files present | `GEMINI.md` and extension metadata exist, but runtime behavior has not been dogfooded to the same degree |
| Cursor | metadata present | `.cursor-plugin/plugin.json` exists; runtime behavior not yet equally validated |
| Codex | metadata present | `.codex-plugin/plugin.json` exists; runtime behavior not yet equally validated |
| Kimi | metadata present | `.kimi-plugin/plugin.json` exists; runtime behavior not yet equally validated |

## Repo Structure

```
packages/claude-skills/               # Skill source for distribution inside the repo, not auto-loaded per project
├── sybermem-digest/
├── sybermem-init-project/
├── sybermem-link/
├── sybermem-phase-analyze/
├── sybermem-phase-confirm/
├── sybermem-record/
├── sybermem-search/
├── sybermem-summary/
├── sybermem-theme-digest/
├── sybermem-update/
└── using-sybermem/

scripts/                              # Install & update scripts
├── install-remote.sh / .ps1          # One-liner remote install
├── install.sh / .ps1                 # Local install
├── update.sh / .ps1                  # Update existing install
└── check-plugin-package.py           # Plugin package + real CLI validate check

docs/zh/                              # Chinese documentation
```

## Team MVP (in progress)

SyberMem is now moving into the Team MVP track:

- **Phase A**: `sybermem team init` — create the Team repo skeleton, write `team.yaml`, and bind the Git remote
- **Phase B**: `sybermem publish status` — publish the current project's `project.md` + `current-status.md` into the Team repo

`team sync`, `team review`, and digest/lesson publication will build on top of that foundation.

## License

MIT
