import { boundedJsonlAppend } from "./state"
import { classifyPackets } from "./prompt_context"

export interface MemoryUsageEntry {
  readonly schema_version: 1
  readonly timestamp: string
  readonly host: "opencode"
  readonly session_id: string
  readonly total_items: number
  readonly total_chars: number
  readonly digest_items: number
  readonly recall_items: number
  readonly recall_chars: number
  readonly habit_items: number
  readonly habit_chars: number
  readonly norm_items: number
  readonly norm_chars: number
  readonly startup_items: number
  readonly startup_chars: number
  readonly injected_ids: readonly string[]
  readonly startup_present: boolean
}

export interface MemoryUsageInput {
  readonly sessionID: string
  readonly packets: readonly string[]
  readonly startup: string
}

export interface MemoryUsageOptions {
  readonly timestamp?: string
}

const RECORD_ID_RE = /\b(?:change|decision|requirement|bug|digest|habit|norm)-[a-z0-9-]+\b/gi
const STRUCTURED_ID_RE = /^\s*-\s*\[([^\]]{1,120})\]/
const MAX_PACKET_SCAN_CHARS = 8_000
const MAX_TOTAL_SCAN_CHARS = 24_000
const MAX_SESSION_ID_CHARS = 80
const MAX_INJECTED_IDS = 40

function boundText(value: string, maxChars: number): string {
  return value.length > maxChars ? value.slice(0, maxChars) : value
}

function structuredIds(text: string): readonly string[] {
  const ids: string[] = []
  for (const line of boundText(text, MAX_PACKET_SCAN_CHARS).split("\n")) {
    const id = line.match(STRUCTURED_ID_RE)?.[1]?.match(RECORD_ID_RE)?.[0]
    if (id) ids.push(id.toLowerCase())
  }
  return ids
}

function uniqueStructuredIds(packets: readonly string[], startup: string): readonly string[] {
  const ids = new Set<string>()
  let scanned = 0
  for (const text of [...packets, startup]) {
    if (scanned >= MAX_TOTAL_SCAN_CHARS || ids.size >= MAX_INJECTED_IDS) break
    const remaining = MAX_TOTAL_SCAN_CHARS - scanned
    const bounded = boundText(text, Math.min(MAX_PACKET_SCAN_CHARS, remaining))
    scanned += bounded.length
    for (const id of structuredIds(bounded)) {
      ids.add(id)
      if (ids.size >= MAX_INJECTED_IDS) break
    }
  }
  return [...ids]
}

function packetChars(packets: readonly string[], heading: string): number {
  return packets.find((packet) => packet.trim().startsWith(heading))?.length ?? 0
}

function startupItemCount(startup: string): number {
  if (!startup) return 0
  const bullets = startup.split("\n").filter((line) => /^-\s/.test(line.trim())).length
  return bullets > 0 ? bullets : 1
}

export function buildMemoryUsageEntry(input: MemoryUsageInput, options: MemoryUsageOptions = {}): MemoryUsageEntry {
  const summary = classifyPackets(input.packets)
  const startup = input.startup.trim()
  const startupItems = startupItemCount(startup)
  const recallChars = packetChars(input.packets, "## SyberMem Recall Hints")
  const habitChars = packetChars(input.packets, "## User Habit Reminder")
  const normChars = packetChars(input.packets, "## Relevant Project Norms")
  const injectedIds = uniqueStructuredIds(input.packets, startup)
  const digestItems = injectedIds.filter((id) => id.startsWith("digest-")).length
  return {
    schema_version: 1,
    timestamp: options.timestamp ?? new Date().toISOString(),
    host: "opencode",
    session_id: boundText(input.sessionID, MAX_SESSION_ID_CHARS),
    total_items: summary.recallCount + summary.habitCount + summary.normCount + startupItems,
    total_chars: recallChars + habitChars + normChars + startup.length,
    digest_items: digestItems,
    recall_items: summary.recallCount,
    recall_chars: recallChars,
    habit_items: summary.habitCount,
    habit_chars: habitChars,
    norm_items: summary.normCount,
    norm_chars: normChars,
    startup_items: startupItems,
    startup_chars: startup.length,
    injected_ids: injectedIds,
    startup_present: startupItems > 0,
  }
}

export function appendMemoryUsage(root: string, input: MemoryUsageInput, options: MemoryUsageOptions = {}): MemoryUsageEntry {
  const entry = buildMemoryUsageEntry(input, options)
  if (entry.total_items > 0) boundedJsonlAppend(root, ".memory-usage.jsonl", entry, 200)
  return entry
}
