---
name: using-sybermem
description: Use when unsure what to do next in SyberMem. Gives read-only project orientation and the canonical next-step recommendation, with runtime evidence diagnostics only on demand.
---

# using-sybermem Skill

**Announce at start:** "I'm using the using-sybermem skill to diagnose the current SyberMem state."

`using-sybermem` is the visible advisory entrypoint for the SyberMem system. It does not replace concrete skills like `record`, `summary`, `digest`, or `phase-analyze`. It reports the current project's SyberMem state and tells the user what the correct next command is.

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill unless the task explicitly asks for SyberMem diagnostics.
</SUBAGENT-STOP>

## Quick guide (for humans)

> Plain-language overview for people. **Not** the execution contract — the
> `<HARD-GATE>`, `## Default orientation flow`, and the routing rules below are
> authoritative and win on any conflict.

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
Do NOT run downstream actions, including initialization, refresh, record, phase-analyze, summary, or digest, as part of orientation.
Do NOT treat candidate phases as canonical.
Do NOT ignore the resolved root and answer from the wrong directory context.
</HARD-GATE>

## CLI Resolution

Before running SyberMem CLI commands, resolve a command variable first. On Windows PowerShell, prefer `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd` and store the chosen command in `$SyberMemCli`; on Unix, prefer `$HOME/.claude/sybermem/cli/sybermem` and store the chosen command in `"$SYBERMEM_CLI"`. If the fixed launcher is unavailable, fall back to bare `sybermem`. Do not modify persistent PATH automatically. Command examples below use `$SyberMemCli` / `"$SYBERMEM_CLI"`.

## Default orientation flow

This is the normal path. It is four short steps and it never mutates anything.

### Step 1: Resolve the project root

Walk up from cwd to find `.sybermem/` + (`.sybermem/project.yaml` OR `.claude/settings.json`) and report the
resolved **project root**. If no root resolves, say so and let Step 3 route.

### Step 2: Report a compact state summary

Report two high-level lines only — no implementation-level checklist here:

- **installation status** — is the SyberMem CLI reachable (fixed launcher or bare
  `sybermem`), and does the installed version match this project's recorded
  version (run `doctor` only when the CLI is reachable)? This is installation
  evidence, not proof of a loaded plugin or current-turn injection.
- **project status** — does `.sybermem/` exist with `INDEX.md`, `digests/`, and
  `analysis/phase-index.md` present?

If the CLI cannot be reached, skip all CLI calls (including doctor and next-step).
Report CLI unavailable and recommend the existing install/recovery guidance in
the README or `/sybermem-install`; do not initialize or repair here. Otherwise
continue to Step 3; use advanced diagnostics only when needed or requested.

### Step 3: Get the canonical recommendation

**Authoritative source: run the deterministic router, do not re-derive by hand.**

The canonical routing command is `sybermem next-step --format json`. Invoke it
through the resolved launcher — `& $SyberMemCli next-step --format json` or
`"$SYBERMEM_CLI" next-step --format json` — and treat its `action` + `reason` as the
canonical recommendation. This is the same core router (`recommend_next_step`)
that `/sybermem-resume` uses, so `using-sybermem` and `resume` never disagree.
When no project root resolves, this route returns `/sybermem-init-project`
successfully — report that action rather than guessing.

Present the returned action verbatim, then add human-friendly context. An empty
project has no records yet; do not invent prior work or write a record to fill it.
Keep existing projects and old entrypoints usable without forced reinitialization.

User journey: new project → `/sybermem-init-project`; unsure what next →
`/using-sybermem`; resume work → `/sybermem-resume`; close meaningful work →
`/sybermem-record`. These are choices, not a sequence to execute automatically.
If skills were just installed in this session, they are not hot-loaded.
First confirm the target existing directory with the user; cwd alone is not authorization. If a
SyberMem ancestor exists, ask whether the user wants an independent nested project
before recommending setup there. Recommend only the verified CLI path
`sybermem project refresh --root "<confirmed-target>" --format json`, or a new session
for the slash skill. PowerShell: `& $SyberMemCli project refresh --root "<confirmed-target>" --format json`;
Bash: `"$SYBERMEM_CLI" project refresh --root "<confirmed-target>" --format json`.
Do not execute refresh here.
Nested-project approval does not bypass CLI safety checks: `--root` rejects target
or ancestor symlink/reparse points, a target inside an ancestor Git worktree unless
it has its own independent repository, and an unconfirmed Git boundary. Core may
otherwise run `git rm --cached` against an ancestor index. On rejection, stop;
never fall back to no-argument refresh. Not every nested directory is supported.
The explicit branch rejects nonempty `GIT_*` environment overrides and unavailable
Git or an unknown boundary; Git probes use a fixed locale (`C`) and strictly recognize
non-repository results. An independent repository at the target is allowed, an
ancestor-worktree subdirectory is rejected. `--root` is a static exact-target check,
not an OS sandbox or a race-safety/full-chain-redaction guarantee. Real refresh
validation requires VM/OS isolation and has not yet been performed.
Normalize the user-confirmed target to an absolute path before recommending the
command; show that normalized path and reconfirm if it differs from the intended
scope. Compare returned `root` using that same normalized target. These checks do
not prove model consumption.
Explicit `--root` uses exactly that existing directory: no upward resolution,
implicit mkdir, or fallback. The downstream workflow must check returned `root`
against the authorized target and `overall` for `fresh` or `updated`, as well as exit
status and valid JSON. Failure may leave partial writes; do not blindly retry.
If an older CLI rejects `--root`, stop and recommend upgrading or using the skill in
a new session; never downgrade to a no-argument refresh.
Legacy `sybermem project refresh --format json` still walks physical ancestors for
markers and exits 1 if no root resolves; changing HOME does not prevent that search.
Legacy `sybermem project init` provides identity for an existing resolved root,
not a full fresh-project initialization.

### Step 4: Present exactly one recommended command and stop

Report the single recommended command with its reason. **Do not run downstream actions**
such as `record`, `digest`, `theme-digest`, `phase-analyze`, `summary`, or
`update` as part of this skill — name the command and hand control back to the user.

## Advanced diagnostics

Use this section **only** on user request, when the CLI routing in Step 3 is unavailable,
or when a Step 2 health signal is unhealthy and the user needs to know why. These checks are
read-only; they diagnose and explain, they never repair.

### On-demand runtime evidence

Only `doctor --runtime` and `project refresh --root` are authorized interface
additions in this change; runtime diagnostics remain on demand.

With a reachable, compatible CLI, use `sybermem doctor --runtime --format json`
through the resolved launcher (`& $SyberMemCli doctor --runtime --format json`
in PowerShell; `"$SYBERMEM_CLI" doctor --runtime --format json` on Unix).
Do not run this every turn. Plain `sybermem doctor` retains its existing behavior.
If the installed CLI rejects `--runtime`, report the version mismatch and recommend
the existing global update, project update, and new-session sequence; do not repair.

- Installed: current CLI/core evidence only; do not call this proof of plugin installation.
- Loaded: ordinary CLI has no live host/session identity, so current loaded state is `unknown`.
- Current turn: no live turn association, so actual current-turn injection is `unknown`.

This command displays three evidence layers and their limits on demand; it does not
automatically detect the current host. File presence and the latest log cannot prove
current loading or delivery. Even host-context delivery evidence does not prove model
consumption. `unknown` means missing evidence; `unsupported` needs an explicit support
boundary; `unmatched` needs affirmative evidence of no match in that turn. Empty results
or packets alone do not establish `unmatched`. Disk upgrades need a new host session
before loaded-version verification. If the CLI is missing, do not run doctor: use the
installation recovery guidance above.

### Manual health checks

- `.claude/settings.json` exists for Claude hook configuration; root resolution can also use `.sybermem/project.yaml`, so missing settings alone does not mean every skill lacks a root
- `.sybermem/INDEX.md` contains all expected anchor comments — anchors
  `<!-- add new records here -->`, `<!-- add new conclusions here -->`, `<!-- add new digest records here -->`
- `.sybermem/analysis/phase-index.md` has `status:` field that is not `not_yet_analyzed` (if stale: phase-aware workflows will not work)
- project hooks under `.sybermem/hooks/` exist, in particular
  `.sybermem/hooks/record_change_on_stop.py` (if missing: auto-record mode is broken)
- no legacy protocol block remains in `CLAUDE.md` / `AGENTS.md` (a leftover legacy protocol
  block means init/update did not finish cleanly)

Report findings and name the command that would fix them (usually
`/sybermem-update` or `/sybermem-init-project`). Do not apply the fix here.

### Manual routing fallback

If the `sybermem` CLI is unavailable, recommend installation recovery first.
The graph below is explanatory context only, not a replacement canonical result
or permission to run a downstream action. When the CLI is reachable, use next-step.

Priority order when several actions seem plausible:

```text
record > digest
```

```dot
digraph recommend_command {
    "Phase index exists?" [shape=diamond];
    "Recommend /sybermem-phase-analyze" [shape=box];
    "Important work with only auto trail?" [shape=diamond];
    "Recommend /sybermem-record" [shape=box];
    "Project partially upgraded?" [shape=diamond];
    "Recommend /sybermem-update" [shape=box];
    "Recommend /sybermem-summary" [shape=box];

    "Phase index exists?" -> "Recommend /sybermem-phase-analyze" [label="no"];
    "Phase index exists?" -> "Important work with only auto trail?" [label="yes"];
    "Important work with only auto trail?" -> "Recommend /sybermem-record" [label="yes"];
    "Important work with only auto trail?" -> "Project partially upgraded?" [label="no"];
    "Project partially upgraded?" -> "Recommend /sybermem-update" [label="yes"];
    "Project partially upgraded?" -> "Recommend /sybermem-summary" [label="no"];
}
```

Examples:
- if no phase index exists and the user wants phase-aware workflows → recommend `/sybermem-phase-analyze`
- if important work is happening and only a lightweight trail exists → recommend `/sybermem-record`
- if the current project has enough material but no digest → recommend `/sybermem-digest`
- if the project appears partially upgraded → recommend `/sybermem-update`

## Output Style

Return a short advisory report, for example:

```md
## SyberMem Status
- Project root: ...
- Installation: CLI reachable, version current / behind
- Project: index / digests / phase index present or missing

## Recommended next step
- <action> — <reason>
```

Only add an `## Advanced diagnostics` block to the report when the fallback or
manual health checks above were actually needed, or when the user explicitly
requested runtime evidence diagnostics.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Running downstream actions during orientation, even after announcing them
- Walking the full manual health checklist before you have the `next-step` result
- Treating candidate phases as canonical
- Ignoring the resolved root and answering from the wrong directory context

## Terminal State

This skill is complete when:
- the resolved project root and a compact installation/project state have been reported
- the canonical `next-step` action has been presented with its reason, or CLI unavailability and installation recovery have been reported
- exactly one recommended next command has been given, with no downstream action run

## Integration

**Related skills:**
- **sybermem-record** — Recommended when important work is happening
- **sybermem-phase-analyze** — Recommended when phase index is missing or stale
- **sybermem-summary** — Recommended for status overview
- **sybermem-update** — Recommended when project appears partially upgraded
