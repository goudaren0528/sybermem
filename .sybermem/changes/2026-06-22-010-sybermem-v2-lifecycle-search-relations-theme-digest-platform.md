---
type: change
date: 2026-06-22
number: 010
title: SyberMem v2 — lifecycle layer, search, relations, theme digest, and platform ecosystem
status: implemented
author: Developer
related_files: .sybermem/hooks/session_start_context.py, .sybermem/hooks/record_change_on_stop.py, .sybermem/hooks/check_project_health.py, packages/claude-skills/sybermem-search/SKILL.md, packages/claude-skills/sybermem-link/SKILL.md, packages/claude-skills/sybermem-theme-digest/SKILL.md, packages/opencode-plugin/sybermem.ts, .claude-plugin/plugin.json, hooks/hooks.json, hooks/session-start, hooks/stop, scripts/global-session-start-launcher.py
implements: [requirement-002]
related: [change-006, change-008]
---

## Change Content

Six major capability rounds implemented in a single session:

1. **Lifecycle Layer** — SessionStart hook for deterministic startup context injection (Key Conclusions + Topic Index + phase status + stale signal); Stop hook enhanced with commit-gap detection, auto-trail dedup, and unified `.nudge-state.json`; OpenCode plugin enhanced with stale detection and compaction length limits; cross-platform nudge dedup.

2. **Update Fast-Path** — `check_project_health.py` script does all managed-file classification in one pass; init-project fast-path exits in seconds for up-to-date projects; non-destructive update rules (protocol-block-only for CLAUDE.md, surgical JSON patch for settings.json).

3. **Skill Design Optimization** — Rationalization Tables added to record/init-project/update; Integration sections added to all 8 skills; Flowcharts added to init-project and using-sybermem; init-project split into SKILL.md + 3 auxiliary files.

4. **Platform Ecosystem** — Claude Code plugin skeleton (.claude-plugin/, hooks/hooks.json, polyglot run-hook.cmd); Gemini/Cursor/Codex/Kimi/OpenCode entry files; plugin skill sync script; marketplace validation; plugin package checker with real `claude plugins validate`.

5. **Search & Relations** — `/sybermem-search` (AI-driven retrieval by keyword/topic/phase/date/record ID with reverse references); `/sybermem-link` (forward-only relation management); record relation inference at creation time; optional `implements`/`fixes`/`related` frontmatter fields in all 4 record templates.

6. **Theme Digest Layer** — `/sybermem-theme-digest` (topic-level compression above phase digests); `theme-digest-template.md`; `.sybermem/theme-digests/` directory; INDEX.md Theme Digests section; init-project provisioning + health check detection.

## Reason for Change

SyberMem v1 was a recording + grouping + compression system. Real usage exposed three gaps: (a) knowledge was hard to find back (no retrieval/query), (b) records were isolated (no cross-references), (c) the system didn't integrate into the session lifecycle (startup/stop/compaction were manual or unreliable). Additionally, the manual install/update flow was too slow and the skill design missed several Superpowers best practices.

This session addressed all of these by evolving SyberMem into a lifecycle-aware, retrieval-capable, relation-linked, topic-compressible project memory system that works as a first-class Claude Code plugin.

## Impact Scope

- **Session experience**: project memory loads automatically at startup; ends with smart record/digest nudges; survives compaction
- **Retrieval**: users can now search by keyword, topic, phase range, date range, or record ID
- **Knowledge graph**: records can declare implements/fixes/related relationships; reverse references computed at query time
- **Compression**: theme digests compress one topic across multiple phases into one durable artifact
- **Platform**: Claude Code plugin, Gemini, Cursor, Codex, Kimi, OpenCode all have entry points
- **Maintenance**: update fast-path reduces init-project from 15-25 tool calls to 1 script + targeted fixes
- **Skill quality**: Rationalization Tables, Integration sections, Flowcharts improve AI compliance

## Implementation

~50 commits across 6 rounds. Key new files:
- `.sybermem/hooks/session_start_context.py` — SessionStart hook
- `scripts/global-session-start-launcher.py` — global launcher
- `.sybermem/hooks/check_project_health.py` — fast-path health checker
- `packages/claude-skills/sybermem-search/SKILL.md` — retrieval skill
- `packages/claude-skills/sybermem-link/SKILL.md` — relation skill
- `packages/claude-skills/sybermem-theme-digest/SKILL.md` — theme digest skill
- `.claude-plugin/plugin.json` + `hooks/hooks.json` — Claude Code plugin
- `hooks/run-hook.cmd` + `hooks/session-start` + `hooks/stop` — plugin lifecycle hooks
- `GEMINI.md`, `.cursor-plugin/`, `.codex-plugin/`, `.kimi-plugin/` — multi-platform entries

## Test Verification

- All hooks verified via real CLI: `python .sybermem/hooks/session_start_context.py` outputs valid JSON; `python .sybermem/hooks/record_change_on_stop.py` exits 0
- Plugin verified: `claude --plugin-dir . -p "/sybermem:using-sybermem"` and `claude --plugin-dir . -p "/sybermem:sybermem-search hooks"` both returned correct results
- Marketplace validated: `claude plugins validate .claude-plugin/plugin.json` and `claude plugins validate .claude-plugin/marketplace.json` both pass
- Plugin package checker: `python scripts/check-plugin-package.py` → `OK (static checks + claude plugins validate)`
- Health check: `python .sybermem/hooks/check_project_health.py` → `overall: fresh` after dogfood update

## Notes

This is the largest single-session change in SyberMem's history. It transforms the system from v1 (record + group + compress) to v2 (lifecycle + retrieve + relate + theme-compress + multi-platform). Two backlog items remain deferred: marketplace formal release and install-path migration (documented in `docs/superpowers/BACKLOG.md`).
