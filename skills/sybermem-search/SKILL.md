---
name: sybermem-search
description: Use when searching or querying SyberMem project records by keyword, topic, phase range, date range, or record ID, including finding which records reference a given record.
---

# sybermem-search Skill

**Announce at start:** "I'm using the sybermem-search skill to query project records."

AI-driven retrieval over SyberMem records. Searches Key Conclusions, Topic Index, phase coverage, and record bodies using file-system tools. Zero dependencies, no index files.

## Core Invariant

- **Search is read-only. It never creates, modifies, or deletes records.**

<HARD-GATE>
Do NOT write any file to disk. Search is non-persistent output only.
Do NOT fabricate records or relations that are not present on disk.
Do NOT report a record without verifying it exists with a file-system tool.
</HARD-GATE>

## Directory Resolution

Resolve project root by walking up from cwd to find `.sybermem/` + `.claude/settings.json`. Auto-migrate `ADR/` if found. Full rules in the session protocol block in AGENTS.md/CLAUDE.md.

## Query Syntax

| Query form | Meaning |
|---|---|
| `auth` | free keyword search |
| `#hooks` | search by topic tag |
| `phase-002..phase-004` | phase range |
| `2026-05-01..2026-06-15` | date range |
| `requirement-002` | record ID lookup, including reverse references |
| `--scope workspace` | search across all registered projects in `~/.sybermem/projects.yaml` |

## Flow

You MUST complete these steps in order:

1. **Resolve project root** — apply directory resolution rules above. If `.sybermem/INDEX.md` does not exist, tell the user to run `/sybermem-init-project` and stop.
2. **Parse the query type** — classify the query as topic (`#tag`), phase range (`phaseN..phaseM`), date range (`date..date`), record ID (`type-NNN`), or free keyword.
3. **Run the matching retrieval path:**
   - **topic** → read `## Topic Index` in `.sybermem/INDEX.md`, collect the record IDs listed for that topic, and inspect any optional suffix on the topic line: `[active]`, `[low]`, or `[deprecated → <new-topic>]`.
   - **phase range** → read `.sybermem/analysis/phase-index.md` coverage map, collect records covered by phases in the range.
   - **date range** → list record files whose `YYYY-MM-DD` filename prefix falls in the range.
   - **record ID** → locate that record, AND reverse-scan all records' `implements`/`fixes`/`related` frontmatter fields for the ID, plus scan for records whose `superseded_by:` field points to the ID (see Reverse references below).
   - **free keyword** → Grep `## Key Conclusions` first, then Grep `## Archived Conclusions`, then Grep record bodies under `.sybermem/{changes,decisions,requirements,bugs}/`. Results from `## Archived Conclusions` are marked with their archive reason (e.g. `[superseded by ...]`, `[archived]`).

   **When `--scope workspace` is specified:**
   - Prefer running `sybermem search <query> --scope workspace --format json`.
   - Optional filters may be added: `--project <slug>`, `--type <change|decision|requirement|bug>`, `--project-status <active|missing|stale>`.
   - If the CLI reports that the workspace index is missing, tell the user to run `sybermem index build` first.
   - Use the returned JSON as the source of truth, then explain or group the results for the user.
4. **Enrich each hit** — for every matched record, look up its phase (from phase-index coverage map), read its `implements`/`fixes`/`related` fields, read its optional `superseded_by` field, and reverse-scan for records that it supersedes.
5. **Rank** — keyword hits in Key Conclusions rank above body-only hits; newer dates rank higher within the same tier.
6. **Output** — render the result list (see Output Format). Do not write anything to disk.

## Abstention and historical evidence

- Automatic/compact recall must prefer silence over weak memory. If only weak-overlap, auto-trail-only, stale-only, superseded-only, archived-only, or resolved-only matches are available, do not present them as task recall hints.
- Explicit historical search remains allowed: if the user asks to search records, inspect and show historical evidence, but mark Authority, Lifecycle, Freshness, Conflict, and successor/current guidance clearly.
- If a compact diagnostic path returns `no_reliable_recall`, treat it as a terminal abstention result, not as a record hit. Do not pad the answer with low-signal records.

```md
No reliable SyberMem recall for "<query>".
- Reason: weak overlap | only auto-trail evidence | only historical or stale matches
- Explicit historical search can still inspect matching evidence if the user asks for it.
```

## Reverse references

When the query is a record ID, also find which records point AT it:
- Grep all record frontmatter under `.sybermem/{changes,decisions,requirements,bugs}/` for the target ID appearing in `implements:`, `fixes:`, or `related:` fields.
- Grep for records whose `superseded_by:` field points to the target ID; list those under `Supersedes:`.
- List the first set under `Referenced by:` with the relation type.

This is computed live; no reverse index is stored.

## Output Format

```md
## SyberMem Search: "<query>"

[Optional warning line: deprecated topic / low activity]

Found N records:

1. **[type-NNN]** title (date)
   - Authority: authoritative | summarized | evidence
   - Lifecycle: active | resolved | superseded | archived
   - Freshness: current | historical | stale
   - Match: keyword | topic | relation | record-id
   - Related digest: digest-NNN (if any)
   - Phase: phase-00X (phase title)
   - File: .sybermem/<type>/<file>.md
   - Relations: implements requirement-002, related change-005
   - Referenced by: change-008 (implements)
   - Superseded by: decision-007 — one-line conclusion
   - Supersedes: decision-003 — archived old conclusion
   - Current guidance: Prefer successor decision-007 for current guidance.

2. ...
```

When `--scope workspace`, use this format instead:

```md
## SyberMem Workspace Search: "<query>"

### [eszyzu] (N results)
1. **[type-NNN]** title (date)
   - Authority: authoritative | summarized | evidence
   - Lifecycle: active | resolved | superseded | archived
   - Freshness: current | historical | stale
   - Match: keyword | topic | relation | record-id
   - Related digest: digest-NNN (if any)
   - File: <absolute-path>/.sybermem/<type>/<file>.md
   ...

### [old-project] [unavailable]
Project path not accessible.
```

Omit the per-project section entirely if the project has zero results and is available (to reduce noise). Always show `[unavailable]` projects.

Omit `Relations:`, `Referenced by:`, `Superseded by:`, `Supersedes:`, or `Related digest:` lines when there are none.

Archived, superseded, or resolved records are still searchable, but they must be marked clearly and never presented as the current authoritative fact when newer records exist.

## Corrections and supersession

Historical records are durable evidence. When a search result is outdated or wrong:

1. Create a new `decision`, `requirement`, `bug`, or `change` record with the corrected current truth.
2. Link the old record to the successor with `superseded_by: <new-record-id>` or link the fixing/current record with `fixes: <old-record-id>` where appropriate.
3. Present both sides in search: the old record remains visible as historical evidence, and the successor/current record is the guidance to follow.

Do not silently edit historical truth away just to make search look current. If the user asks to correct memory, route them to `/sybermem-record` and `/sybermem-link` after showing the evidence.

## Error Handling

- `.sybermem/INDEX.md` missing → prompt `/sybermem-init-project`, stop.
- No matches → say so plainly; do not invent results.
- Phase-index missing → skip phase enrichment, still return keyword/topic/date results.
- Deprecated topic → still return legacy results, but show a warning suggesting the replacement topic.
- Low-activity topic → still return results, but show an informational Low-activity topic note.
- `--scope workspace` with no `~/.sybermem/projects.yaml` → tell the user to run `/sybermem-update` in target projects.
- `--scope workspace` with all projects unavailable → report all unavailable, no results.
- `--scope workspace` with some unavailable → show available results + list unavailable projects at the end.

## Red Flags — STOP and Re-check

If you catch yourself doing any of these, STOP:
- Writing search output to a file
- Reporting a record without verifying it exists on disk
- Inventing a relation or phase that is not in the frontmatter / coverage map
- Returning results when the query clearly matched nothing
- Treating `no_reliable_recall` as permission to show weak or stale automatic recall hits
- Mutating an old record instead of creating/linking a successor for correction

**All of these mean: go back to the relevant step and re-verify.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I roughly remember the records, I'll answer from memory" | Memory drifts. Grep the actual files. |
| "Close enough match, I'll report it as a hit" | Report what matched, with evidence. Don't pad results. |
| "Phase-index is missing, I'll guess the phase" | Skip phase enrichment. Never invent a phase. |
| "The old topic still kind of works, no need to mention it's deprecated" | Search should help users migrate. Show the replacement topic explicitly. |
| "If a record is superseded, I can ignore it entirely" | Users may be searching historical decisions. Show it, but point them to the replacement. |

## Terminal State

This skill is complete when:
- the query has been parsed and the matching retrieval path run
- each hit is enriched with phase and relations where available
- the ranked result list has been output to the user
- no file was written

## Integration

**Related skills:**
- **sybermem-record** — creates the records this skill searches
- **sybermem-link** — adds the relations this skill surfaces
- **sybermem-phase-analyze** — produces the phase coverage used for enrichment
