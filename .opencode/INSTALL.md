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

This means:

- `/sybermem-resume` is manual
- `/sybermem-search` is manual
- there is no hidden auto-resume
- there is no unsupported per-prompt injection
- the plugin does not create a second memory store

`/sybermem-resume` is also manual on OpenCode. Use it when you want a bounded,
read-only restart brief for the current project. It can show the current phase,
recent progress, risks, next action, confidence, freshness, and reason, but it
never auto-runs the suggested action.

Mode guidance on OpenCode is the same as elsewhere:

- `fast` for the short restart brief
- `standard` for the default handoff with a bit more trust context
- `deep` for a bounded follow-up that points you to the right records or digests

Deep mode still does not auto-read or inject full history. When you need
historical evidence, run `/sybermem-search`. When OpenCode compacts a session,
rely on the supported compaction hook rather than unsupported prompt-time
injection.

## Install and update boundaries

The OpenCode side is refreshed by the same global install/update scripts used for
the rest of SyberMem.

- global install or global update refreshes `~/.config/opencode/skills/`
- global install or global update refreshes `~/.config/opencode/plugins/sybermem.ts`
- re-running the remote install command is a real refresh path for the OpenCode plugin and skills

That global refresh does not replace project-local SyberMem files. Existing
projects still need `/sybermem-update` when you want refreshed managed hooks,
templates, or instruction files inside the project.

Project initialization still uses `/sybermem-init-project`.

The project-local distribution path is still important on OpenCode: `/sybermem-init-project`
or `/sybermem-update` can create or refresh `.sybermem/`, `AGENTS.md`,
`.claude/settings.json`, `.sybermem/hooks/detect_record_intent.py`, and
`.sybermem/hooks/task_recall.py` for Claude-compatible project sharing. That does
not change the OpenCode limitation above, and it does not mean OpenCode supports
automatic `UserPromptSubmit` prompt injection.

Use this workflow:

1. run the global install or global update first
2. run `/sybermem-update` inside an existing project
3. run `/sybermem-init-project` when initialization is still missing

The OpenCode plugin does not replace project `.sybermem/` files. It complements the project-managed `.sybermem/`, `AGENTS.md`, and `.claude/settings.json` setup.
