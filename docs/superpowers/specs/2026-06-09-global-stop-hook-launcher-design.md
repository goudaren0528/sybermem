# SyberMem Global Stop Hook Launcher Design

Date: 2026-06-09
Status: Proposed

## Overview

SyberMem’s stop hook has two distinct layers:

1. **Launcher layer** — can the configured command locate a Python file to run at all?
2. **Runtime layer** — once the hook script starts, can it resolve the correct project root and behave correctly?

Recent work improved the runtime layer by teaching the stop hook to walk up from subdirectories and find the correct SyberMem root. However, that fix does not address the earlier launcher layer.

Today the managed Stop hook command still depends on a relative-path Python invocation. Even when that relative path points at a launcher, the launcher file itself must still be found relative to the session’s current working directory. If Claude is running inside a subdirectory such as:

- `D:\erp-lite\web`
- `D:\erp-lite\.sybermem\digests\`

then a command like:

```text
python .sybermem/hooks/launch_record_change_on_stop.py
```

still fails before the launcher can execute, because Python first tries to open:

- `D:\erp-lite\web\.sybermem\hooks\launch_record_change_on_stop.py`
- or `D:\erp-lite\.sybermem\digests\.sybermem\hooks\launch_record_change_on_stop.py`

The launcher logic never gets a chance to run.

This spec introduces a **global stop hook launcher** to solve that problem completely.

## Goals

- Make stop hook invocation independent of the current working directory
- Ensure existing projects are automatically repaired on upgrade
- Keep the actual hook logic project-local
- Preserve non-blocking stop-hook behavior
- Minimize per-project manual intervention

## Non-Goals

- Do not replace the project-local runtime hook
- Do not remove `.sybermem/hooks/record_change_on_stop.py`
- Do not turn stop-hook execution into an interactive workflow
- Do not require every user to hand-edit `.claude/settings.json`
- Do not depend on a launcher inside each working subdirectory

## Core Problem

A project-local launcher still fails when launched through a relative path from the wrong `cwd`.

Therefore, the launcher itself must be reachable through a path that does **not** depend on the current project subdirectory.

That means the stop hook command must point at a **globally reachable absolute launcher path**.

## Proposed Architecture

### Global launcher path

Install one global launcher at a stable user-level location:

```text
~/.claude/sybermem/launch_record_change_on_stop.py
```

On Windows this resolves to a path like:

```text
C:\Users\<user>\.claude\sybermem\launch_record_change_on_stop.py
```

### Managed Stop hook command

Project-local `.claude/settings.json` should use:

```text
python <absolute-launcher-path>
```

For example on Windows:

```text
python C:/Users/69046/.claude/sybermem/launch_record_change_on_stop.py
```

### Launcher responsibilities

The global launcher should:

1. start from the current working directory
2. walk upward to find the nearest valid SyberMem project root
3. if found, locate that root’s `.sybermem/hooks/record_change_on_stop.py`
4. invoke that runtime hook
5. if no valid root is found, exit 0 silently
6. if a valid root is found but the runtime hook file is missing, exit 0 silently

### Runtime hook responsibilities

The actual project behavior remains in the project-local runtime hook:

```text
<project-root>/.sybermem/hooks/record_change_on_stop.py
```

That file continues to own:
- workspace diff scanning
- auto change trail creation
- nudge logic
- index updates
- local state files

This keeps behavior local to the project while making the launcher globally reachable.

## Why a Global Launcher Is Better Than a Project-Local Launcher

### Project-local launcher problem

A project-local launcher still relies on a relative path from `cwd`, so it fails in subdirectories before any root-resolution logic can execute.

### Global launcher advantage

A global absolute path is reachable from anywhere. Once the Python interpreter can open the launcher, the launcher can safely walk up and find the correct project root.

This directly fixes the class of failures seen in existing projects.

## Distribution Model

The launcher must use a **double-safety installation model**.

### Layer 1: install/update scripts preinstall the global launcher

The normal install/update scripts should create or refresh:

```text
~/.claude/sybermem/launch_record_change_on_stop.py
```

This makes the launcher available as soon as global skills are updated.

### Layer 2: `/sybermem-update` checks and repairs launcher state per project

When run inside a project, `/sybermem-update` should:

1. verify that the global launcher exists
2. create or refresh it if missing
3. update the project’s `.claude/settings.json` Stop hook command to the global absolute launcher path
4. preserve or update the rest of the settings file according to managed/custom rules

This gives both:
- normal installation reliability
- project-specific repair for existing users

## Existing Project Auto-Repair

This spec is especially about old projects that already have a managed Stop hook command pointing at the old relative path.

### Required behavior

When an existing project runs `/sybermem-update`, the system must automatically:

- detect the old direct-hook command
- detect the newer but still subdirectory-fragile project-local launcher command
- replace either one with the new global absolute launcher command

This should happen even when the project’s `.claude/settings.json` is otherwise classified as custom, **if and only if** the exact old SyberMem Stop hook entry is recognized.

## Custom Settings Policy

### Rule

If `.claude/settings.json` is otherwise custom, but the Stop hook still contains a recognizable old SyberMem-managed command, SyberMem should still replace **that one hook command** with the new global launcher form.

### Why this is acceptable

- it is a surgical migration, not a full overwrite
- it solves a real failure for existing users
- it preserves the rest of the custom settings file
- the user explicitly asked that old projects be automatically repaired

### Scope of rewrite

The auto-migration should be limited to recognized SyberMem hook command variants, such as:

```text
python .sybermem/hooks/record_change_on_stop.py
python .sybermem/hooks/launch_record_change_on_stop.py
```

If the Stop hook command is not recognizably SyberMem-managed, do not rewrite it automatically.

## Global Launcher Behavior

### Root resolution rule

The global launcher should use the same root-resolution logic already established elsewhere:

Walk up from `cwd` and find the nearest ancestor containing:
- `.sybermem/`
- and either `.claude/settings.json` or `.sybermem/INDEX.md`

This is necessary because:
- worktrees and some local setups may not have a tracked `.claude/settings.json`
- `.sybermem/INDEX.md` is a strong project-local fallback marker

### Stop conditions

Stop when:
- a valid SyberMem root is found
- the git repository root is reached without a valid match
- the filesystem root is reached without a valid match

### Missing-runtime-hook behavior

If the project root is found but:

```text
<root>/.sybermem/hooks/record_change_on_stop.py
```

does not exist:
- exit 0 silently
- do not block the session stop

## Settings File Handling

### Managed settings template

The packaged template for `.claude/settings.json` should already point at the global launcher command.

### Existing managed projects

If the project is using the managed settings template lineage, `/sybermem-update` should refresh the Stop hook entry automatically.

### Existing custom projects with old SyberMem hook entry

If the file is custom but contains a recognized old SyberMem Stop hook command, replace that command only.

### Existing custom projects with unrelated hook commands

Do not auto-rewrite them.

## User-Facing Upgrade Behavior

For existing users, the intended experience should be:

1. update global SyberMem skills
2. run `/sybermem-update` in the project
3. project now has:
   - the global launcher available
   - the project-local runtime hook available
   - the Stop hook command migrated to the global launcher path
4. working from subdirectories no longer produces file-not-found hook errors

## Risks

### Risk: absolute path portability

The global launcher path contains the user’s home directory.

Mitigation:
- write the path at install/update time for the current machine
- never commit that path into repository files outside the local project’s `.claude/settings.json`

### Risk: custom settings mutation feels surprising

Mitigation:
- limit the mutation to exact recognized SyberMem Stop hook commands
- preserve the rest of the file untouched
- document this behavior clearly

### Risk: launcher and runtime drift apart

Mitigation:
- keep launcher logic minimal
- keep all real stop-hook behavior in `record_change_on_stop.py`
- test the launcher separately from runtime logic

## Acceptance Criteria

1. The global launcher exists at a stable absolute user-level path.
2. The managed Stop hook command uses `python <absolute-launcher-path>`.
3. Running the Stop hook from any project subdirectory no longer fails with file-not-found before launcher execution.
4. The global launcher can find the nearest valid SyberMem root and invoke that root’s runtime hook.
5. If no valid root exists, the launcher exits 0 silently.
6. If a root exists but the runtime hook is missing, the launcher exits 0 silently.
7. `/sybermem-update` automatically migrates existing projects from old relative hook commands to the new global absolute launcher command.
8. This migration still happens when `.claude/settings.json` is otherwise custom, as long as the old SyberMem hook command is clearly recognized.

## Recommendation

The project-local launcher approach is not sufficient because it still fails before execution when invoked through a relative path from the wrong `cwd`.

The correct solution is a globally reachable launcher plus project-local runtime hook.

In one sentence:

**SyberMem should install a global stop-hook launcher at a stable user-level path, have `/sybermem-update` migrate existing projects to call that launcher through an absolute path, and let the launcher resolve the real project root before invoking the project-local runtime hook.**
