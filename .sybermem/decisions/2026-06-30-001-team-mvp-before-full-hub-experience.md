---
type: decision
date: 2026-06-30
number: 001
title: Team MVP should precede full Hub experience for Requirement-003
status: decided
supersedes: none
implements: [requirement-003]
---

## Context

Requirement-003 defines SyberMem's evolution from single-project memory to Project / Hub / Team scopes. The original phased plan placed Hub expansion (Portfolio, Promote, Personal Lesson, Obsidian views) before Team. But the actual product goal is not “make the personal Hub beautiful first”; it is “get multiple projects' engineering memory into a single team-managed store as early as possible.”

By the time Phase 2 and Phase 2.1 completed, SyberMem already had enough individual-project and cross-project foundations to support a minimal Team MVP:
- stable `project.yaml` identities
- `~/.sybermem/projects.yaml` registry
- workspace search
- project status snapshots
- portfolio view

So the real decision point was whether to continue polishing Hub conveniences (Lesson / Promote / richer portfolio / Obsidian) first, or re-order the roadmap so that Team unified storage arrives earlier.

## Considered Options

### Option 1: Follow the original roadmap strictly
- Finish the complete Hub experience first
- Add Promote / Personal Lesson / Obsidian views before Team
- Only start Team after Hub feels feature-complete

### Option 2: Re-order the roadmap toward Team MVP (chosen)
- Keep the Hub MVP minimal but usable
- Use the existing Hub/CLI foundations as the bridge into Team
- Prioritize a minimal Team Git repository that can receive project status and digest-like summaries from multiple projects
- Delay richer personal-Hub ergonomics until after the team storage loop is proven valuable

### Option 3: Pause all architecture work and continue only project-local features
- Continue improving records / digests / search within single projects
- Delay Hub and Team until later

## Final Decision

**Choose Option 2:** re-order Requirement-003 so that the next major milestone after Hub MVP is a **minimal Team Git repository** for unified team storage and management, instead of first building out the full personal-Hub experience.

Concretely, this means:
1. Treat Phase 2 as “good enough” once workspace search, project status, and portfolio work in real dogfood.
2. Move directly into a Team MVP that can:
   - initialize a team repository
   - publish per-project status/current-state summaries
   - provide a unified team-readable store
3. Delay deeper Hub features (Promote / Personal Lesson / Obsidian generation polish) until after the Team storage loop is validated.

## Impact and Consequences

### Positive
- Aligns implementation order with the real user/business goal: unified team-managed storage.
- Avoids over-investing in a personal Hub that may not be the primary source of value.
- Lets the current CLI/registry/search foundations prove their usefulness in a real multi-project team workflow sooner.

### Trade-offs
- The personal-Hub experience remains intentionally incomplete for a while.
- Some later abstractions (Lesson, Promote, Obsidian views) will need to adapt to the Team-first sequencing.
- Team MVP must be scoped aggressively to avoid becoming a large governance system too early.

### Non-goals of this decision
- This does **not** cancel Hub features.
- This does **not** imply publishing raw project records directly to Team.
- This does **not** mean moving immediately to a service; Team Git remains the intended MVP path.

## Related Changes

- Requirement-003 established the full Project / Hub / Team architecture and phased rollout.
- Hub MVP work (Phase 2 / 2.1) created the minimal prerequisites needed to support this re-ordering.

## Notes

This is a sequencing decision, not a schema rewrite. The architecture remains the same; only the priority order changes.