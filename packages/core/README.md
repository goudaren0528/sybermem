# sybermem-core

Core identity, registry, indexing, search, resume, user-habit memory, and norm/digest
governance for [SyberMem](https://github.com/goudaren0528/sybermem) — a project engineering
memory system for AI workflows.

This package is the programmatic core consumed by `sybermem-cli` and the SyberMem
hooks/skills. See the [main repository](https://github.com/goudaren0528/sybermem)
for installation and usage.

User Habit Memory stores explicit personal preferences under `~/.sybermem/user-habits/`
or `SYBERMEM_HOME/user-habits/`. It is separate from project `.sybermem/` records;
only active, high-confidence, directly relevant habits
are eligible for bounded Markdown injection. Visible reminders are available through
`render_habit_reminder_markdown` and `sybermem habit remind`; they do not create active
habits without user confirmation. Passive candidate capture never persists unbounded or
unfiltered prompt text: it stores only a bounded, secret/injection-filtered summary of the
triggering prompt (mirroring the record-intent summary contract) in a user-scoped,
bounded candidate list so the confirm step can propose a normalized statement.

## License

MIT
