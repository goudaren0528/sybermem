---
name: record
description: Use when creating SyberMem project records for changes, decisions, requirements, or bugs, including projects that still have legacy ADR/ storage.
---

# record Skill

Unified SyberMem record entry point. AI auto-detects the record type from context; the user does not need to choose.

## Directory Resolution Rules

Resolve the project data directory before reading or writing records:

1. If `.sybermem/` exists, use it.
2. If only `ADR/` exists, rename `ADR/` to `.sybermem/` and tell the user the legacy directory was auto-migrated.
3. If both `.sybermem/` and `ADR/` exist, use `.sybermem/`, warn that `ADR/` was ignored, and do not auto-merge them.
4. If neither exists, prompt the user to run `/init-project` first.

## Flow

### Step 1: Determine record type

Auto-detect from current work context, no need to ask the user:

| Signal | Type | Directory |
|--------|------|-----------|
| Add/modify/delete feature code | change | `.sybermem/changes/` |
| Tech selection, architecture design, multi-option evaluation | decision | `.sybermem/decisions/` |
| User raises requirement, discusses feature direction | requirement | `.sybermem/requirements/` |
| Fix bug, troubleshoot issue | bug | `.sybermem/bugs/` |

**When uncertain**, use AskUserQuestion to let the user choose.

### Step 2: Get next number

```
Check .sybermem/{type}/ directory → find max number → +1
Empty directory → 001
Format: 001, 002, 003...
```

### Step 3: Collect information

Extract from current session context, only ask the user when key information is missing.

**change** (required: change content, reason, impact scope):

```yaml
frontmatter:
  type: change
  date: YYYY-MM-DD
  number: NNN
  title: brief title
  status: implemented | planned | reverted
sections:
  - Change Content
  - Reason for Change
  - Impact Scope
```

**decision** (required: context, considered options, final decision):

```yaml
frontmatter:
  type: decision
  date: YYYY-MM-DD
  number: NNN
  title: brief title
  status: accepted | deprecated | superseded
sections:
  - Context
  - Considered Options
  - Final Decision
  - Impact and Consequences
```

**requirement** (required: source, content, conclusion):

```yaml
frontmatter:
  type: requirement
  date: YYYY-MM-DD
  number: NNN
  title: brief title
  source: source
  priority: high | medium | low
sections:
  - Requirement Source
  - Requirement Content
  - Final Conclusion
```

**bug** (required: description, root cause, solution):

```yaml
frontmatter:
  type: bug
  date: YYYY-MM-DD
  number: NNN
  title: brief title
  severity: critical | high | medium | low
sections:
  - Bug Description
  - Root Cause
  - Solution
  - Prevention Measures
```

### Step 4: Create file

Path: `.sybermem/{type}/{YYYY-MM-DD}-{NNN}-{title}.md`

Use `.claude/skills/record/templates/{type}.md` as the content template.

### Step 5: Update INDEX.md table

Insert a new row above the `<!-- add new records here -->` comment in the corresponding table in `.sybermem/INDEX.md`.

### Step 6: Write back key conclusion

Insert a line above the `<!-- add new conclusions here -->` comment in the `## Key Conclusions` section of `.sybermem/INDEX.md`:

```
- [type-number] one-line core conclusion (date)
```

Examples:
```
- [decision-003] Chose JWT auth over Session to support multi-platform scenarios (2026-05-11)
- [change-007] Login flow changed to phone+OTP, removed password (2026-05-11)
- [bug-002] Fixed data loss from concurrent writes by adding row locks (2026-05-11)
```

Requirement: the conclusion must include **what was done** and **why**, completed in one sentence.

## Error Handling

- `.sybermem/INDEX.md` doesn't exist after resolution → prompt to initialize the project first
- Number conflict → auto-increment
- Required field missing → ask the user to provide it

## When NOT to Record

- Simple formatting adjustments, comment edits
- Config file tweaks (no functional impact)
- WIP/draft work
