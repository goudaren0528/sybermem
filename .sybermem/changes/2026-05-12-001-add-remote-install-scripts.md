---
type: change
date: 2026-05-12
number: 001
title: Add remote install scripts for one-liner installation
status: implemented
author: Developer
related_files: scripts/install-remote.sh, scripts/install-remote.ps1, INSTALL.md, README.md
---

## Change Content

Added two remote install scripts that allow new users to install the ADR system with a single command, without needing to clone the repository:

- `scripts/install-remote.sh` — Downloads GitHub tarball, extracts skills, installs to `~/.claude/skills/` and `~/.config/opencode/skills/`
- `scripts/install-remote.ps1` — Same flow for Windows, uses GitHub zip archive

Usage:
```bash
# macOS / Linux
curl -sSL https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.sh | bash

# Windows (PowerShell)
irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex
```

Updated `INSTALL.md` to promote one-liner as Option 1 (recommended). Simplified `README.md` Quick Start section to show one-liner first.

## Reason for Change

Previous installation required cloning the repo, navigating into it, and running a local script — 3 steps minimum. For new users this friction is unnecessary since they only need the skill files, not the full repo.

## Impact Scope

- New users: significantly simplified onboarding (3 steps → 1 command)
- Existing users: no impact, existing install methods still available
- Update flow: re-running the one-liner overwrites with latest version

## Implementation

- Bash script uses `curl | tar xz` to download and extract GitHub tarball
- PowerShell script uses `Invoke-WebRequest` + `Expand-Archive` for GitHub zip
- Both scripts use temp directories with cleanup on exit
- Archive prefix (`sybermem-main`) is derived from repo/branch name

## Test Verification

Scripts are ready for testing after the repo is pushed to GitHub. Local install scripts remain as fallback.

## Notes

N/A
