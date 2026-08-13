# SyberMem Feature Map

Last updated: 2026-08-13

This is the source-of-truth feature map for SyberMem project capabilities and
platform support claims. Public READMEs and platform install docs should stay
consistent with this file.

## Support Legend

| Label | Meaning |
|---|---|
| Full | Real platform runtime, hook, plugin, or CLI support exists and the capability can run automatically where described. |
| Partial | Real support exists, but only for a narrower sub-capability. |
| Manual | User or agent must explicitly invoke a skill or CLI command. |
| Metadata | Only manifest, entry-file, or documentation support exists; no runtime wiring is installed. |
| Unsupported | Not implemented and must not be claimed as supported. |

## Platform Summary

| Platform | Current Level | Mechanism | Current Conclusion |
|---|---|---|---|
| Claude Code | Full | `.claude-plugin` plus `SessionStart`, `UserPromptSubmit`, and `Stop` hooks | Full baseline platform for prompt-time recall, record intent, habit reminders, startup context, and stop-time nudges. |
| OpenCode | Full for supported seams | TypeScript plugin with `session.created`, `session.idle`, `chat.message`, `experimental.chat.system.transform`, and `experimental.session.compacting` | Real runtime integration. OpenCode now supports prompt-time project recall and bounded User Habit Memory reminders through the chat transform path. |
| Codex | Partial runtime plus skills | User skills under `~/.agents/skills` plus managed `.codex/hooks/user_prompt.py` registered under `UserPromptSubmit` | Not skills-only anymore. Codex supports bounded User Habit Memory prompt reminders via `hookSpecificOutput.additionalContext`, but project memory remains manual. |
| Gemini | Metadata | `gemini-extension.json` and `GEMINI.md` | Entry/manifest support only. No SyberMem runtime hooks or installer-managed Gemini integration. |
| Cursor | Metadata | `.cursor-plugin/plugin.json` | Manifest support only. No SyberMem runtime hooks or installer-managed Cursor integration. |
| Kimi | Metadata | `.kimi-plugin/plugin.json` | Manifest support only. No SyberMem runtime hooks or installer-managed Kimi integration. |

## Capability Matrix

| Capability | Claude Code | OpenCode | Codex | Gemini | Cursor | Kimi |
|---|---|---|---|---|---|---|
| User-level skills | Full: plugin/user skills | Full: copied to `~/.config/opencode/skills` | Full: copied to `~/.agents/skills` | Metadata/entry only | Metadata only | Metadata only |
| CLI/Core access | Full | Full; plugin and CLI-using skills prefer the fixed launcher | Full when invoked manually or from skills; hook also prefers fixed launcher | Manual only if `sybermem` is installed | Manual only if `sybermem` is installed | Manual only if `sybermem` is installed |
| Project memory records | Full via `.sybermem/` | Full via the same project `.sybermem/` | Full via manual skills/CLI and `AGENTS.md` guidance | Manual only | Manual only | Manual only |
| Project init/update | Full: `/sybermem-init-project`, `/sybermem-update` | Full through skills | Full through user skills | Manual/entry guidance only | Manual/entry guidance only | Manual/entry guidance only |
| Session-start project context | Full: `SessionStart` hook | Partial automatic: `session.created` loads key-conclusion/stale/commit-gap signals | Unsupported runtime hook; use `/sybermem-resume` manually | Unsupported | Unsupported | Unsupported |
| Stop/idle change nudge | Full: `Stop` hook | Full on OpenCode seam: `session.idle` record/digest nudges and bounded auto-trail journal | Unsupported | Unsupported | Unsupported | Unsupported |
| Prompt-time project recall | Full: `UserPromptSubmit` task recall | Full on OpenCode seam: `chat.message` plus `experimental.chat.system.transform` | Unsupported; use `/sybermem-search` or `sybermem context prompt/recall` manually | Unsupported | Unsupported | Unsupported |
| Prompt-time recall markers | Full: `⭐` important and `💡` ordinary recall hints | Full: same markers injected on qualifying prompts | Unsupported for project recall | Unsupported | Unsupported | Unsupported |
| Prompt-time recall observability log | Full where Claude prompt hook logs recall injection/abstention | Unsupported `.recall-debug.jsonl`; OpenCode uses visible `⭐`/`💡` injected context instead | Unsupported | Unsupported | Unsupported | Unsupported |
| Prompt-time User Habit Memory reminder | Full: managed `UserPromptSubmit` hook | Full on OpenCode seam: same chat transform path as recall | Partial: habit-only `UserPromptSubmit` hook returning `hookSpecificOutput.additionalContext` | Unsupported | Unsupported | Unsupported |
| Prompt-time record-intent capture | Full: `UserPromptSubmit` captures explicit record intent into `.record-intent.json` | Unsupported | Unsupported | Unsupported | Unsupported | Unsupported |
| Compaction carry-forward | Full through Claude-managed context/hook flow where available | Full: `experimental.session.compacting` injects session context, phase info, digest heads-up, next-step, and habit inject output | Unsupported | Unsupported | Unsupported | Unsupported |
| Manual resume/search/record/habit | Full | Full | Full via installed skills and CLI | Manual only | Manual only | Manual only |
| Team publish/summary | Full via skill/CLI | Manual skill/CLI | Manual skill/CLI | Manual CLI only | Manual CLI only | Manual CLI only |
| Hidden auto-resume | Not claimed as hidden behavior | Unsupported | Unsupported | Unsupported | Unsupported | Unsupported |
| Background automation | Claude managed hook scope only | OpenCode plugin lifecycle scope only; no hidden background worker | Unsupported | Unsupported | Unsupported | Unsupported |
| `.codex/config.toml` management | Not applicable | Not applicable | Unsupported; installers must not create or require it | Not applicable | Not applicable | Not applicable |
| Installer coverage | Full: Claude skills, CLI/Core, global launchers | Full: OpenCode skills and plugin | Full: Codex skills, Codex habit hook, hooks.json merge | Version/manifest only | Version/manifest only | Version/manifest only |
| Integrity guards | Full packaging and hook guards | OpenCode plugin route, update wiring, and fixed-launcher guards | Codex skill distribution, habit hook, honesty, and no-config guards | Version consistency | Version consistency | Version consistency |

## Project/Core Feature Map

| Feature Area | Status | Main Entrypoints | Notes |
|---|---|---|---|
| Project Memory | Full | `.sybermem/changes`, `.sybermem/decisions`, `.sybermem/requirements`, `.sybermem/bugs` | Canonical Markdown records with UUID-backed `record_id`, relation fields, source/trust metadata, and legacy ID compatibility. |
| Derived Project Index | Full | `sybermem project index build`, `sybermem project index check` | `.sybermem/INDEX.md` is generated from canonical records and can be mechanically checked. |
| Resume | Full | `/sybermem-resume`, `sybermem resume --mode fast|standard|deep` | Read-only restart brief with phase, progress, risks, confidence, freshness, and next action. |
| Search | Full | `/sybermem-search`, `sybermem search` | Supports project/workspace search, record-id/topic/keyword/relation matching, successor guidance, conflict notes, and stale-index warnings. |
| High-signal Recall | Full | Claude `UserPromptSubmit`, OpenCode `chat.message`/transform, `sybermem context recall` | Automatic only on Claude/OpenCode; manual preview elsewhere. Uses stricter gate than explicit search. |
| Workspace/Hub | Full | `sybermem index build`, workspace `sybermem search`, `sybermem portfolio` | SQLite FTS5 workspace index with project/type/status filters and stale-index detection. |
| Digest Governance | Full | `/sybermem-digest`, `/sybermem-theme-digest`, `sybermem digest status` | Phase/theme digests with coverage hash and current/stale/unknown verdicts. |
| Team Memory | Full | `sybermem team init`, `sybermem publish status`, `sybermem team summary`, `/sybermem-team-publish`, `/sybermem-team-summary` | Preview hash protection, Team overview, management summary, and digest-history sync. |
| User Habit Memory | Full | `/sybermem-habit`, `sybermem habit add/list/search/pause/delete/remind/inject` | User-owned storage under `~/.sybermem/user-habits` or `SYBERMEM_HOME/user-habits`; not project or Team memory. |
| Context Helpers | Full | `sybermem context session|prompt|recall|habit` | Shared host-neutral context contract. OpenCode/Codex automation reuses the same conservative CLI behavior where supported. |
| Record Authoring | Skill-orchestrated | `/sybermem-record`; CLI helper `sybermem record id --type ...` | CLI mints IDs and validates indexes; full record writing remains skill workflow. |
| Distribution/Verification | Full | install/update scripts, `scripts/check-plugin-package.py`, pytest package integrity tests | Installers refresh Claude/OpenCode/Codex skills, OpenCode plugin, Codex hook, CLI/Core runtime, fixed launchers, and guards. |

## OpenCode Detail

| Capability | Status | Mechanism | Boundary |
|---|---|---|---|
| Skills | Full | `~/.config/opencode/skills` | Refreshed by global install/update. |
| Plugin | Full | `~/.config/opencode/plugins/sybermem.ts` | Refreshed by global install/update. |
| Session-start context | Partial automatic | `session.created` | Toast-level load/stale/commit-gap signals; hidden auto-resume is unsupported. |
| Idle nudge | Full | `session.idle` | Mirrors Claude Stop follow-up thresholds using OpenCode lifecycle seam. |
| Prompt-time project recall | Full | `chat.message` -> `sybermem context recall` -> `experimental.chat.system.transform` | Same-turn system prompt injection; only high-signal recall qualifies. |
| Prompt-time habit reminder | Full | `chat.message` -> `sybermem context habit --delivery prompt-time` -> system transform | Bounded, fail-open, active/high-confidence/directly relevant/prompt-ok habits only. |
| Compaction carry-forward | Full | `experimental.session.compacting` | Includes session context, phase/status, digest heads-up, next-step, and compaction habit inject. |
| Record-intent capture | Unsupported | None | Do not claim `.record-intent.json` prompt capture on OpenCode. |
| Recall debug log | Unsupported | None | OpenCode uses visible `⭐`/`💡` markers instead of Claude `.recall-debug.jsonl`. |

## Codex Detail

| Capability | Status | Mechanism | Boundary |
|---|---|---|---|
| User skills | Full | `~/.agents/skills` | Same SyberMem skill set as other hosts when Codex loads user skills. |
| Project setup/update | Full manual | `/sybermem-init-project`, `/sybermem-update` | Refreshes `.sybermem/` and `AGENTS.md`; no Codex project runtime required. |
| Habit prompt reminder | Partial runtime | `.codex/hooks/user_prompt.py` registered under `UserPromptSubmit` | Habit-only. Emits `hookSpecificOutput.additionalContext` only for `## User Habit Reminder`. |
| Project memory prompt recall | Unsupported | None | Use `/sybermem-search`, `/sybermem-resume`, or `sybermem context prompt/recall` manually. |
| Record-intent capture | Unsupported | None | Does not write `.record-intent.json`. |
| Session lifecycle hooks | Unsupported | None | No SessionStart/Stop equivalent is claimed. |
| Hidden auto-resume | Unsupported | None | Must not be claimed. |
| Background automation | Unsupported | None | Must not be claimed. |
| `.codex/config.toml` | Unsupported | None | Installers and guards must not create it. |

## Explicit Unsupported Claims

All bullets below are unsupported claims. These statements are stale or wrong and
should not appear in current public docs:

- Unsupported claim: OpenCode is manual-only for prompt-time recall.
- Unsupported claim: OpenCode supports only compaction-time habit injection.
- Unsupported claim: OpenCode lacks prompt-time User Habit Memory reminders.
- Unsupported claim: Codex is skills-only.
- Unsupported claim: Codex supports project recall, record-intent capture, lifecycle hooks, hidden auto-resume, background automation, prompt/agent handler runtimes, or `.codex/config.toml`.
- Unsupported claim: Gemini, Cursor, or Kimi have SyberMem runtime integration beyond metadata/entry manifests.
