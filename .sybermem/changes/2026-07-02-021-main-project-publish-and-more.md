---
type: change
date: 2026-07-02
number: 021
title: main project publish and more
status: implemented
author: Developer
related_files: packages/cli/sybermem_cli/main.py, packages/core/sybermem_core/project.py, packages/core/sybermem_core/publish.py, packages/core/sybermem_core/__pycache__/__init__.cpython-310.pyc, packages/core/sybermem_core/__pycache__/identity.cpython-310.pyc, packages/core/sybermem_core/__pycache__/project.cpython-310.pyc, packages/core/sybermem_core/__pycache__/publish.cpython-310.pyc, packages/core/sybermem_core/__pycache__/records.cpython-310.pyc, packages/core/sybermem_core/__pycache__/status.cpython-310.pyc, packages/core/sybermem_core/__pycache__/storage.cpython-310.pyc, packages/core/sybermem_core/__pycache__/team.cpython-310.pyc
---

## Change Content
Auto-generated from workspace changes detected at session stop.

- Updated `packages/cli/sybermem_cli/main.py`
- Updated `packages/core/sybermem_core/project.py`
- Updated `packages/core/sybermem_core/publish.py`
- Updated `packages/core/sybermem_core/__pycache__/__init__.cpython-310.pyc`
- Updated `packages/core/sybermem_core/__pycache__/identity.cpython-310.pyc`
- Updated `packages/core/sybermem_core/__pycache__/project.cpython-310.pyc`
- Updated `packages/core/sybermem_core/__pycache__/publish.cpython-310.pyc`
- Updated `packages/core/sybermem_core/__pycache__/records.cpython-310.pyc`
- Updated `packages/core/sybermem_core/__pycache__/status.cpython-310.pyc`
- Updated `packages/core/sybermem_core/__pycache__/storage.cpython-310.pyc`
- Updated `packages/core/sybermem_core/__pycache__/team.cpython-310.pyc`

## Reason for Change
Persist the current workspace change set in SyberMem without requiring a manual /sybermem-record step. 11 file(s) changed.

## Impact Scope
- Project history: keeps a lightweight change trail in `.sybermem/changes/`
- Current workspace: captures 11 changed file(s) at stop time

## Implementation
- `packages/cli/sybermem_cli/main.py`
- `packages/core/sybermem_core/project.py`
- `packages/core/sybermem_core/publish.py`
- `packages/core/sybermem_core/__pycache__/__init__.cpython-310.pyc`
- `packages/core/sybermem_core/__pycache__/identity.cpython-310.pyc`
- `packages/core/sybermem_core/__pycache__/project.cpython-310.pyc`
- `packages/core/sybermem_core/__pycache__/publish.cpython-310.pyc`
- `packages/core/sybermem_core/__pycache__/records.cpython-310.pyc`
- `packages/core/sybermem_core/__pycache__/status.cpython-310.pyc`
- `packages/core/sybermem_core/__pycache__/storage.cpython-310.pyc`
- `packages/core/sybermem_core/__pycache__/team.cpython-310.pyc`

## Test Verification
Auto-generated from git workspace status; no extra verification was captured by the stop hook.

## Notes
Automatic mode only writes basic `change` records. Use `/sybermem-record` for decisions, requirements, bugs, or richer summaries.
followup_hint: digest
