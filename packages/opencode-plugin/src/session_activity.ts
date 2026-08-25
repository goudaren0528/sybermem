// Per-session, in-memory accumulation of edit/activity signals. Events only
// mutate this map; the real computation and disk write happen at session.idle,
// so there is no hidden background worker (OpenCode plugin lifecycle scope only).
import type { MemoryUsageEntry } from "./memory_usage"

const RECORD_ID_RE = /\b(?:change|decision|requirement|bug|digest)-[a-z0-9-]+\b/gi
const SKIP_PREFIXES = [".git/", ".sybermem/", "ADR/", ".claude/", ".opencode/", "node_modules/"]

export type ToolSignal = "tests_passed" | "build_ok" | null

export interface SessionActivity {
  editedFiles: Map<string, number>
  todoCompletedBatches: number
  lastToolSignal: ToolSignal
  injectedRecords: Set<string>
  memoryTurns: number
  memoryItems: number
  memoryChars: number
  recallItems: number
  recallChars: number
  habitItems: number
  habitChars: number
  normItems: number
  normChars: number
  startupItems: number
  startupChars: number
}

const SESSIONS = new Map<string, SessionActivity>()

function freshActivity(): SessionActivity {
  return {
    editedFiles: new Map(),
    todoCompletedBatches: 0,
    lastToolSignal: null,
    injectedRecords: new Set(),
    memoryTurns: 0,
    memoryItems: 0,
    memoryChars: 0,
    recallItems: 0,
    recallChars: 0,
    habitItems: 0,
    habitChars: 0,
    normItems: 0,
    normChars: 0,
    startupItems: 0,
    startupChars: 0,
  }
}

export function getSessionActivity(sessionID: string): SessionActivity {
  let activity = SESSIONS.get(sessionID)
  if (!activity) {
    activity = freshActivity()
    SESSIONS.set(sessionID, activity)
  }
  return activity
}

export function resetSessionActivity(sessionID: string): void {
  SESSIONS.delete(sessionID)
}

function normalizePath(raw: string): string {
  return raw.trim().replace(/\\/g, "/")
}

function isTracked(file: string): boolean {
  return file.length > 0 && !SKIP_PREFIXES.some((p) => file.startsWith(p))
}

// Defensive: OpenCode's per-event payload shapes are not fully documented, so we
// probe several plausible field names via Reflect.get and treat anything we
// cannot read as "no signal" rather than throwing.
function readString(source: unknown, keys: readonly string[]): string {
  if (typeof source !== "object" || source === null) return ""
  for (const key of keys) {
    const value = Reflect.get(source, key)
    if (typeof value === "string" && value) return value
  }
  return ""
}

export function extractEditedFile(properties: unknown): string {
  const raw = readString(properties, ["file", "path", "filePath", "filename"])
  return raw ? normalizePath(raw) : ""
}

export function recordEditedFile(sessionID: string, file: string): void {
  const normalized = normalizePath(file)
  if (!isTracked(normalized)) return
  const activity = getSessionActivity(sessionID)
  activity.editedFiles.set(normalized, (activity.editedFiles.get(normalized) ?? 0) + 1)
}

// A "completed batch" is any todo update where every item is done. OpenCode's
// todo payload is a list of items with a status field; be liberal about the
// exact shape and fail closed (no signal) when we cannot read it.
export function isTodoBatchComplete(properties: unknown): boolean {
  if (typeof properties !== "object" || properties === null) return false
  const todos = Reflect.get(properties, "todos") ?? Reflect.get(properties, "items")
  if (!Array.isArray(todos) || todos.length === 0) return false
  return todos.every((item) => {
    const status = readString(item, ["status", "state"]).toLowerCase()
    return status === "completed" || status === "done"
  })
}

export function recordTodoUpdate(sessionID: string, properties: unknown): void {
  if (isTodoBatchComplete(properties)) getSessionActivity(sessionID).todoCompletedBatches += 1
}

// Only a passing test or a clean build after a real edit is a useful "one round
// of work finished" signal. Match conservatively on the bash command text and
// require a zero exit code; anything else leaves the signal untouched.
export function classifyToolSignal(input: unknown, output: unknown): ToolSignal {
  const tool = readString(input, ["tool"])
  if (tool !== "bash") return null
  const args = Reflect.get(input as object, "args")
  const command = readString(args, ["command"]).toLowerCase()
  if (!command) return null
  const exit = Reflect.get(output as object, "exit") ?? Reflect.get(output as object, "exitCode") ?? Reflect.get(output as object, "code")
  if (typeof exit === "number" && exit !== 0) return null
  if (/\b(pytest|vitest|jest|bun test|go test|cargo test|npm test|yarn test|pnpm test)\b/.test(command)) return "tests_passed"
  if (/\b(build|tsc|cargo build|go build|make)\b/.test(command)) return "build_ok"
  return null
}

export function recordToolExecution(sessionID: string, input: unknown, output: unknown): void {
  const signal = classifyToolSignal(input, output)
  if (signal) getSessionActivity(sessionID).lastToolSignal = signal
}

// The injected record IDs come from the recall packet the plugin already builds;
// this mirrors recall_debug's extraction so both stay consistent.
export function recordInjectedRecords(sessionID: string, packets: readonly string[]): void {
  const recallPacket = packets.find((packet) => packet.trim().startsWith("## SyberMem Recall Hints"))
  if (!recallPacket) return
  const activity = getSessionActivity(sessionID)
  for (const match of recallPacket.matchAll(RECORD_ID_RE)) activity.injectedRecords.add(match[0].toLowerCase())
}

export function recordMemoryUsage(sessionID: string, entry: MemoryUsageEntry): void {
  if (entry.total_items === 0) return
  const activity = getSessionActivity(sessionID)
  activity.memoryTurns += 1
  activity.memoryItems += entry.total_items
  activity.memoryChars += entry.total_chars
  activity.recallItems += entry.recall_items
  activity.recallChars += entry.recall_chars
  activity.habitItems += entry.habit_items
  activity.habitChars += entry.habit_chars
  activity.normItems += entry.norm_items
  activity.normChars += entry.norm_chars
  activity.startupItems += entry.startup_items
  activity.startupChars += entry.startup_chars
}
