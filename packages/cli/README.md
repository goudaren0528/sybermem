# sybermem-cli

Command-line interface for [SyberMem](https://github.com/goudaren0528/sybermem) —
a project/team engineering memory system for AI workflows.

Provides the `sybermem` command wrapping `sybermem-core` operations: project
`status`/`refresh`/`resume`, `search`, manual `context` briefs, `portfolio`, `digest status`, workspace `index build`, project `index build`/`check`, user-habit `add`/`list`/`search`/`pause`/`delete`/`remind`/`inject`, and Team `init`/`summary`/`publish status`.

`sybermem index build` builds the workspace SQLite search index. `sybermem project refresh --format json` deterministically creates missing SyberMem-managed project files, refreshes stale managed hooks/templates with `.bak` backups, preserves custom instruction content while inserting or refreshing the marker-bounded protocol block, and ensures `.sybermem/project.yaml`. `sybermem project index build` and `sybermem project index check` manage the derived `.sybermem/INDEX.md`. `sybermem digest status` scans every phase/theme digest and reports its coverage health (current / stale / unknown), pinpointing which source records drifted; it exits non-zero when any digest is stale so scripts can gate on governance health. `sybermem record id --type <change|decision|requirement|bug>` mints a canonical record id. Record creation itself remains `/sybermem-record` skill orchestration, not a CLI command.

User habits are explicit personal preferences stored outside projects:

```bash
sybermem habit add --type workflow --applies-to planning "Prefer plans before implementation"
sybermem habit list --format json
sybermem habit remind --context planning --format markdown
sybermem habit inject --context planning --format markdown
```

`pause` and `delete` keep habits out of reminders and injection. Reminder output is
visible and confirmation-first; injection emits at most three active, high-confidence,
directly relevant habits. On hosts that support prompt-time reminder injection,
the same conservative gate also requires the habit to be prompt-ok-when-supported,
and the host should fail open if nothing qualifies.

Manual context helpers provide copy/paste-safe memory briefs for hosts without
Claude Code's prompt-time hook surface:

```bash
sybermem context session --format markdown
sybermem context prompt --query "auth flow" --format markdown
sybermem context recall --query "auth flow" --format markdown
sybermem context habit --context planning --format markdown
```

`context session` / `context prompt` / `context habit` are explicit manual delivery
surfaces. They remain the documented manual path for OpenCode and for Codex
project memory. They do not install project recall hooks, background automation,
or unsupported runtimes.

`context recall` runs the exact high-signal recall gate the Claude prompt hook uses
and renders the same `⭐` (important) / `💡` (ordinary) markers. The OpenCode plugin
calls it on every prompt to deliver gated, marker-tagged project recall through
`chat.message` + `experimental.chat.system.transform`, and the managed Codex
`UserPromptSubmit` hook uses the same CLI route when Codex hook support is
installed. You can also invoke it manually to preview what would be recalled for
a given prompt:

```bash
sybermem context recall --query "deploy checklist" --format markdown
```

See the [main repository](https://github.com/goudaren0528/sybermem) for
installation and usage.

## License

MIT
