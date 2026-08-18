---
name: using-sybermem
description: Use when you want a visible SyberMem entrypoint that diagnoses the current project root, loaded SyberMem layers, and the recommended next workflow command.
---

# using-sybermem Skill

**Announce at start:** "I'm using the using-sybermem skill to diagnose the current SyberMem state."

`using-sybermem` is the visible advisory entrypoint for the SyberMem system. It does not replace concrete skills like `record`, `summary`, `digest`, or `phase-analyze`. It reports the current project's SyberMem state and tells the user what the correct next command is.

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill unless the task explicitly asks for SyberMem diagnostics.
</SUBAGENT-STOP>

## Quick guide (for humans)

> Plain-language overview for people. **Not** the execution contract — the
> `<HARD-GATE>`, `## Flow`, and the routing rules below are authoritative and win
> on any conflict.

**What it does:** a "where am I / what next" entrypoint. It checks the current
project's SyberMem state and tells you the single recommended next command — it
does not do the downstream work itself.

**When to run:** when you're unsure what to do next, or want a quick read on
whether the project is initialized, up to date, and what command fits now.

**What you get:** the resolved project root, a short state summary, and one
recommended next command with the reason — never a silent record/digest/analyze.

## Core Invariant

- **`using-sybermem` reports and routes; it does not silently perform downstream business actions.**

<HARD-GATE>
Do NOT auto-run `phase-analyze`, `record`, `summary`, or `digest` without telling the user.
Do NOT treat candidate phases as canonical.
Do NOT ignore the resolved root and answer from the wrong directory context.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`.

## CLI Resolution

Before running SyberMem CLI commands, resolve a command variable first. On Windows PowerShell, prefer `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd` and store the chosen command in `$SyberMemCli`; on Unix, prefer `$HOME/.claude/sybermem/cli/sybermem` and store the chosen command in `"$SYBERMEM_CLI"`. If the fixed launcher is unavailable, fall back to bare `sybermem`. Do not modify persistent PATH automatically. Command examples below use `$SyberMemCli` / `"$SYBERMEM_CLI"`.

## Flow

### Step 1: Health check and report current SyberMem state

First, run these diagnostic checks and flag any failures:
- `.claude/settings.json` exists (if missing: root resolution will fail for all skills, stop hook will not trigger)
- `.sybermem/INDEX.md` contains all expected anchor comments (`<!-- add new records here -->`, `<!-- add new conclusions here -->`, `<!-- add new digest records here -->`)
- `.sybermem/analysis/phase-index.md` has `status:` field that is not `not_yet_analyzed` (if stale: phase-aware workflows will not work)
- `.sybermem/hooks/record_change_on_stop.py` exists (if missing: auto-record mode is broken)

Then report:
- resolved project root
- whether `.sybermem/INDEX.md` exists
- whether `.sybermem/digests/` exists
- whether `.sybermem/analysis/phase-index.md` exists
- whether any legacy SyberMem protocol block remains in `CLAUDE.md` / `AGENTS.md` (should be removed by init/update)
- whether `.sybermem/project.yaml` contains a `team:` block
- whether the configured Team path is accessible
- whether the current project appears Team-publishable

### Step 2: Report current routing behavior

Explain what would currently happen if the user runs:
- `/sybermem-summary`
- `/sybermem-digest`
- `/sybermem-phase-analyze`
- `/sybermem-record`
- `/sybermem-update`
- `/sybermem-team-publish`
- `/sybermem-team-summary`

### Step 3: Recommend the next command

**Authoritative source: run the deterministic router, do not re-derive by hand.**

Run `$SyberMemCli next-step --format json` or `"$SYBERMEM_CLI" next-step --format json` and treat its `action` + `reason` as the
canonical recommendation. This is the same core router (`recommend_next_step`)
that `/sybermem-resume` uses, so `using-sybermem` and `resume` never disagree.
Present the returned action verbatim, then add human-friendly context.

If the `sybermem` CLI is unavailable in this environment, and only then, fall
back to the decision graph below to derive an equivalent recommendation manually.
The graph documents the router's logic; it is not a second, competing source.

Team-aware priority order when several actions seem plausible:

```text
record > digest > team-publish
```

```dot
digraph recommend_command {
    "Phase index exists?" [shape=diamond];
    "Recommend /sybermem-phase-analyze" [shape=box];
    "Has candidate phases only?" [shape=diamond];
    "Recommend /sybermem-phase-confirm" [shape=box];
    "Important work with only auto trail?" [shape=diamond];
    "Recommend /sybermem-record" [shape=box];
    "Project partially upgraded?" [shape=diamond];
    "Recommend /sybermem-update" [shape=box];
    "Recommend /sybermem-summary" [shape=box];

    "Phase index exists?" -> "Recommend /sybermem-phase-analyze" [label="no"];
    "Phase index exists?" -> "Has candidate phases only?" [label="yes"];
    "Has candidate phases only?" -> "Recommend /sybermem-phase-confirm" [label="yes"];
    "Has candidate phases only?" -> "Important work with only auto trail?" [label="no"];
    "Important work with only auto trail?" -> "Recommend /sybermem-record" [label="yes"];
    "Important work with only auto trail?" -> "Project partially upgraded?" [label="no"];
    "Project partially upgraded?" -> "Recommend /sybermem-update" [label="yes"];
    "Project partially upgraded?" -> "Recommend /sybermem-summary" [label="no"];
}
```

Examples:
- if no phase index exists and the user wants phase-aware workflows → recommend `/sybermem-phase-analyze`
- if a candidate phase exists but no confirmed phase exists → recommend `/sybermem-phase-confirm`
- if important work is happening and only a lightweight trail exists → recommend `/sybermem-record`
- if the current project has enough material but no digest → recommend `/sybermem-digest`
- if the project has a Team association and Team memory is stale → recommend `/sybermem-team-publish`
- if the project appears partially upgraded → recommend `/sybermem-update`

## Output Style

Return a short advisory report, for example:

```md
## SyberMem Status
- Project root: ...
- Index: present / missing
- Digests: present / missing
- Phase index: present / missing

## Current routing
- summary: ...
- digest: ...
- analyze: ...
- record: ...
- update: ...
- stop-hook mode: auto / remind, and what that means in this project

## Recommended next step
- ...
```

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Auto-running `phase-analyze`, `record`, `summary`, or `digest` without telling the user
- Treating candidate phases as canonical
- Ignoring the resolved root and answering from the wrong directory context

## Terminal State

This skill is complete when:
- the current SyberMem state has been reported
- the routing implications for the main SyberMem commands have been explained
- a recommended next command has been given

## Integration

**Related skills:**
- **sybermem-record** — Recommended when important work is happening
- **sybermem-phase-analyze** — Recommended when phase index is missing or stale
- **sybermem-phase-confirm** — Recommended when candidate phases need confirmation
- **sybermem-summary** — Recommended for status overview
- **sybermem-update** — Recommended when project appears partially upgraded
