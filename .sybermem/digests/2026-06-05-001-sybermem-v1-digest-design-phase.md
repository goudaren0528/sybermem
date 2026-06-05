---
type: digest
kind: phase
date: 2026-06-05
number: 001
title: sybermem v1 digest design phase
status: completed
source_records:
  - changes/2026-05-12-002-migrate-global-skill-source-to-packages.md
  - changes/2026-05-13-005-refresh-project-instructions-and-add-auto-record-hook-files.md
  - requirements/2026-06-05-002-阶段性总结与记录压缩需求.md
coverage:
  from: 2026-05-12
  to: 2026-06-05
fingerprint: 11b53dd3be6559ad471b1faa84a3d487361f88db6883dad5798cee91dd255095
---

## Phase Scope
This digest covers the SyberMem evolution phase from package-source migration through project refresh automation to the newly raised requirement for durable stage-level compression.

## Core Conclusions
- SyberMem moved to `packages/claude-skills/`, so globally installed skills now have a single in-repo source of truth and no longer depend on repo-local runnable skill copies.
- Project refresh automation became a first-class workflow, so projects can adopt the current `.sybermem/` instructions and auto-record helper without overwriting user-owned local settings.
- Real usage exposed a new understanding bottleneck: raw records plus one-line conclusions are not enough once project history grows, so a durable digest layer became a justified next step.

## Key Decisions and Changes
- The skill source migration established `packages/claude-skills/` as the distribution source for global installs.
- The auto/remind project refresh work introduced stop-hook based lightweight `change` capture and explicit protection for local custom settings.
- The new requirement record formalized the need for persistent phase/topic summaries and record compaction.

## Current State
SyberMem now has a clear reason to add a durable digest layer. The repository has the raw records needed to explain the transition, but future understanding should rely on digest navigation instead of rereading every contributing record.

## Recommended Next Reads
- `changes/2026-05-12-002-migrate-global-skill-source-to-packages.md`
- `changes/2026-05-13-005-refresh-project-instructions-and-add-auto-record-hook-files.md`
- `requirements/2026-06-05-002-阶段性总结与记录压缩需求.md`

## Source Coverage
This digest covers exactly these source records:
- `changes/2026-05-12-002-migrate-global-skill-source-to-packages.md`
- `changes/2026-05-13-005-refresh-project-instructions-and-add-auto-record-hook-files.md`
- `requirements/2026-06-05-002-阶段性总结与记录压缩需求.md`
