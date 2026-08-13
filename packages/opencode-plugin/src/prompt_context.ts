import type { Shell } from "./runtime"
import { sybermemText } from "./runtime"

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
  return packets
}

export function stashPromptPackets(sessionID: string, packets: readonly string[]): void {
  if (packets.length > 0) RECALL_STASH.set(sessionID, packets)
  else RECALL_STASH.delete(sessionID)
}

export function injectStashedPromptPackets(sessionID: string, output: SystemTransformOutput): boolean {
  const packets = RECALL_STASH.get(sessionID)
  RECALL_STASH.delete(sessionID)
  if (!packets || packets.length === 0) return false
  const hints = packets.join("\n\n")
  if (output.system && output.system.length > 0) output.system[0] = `${hints}\n\n${output.system[0]}`
  else output.system = [hints, ...(output.system ?? [])]
  return true
}
