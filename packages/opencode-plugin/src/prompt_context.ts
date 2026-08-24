import type { Shell } from "./runtime"
import { normsListText, sybermemText } from "./runtime"
import { parseNorms, scopedNormSection } from "./norm_signal"

export const RECALL_STASH = new Map<string, readonly string[]>()

export interface TextPart { readonly type: string; readonly text?: string }
export interface ChatMessageOutput { readonly parts?: readonly TextPart[] }
export interface SystemTransformOutput { system?: string[] }

export function extractPromptText(output: ChatMessageOutput): string {
  return (output.parts ?? []).filter((p) => p.type === "text").map((p) => p.text ?? "").join(" ").trim()
}

export function appendPromptPacket(packets: string[], raw: string, heading: string): void {
  const trimmed = raw.trim()
  if (trimmed.startsWith(heading)) packets.push(trimmed)
}

export async function collectPromptPackets($: Shell, root: string, text: string): Promise<readonly string[]> {
  const packets: string[] = []
  try {
    const raw = await sybermemText($, root, ["context", "recall", "--query", text, "--format", "markdown"])
    appendPromptPacket(packets, raw, "## SyberMem Recall Hints")
  } catch {
    // Fail open: recall is additive context only.
  }
  try {
    const raw = await sybermemText($, root, ["context", "habit", "--context", text, "--delivery", "prompt-time", "--format", "markdown"])
    appendPromptPacket(packets, raw, "## User Habit Reminder")
  } catch {
    // Fail open: habit reminders are additive context only.
  }
  try {
    // Scope-matched binding norms for THIS prompt's area. Global norms are handled by the
    // startup constitution, so here we only surface scoped norms relevant to the task.
    const section = scopedNormSection(parseNorms(await normsListText($, root, "scoped", text)))
    if (section.trim()) packets.push(`## Relevant Project Norms\n${section.trim().replace(/^### Relevant Project Norms\n?/, "")}`)
  } catch {
    // Fail open: scoped norms are additive context only.
  }
  return packets
}

export function stashPromptPackets(sessionID: string, packets: readonly string[]): void {
  if (packets.length > 0) RECALL_STASH.set(sessionID, packets)
  else RECALL_STASH.delete(sessionID)
}

export interface InjectionSummary {
  readonly injected: boolean
  readonly recallCount: number
  readonly habitCount: number
  readonly habitCandidate: boolean
  readonly normCount: number
}

const NO_INJECTION: InjectionSummary = { injected: false, recallCount: 0, habitCount: 0, habitCandidate: false, normCount: 0 }

export function classifyPackets(packets: readonly string[]): InjectionSummary {
  if (packets.length === 0) return NO_INJECTION
  let recallCount = 0
  let habitCount = 0
  let habitCandidate = false
  let normCount = 0
  for (const packet of packets) {
    const trimmed = packet.trim()
    if (trimmed.startsWith("## SyberMem Recall Hints")) {
      recallCount += countBullets(trimmed)
    } else if (trimmed.startsWith("## User Habit Reminder")) {
      const habitLines = trimmed.split("\n").filter((line) => line.startsWith("- [habit-"))
      habitCount += habitLines.length
      // A habit packet with no concrete habit reference is a "preference candidate":
      // the prompt looked like a reusable preference but no stored habit matched.
      if (habitLines.length === 0) habitCandidate = true
    } else if (trimmed.startsWith("## Relevant Project Norms")) {
      normCount += trimmed.split("\n").filter((line) => line.startsWith("- [norm-")).length
    }
  }
  return { injected: recallCount > 0 || habitCount > 0 || habitCandidate || normCount > 0, recallCount, habitCount, habitCandidate, normCount }
}

function countBullets(packet: string): number {
  return packet.split("\n").filter((line) => /^-\s/.test(line.trim())).length
}

export function injectStashedPromptPackets(sessionID: string, output: SystemTransformOutput): InjectionSummary {
  const packets = RECALL_STASH.get(sessionID)
  RECALL_STASH.delete(sessionID)
  if (!packets || packets.length === 0) return NO_INJECTION
  const hints = packets.join("\n\n")
  if (output.system && output.system.length > 0) output.system[0] = `${hints}\n\n${output.system[0]}`
  else output.system = [hints, ...(output.system ?? [])]
  return classifyPackets(packets)
}
