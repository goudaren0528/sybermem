---
type: change
record_id: change-b135cb2e65a24808aaef1f3007acee43
date: 2026-08-07
title: Record skill offers a one-shot fast path
key_conclusion: Added a fast path to the record skill that writes a single unambiguous record in one pass from context, skipping per-item confirmation friction while keeping the same HARD-GATE completion guarantees
topics: [usability, skills]
status: implemented
related: [change-049]
---

## Change Content

Added a "Choose a path: fast vs full" section to `sybermem-record/SKILL.md`:

- **Fast path (default for a single, unambiguous record):** auto-detect type, generate metadata, infer + write relations, write the file, build/check the index — all in one pass, no per-item confirmation. Announce what was recorded once at the end so the user can correct.
- **Full path:** the existing step-by-step flow, used when type is unclear, multiple records may be warranted, it is a trade-off-heavy `decision`, or the user wants review first.

Both paths obey the same `<HARD-GATE>` and `## Verification`. The relation step now writes inferred relations directly on the fast path (mentioned in the final summary) instead of prompting per relation. Synced to the mirror skill copy.

## Reason for Change

A2: the 11-step flow with per-item confirmation is right for high-stakes decisions but over-heavy for routine records, discouraging timely recording. Fast path removes confirmation friction, never the completion guarantees.

## Impact Scope

- `packages/claude-skills/sybermem-record/SKILL.md` + mirror.
- A new distribution test asserts all skill definitions stay byte-identical across the canonical and mirror trees.
