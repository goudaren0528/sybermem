// Opt-in (default OFF) reply marker. When SYBERMEM_REPLY_MARKER is truthy, the
// plugin prepends ONE compact line to the FIRST assistant text part of a turn
// whenever SyberMem actually injected recall/habit context that turn. This gives
// a guaranteed, model-independent visibility signal via experimental.text.complete
// (the only OpenCode seam that mutates the visible reply). It is OFF by default
// because the API is experimental and the marker persists in message history.

interface PendingMarker {
  readonly recallCount: number
  readonly habitCount: number
}

// sessionID -> marker pending for the NEXT assistant text part in this turn.
const PENDING = new Map<string, PendingMarker>()
// messageID already marked, so multi-part replies only get ONE marker at the top.
const MARKED = new Set<string>()

export function replyMarkerEnabled(): boolean {
  const raw = (process.env.SYBERMEM_REPLY_MARKER ?? "").trim().toLowerCase()
  return raw === "1" || raw === "true" || raw === "yes" || raw === "on"
}

// Record that this turn injected material, so the upcoming reply gets a marker.
// Called at system-transform time with the injection summary.
export function armReplyMarker(sessionID: string, recallCount: number, habitCount: number): void {
  if (!sessionID) return
  if (recallCount <= 0 && habitCount <= 0) {
    PENDING.delete(sessionID)
    return
  }
  PENDING.set(sessionID, { recallCount, habitCount })
}

function formatMarker(m: PendingMarker): string {
  const parts: string[] = []
  if (m.recallCount > 0) parts.push(`⭐ ${m.recallCount} 条记忆`)
  if (m.habitCount > 0) parts.push(`🧠 ${m.habitCount} 条习惯`)
  return `> SyberMem: 本轮参考了 ${parts.join(" · ")}`
}

// Return the text to write back for this text part. Prepends the marker exactly
// once per assistant message (first text part), then clears the pending state.
export function applyReplyMarker(sessionID: string, messageID: string, text: string): string {
  if (!replyMarkerEnabled()) return text
  if (!sessionID || !messageID) return text
  if (MARKED.has(messageID)) return text
  const pending = PENDING.get(sessionID)
  if (!pending) return text
  MARKED.add(messageID)
  PENDING.delete(sessionID)
  if (MARKED.size > 500) MARKED.clear()
  return `${formatMarker(pending)}\n\n${text}`
}
