import { resolve } from "node:path"

// Portable JSON Schema: the same definition is passed to the V2 server RPC
// registration and the independently loaded TUI client (no shared process state).
const text = { type: "string" } as const
const integer = { type: "integer", minimum: 0 } as const
const summarySchema = { type: "object", additionalProperties: false, required: ["epoch", "sessionID", "sequence", "messageID", "message", "totalItems", "totalChars"], properties: {
  epoch: text, sessionID: text, sequence: integer, messageID: text, message: text, totalItems: integer, totalChars: integer,
} } as const
export const feedbackRpc = {
  id: "sybermem-feedback",
  methods: { status: {
    input: { type: "object", additionalProperties: false, required: ["sessionID"], properties: { sessionID: text } },
    output: { type: "object", additionalProperties: false, required: ["epoch", "summary"], properties: { epoch: text, summary: { anyOf: [summarySchema, { type: "null" }] } } },
  } },
  events: { notice: { schema: { type: "object", additionalProperties: false, required: ["epoch", "sessionID", "sequence", "kind", "message", "messageID", "totalItems", "totalChars"], properties: {
    epoch: text, sessionID: text, sequence: integer, kind: { type: "string", enum: ["summary", "advisory"] }, message: text, messageID: text, totalItems: integer, totalChars: integer,
  } } } },
} as const

export interface FeedbackNotice {
  epoch: string
  sessionID: string
  sequence: number
  kind: "summary" | "advisory"
  message: string
  messageID: string
  totalItems: number
  totalChars: number
}
export type FeedbackSummary = Omit<FeedbackNotice, "kind">
export interface FeedbackStatus { epoch: string; summary: FeedbackSummary | null }

export function sameLocation(left: string | undefined, right: string | undefined): boolean {
  return !!left && !!right && resolve(left).toLowerCase() === resolve(right).toLowerCase()
}

// Sequence is scoped to an explicit server instance, not guessed from message IDs.
export function feedbackGate(directory: string, current: () => { type: string; sessionID?: string }, show: (notice: FeedbackNotice) => void) {
  const seen = new Map<string, { epoch: string; sequence: number; revision: number; retired: Set<string> }>()
  const summaries = new Map<string, Set<string>>()
  // At most one unverified live notice per session. An epoch is never elected
  // from event delivery order: status is the only authority for transitions.
  const candidates = new Map<string, { notice: FeedbackNotice; version: number }>()
  let candidateVersion = 0
  const selected = (sessionID: string) => { const route = current(); return route.type === "session" && route.sessionID === sessionID }
  // Call only from an accepted status response. Unknown live epochs are held
  // for confirmation, never promoted by arrival order.
  const advance = (sessionID: string, epoch: string) => {
    const state = seen.get(sessionID)
    if (state?.retired.has(epoch)) return undefined
    if (state?.epoch === epoch) return state
    const next = { epoch, sequence: 0, revision: (state?.revision ?? 0) + 1, retired: new Set(state?.retired) }
    if (state) next.retired.add(state.epoch)
    seen.set(sessionID, next)
    return next
  }
  return {
    revision(sessionID: string) { return seen.get(sessionID)?.revision ?? 0 },
    challenge(sessionID: string) { return candidates.get(sessionID)?.version ?? 0 },
    accept(event: { location?: { directory?: string }; data?: FeedbackNotice }): boolean | undefined {
      const item = event.data
      if (!sameLocation(event.location?.directory, directory) || !item || !item.sessionID || !item.epoch || !Number.isSafeInteger(item.sequence) || item.sequence < 1 || !selected(item.sessionID)) return
      const currentState = seen.get(item.sessionID)
      if (currentState?.retired.has(item.epoch)) return
      if (!currentState || currentState.epoch !== item.epoch) {
        const previous = candidates.get(item.sessionID)
        if (!previous || previous.notice.epoch !== item.epoch || item.sequence > previous.notice.sequence) {
          candidates.set(item.sessionID, { notice: item, version: ++candidateVersion })
        }
        return true // request/queue authoritative status for this session
      }
      const state = currentState
      if (item.sequence <= state.sequence) return
      state.sequence = item.sequence
      state.revision++
      if (item.kind === "summary" && item.messageID) {
        const ids = summaries.get(item.sessionID) ?? new Set<string>()
        if (ids.has(item.messageID)) return
        ids.add(item.messageID)
        summaries.set(item.sessionID, ids)
      }
      show(item)
    },
    // A snapshot cannot overwrite newer confirmed live traffic observed after
    // its request. Retired epochs are never restored by late status responses.
    restore(status: FeedbackStatus, sessionID: string, requestedRevision = this.revision(sessionID), requestedChallenge = this.challenge(sessionID)) {
      if (!status?.epoch || !selected(sessionID) || requestedRevision !== this.revision(sessionID)) return
      if (status.summary && (status.summary.sessionID !== sessionID || status.summary.epoch !== status.epoch)) return
      const state = advance(sessionID, status.epoch)
      if (!state) return
      const candidate = candidates.get(sessionID)
      // A live notice received while the request was pending outranks an older
      // snapshot of the same confirmed epoch, even on first connection.
      if (status.summary && !(candidate?.notice.epoch === status.epoch && candidate.notice.sequence > status.summary.sequence)) {
        this.accept({ location: { directory }, data: { ...status.summary, kind: "summary" } })
      }
      if (candidate && candidate.notice.epoch === status.epoch) {
        candidates.delete(sessionID)
        this.accept({ location: { directory }, data: candidate.notice })
      } else if (candidate && candidate.version <= requestedChallenge) {
        // The authoritative response disproved the epoch that prompted it.
        // Keep it retired so another delayed event cannot reopen the contest.
        state.retired.add(candidate.notice.epoch)
        candidates.delete(sessionID)
      }
    },
    clear() { seen.clear(); summaries.clear(); candidates.clear() },
  }
}
