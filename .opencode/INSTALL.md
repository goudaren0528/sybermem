# OpenCode Installation Notes

SyberMem currently installs into OpenCode in two parts:

- Skills are copied to `~/.config/opencode/skills/`
- The plugin file is copied to `~/.config/opencode/plugins/sybermem.ts`

The current OpenCode plugin implements these lifecycle hooks:

- `session.created`
- `session.idle`
- `experimental.session.compacting`

OpenCode does not currently expose a documented prompt-time plugin callback for
injecting `additionalContext` on every user prompt. SyberMem therefore does not
invent or register an unsupported `UserPromptSubmit` event there. Use
`/sybermem-search` for manual task recall, or rely on the supported compaction
hook to add project memory when OpenCode compacts the session.

Project initialization still uses `/sybermem-init-project`.

The project-local distribution path is still important on OpenCode: `/sybermem-init-project`
or `/sybermem-update` can create or refresh `.sybermem/`, `AGENTS.md`,
`.claude/settings.json`, `.sybermem/hooks/detect_record_intent.py`, and
`.sybermem/hooks/task_recall.py` for Claude-compatible project sharing. That does
not change the OpenCode limitation above, and it does not mean OpenCode supports
automatic `UserPromptSubmit` prompt injection.

The OpenCode plugin does not replace project `.sybermem/` files. It complements the project-managed `.sybermem/`, `AGENTS.md`, and `.claude/settings.json` setup.
