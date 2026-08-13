/**
 * SyberMem OpenCode Plugin
 *
 * Provides session lifecycle hooks for the SyberMem memory system:
 * - session.created  → load Key Conclusions and notify user
 * - session.idle     → detect git changes, nudge for /sybermem-record
 * - session.compacting → inject Key Conclusions + active phase into compaction context
 */

import type { Plugin } from "@opencode-ai/plugin"
import { readFileSync, existsSync, writeFileSync } from "fs"
import { join, resolve } from "path"

// ---------------------------------------------------------------------------
// Project root resolution (mirrors the Python launcher logic)
// ---------------------------------------------------------------------------

function resolveRoot(cwd: string): string | null {
  let current = resolve(cwd)
  while (true) {
    const hasSybermem = existsSync(join(current, ".sybermem"))
    const hasSettings = existsSync(join(current, ".claude", "settings.json"))
    const hasIndex = existsSync(join(current, ".sybermem", "INDEX.md"))
    if (hasSybermem && (hasSettings || hasIndex)) return current
    const parent = resolve(current, "..")
    if (parent === current) break
    current = parent
  }
  return null
}

function userHome(): string | null {
  return process.env.USERPROFILE ?? process.env.HOME ?? null
}

function resolveSybermemCommand(): string {
  const home = userHome()
  if (!home) return "sybermem"
  const launcher = process.platform === "win32"
    ? join(home, ".claude", "sybermem", "cli", "sybermem.cmd")
    : join(home, ".claude", "sybermem", "cli", "sybermem")
  return existsSync(launcher) ? launcher : "sybermem"
}

async function sybermemText(
  $: any,
  root: string,
  args: string[]
): Promise<string> {
  const sybermem = resolveSybermemCommand()
  if (args[0] === "next-step") {
    return $`${sybermem} next-step ${args[1]} ${args[2]}`.cwd(root).text()
  }
  if (args[0] === "habit" && args[1] === "inject") {
    return $`${sybermem} habit inject ${args[2]} ${args[3]} ${args[4]} ${args[5]}`.cwd(root).text()
  }
  if (args[0] === "context" && args[1] === "session") {
    return $`${sybermem} context session ${args[2]} ${args[3]}`.cwd(root).text()
  }
  throw new Error(`Unsupported SyberMem command route: ${args[0] ?? ""} ${args[1] ?? ""}`.trim())
}

async function digestStatusText($: any, root: string): Promise<string> {
  const sybermem = resolveSybermemCommand()
  return $`${sybermem} digest status --format json`.cwd(root).nothrow().text()
}

// ---------------------------------------------------------------------------
// INDEX.md parsing
// ---------------------------------------------------------------------------

interface ParsedIndex {
  conclusions: string[]
  topicIndex: Record<string, string[]>
}

function parseIndex(root: string): ParsedIndex | null {
  const indexPath = join(root, ".sybermem", "INDEX.md")
  if (!existsSync(indexPath)) return null
  const content = readFileSync(indexPath, "utf-8")

  // Parse Key Conclusions
  const conclusionsMatch = content.match(
    /## Key Conclusions\s*\n([\s\S]*?)(?=\n---|\n## )/
  )
  const conclusions: string[] = []
  if (conclusionsMatch) {
    for (const line of conclusionsMatch[1].split("\n")) {
      const trimmed = line.trim()
      if (trimmed.startsWith("- [")) conclusions.push(trimmed)
    }
  }

  // Parse Topic Index
  const topicMatch = content.match(
    /## Topic Index\s*\n([\s\S]*?)(?=\n---|\n## |$)/
  )
  const topicIndex: Record<string, string[]> = {}
  if (topicMatch) {
    for (const line of topicMatch[1].split("\n")) {
      const m = line.match(/^- (\S+):\s*(.+)/)
      if (m) {
        topicIndex[m[1]] = m[2].split(",").map((s) => s.trim())
      }
    }
  }

  return { conclusions, topicIndex }
}

// ---------------------------------------------------------------------------
// Phase index parsing
// ---------------------------------------------------------------------------

function getActivePhase(root: string): string | null {
  const phasePath = join(root, ".sybermem", "analysis", "phase-index.md")
  if (!existsSync(phasePath)) return null
  const content = readFileSync(phasePath, "utf-8")

  // Find the last confirmed phase block
  const phases = [...content.matchAll(/### Phase: (.+)/g)]
  if (phases.length === 0) return null
  return phases[phases.length - 1][1]
}

interface PhaseIndexInfo {
  exists: boolean
  status?: string
  confirmedCount?: number
  activePhase?: string | null
}

/**
 * Parse phase-index status + confirmed count, mirroring the Claude SessionStart
 * hook (session_start_context.py::parse_phase_index) so compaction context carries
 * the same phase signal Claude injects at startup.
 */
function parsePhaseIndex(root: string): PhaseIndexInfo {
  const phasePath = join(root, ".sybermem", "analysis", "phase-index.md")
  if (!existsSync(phasePath)) return { exists: false }
  const content = readFileSync(phasePath, "utf-8")
  const statusMatch = content.match(/^- status:\s*(.+)/m)
  const phases = [...content.matchAll(/### Phase: (.+)/g)]
  return {
    exists: true,
    status: statusMatch ? statusMatch[1].trim() : "unknown",
    confirmedCount: phases.length,
    activePhase: getActivePhase(root),
  }
}

interface ProjectIdentity {
  exists: boolean
  projectId?: string | null
  slug?: string | null
}

/**
 * Read .sybermem/project.yaml identity (slug, project_id) with the same simple
 * line-based parsing the Claude hook uses (session_start_context.py::parse_project_identity),
 * so injected memory context is attributable to a concrete project.
 */
function parseProjectIdentity(root: string): ProjectIdentity {
  const projPath = join(root, ".sybermem", "project.yaml")
  if (!existsSync(projPath)) return { exists: false }
  let projectId: string | null = null
  let slug: string | null = null
  for (const raw of readFileSync(projPath, "utf-8").split("\n")) {
    const line = raw.trim()
    if (line.startsWith("project_id:")) projectId = line.split(":").slice(1).join(":").trim()
    else if (line.startsWith("slug:")) slug = line.split(":").slice(1).join(":").trim()
  }
  return { exists: true, projectId, slug }
}

// ---------------------------------------------------------------------------
// Stale phase-index detection
// ---------------------------------------------------------------------------

interface StaleSignal {
  stale: boolean
  commitsAhead: number
  boundary?: string
  head?: string
}

async function detectStaleSignal(
  $: any,
  root: string
): Promise<StaleSignal> {
  const phasePath = join(root, ".sybermem", "analysis", "phase-index.md")
  if (!existsSync(phasePath)) return { stale: false, commitsAhead: 0 }
  const content = readFileSync(phasePath, "utf-8")
  const boundaryMatch = content.match(/^- last_git_boundary:\s*(\S+)/m)
  if (!boundaryMatch) return { stale: false, commitsAhead: 0 }
  const boundary = boundaryMatch[1]

  try {
    const head = (await $`git rev-parse HEAD`.cwd(root).text()).trim()
    if (head === boundary) return { stale: false, commitsAhead: 0 }
    const countStr = (
      await $`git rev-list --count ${boundary}..HEAD`.cwd(root).text()
    ).trim()
    const count = parseInt(countStr, 10) || 0
    return {
      stale: count >= 3,
      commitsAhead: count,
      boundary,
      head: head.substring(0, 7),
    }
  } catch {
    return { stale: false, commitsAhead: 0 }
  }
}

// ---------------------------------------------------------------------------
// Git change detection (lightweight, no Python dependency)
// ---------------------------------------------------------------------------

const SKIP_PREFIXES = [
  ".git/",
  ".sybermem/",
  "ADR/",
  ".claude/",
  ".opencode/",
  "node_modules/",
]
const SOFT_SKIP = new Set(["CLAUDE.md", "AGENTS.md"])

async function getChangedFiles(
  $: any,
  cwd: string
): Promise<string[]> {
  const files = new Set<string>()
  try {
    const diff = await $`git diff --name-only`.cwd(cwd).text()
    const cached = await $`git diff --cached --name-only`.cwd(cwd).text()
    const untracked =
      await $`git ls-files --others --exclude-standard`.cwd(cwd).text()
    for (const output of [diff, cached, untracked]) {
      for (const line of output.split("\n")) {
        const f = line.trim().replace(/\\/g, "/")
        if (!f) continue
        if (SKIP_PREFIXES.some((p) => f.startsWith(p))) continue
        files.add(f)
      }
    }
  } catch {
    // Not a git repo or git not available
  }
  return [...files]
}

function trailFiles(files: string[]): string[] {
  const nonSoft = files.filter((f) => !SOFT_SKIP.has(f))
  return nonSoft.length > 0 ? files : []
}

// ---------------------------------------------------------------------------
// Follow-up classification (parity with the Claude Stop hook
// record_change_on_stop.py::classify_followup). Mirrors the same thresholds and
// signal/area detection so the OpenCode idle nudge distinguishes record vs digest
// vs no-nudge with the same heuristics Claude uses at Stop.
// ---------------------------------------------------------------------------

const RECORD_FILE_THRESHOLD = 5
const COMMIT_GAP_THRESHOLD = 5
const THEME_WINDOW_SIZE = 10
const DIGEST_CLUSTER_THRESHOLD = 2
const DIGEST_SIGNAL_FILE_FLOOR = 3

const HIGH_SIGNAL_PATTERNS: RegExp[] = [
  /^README(?:\..+)?$/i,
  /^INSTALL(?:\..+)?$/i,
  /^CLAUDE\.md$/i,
  /^AGENTS\.md$/i,
  /^packages\/claude-skills\/.+\/SKILL\.md$/i,
  /^\.sybermem\/hooks\//i,
  /^scripts\/install/i,
  /^scripts\/update/i,
  /^docs\/superpowers\/specs\//i,
]
const HIGH_LEVEL_AREAS: [string, RegExp][] = [
  ["skills", /^packages\/claude-skills\//i],
  ["scripts", /^scripts\//i],
  ["docs", /^(docs\/|README|INSTALL)/i],
  ["instructions", /^(CLAUDE\.md|AGENTS\.md)$/i],
  ["sybermem", /^\.sybermem\//i],
]

function matchesHighSignal(file: string): boolean {
  return HIGH_SIGNAL_PATTERNS.some((p) => p.test(file))
}

function detectHighLevelAreas(files: string[]): Set<string> {
  const areas = new Set<string>()
  for (const file of files) {
    for (const [name, pattern] of HIGH_LEVEL_AREAS) {
      if (pattern.test(file)) areas.add(name)
    }
  }
  return areas
}

function slugifyAreas(areas: Set<string>): string {
  return [...areas].sort().join("-") || "misc"
}

interface FollowupResult {
  type: "record" | "digest" | "none"
  themeKey: string
  message: string | null
}

/**
 * Classify whether the current changed-file set warrants a record nudge, a digest
 * nudge, or nothing — mirroring classify_followup in the Claude Stop hook. The
 * digest branch requires a recent same-theme cluster (DIGEST_CLUSTER_THRESHOLD)
 * plus a qualifying current stop; the record branch fires on strong signal,
 * cross-area, large change, or commit gap, with a per-theme dedup guard.
 */
function classifyFollowup(
  files: string[],
  commitsSinceRecord: number,
  state: NudgeState
): FollowupResult {
  const highSignal = files.filter(matchesHighSignal)
  const areas = detectHighLevelAreas(files)
  const themeKey = slugifyAreas(areas)

  const recentStops = state.theme_recent_stops?.[themeKey] ?? []
  const recentOverlap = recentStops.length >= DIGEST_CLUSTER_THRESHOLD
  const presentQualifies =
    highSignal.length > 0 || areas.size >= 2 || files.length >= DIGEST_SIGNAL_FILE_FLOOR
  const nudgedAt = state.digest_nudged_at_window_len?.[themeKey]
  const alreadyDigested = nudgedAt !== undefined && recentStops.length <= nudgedAt

  if (recentOverlap && presentQualifies && !alreadyDigested) {
    return {
      type: "digest",
      themeKey,
      message:
        "SyberMem: recent records around this area may now be enough for a /sybermem-digest if this phase has reached a stable stopping point.",
    }
  }

  const crossArea = areas.size >= 2
  const strongSignal = highSignal.length > 0
  const largeChange = files.length >= RECORD_FILE_THRESHOLD
  const commitGap = commitsSinceRecord >= COMMIT_GAP_THRESHOLD
  const lastType = state.last_nudge_type
  const lastTheme = state.last_theme
  if (
    (strongSignal || crossArea || largeChange || commitGap) &&
    !(lastType === "record" && lastTheme === themeKey)
  ) {
    const gapNote = commitGap ? ` (${commitsSinceRecord} commits since last record)` : ""
    return {
      type: "record",
      themeKey,
      message: `SyberMem: this change looks important enough for a manual /sybermem-record so the reason and impact are preserved.${gapNote}`,
    }
  }

  return { type: "none", themeKey, message: null }
}

// ---------------------------------------------------------------------------
// Auto-trail journal (parity with record_change_on_stop.py auto-trail): a bounded
// rolling .sybermem/.auto-trail.jsonl of low-signal change trails, with >80%
// overlap dedup against the last few entries so repeated idle stops on the same
// file set do not re-nudge or bloat the journal.
// ---------------------------------------------------------------------------

const AUTO_TRAIL_JOURNAL_FILE = ".auto-trail.jsonl"
const AUTO_TRAIL_JOURNAL_MAX = 200
const AUTO_TRAIL_DEDUP_WINDOW = 3
const AUTO_TRAIL_OVERLAP_THRESHOLD = 0.8

interface AutoTrailEntry {
  date: string
  files: string[]
  areas: string[]
  followup_hint: string
}

function readRecentAutoTrail(root: string, limit: number): AutoTrailEntry[] {
  const p = join(root, ".sybermem", AUTO_TRAIL_JOURNAL_FILE)
  if (!existsSync(p)) return []
  try {
    const lines = readFileSync(p, "utf-8").split("\n")
    const entries: AutoTrailEntry[] = []
    for (const line of lines.slice(-limit)) {
      const t = line.trim()
      if (!t) continue
      try {
        const parsed = JSON.parse(t)
        if (parsed && typeof parsed === "object") entries.push(parsed)
      } catch {
        // skip malformed line
      }
    }
    return entries
  } catch {
    return []
  }
}

function overlapsRecentAutoTrails(root: string, files: string[]): boolean {
  const current = new Set(files)
  if (current.size === 0) return false
  for (const entry of readRecentAutoTrail(root, AUTO_TRAIL_DEDUP_WINDOW)) {
    const trail = new Set((entry.files ?? []).map((f) => String(f).trim()).filter(Boolean))
    if (trail.size === 0) continue
    let shared = 0
    for (const f of current) if (trail.has(f)) shared++
    const overlap = shared / Math.max(current.size, trail.size)
    if (overlap >= AUTO_TRAIL_OVERLAP_THRESHOLD) return true
  }
  return false
}

function appendAutoTrailJournal(
  root: string,
  date: string,
  files: string[],
  areas: Set<string>,
  followupHint: string
): void {
  const p = join(root, ".sybermem", AUTO_TRAIL_JOURNAL_FILE)
  try {
    const entry: AutoTrailEntry = {
      date,
      files: [...files],
      areas: [...areas].sort(),
      followup_hint: followupHint,
    }
    let existing: string[] = []
    if (existsSync(p)) existing = readFileSync(p, "utf-8").split("\n")
    existing = existing.filter((l) => l.trim())
    existing.push(JSON.stringify(entry))
    const bounded = existing.slice(-AUTO_TRAIL_JOURNAL_MAX)
    writeFileSync(p, bounded.join("\n") + "\n", "utf-8")
  } catch {
    // never raise out of the hook
  }
}

// ---------------------------------------------------------------------------
// Nudge state (persisted in .sybermem/.nudge-state.json)
// ---------------------------------------------------------------------------

interface NudgeState {
  lastFingerprint?: string
  lastNudgeCommitCount?: number
  last_nudge?: {
    platform: string
    type: string
    theme: string
    date: string
  }
  // Cross-platform fields (shared with Python Stop hook)
  theme_recent_stops?: Record<string, string[]>
  digest_nudged_at_window_len?: Record<string, number>
  last_theme?: string
  last_nudge_type?: string
}

const NUDGE_STATE_FILE = ".nudge-state.json"
const LEGACY_NUDGE_STATE_FILE = ".opencode-nudge-state.json"

function loadNudgeState(root: string): NudgeState {
  const p = join(root, ".sybermem", NUDGE_STATE_FILE)
  if (existsSync(p)) {
    try {
      return JSON.parse(readFileSync(p, "utf-8"))
    } catch {
      // fall through to legacy
    }
  }
  // Migrate from legacy file if it exists
  const legacy = join(root, ".sybermem", LEGACY_NUDGE_STATE_FILE)
  if (existsSync(legacy)) {
    try {
      const data = JSON.parse(readFileSync(legacy, "utf-8"))
      saveNudgeState(root, data)
      return data
    } catch {
      // fall through
    }
  }
  return {}
}

function saveNudgeState(root: string, state: NudgeState) {
  const p = join(root, ".sybermem", NUDGE_STATE_FILE)
  writeFileSync(p, JSON.stringify(state, null, 2) + "\n", "utf-8")
}

// ---------------------------------------------------------------------------
// Record gap detection
// ---------------------------------------------------------------------------

async function countCommitsSinceLastRecord(
  $: any,
  root: string
): Promise<number> {
  const recordDirs = ["changes", "decisions", "requirements", "bugs"]
  try {
    const { readdirSync } = await import("fs")
    let latestDate = ""
    for (const subdir of recordDirs) {
      const dir = join(root, ".sybermem", subdir)
      if (!existsSync(dir)) continue
      const files = readdirSync(dir)
        .filter((f: string) => f.endsWith(".md"))
        .sort()
      if (files.length === 0) continue
      const lastFile = files[files.length - 1]
      const dateMatch = lastFile.match(/^(\d{4}-\d{2}-\d{2})/)
      if (dateMatch && dateMatch[1] > latestDate) {
        latestDate = dateMatch[1]
      }
    }
    if (!latestDate) return 0

    const log = await $`git log --oneline --since=${latestDate}`.cwd(root).text()
    return log.split("\n").filter((l: string) => l.trim()).length
  } catch {
    return 0
  }
}

// ---------------------------------------------------------------------------
// Plugin export
// ---------------------------------------------------------------------------

export const SyberMemPlugin: Plugin = async ({ $, directory }) => {
  const root = resolveRoot(directory)

  return {
    // --- Session start: load Key Conclusions ---
    event: async ({ event }) => {
      if (event.type === "session.created" && root) {
        const parsed = parseIndex(root)
        if (parsed && parsed.conclusions.length > 0) {
          const stale = await detectStaleSignal($, root)
          const staleNote = stale.stale
            ? ` (phase-index ${stale.commitsAhead} commits behind)`
            : ""
          // Commit-gap record reminder, mirroring the Claude SessionStart hook
          // (session_start_context.py::detect_record_gap, threshold >= 3): surface a
          // proactive nudge when unrecorded commits have accrued since the last record.
          const commitsSinceRecord = await countCommitsSinceLastRecord($, root)
          const recordNote =
            commitsSinceRecord >= 3
              ? `. ${commitsSinceRecord} commits since last record — consider /sybermem-record`
              : ""
          // Prefix a scarce ⭐ only when a real signal fired (stale index or record
          // gap) so the marker flags an aha moment worth attention, not every load.
          const ahaMarker = stale.stale || commitsSinceRecord >= 3 ? "⭐ " : ""
          return {
            "tui.toast.show": {
              message: `${ahaMarker}SyberMem: loaded ${parsed.conclusions.length} key conclusions${staleNote}${recordNote}`,
              level: "info",
            },
          }
        }
      }

      // --- Session idle: detect changes and nudge (parity with Claude Stop hook) ---
      if (event.type === "session.idle" && root) {
        const files = await getChangedFiles($, root)
        const trail = trailFiles(files)

        if (trail.length === 0) return

        const fingerprint = JSON.stringify(trail)
        const state = loadNudgeState(root)
        if (state.lastFingerprint === fingerprint) return

        // Dedup: skip nudging when this file set already overlaps >80% with a recent
        // auto-trail entry, matching the Claude Stop hook's dedup guard.
        if (overlapsRecentAutoTrails(root, trail)) {
          saveNudgeState(root, { ...state, lastFingerprint: fingerprint })
          return
        }

        const commitsSince = await countCommitsSinceLastRecord($, root)
        const followup = classifyFollowup(trail, commitsSince, state)
        const today = new Date().toISOString().split("T")[0]

        // Persist a bounded auto-trail entry regardless of nudge decision, so dedup
        // and digest-cluster detection have durable history across idle stops.
        appendAutoTrailJournal(root, today, trail, detectHighLevelAreas(trail), followup.type)

        if (followup.type === "none") {
          // Track same-theme activity so a future qualifying stop can cross the
          // digest cluster threshold, then persist the fingerprint.
          const windows = { ...(state.theme_recent_stops ?? {}) }
          const current = [...(windows[followup.themeKey] ?? []), today]
          windows[followup.themeKey] = current.slice(-THEME_WINDOW_SIZE)
          saveNudgeState(root, {
            ...state,
            lastFingerprint: fingerprint,
            theme_recent_stops: windows,
          })
          return
        }

        // A record/digest nudge fires: update theme window + per-theme dedup guards.
        const windows = { ...(state.theme_recent_stops ?? {}) }
        const current = [...(windows[followup.themeKey] ?? []), today]
        windows[followup.themeKey] = current.slice(-THEME_WINDOW_SIZE)
        const digestGuard = { ...(state.digest_nudged_at_window_len ?? {}) }
        if (followup.type === "digest") {
          digestGuard[followup.themeKey] = windows[followup.themeKey].length
        }

        saveNudgeState(root, {
          ...state,
          lastFingerprint: fingerprint,
          lastNudgeCommitCount: commitsSince,
          theme_recent_stops: windows,
          digest_nudged_at_window_len: digestGuard,
          last_theme: followup.themeKey,
          last_nudge_type: followup.type,
          last_nudge: {
            platform: "opencode",
            type: followup.type,
            theme: followup.themeKey,
            date: today,
          },
        })
        return {
          "tui.toast.show": {
            message: followup.message ?? "SyberMem: consider recording this work.",
            level: "info",
          },
        }
      }
    },

    // --- Compaction: inject Key Conclusions + active phase ---
    "experimental.session.compacting": async (_input, output) => {
      if (!root) return

      const parsed = parseIndex(root)
      if (!parsed || parsed.conclusions.length === 0) return

      const phaseInfo = parsePhaseIndex(root)
      const identity = parseProjectIdentity(root)
      const stale = await detectStaleSignal($, root)

      let context = ""

      try {
        const manualContext = (
          await sybermemText($, root, ["context", "session", "--format", "markdown"])
        ).trim()
        if (manualContext.startsWith("## SyberMem Manual Session Context")) {
          context += `${manualContext}\n\n`
        }
      } catch {
        // Old CLI or unavailable launcher — fall back to the inline compaction context below.
      }

      if (!context) {
        context = "## SyberMem Project Memory\n\n"
      }

      if (identity.exists && identity.slug) {
        context += `Project: ${identity.slug} (${identity.projectId ?? "no id"}).\n\n`
      }

      context += "### Key Conclusions\n"
      for (const c of parsed.conclusions) {
        context += c + "\n"
      }

      // Aha expressiveness (parity with the Claude recall packet): a scarce ⭐ heads-up
      // is added ONLY when a genuinely load-bearing, already-computed signal exists —
      // here, a stale phase index. This mirrors the "symbol scarcity = value" rule so
      // the marker means something instead of decorating every compaction.
      if (stale.stale) {
        context += `\n⭐ Heads-up: phase index trails HEAD by ${stale.commitsAhead} commits — the conclusions above may lag your latest work. Consider /sybermem-phase-analyze before relying on phase context.\n`
      }

      // Digest governance heads-up (G5): shell to the single-source-of-truth
      // `sybermem digest status` and flag mechanically-stale digests so drifted phase
      // summaries stop reading as authoritative during compaction. Read-only — it points
      // to /sybermem-digest, never regenerates. Fails open when the CLI is unavailable.
      try {
        const raw = await digestStatusText($, root)
        const report = JSON.parse(raw)
        const staleDigests = typeof report?.stale === "number" ? report.stale : 0
        if (staleDigests > 0) {
          context += `\n⭐ Digest heads-up: ${staleDigests} digest(s) are stale — their source records changed. Run /sybermem-digest to regenerate, or \`sybermem digest status\` to see which sources drifted.\n`
        }
      } catch {
        // CLI missing or errored — skip the digest governance line.
      }

      if (phaseInfo.exists) {
        context += `\n### Phase Index\nStatus: ${phaseInfo.status}. ${phaseInfo.confirmedCount} confirmed phases.\n`
        if (phaseInfo.activePhase) {
          context += `Active phase: ${phaseInfo.activePhase}.\n`
        }
      }

      if (stale.stale) {
        context += `\n### Stale Signal\nPhase-index last git boundary: ${stale.boundary}, current HEAD: ${stale.head} (${stale.commitsAhead} commits ahead).\n`
      }

      if (Object.keys(parsed.topicIndex).length > 0) {
        context += "\n### Topic Index\n"
        for (const [topic, records] of Object.entries(parsed.topicIndex)) {
          context += `- ${topic}: ${records.join(", ")}\n`
        }
      }

      // Next-step router fallback, mirroring the Claude Stop hook's use of the
      // deterministic next-step router. Shells to the installed `sybermem next-step`
      // CLI so the recommendation matches resume/using-sybermem; fails open when the
      // CLI is unavailable so compaction never breaks.
      try {
        const raw = await sybermemText($, root, ["next-step", "--format", "json"])
        const rec = JSON.parse(raw)
        const action = typeof rec?.action === "string" ? rec.action.trim() : ""
        const reason = typeof rec?.reason === "string" ? rec.reason.trim() : ""
        if (action) {
          context += `\n### Recommended Next Step\n${action}${reason ? ` — ${reason}` : ""}\n`
        }
      } catch {
        // CLI missing or errored — skip the recommendation line.
      }

      // User Habit Memory is user-owned and injected only at supported compaction
      // time. This deliberately avoids claiming an undocumented per-prompt hook.
      try {
        const habitContext = "compaction planning review implementation coding documentation"
        const habitMarkdown = (
          await sybermemText($, root, ["habit", "inject", "--context", habitContext, "--format", "markdown"])
        ).trim()
        if (habitMarkdown) {
          context += `\n${habitMarkdown}\n`
        }
      } catch {
        // CLI missing, old install, or no habit support — compaction stays fail-open.
      }

      context += "\n### SyberMem Commands\n"
      context +=
        "- /sybermem-record — create a record after meaningful work\n"
      context +=
        "- /sybermem-summary — view current phase status\n"
      context +=
        "- /sybermem-digest — create durable phase digest\n"

      // Enforce 3000-char limit to avoid compaction noise
      if (context.length > 3000) {
        context = context.substring(0, 2997) + "..."
      }

      output.context.push(context)
    },
  }
}
