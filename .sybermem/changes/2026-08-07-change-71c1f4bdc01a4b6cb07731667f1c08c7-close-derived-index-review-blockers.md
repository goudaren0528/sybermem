---
type: change
record_id: change-71c1f4bdc01a4b6cb07731667f1c08c7
date: 2026-08-07
title: Close derived INDEX review blockers
status: implemented
source: Code review follow-up
key_conclusion: SyberMem derived INDEX generation now validates untrusted record metadata, escapes Markdown safely, and update/install propagation carries the UUID-backed record contract end to end.
topics: [quality, distribution, index]
author: Sisyphus
related_files: [packages/core/sybermem_core/project_index.py, packages/core/sybermem_core/project_index_render.py, packages/cli/sybermem_cli/main.py, packages/claude-skills/sybermem-init-project/project-files/.sybermem/INDEX.md, scripts/check-plugin-package.py]
related: [change-6a3ab8a0e44e4c41843b66bde8b7134a]
---

## Change Content

Closed the blocking review findings for UUID-backed records and derived project INDEX generation. The Core project-index boundary now accepts only legacy `type-001` IDs and UUID-backed `type-32hex` IDs for change, decision, requirement, and bug records; rejects unsafe topics and paths with typed metadata errors; escapes Markdown metacharacters in generated rows and conclusions; and keeps generated output idempotent.

The CLI `project index build` and `project index check` commands now catch project-index typed errors and return exit code 1 with concise stderr instead of leaking tracebacks. Init-project distribution now ships ID-column derived-index wording plus four record templates carrying `record_id`, `key_conclusion`, `topics`, and source/priority/severity metadata. Project health checks now detect missing and stale record templates so `/sybermem-update` can propagate the contract to existing projects. Local install/update scripts force-refresh Core and CLI packages, and package integrity checks enforce all runtime refresh scripts.

## Reason for Change

The initial UUID/derived-INDEX feature left unsafe Markdown interpolation, traceback-prone CLI errors, stale init-project templates, and local installer refresh gaps. Those gaps made the feature unsafe for untrusted record metadata and incomplete for fresh or upgraded projects.

## Impact Scope

- Core derived project INDEX generation and check/build idempotence
- CLI project-index build/check error handling
- Init-project distributed project-files and health-check propagation
- Local/remote installer runtime refresh package integrity
- Source-to-mirror skill tree synchronization

## Implementation

- Added strict validation for record IDs, topics, and generated link paths.
- Escaped table and inline Markdown text and percent-encoded generated link targets from actual `.sybermem` paths.
- Preserved legacy numeric IDs and UUID-backed IDs while rejecting invalid metadata at the derived-index boundary.
- Added concise CLI handling for duplicate IDs and invalid metadata errors.
- Updated init-project INDEX/template/health-check source and synced plugin mirrors.
- Updated local Bash/PowerShell install/update scripts and package checker runtime refresh coverage.

## Test Verification

- `uv run pytest packages/core packages/cli` -> 133 passed
- `uv run pytest packages/cli -q` -> 19 passed
- `python -B scripts/check-plugin-package.py` -> OK
- `python -m build --no-isolation --outdir <temp> packages/core` -> passed
- `python -m build --no-isolation --outdir <temp> packages/cli` -> passed
- `python -B -m sybermem_cli.main project index build` -> current
- `python -B -m sybermem_cli.main project index check` -> current

## Notes

Python LSP diagnostics could not run because the configured `basedpyright` server is not installed and was previously declined in this environment.
