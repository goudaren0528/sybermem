import { boundedJsonlAppend } from "./state"
import { classifyPackets } from "./prompt_context"

export interface MemoryUsageEntry {
  readonly schema_version: 1
  readonly timestamp: string
  readonly host: "opencode"
  readonly session_id: string
  readonly total_items: number
  readonly total_chars: number
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

function uniqueIds(text: string): readonly string[] {
  return [...new Set([...text.matchAll(RECORD_ID_RE)].map((match) => match[0].toLowerCase()))].slice(0, 40)
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
  const injectedIds = uniqueIds([...input.packets, startup].join("\n"))
  return {
    schema_version: 1,
    timestamp: options.timestamp ?? new Date().toISOString(),
    host: "opencode",
    session_id: input.sessionID,
    total_items: summary.recallCount + summary.habitCount + summary.normCount + startupItems,
    total_chars: recallChars + habitChars + normChars + startup.length,
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
