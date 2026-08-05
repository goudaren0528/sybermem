---
name: sybermem-theme-digest
description: Use when creating a durable topic-based digest that compresses multiple related phases or records into one theme-level conclusion.
---

# sybermem-theme-digest Skill

**Announce at start:** "I'm using the sybermem-theme-digest skill to create a durable topic-level digest."

Create a durable theme digest in `.sybermem/theme-digests/` so future project understanding does not require re-reading every phase digest or all raw records for one topic.

## Core Invariants

- **No theme digest without explicit source coverage.**
- **Theme digests are topic-based. First version supports one topic slug only.**
- **Coverage strategy is phase-digests-first-then-records.**

<HARD-GATE>
Do NOT create a theme digest unless ALL of the following are true:
1. A single topic slug has been identified
2. `source_phases`, `source_digests`, and `source_records` have been explicitly built and deduplicated
3. The output path, INDEX row, and theme digest file can all be written consistently

If any of these is false, STOP. Do not write the theme digest file.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Preconditions

Before creating a theme digest, verify all of the following:
- `.sybermem/theme-digests/` exists
- `.sybermem/templates/theme-digest-template.md` exists
- `.sybermem/INDEX.md` contains a `## Theme Digests` section
- `.sybermem/INDEX.md` contains the exact insertion anchor `<!-- add new theme digest records here -->` within that section

If any are missing, explain that theme-digest capability has not been enabled in this project yet and ask the user to run `/sybermem-update`.

## Usage

```text
/sybermem-theme-digest hooks
```

First version supports one topic slug only.

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply directory resolution rules above.
2. **Verify preconditions** — `.sybermem/theme-digests/` exists, `theme-digest-template.md` exists, `INDEX.md` has `## Theme Digests` with `<!-- add new theme digest records here -->`. If any missing, ask the user to run `/sybermem-update`.
3. **Identify the topic scope** — the user provides one topic slug (e.g. `hooks`). Do not merge topics in this first version.
4. **Collect candidate records** — read `## Topic Index` in `.sybermem/INDEX.md` for that topic. If the topic is missing, refuse and explain.
5. **Enrich with phase coverage** — read `.sybermem/analysis/phase-index.md` coverage map and determine which confirmed phases cover those records.
6. **Prefer phase digests first** — if any of those phases already have digests listed in `## Phase Digests`, use them as primary compressed sources.
7. **Fill gaps with raw records** — for records not covered by any existing phase digest, include the raw record file as a direct source.
8. **Deduplicate** — deduplicate `source_phases`, `source_digests`, and `source_records` by ID or path.
9. **Write the theme digest file** — path: `.sybermem/theme-digests/{YYYY-MM-DD}-{NNN}-{topic}.md`. Use `.sybermem/templates/theme-digest-template.md`. Set `coverage_strategy: phase-digests-first-then-records`.
10. **Update INDEX.md** — insert a row above `<!-- add new theme digest records here -->` in `## Theme Digests`: `| NNN | YYYY-MM-DD | topic | completed | X phases, Y digests, Z records | [link](theme-digests/file.md) |`

## Output Shape

```md
# Theme Digest: hooks

## Theme
- hooks

## Why This Theme Matters
- ...

## What Stabilized
- ...

## Cross-Phase Evolution
- phase-001: ...
- phase-004: ...

## Current Reusable Conclusions
- ...

## Open Edges
- ...

## Source Coverage
- Digests used: digest-001
- Raw records used: change-003, bug-001
```

## Error Handling

- Topic not found in Topic Index → stop and explain.
- Theme-digest capability missing → ask user to run `/sybermem-update`.
- No records for topic → stop and explain.
- Exact duplicate source coverage with an existing theme digest → do not create a second one; point to the existing file.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Merging multiple topic slugs into one theme digest
- Creating a theme digest without explicit source lists
- Repeating raw records already covered by a phase digest without a reason
- Treating a theme digest as a current-state summary instead of a durable conclusion

**All of these mean: go back to the relevant step and re-verify source coverage.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll just summarize all related topics together" | First version is one topic only. Keep the scope explicit. |
| "Those phase digests probably cover everything" | Verify. Use raw records to fill actual gaps. |
| "This is basically the same as /sybermem-digest" | No. Phase digest summarizes one phase; theme digest summarizes one topic across phases. |

## Terminal State

This skill is complete when:
- the theme digest file is written to `.sybermem/theme-digests/`
- the `INDEX.md` Theme Digests table has a new row
- `source_phases`, `source_digests`, and `source_records` are explicitly listed
- the user has been shown the theme digest path and coverage

## Integration

**Related skills:**
- **sybermem-digest** — phase digests are preferred source material
- **sybermem-summary** — current-state panel remains separate from durable theme conclusions
- **sybermem-update** — enables theme-digest support in older projects
