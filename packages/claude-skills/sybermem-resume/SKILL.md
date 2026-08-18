---
name: sybermem-resume
description: Use when resuming work in a SyberMem project from natural language, with bounded current-state context and trust signals.
---

# sybermem-resume Skill

**Announce at start:** "I'm using the sybermem-resume skill to rebuild the current project context."

`sybermem-resume` is the thin, natural-language-first resume entrypoint for SyberMem. Use it when the user says things like "resume this project", "what was I doing", "catch me up", or "where should I start". It routes to the existing bounded resume, status, search, and next-step behavior. It does not define a new memory store, a new record format, or a second canonical source of truth.

## Core Invariants

- **Resume is read-only. It never writes records, edits settings, or mutates project memory.**
- **Resume suggests one next action, but never executes that action automatically.**
- **`.sybermem/` records, digests, and phase index remain the canonical source of truth.**

<HARD-GATE>
Do NOT create, update, or delete any file while resuming.
Do NOT auto-run the suggested next command.
Do NOT invent a second memory layer, hidden cache, or prompt-time state store.
Do NOT silently expand into full-history reading when the user asked for a bounded resume.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`.

## Natural-Language Triggers

Use this skill for requests like:

- "Resume this project"
- "What was I doing here?"
- "Catch me up on the current state"
- "What's the safest next step?"
- "Give me the short version before I continue"

If the user explicitly wants a durable conclusion artifact, route to `/sybermem-digest` instead. If they want a broad historical search, route to `/sybermem-search`.

## Resume Modes

Use user-facing language when explaining the modes:

- `/sybermem-resume` or `/sybermem-resume fast`  
  Short restart brief. Show only the current phase, the latest meaningful progress, the main risk, the recommended next action, and why that action is the best next step.

- `/sybermem-resume standard`  
  Default handoff brief. Include the fast view plus a bit more trust context, such as whether a digest already covers the current phase and which open issue or unresolved question most affects the next step.

- `/sybermem-resume deep`  
  Still bounded, but more deliberate. Show the same current-state fields plus the most useful read targets for deeper follow-up. Deep mode points the user to the right records or digests. It does not auto-read or dump the full history.

## Required Output

Return a bounded current-state handoff that includes:

- current phase
- recent progress
- risks or open questions
- next action
- confidence
- freshness
- reason

When available, keep the trust explanation source-aware. Make it clear whether a point comes from an authoritative current record, a digest, or lower-confidence supporting evidence.

Suggested shape:

```md
## SyberMem Resume
- Mode: fast | standard | deep
- Current phase: <phase id or title>
- Recent progress: <one short paragraph or bullets>
- Risks: <top risk or open question>
- Next action: <one recommended action>
- Confidence: high | medium | low
- Freshness: current | mixed | stale
- Reason: <why this action is recommended>
```

## Flow

1. **Resolve project root** — apply the directory resolution rules above.
2. **Choose mode**:
   - no explicit mode or "quick" wording → `fast`
   - ordinary resume / catch-up wording → `standard`
   - explicit deep handoff / review wording → `deep`
3. **Collect bounded current-state context** — use the existing resume/status/search/next-step path, not a new retrieval system.
4. **Render the handoff** — show current phase, recent progress, risks, next action, confidence, freshness, and reason.
5. **Stop after the handoff** — do not execute the suggested action unless the user asks for that next step separately.

## OpenCode Notes

On OpenCode, this skill remains manual and read-only:

- run `/sybermem-resume` when you want to rebuild context
- use `/sybermem-search` when you need explicit historical evidence
- rely on the supported compaction flow when OpenCode compacts the session

Do not claim unsupported hidden automation. OpenCode prompt-time project recall and habit reminders use the documented chat transform seam; Codex prompt-time recall and habit reminders use `UserPromptSubmit` `additionalContext`.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Writing a record, digest, or settings file during resume
- Auto-running the suggested next command
- Claiming certainty when the source is stale, superseded, or only evidentiary
- Dumping full record bodies instead of a bounded handoff
- Claiming OpenCode supports unsupported per-prompt injection

## Terminal State

This skill is complete when:
- the user has a bounded resume handoff
- the trust fields are shown clearly
- no file was written
- no follow-up command was executed automatically

## Integration

**Related skills:**
- **sybermem-summary** — Use for a phase-aware status panel
- **sybermem-search** — Use for explicit historical evidence
- **using-sybermem** — Use when the user wants routing or install health
- **sybermem-digest** — Use for a durable conclusion artifact
