# SyberMem Requirement-003 Re-prioritization — Team MVP Before Full Hub Polish

**Date:** 2026-06-30
**Status:** Confirmed decision
**Decision record:** `.sybermem/decisions/2026-06-30-001-team-mvp-before-full-hub-experience.md`

## Decision Summary

Requirement-003 originally implied a path of:

```text
Hub MVP → Promote / Personal Lesson → Obsidian polish → Team Git MVP
```

After building and dogfooding:
- Phase 0.5 (project identity + workspace search bridge)
- Phase 1 (Core CLI foundation)
- Phase 1.5 (CLI installability)
- Phase 2 (Hub MVP)
- Phase 2.1 (Portfolio polish)

we now know the immediate product value is not “make the personal Hub beautiful first,” but rather:

> **get multiple projects’ engineering memory into a single team-managed storage as early as possible.**

Therefore the priority order is adjusted.

## New priority order

### Keep
- Project / Hub / Team architecture
- Team Git repository as the MVP storage backend
- Skill semantic layer + Core CLI deterministic layer

### Re-prioritize

```text
Current:
Phase 2.1 complete
        ↓
Next: Team MVP
        ↓
Later: Promote / Personal Lesson
        ↓
Later: Obsidian polish / richer Hub experience
```

## Why this is the correct MVP

### What users already have
- Stable `project.yaml` identities
- Local Hub registry
- Workspace search
- Project status snapshots
- Portfolio view

### What they still do not have
- A single team-visible place to see all project status summaries
- A team-owned storage target
- A first real shared memory loop

So the next smallest useful thing is not a richer personal Hub. It is:

```text
project status
  → publish to Team Git repo
  → team repo becomes the shared store
```

## Resulting MVP shape

### Team MVP (minimal)
- `sybermem team init`
- Team Git repo structure
- `sybermem publish status`
- `projects/<slug>/project.md`
- `projects/<slug>/current-status.md`

### Deferred
- Promote
- Personal Lesson
- Obsidian views
- Team review workflow (full)
- Team search scope

## Implications for planning

1. Future design/implementation should prioritize:
   - team identity
   - team repo bootstrapping
   - status publication format
   - sync model
2. Hub polish work should be opportunistic, not roadmap-blocking.
3. Personal Lesson remains important, but it is no longer on the critical path to proving the product.

## Recommended next implementation sequence

```text
Team MVP Phase A:
- team.yaml
- sybermem team init
- team repo structure

Team MVP Phase B:
- sybermem publish status
- current-status.md / project.md generation

Team MVP Phase C:
- basic team sync / read path
```

Only after that should we consider Promote / Lesson and broader governance layers.
