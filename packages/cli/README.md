# sybermem-cli

Command-line interface for [SyberMem](https://github.com/goudaren0528/sybermem) —
a project/team engineering memory system for AI workflows.

Provides the `sybermem` command wrapping `sybermem-core` operations: project
`status`/`resume`, `search`, `portfolio`, `digest status`, workspace `index build`, project `index build`/`check`, and Team `init`/`summary`/`publish status`.

`sybermem index build` builds the workspace SQLite search index. `sybermem project index build` and `sybermem project index check` manage the derived `.sybermem/INDEX.md`. `sybermem digest status` scans every phase/theme digest and reports its coverage health (current / stale / unknown), pinpointing which source records drifted; it exits non-zero when any digest is stale so scripts can gate on governance health. `sybermem record id --type <change|decision|requirement|bug>` mints a canonical record id. Record creation itself remains `/sybermem-record` skill orchestration, not a CLI command.

See the [main repository](https://github.com/goudaren0528/sybermem) for
installation and usage.

## License

MIT
