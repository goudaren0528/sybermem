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
          return {
            "tui.toast.show": {
              message: `SyberMem: loaded ${parsed.conclusions.length} key conclusions${staleNote}`,
              level: "info",
            },
          }
        }
      }

      // --- Session idle: detect changes and nudge ---
      if (event.type === "session.idle" && root) {
        const files = await getChangedFiles($, root)
        const trail = trailFiles(files)

        if (trail.length === 0) return

        const fingerprint = JSON.stringify(trail)
        const state = loadNudgeState(root)
        if (state.lastFingerprint === fingerprint) return

        // Check record gap
        const commitsSince = await countCommitsSinceLastRecord($, root)
        const shouldNudge = trail.length >= 5 || commitsSince >= 10

        if (shouldNudge) {
          saveNudgeState(root, {
            ...state,
            lastFingerprint: fingerprint,
            lastNudgeCommitCount: commitsSince,
            last_nudge: {
              platform: "opencode",
              type: "record",
              theme: "idle-detect",
              date: new Date().toISOString().split("T")[0],
            },
          })
          return {
            "tui.toast.show": {
              message: `SyberMem: ${trail.length} files changed${commitsSince >= 10 ? `, ${commitsSince} commits since last record` : ""}. Consider /sybermem-record`,
              level: "info",
            },
          }
        }

        saveNudgeState(root, { ...state, lastFingerprint: fingerprint })
      }
    },

    // --- Compaction: inject Key Conclusions + active phase ---
    "experimental.session.compacting": async (_input, output) => {
      if (!root) return

      const parsed = parseIndex(root)
      if (!parsed || parsed.conclusions.length === 0) return

      const activePhase = getActivePhase(root)
      const stale = await detectStaleSignal($, root)

      let context = "## SyberMem Project Memory\n\n"
      context += "### Key Conclusions\n"
      for (const c of parsed.conclusions) {
        context += c + "\n"
      }

      if (activePhase) {
        context += `\n### Active Phase: ${activePhase}\n`
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
