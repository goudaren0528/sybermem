# Phase Index

## Analysis Progress
- status: analyzed
- last_analysis_at: 2026-08-05
- last_record_boundary: change-043 (2026-08-05)
- last_git_boundary: dde4857
- pending_new_records: none
- unassigned_git_work: none
- latest_active_phase: phase-013
- unassigned_records: change-014, change-016, change-017, change-019, change-020, change-021, change-022, change-024, change-025, change-028, change-029, change-031, change-034, change-035, change-038, change-042, change-043

## Phase Candidates
<!-- use canonical candidate blocks: ### Candidate: <title> + candidate_id/status/covered_records/rationale/proposed_at -->

## Confirmed Phases

### Phase: Global skill distribution and project refresh
- phase_id: phase-001
- source_candidate_id: candidate-phase-001
- status: confirmed
- lifecycle: completed
- completed_at: 2026-06-22
- covered_records:
  - change-002
  - change-005
- confirmed_at: 2026-06-09
- notes: Confirmed from the initial packaging-and-refresh candidate during the Task 5 smoke test.

### Phase: Foundation and distribution
- phase_id: phase-002
- source_candidate_id: candidate-phase-002
- status: confirmed
- lifecycle: completed
- completed_at: 2026-06-22
- covered_records:
  - requirement-001
  - change-001
  - change-003
- confirmed_at: 2026-06-16
- notes: Covers the initial ADR system design, remote install scripts, and auto-change hook template.

### Phase: Digest and compression layer design
- phase_id: phase-003
- source_candidate_id: candidate-phase-003
- status: confirmed
- lifecycle: completed
- completed_at: 2026-06-22
- covered_records:
  - requirement-002
- confirmed_at: 2026-06-16
- notes: Formalized the need for persistent phase summaries and durable compression.

### Phase: Root resolution and hook hardening
- phase_id: phase-004
- source_candidate_id: candidate-phase-004
- status: confirmed
- lifecycle: completed
- completed_at: 2026-06-22
- covered_records:
  - bug-001
- confirmed_at: 2026-06-16
- notes: Fixed init-project file classification and project-root resolution from subdirectories.

### Phase: Framework hardening and skill upgrade
- phase_id: phase-007
- source_candidate_id: candidate-phase-007
- status: confirmed
- lifecycle: completed
- completed_at: 2026-06-22
- covered_records:
  - change-006
- confirmed_at: 2026-06-22
- notes: Repaired project framework state and upgraded the initial skill set with hard gates and health checks.

### Phase: Platform ecosystem and plugin packaging
- phase_id: phase-009
- source_candidate_id: candidate-phase-009
- status: confirmed
- lifecycle: completed
- completed_at: 2026-06-22
- covered_records:
  - change-007
  - change-008
  - change-009
- confirmed_at: 2026-06-22
- notes: Added the Claude plugin skeleton, multi-platform entry files, and package validation.

### Phase: Search, relations, and theme digest
- phase_id: phase-010
- source_candidate_id: candidate-phase-010
- status: confirmed
- lifecycle: completed
- completed_at: 2026-07-10
- covered_records:
  - change-010
- confirmed_at: 2026-06-22
- notes: Added lifecycle-aware search, relations, theme digest, and the v2 cross-platform capability layer.

### Phase: Skill and lifecycle quality hardening
- phase_id: phase-011
- source_candidate_id: candidate-phase-011
- status: confirmed
- lifecycle: completed
- covered_records:
  - change-011
  - change-012
  - change-013
  - change-027
  - change-032
- confirmed_at: 2026-08-05
- notes: Hardened skill design, reminder-first record intent, injection footprint, lifecycle quality, and distribution safety.

### Phase: CLI, Hub, and Team memory foundation
- phase_id: phase-012
- source_candidate_id: candidate-phase-012
- status: confirmed
- lifecycle: completed
- covered_records:
  - decision-001
  - requirement-003
  - change-015
  - change-018
  - change-023
  - change-026
  - change-030
- confirmed_at: 2026-08-05
- notes: Established installable CLI, Hub/workspace foundations, Team publication and summaries, Team skills, and project-local propagation.

### Phase: Continuity and source-aware trust experience
- phase_id: phase-013
- source_candidate_id: candidate-phase-013
- status: confirmed
- lifecycle: active
- covered_records:
  - decision-002
  - change-033
  - change-036
  - change-037
  - change-039
  - change-040
  - change-041
  - bug-002
  - bug-003
- confirmed_at: 2026-08-05
- notes: Current active phase for bounded resume, source-aware recall, correction guidance, workspace trust, Team preview, and review-driven hardening.

## Historical Git-only Notes

- phase-005: Dual-entry protocol and visible skill — git-only history introducing the marker-bounded session protocol and visible /using-sybermem entrypoint; no raw SyberMem record exists.
- phase-006: Phase analysis and digest automation — git-only history introducing automatic phase analysis, confirmation, and batch digest behavior; no raw SyberMem record exists.
- phase-008: Lifecycle layer and cross-platform integration — git-only history for SessionStart, Stop, OpenCode lifecycle, nudge state, and update fast-path integration; no raw SyberMem record exists.

## Coverage Map
- requirement-001 -> phase-002
- change-001 -> phase-002
- change-002 -> phase-001
- change-003 -> phase-002
- change-005 -> phase-001
- requirement-002 -> phase-003
- bug-001 -> phase-004
- change-006 -> phase-007
- change-007 -> phase-009
- change-008 -> phase-009
- change-009 -> phase-009
- change-010 -> phase-010
- change-011 -> phase-011
- change-012 -> phase-011
- change-013 -> phase-011
- change-014 -> unassigned (auto-trail/build artifact record)
- change-015 -> phase-012
- change-016 -> unassigned (auto-trail/build artifact record)
- change-017 -> unassigned (auto-trail/build artifact record)
- change-018 -> phase-012
- change-019 -> unassigned (auto-trail/build artifact record)
- change-020 -> unassigned (auto-trail/build artifact record)
- change-021 -> unassigned (auto-trail/build artifact record)
- change-022 -> unassigned (auto-trail/build artifact record)
- change-023 -> phase-012
- change-024 -> unassigned (auto-trail/build artifact record)
- change-025 -> unassigned (auto-trail/build artifact record)
- change-026 -> phase-012
- change-027 -> phase-011
- change-028 -> unassigned (auto-trail/build artifact record)
- change-029 -> unassigned (auto-trail/build artifact record)
- change-030 -> phase-012
- change-031 -> unassigned (auto-trail/build artifact record)
- change-032 -> phase-011
- change-033 -> phase-013
- change-034 -> unassigned (auto-trail execution artifact record)
- change-035 -> unassigned (auto-trail research/execution artifact record)
- change-036 -> phase-013
- change-037 -> phase-013
- change-038 -> unassigned (auto-trail execution artifact record)
- change-039 -> phase-013
- change-040 -> phase-013
- change-041 -> phase-013
- change-042 -> unassigned (auto-trail execution artifact record)
- change-043 -> unassigned (auto-trail managed-file backup record)
- decision-001 -> phase-012
- decision-002 -> phase-013
- requirement-003 -> phase-012
- bug-002 -> phase-013
- bug-003 -> phase-013
