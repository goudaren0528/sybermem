# sybermem-cli

Command-line interface for [SyberMem](https://github.com/goudaren0528/sybermem) —
a project/team engineering memory system for AI workflows.

Provides the `sybermem` command wrapping `sybermem-core` operations: project
`status`/`resume`, `search`, manual `context` briefs, `portfolio`, `digest status`, workspace `index build`, project `index build`/`check`, user-habit `add`/`list`/`search`/`pause`/`delete`/`remind`/`inject`, and Team `init`/`summary`/`publish status`.

`sybermem index build` builds the workspace SQLite search index. `sybermem project index build` and `sybermem project index check` manage the derived `.sybermem/INDEX.md`. `sybermem digest status` scans every phase/theme digest and reports its coverage health (current / stale / unknown), pinpointing which source records drifted; it exits non-zero when any digest is stale so scripts can gate on governance health. `sybermem record id --type <change|decision|requirement|bug>` mints a canonical record id. Record creation itself remains `/sybermem-record` skill orchestration, not a CLI command.

User habits are explicit personal preferences stored outside projects:

```bash
sybermem habit add --type workflow --applies-to planning "Prefer plans before implementation"
sybermem habit list --format json
sybermem habit remind --context planning --format markdown
sybermem habit inject --context planning --format markdown
```

`pause` and `delete` keep habits out of reminders and injection. Reminder output is
visible and confirmation-first; injection emits at most three active, high-confidence,
directly relevant habits.

Manual context helpers provide copy/paste-safe memory briefs for hosts without
Claude Code's prompt-time hook surface:

```bash
sybermem context session --format markdown
sybermem context prompt --query "auth flow" --format markdown
sybermem context habit --context planning --format markdown
```

These commands are explicit manual delivery surfaces. They do not install hooks,
background automation, or automatic prompt-time injection for OpenCode or Codex.

See the [main repository](https://github.com/goudaren0528/sybermem) for
installation and usage.

## License

MIT
