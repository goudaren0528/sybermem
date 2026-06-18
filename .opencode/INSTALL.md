# OpenCode Installation Notes

SyberMem currently installs into OpenCode in two parts:

- Skills are copied to `~/.config/opencode/skills/`
- The plugin file is copied to `~/.config/opencode/plugins/sybermem.ts`

The current OpenCode plugin implements these lifecycle hooks:

- `session.created`
- `session.idle`
- `experimental.session.compacting`

Project initialization still uses `/sybermem-init-project`.

The OpenCode plugin does not replace project `.sybermem/` files. It complements the project-managed `.sybermem/`, `AGENTS.md`, and `.claude/settings.json` setup.
