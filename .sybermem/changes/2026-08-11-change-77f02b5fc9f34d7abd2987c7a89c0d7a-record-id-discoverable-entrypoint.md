---
type: change
record_id: change-77f02b5fc9f34d7abd2987c7a89c0d7a
date: 2026-08-11
title: Make record-id generation discoverable via CLI command and package export
key_conclusion: Added `sybermem record id --type <type>` CLI command and re-exported generate_record_id from the package root so record creation has a discoverable entrypoint instead of forcing callers to guess a buried module path
topics: [usability, cli, distribution]
status: implemented
related: [change-6a3ab8a0e44e4c41843b66bde8b7134a]
---

## Change Content

Record creation requires a canonical `record_id` from `generate_record_id`, but that helper had no discoverable entrypoint: no CLI command exposed it, and it was not re-exported from the package root. Callers (and the record skill) had to know it lives in `sybermem_core.records` — so in practice they guessed wrong repeatedly (`project id generate`, `sybermem_core.record_id`, `sybermem_core.identity`, package-root import), then fell back to hand-crafting a UUID, which the skill explicitly forbids.

Fixes:
- **A (CLI):** added `sybermem record id --type <change|decision|requirement|bug>` (`cmd_record_id`), text or `--format json`, with the type validated against `RECORD_TYPES` at the argparse boundary. Mirrors the discoverable shape of `sybermem project index build/check`.
- **C (export):** re-exported `generate_record_id` from `sybermem_core/__init__.py` (`__all__`), so `from sybermem_core import generate_record_id` — the natural first guess — works.
- Updated the record skill Step 5 to give the exact CLI command first and the `from sybermem_core import generate_record_id` fallback, explicitly telling it not to guess import paths or subcommands. Updated the CLI README.

## Reason for Change

A real discoverability / interface-consistency defect surfaced from a live record session: the AI spent almost the entire run probing for how to mint an id (7+ failed forms) instead of writing the record. The capability existed but had no findable door.

## Impact Scope

- `packages/cli/sybermem_cli/main.py`: `cmd_record_id` + `record id` subparser + imports.
- `packages/core/sybermem_core/__init__.py`: re-export.
- `packages/claude-skills/sybermem-record/SKILL.md` + mirror; `packages/cli/README.md`.
- Tests: `test_cli_record_id.py` (3) + package-root export test in `test_records.py`.
- Verified: core 139 + cli 22 pass; both entrypoints exercised live.
