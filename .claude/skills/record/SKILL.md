---
name: record
description: Create project records (change/decision/requirement/bug), auto-detect type, single entry point for all records
---

# record Skill

Unified record entry point. AI auto-detects record type from context, no user selection needed.

## Flow

### Step 1: Determine record type

Auto-detect from current work context, no need to ask user:

| Signal | Type | Directory |
|--------|------|-----------|
| Add/modify/delete feature code | change | ADR/changes/ |
| Tech selection, architecture design, multi-option evaluation | decision | ADR/decisions/ |
| User raises requirement, discusses feature direction | requirement | ADR/requirements/ |
| Fix bug, troubleshoot issue | bug | ADR/bugs/ |

**When uncertain**, use AskUserQuestion to let user choose.

### Step 2: Get next number

```
Check ADR/{type}/ directory → find max number → +1
Empty directory → 001
Format: 001, 002, 003...
```

### Step 3: Collect information

Extract from current session context, only ask user when key information is missing.

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

Path: `ADR/{type}/{YYYY-MM-DD}-{NNN}-{title}.md`

Use `.claude/skills/record/templates/{type}.md` template.

### Step 5: Update INDEX.md table

Insert new row above the `<!-- add new records here -->` comment in the corresponding table in `ADR/INDEX.md`.

### Step 6: Write back key conclusion

Insert a line above the `<!-- add new conclusions here -->` comment in the `## Key Conclusions` section of `ADR/INDEX.md`:

```
- [type-number] one-line core conclusion (date)
```

Examples:
```
- [decision-003] Chose JWT auth over Session to support multi-platform scenarios (2026-05-11)
- [change-007] Login flow changed to phone+OTP, removed password (2026-05-11)
- [bug-002] Fixed data loss from concurrent writes by adding row locks (2026-05-11)
```

Requirement: conclusion must include **what was done** and **why**, completed in one sentence.

## Error Handling

- INDEX.md doesn't exist → prompt to initialize project first
- Number conflict → auto-increment
- Required field missing → ask user to provide

## When NOT to Record

- Simple formatting adjustments, comment edits
- Config file tweaks (no functional impact)
- WIP/draft work
