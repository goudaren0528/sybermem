import { existsSync, readdirSync, readFileSync, writeFileSync } from "fs"
import { join } from "path"
import type { Shell } from "./runtime"
import type { NudgeState } from "./state"

const SKIP_PREFIXES = [".git/", ".sybermem/", "ADR/", ".claude/", ".opencode/", "node_modules/"]
const SOFT_SKIP = new Set(["CLAUDE.md", "AGENTS.md"])
const HIGH_SIGNAL_PATTERNS: readonly RegExp[] = [/^README(?:\..+)?$/i, /^INSTALL(?:\..+)?$/i, /^CLAUDE\.md$/i, /^AGENTS\.md$/i, /^packages\/claude-skills\/.+\/SKILL\.md$/i, /^\.sybermem\/hooks\//i, /^scripts\/install/i, /^scripts\/update/i, /^docs\/superpowers\/specs\//i]
const HIGH_LEVEL_AREAS: readonly (readonly [string, RegExp])[] = [["skills", /^packages\/claude-skills\//i], ["scripts", /^scripts\//i], ["docs", /^(docs\/|README|INSTALL)/i], ["instructions", /^(CLAUDE\.md|AGENTS\.md)$/i], ["sybermem", /^\.sybermem\//i]]
const RECORD_FILE_THRESHOLD = 5
const COMMIT_GAP_THRESHOLD = 5
export const THEME_WINDOW_SIZE = 10
const DIGEST_CLUSTER_THRESHOLD = 2
const DIGEST_SIGNAL_FILE_FLOOR = 3

export interface FollowupResult { readonly type: "record" | "digest" | "none"; readonly themeKey: string; readonly message: string | null }

export async function getChangedFiles($: Shell, cwd: string): Promise<string[]> {
  const files = new Set<string>()
  try {
    for (const output of [await $`git diff --name-only`.cwd(cwd).text(), await $`git diff --cached --name-only`.cwd(cwd).text(), await $`git ls-files --others --exclude-standard`.cwd(cwd).text()]) {
      for (const line of output.split("\n")) {
        const f = line.trim().replace(/\\/g, "/")
        if (f && !SKIP_PREFIXES.some((p) => f.startsWith(p))) files.add(f)
      }
    }
  } catch {
    // Not a git repo or git not available.
  }
  return [...files]
}

export function trailFiles(files: readonly string[]): string[] {
  return files.filter((f) => !SOFT_SKIP.has(f)).length > 0 ? [...files] : []
}

function matchesHighSignal(file: string): boolean {
  return HIGH_SIGNAL_PATTERNS.some((p) => p.test(file))
}

export function detectHighLevelAreas(files: readonly string[]): Set<string> {
  const areas = new Set<string>()
  for (const file of files) for (const [name, pattern] of HIGH_LEVEL_AREAS) if (pattern.test(file)) areas.add(name)
  return areas
}

function slugifyAreas(areas: Set<string>): string {
  return [...areas].sort().join("-") || "misc"
}

export function classifyFollowup(files: readonly string[], commitsSinceRecord: number, state: NudgeState): FollowupResult {
  const highSignal = files.filter(matchesHighSignal)
  const areas = detectHighLevelAreas(files)
  const themeKey = slugifyAreas(areas)
  const recentStops = state.theme_recent_stops?.[themeKey] ?? []
  const presentQualifies = highSignal.length > 0 || areas.size >= 2 || files.length >= DIGEST_SIGNAL_FILE_FLOOR
  const nudgedAt = state.digest_nudged_at_window_len?.[themeKey]
  if (recentStops.length >= DIGEST_CLUSTER_THRESHOLD && presentQualifies && !(nudgedAt !== undefined && recentStops.length <= nudgedAt)) {
    return { type: "digest", themeKey, message: "SyberMem: recent records around this area may now be enough for a /sybermem-digest if this phase has reached a stable stopping point." }
  }
  const shouldRecord = highSignal.length > 0 || areas.size >= 2 || files.length >= RECORD_FILE_THRESHOLD || commitsSinceRecord >= COMMIT_GAP_THRESHOLD
  if (shouldRecord && !(state.last_nudge_type === "record" && state.last_theme === themeKey)) {
    const gapNote = commitsSinceRecord >= COMMIT_GAP_THRESHOLD ? ` (${commitsSinceRecord} commits since last record)` : ""
    return { type: "record", themeKey, message: `SyberMem: this change looks important enough for a manual /sybermem-record so the reason and impact are preserved.${gapNote}` }
  }
  return { type: "none", themeKey, message: null }
}

export async function countCommitsSinceLastRecord($: Shell, root: string): Promise<number> {
  try {
    let latestDate = ""
    for (const subdir of ["changes", "decisions", "requirements", "bugs"]) {
      const dir = join(root, ".sybermem", subdir)
      if (!existsSync(dir)) continue
      const lastFile = readdirSync(dir).filter((f) => f.endsWith(".md")).sort().at(-1)
      const dateMatch = lastFile?.match(/^(\d{4}-\d{2}-\d{2})/)
      if (dateMatch && dateMatch[1] > latestDate) latestDate = dateMatch[1]
    }
    if (!latestDate) return 0
    return (await $`git log --oneline --since=${latestDate}`.cwd(root).text()).split("\n").filter((l) => l.trim()).length
  } catch {
    return 0
  }
}

interface AutoTrailEntry { readonly files?: readonly string[] }

function parseAutoTrailEntry(raw: string): AutoTrailEntry | null {
  const parsed: unknown = JSON.parse(raw)
  if (typeof parsed !== "object" || parsed === null) return null
  const files = Reflect.get(parsed, "files")
  return Array.isArray(files) ? { files: files.map(String) } : {}
}

export function overlapsRecentAutoTrails(root: string, files: readonly string[]): boolean {
  const current = new Set(files)
  if (current.size === 0) return false
  const p = join(root, ".sybermem", ".auto-trail.jsonl")
  const lines = existsSync(p) ? readFileSync(p, "utf-8").split("\n").filter((line) => line.trim()).slice(-3) : []
  for (const line of lines) {
    try {
      const entry = parseAutoTrailEntry(line)
      if (!entry) continue
      const trail = new Set((entry.files ?? []).map((f) => String(f).trim()).filter(Boolean))
      let shared = 0
      for (const f of current) if (trail.has(f)) shared++
      if (trail.size > 0 && shared / Math.max(current.size, trail.size) >= 0.8) return true
    } catch {
      // Malformed auto-trail lines are ignored; idle nudges must remain fail-open.
    }
  }
  return false
}

export function appendAutoTrailJournal(root: string, date: string, files: readonly string[], areas: Set<string>, followupHint: string): void {
  const p = join(root, ".sybermem", ".auto-trail.jsonl")
  try {
    const existing = existsSync(p) ? readFileSync(p, "utf-8").split("\n").filter((l) => l.trim()) : []
    existing.push(JSON.stringify({ date, files: [...files], areas: [...areas].sort(), followup_hint: followupHint }))
    writeFileSync(p, existing.slice(-200).join("\n") + "\n", "utf-8")
  } catch {
    // Auto-trail journaling is advisory and must not block OpenCode idle handling.
  }
}
