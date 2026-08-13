---
name: sybermem-team-publish
description: Publish the current project into Team memory using the remembered Team association or a one-time Team path.
---

# sybermem-team-publish Skill

**Announce at start:** "I'm using the sybermem-team-publish skill to publish this project into Team memory."

Use the existing Team publication pipeline through the `sybermem` CLI. Team publish is a high-impact action: always use preview -> review -> publish with the preview source hash.

## CLI Resolution

Before running SyberMem CLI commands, resolve a command variable first. On Windows PowerShell, prefer `$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd` and store the chosen command in `$SyberMemCli`; on Unix, prefer `$HOME/.claude/sybermem/cli/sybermem` and store the chosen command in `"$SYBERMEM_CLI"`. If the fixed launcher is unavailable, fall back to bare `sybermem`. Do not modify persistent PATH automatically. Command examples below use `$SyberMemCli` / `"$SYBERMEM_CLI"`.

## Flow

1. Resolve the current project root.
2. Check `.sybermem/project.yaml` for a `team:` block.
3. Generate a read-only preview. If the project is already linked to Team memory, run:

```bash
$SyberMemCli publish status --preview --format json
```

4. If the project is not yet linked to Team memory, ask the user for a Team repo path, then preview with:

```bash
$SyberMemCli publish status --team-path <path> --preview --format json
```

5. Review the preview before publishing. Check and report the trust envelope:
- source revision
- source hash
- freshness
- conflicts
- review required

6. Only if the preview is acceptable, publish with the exact preview hash:

```bash
$SyberMemCli publish status --preview-source-hash <source_hash_from_preview> --format json
```

If using a one-time Team path, keep the same path:

```bash
$SyberMemCli publish status --team-path <path> --preview-source-hash <source_hash_from_preview> --format json
```

If publish returns `stale_preview`, stop and generate a new preview. Do not retry with the old hash.

7. Report:
- team ID
- project slug
- files updated
- whether Team push succeeded
- source revision / source hash
- stale / conflict / review-required state

## Output Style

```md
## Team Publish
- Team: ...
- Project: ...
- Files updated:
  - ...
- Source revision: ...
- Source hash: ...
- Trust: stale=no, conflict=no, review-required=yes
- Push: success / failed
```
