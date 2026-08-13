import { boundedJsonlAppend } from "./state"

export type RecallDebugEvent = "inject" | "abstain"

export interface RecallDebugEntry {
  readonly source: "opencode-chat-message"
  readonly timestamp: string
  readonly event: RecallDebugEvent
  readonly record_ids: readonly string[]
  readonly match_classes: readonly string[]
  readonly reason: string
}

const RECORD_ID_RE = /\b(?:change|decision|requirement|bug|digest)-[a-z0-9-]+\b/gi
const MATCH_CLASS_RE = /\b(record-id|relation|topic|keyword|semantic)\b/gi

function uniqueMatches(text: string, pattern: RegExp): readonly string[] {
  return [...new Set([...text.matchAll(pattern)].map((m) => m[0].toLowerCase()))].slice(0, 20)
}

export function buildRecallDebugEntry(packets: readonly string[], timestamp = new Date().toISOString()): RecallDebugEntry {
  const recallPacket = packets.find((packet) => packet.trim().startsWith("## SyberMem Recall Hints")) ?? ""
  if (!recallPacket) return { source: "opencode-chat-message", timestamp, event: "abstain", record_ids: [], match_classes: [], reason: "no-high-signal-recall" }
  return { source: "opencode-chat-message", timestamp, event: "inject", record_ids: uniqueMatches(recallPacket, RECORD_ID_RE), match_classes: uniqueMatches(recallPacket, MATCH_CLASS_RE), reason: "high-signal-recall" }
}

export function appendRecallDebug(root: string, packets: readonly string[], timestamp?: string): void {
  boundedJsonlAppend(root, ".recall-debug.jsonl", buildRecallDebugEntry(packets, timestamp), 200)
}
