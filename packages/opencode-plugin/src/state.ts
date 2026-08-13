import { existsSync, readFileSync, statSync, writeFileSync } from "fs"
import { join } from "path"

export interface NudgeState {
  readonly lastFingerprint?: string
  readonly lastNudgeCommitCount?: number
  readonly last_nudge?: { readonly platform: string; readonly type: string; readonly theme: string; readonly date: string }
  readonly theme_recent_stops?: Readonly<Record<string, readonly string[]>>
  readonly digest_nudged_at_window_len?: Readonly<Record<string, number>>
  readonly last_theme?: string
  readonly last_nudge_type?: string
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function parseNudgeState(raw: string): NudgeState {
  const parsed: unknown = JSON.parse(raw)
  if (!isObject(parsed)) return {}
  const lastNudge = isObject(parsed.last_nudge) ? parsed.last_nudge : null
  const state: NudgeState = {}
  if (typeof parsed.lastFingerprint === "string") state.lastFingerprint = parsed.lastFingerprint
  if (typeof parsed.lastNudgeCommitCount === "number") state.lastNudgeCommitCount = parsed.lastNudgeCommitCount
  if (lastNudge && typeof lastNudge.platform === "string" && typeof lastNudge.type === "string" && typeof lastNudge.theme === "string" && typeof lastNudge.date === "string") state.last_nudge = { platform: lastNudge.platform, type: lastNudge.type, theme: lastNudge.theme, date: lastNudge.date }
  if (isObject(parsed.theme_recent_stops)) state.theme_recent_stops = parseStringArrayMap(parsed.theme_recent_stops)
  if (isObject(parsed.digest_nudged_at_window_len)) state.digest_nudged_at_window_len = parseNumberMap(parsed.digest_nudged_at_window_len)
  if (typeof parsed.last_theme === "string") state.last_theme = parsed.last_theme
  if (typeof parsed.last_nudge_type === "string") state.last_nudge_type = parsed.last_nudge_type
  return state
}

function parseStringArrayMap(raw: Record<string, unknown>): Readonly<Record<string, readonly string[]>> {
  const parsed: Record<string, string[]> = {}
  for (const [key, value] of Object.entries(raw)) if (Array.isArray(value)) parsed[key] = value.filter((item) => typeof item === "string")
  return parsed
}

function parseNumberMap(raw: Record<string, unknown>): Readonly<Record<string, number>> {
  const parsed: Record<string, number> = {}
  for (const [key, value] of Object.entries(raw)) if (typeof value === "number") parsed[key] = value
  return parsed
}

const NUDGE_STATE_FILE = ".nudge-state.json"
const LEGACY_NUDGE_STATE_FILE = ".opencode-nudge-state.json"
const MAX_EXISTING_JSONL_BYTES = 1_000_000

export function loadNudgeState(root: string): NudgeState {
  const p = join(root, ".sybermem", NUDGE_STATE_FILE)
  if (existsSync(p)) {
    try {
      return parseNudgeState(readFileSync(p, "utf-8"))
    } catch {
      // fall through to legacy
    }
  }
  const legacy = join(root, ".sybermem", LEGACY_NUDGE_STATE_FILE)
  if (existsSync(legacy)) {
    try {
      const data = parseNudgeState(readFileSync(legacy, "utf-8"))
      saveNudgeState(root, data)
      return data
    } catch {
      // fall through
    }
  }
  return {}
}

export function saveNudgeState(root: string, state: NudgeState): void {
  writeFileSync(join(root, ".sybermem", NUDGE_STATE_FILE), JSON.stringify(state, null, 2) + "\n", "utf-8")
}

export function boundedJsonlAppend(root: string, fileName: string, entry: object, limit: number): void {
  const p = join(root, ".sybermem", fileName)
  try {
    const existing = existsSync(p) && statSync(p).size <= MAX_EXISTING_JSONL_BYTES ? readFileSync(p, "utf-8").split("\n").filter((line) => line.trim()) : []
    existing.push(JSON.stringify(entry))
    writeFileSync(p, existing.slice(-limit).join("\n") + "\n", "utf-8")
  } catch {
    // fail open
  }
}
