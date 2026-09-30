import { resolve } from "node:path"

// Portable JSON Schema: the same definition is passed to the V2 server RPC
// registration and the independently loaded TUI client (no shared process state).
const text = { type: "string" } as const
const integer = { type: "integer", minimum: 0 } as const
const noticeSchema = { type: "object", additionalProperties: false, required: ["epoch", "sessionID", "sequence", "kind", "message", "messageID", "totalItems", "totalChars"], properties: {
  epoch: text, sessionID: text, sequence: integer, kind: { type: "string", enum: ["summary", "advisory"] }, message: text, messageID: text, totalItems: integer, totalChars: integer,
} } as const
const summarySchema = { type: "object", additionalProperties: false, required: ["epoch", "sessionID", "sequence", "messageID", "message", "totalItems", "totalChars"], properties: {
  epoch: text, sessionID: text, sequence: integer, messageID: text, message: text, totalItems: integer, totalChars: integer,
} } as const
// Optional, server-validated version hints carried by the status snapshot. The
// wrapper only adds the project-vs-remote category; the notice itself keeps the
// exact advisory shape used by live events, so the event schema and the status
// schema can never drift. The server guarantees at most two current entries.
const versionStatusSchema = { type: "object", additionalProperties: false, required: ["type", "notice"], properties: {
  type: { type: "string", enum: ["project", "remote"] }, notice: noticeSchema,
} } as const
// Optional new-capability marker on the status response. It is deliberately NOT
// in `required`, so an old server that omits it is still accepted, and the TUI
// detects the V2 protocol by the presence of `versionStatus` rather than by this
// field. The pinned OpenCode 2.0.15 host validates with an older JSON Schema
// validator that has no `const` keyword, so the constant 2 is expressed as a
// single-value `enum` (equivalent to a JSON Schema `const: 2`).
const protocolVersionSchema = { type: "integer", enum: [2] } as const
export const feedbackRpc = {
  id: "sybermem-feedback",
  methods: { status: {
    input: { type: "object", additionalProperties: false, required: ["sessionID"], properties: { sessionID: text } },
    output: { type: "object", additionalProperties: false, required: ["epoch", "summary"], properties: {
      epoch: text, summary: { anyOf: [summarySchema, { type: "null" }] },
      versionStatus: { type: "array", maxItems: 2, items: versionStatusSchema },
      protocolVersion: protocolVersionSchema,
    } },
  } },
  events: { notice: { schema: noticeSchema } },
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
export interface VersionStatus { type: "project" | "remote"; notice: FeedbackNotice }
export interface FeedbackStatus { epoch: string; summary: FeedbackSummary | null; versionStatus?: VersionStatus[]; protocolVersion?: number }

export function sameLocation(left: string | undefined, right: string | undefined): boolean {
  return !!left && !!right && resolve(left).toLowerCase() === resolve(right).toLowerCase()
}

// Sequence is scoped to an explicit server instance, not guessed from message IDs.
export function feedbackGate(directory: string, current: () => { type: string; sessionID?: string }, show: (notice: FeedbackNotice) => void) {
  const seen = new Map<string, { epoch: string; sequence: number; revision: number; retired: Set<string> }>()
  const summaries = new Map<string, Set<string>>()
  // Last hint actually shown per (session, epoch, category): its message identity
  // and the sequence it was shown at. Only the current confirmed epoch is retained
  // per session, so state stays bounded to the two categories and old epochs are
  // dropped. A changed message at a higher sequence is a genuine update (the
  // server re-issues it with a fresh sequence) and must still display; only the
  // same identity or a non-advancing sequence is suppressed.
  const versions = new Map<string, { epoch: string; shown: Map<"project" | "remote", { sequence: number; message: string }> }>()
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
    // A new epoch is a new server instance: version hint identity resets.
    versions.delete(sessionID)
    return next
  }
  const versionShown = (sessionID: string, epoch: string, type: "project" | "remote") => {
    const state = versions.get(sessionID)
    return state?.epoch === epoch ? state.shown.get(type) : undefined
  }
  // Mark only after a hint actually passed the sequence gate and was shown, so a
  // snapshot dropped as stale never suppresses a later, newer hint. Storing the
  // message identity distinguishes a real update from a plain re-send.
  const markVersion = (sessionID: string, epoch: string, type: "project" | "remote", notice: FeedbackNotice) => {
    let state = versions.get(sessionID)
    if (state?.epoch !== epoch) { state = { epoch, shown: new Map() }; versions.set(sessionID, state) }
    state.shown.set(type, { sequence: notice.sequence, message: notice.message })
  }
  // Version hints are advisory notices wrapped with a project/remote category.
  // Invalid or mis-scoped (wrong session/epoch) entries are safely dropped. The
  // server guarantees at most one current hint per category, so duplicate
  // categories inside one snapshot collapse to the first valid entry.
  const versionNotices = (raw: unknown, sessionID: string, epoch: string): { type: "project" | "remote"; notice: FeedbackNotice; display: boolean }[] => {
    if (!Array.isArray(raw)) return []
    const accepted: { type: "project" | "remote"; notice: FeedbackNotice; display: boolean }[] = []
    const seenTypes = new Set<"project" | "remote">()
    for (const entry of raw) {
      if (accepted.length >= 2) break
      if (!entry || typeof entry !== "object") continue
      const type = (entry as { type?: unknown }).type
      const notice = (entry as { notice?: FeedbackNotice }).notice
      if ((type !== "project" && type !== "remote") || !notice || typeof notice !== "object") continue
      if (notice.sessionID !== sessionID || notice.epoch !== epoch || notice.kind !== "advisory") continue
      if (typeof notice.message !== "string" || notice.message.length === 0) continue
      if (!Number.isSafeInteger(notice.sequence) || notice.sequence < 1) continue
      if (seenTypes.has(type)) continue
      const shown = versionShown(sessionID, epoch, type)
      // A non-advancing sequence re-sends older content: ignore it outright.
      if (shown && notice.sequence <= shown.sequence) continue
      // Same identity at a strictly higher sequence is a re-send, not a new
      // update: never toast it, but return it as a silent watermark entry so the
      // snapshot can still advance the session high-water mark. A changed message
      // at a higher sequence is a real update and remains displayable.
      if (shown && notice.message === shown.message) {
        accepted.push({ type, notice, display: false })
        continue
      }
      seenTypes.add(type)
      accepted.push({ type, notice, display: true })
    }
    return accepted
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
      const outranks = (sequence: number) => !!candidate && candidate.notice.epoch === status.epoch && candidate.notice.sequence > sequence
      // Replay the latest summary together with any version hints oldest-first, so
      // a higher-sequence hint can never make the latest summary look stale and
      // suppress it. Old servers omit versionStatus entirely.
      const replay: { notice: FeedbackNotice; type?: "project" | "remote"; display: boolean }[] = []
      if (status.summary && !outranks(status.summary.sequence)) replay.push({ notice: { ...status.summary, kind: "summary" }, display: true })
      for (const item of versionNotices(status.versionStatus, sessionID, status.epoch)) {
        if (outranks(item.notice.sequence)) continue
        replay.push({ notice: item.notice, type: item.type, display: item.display })
      }
      replay.sort((left, right) => left.notice.sequence - right.notice.sequence)
      for (const item of replay) {
        // A silent watermark entry re-issued a seen hint at a higher sequence. It
        // must not toast, but it still advances the session high-water mark (and
        // the seen version sequence) so a late lower live event cannot replay.
        // Handling it in the merged, sequence-sorted order means a genuinely newer
        // summary is never suppressed by a higher-sequence duplicate hint.
        if (!item.display) {
          if (item.type && item.notice.sequence > state.sequence) {
            state.sequence = item.notice.sequence
            markVersion(sessionID, status.epoch, item.type, item.notice)
          }
          continue
        }
        const previous = state.sequence
        this.accept({ location: { directory }, data: item.notice })
        // Remember a version hint only once it survived the sequence gate, so a
        // stale snapshot can never permanently hide a later, newer hint.
        if (item.type && state.sequence > previous) markVersion(sessionID, status.epoch, item.type, item.notice)
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
    clear() { seen.clear(); summaries.clear(); versions.clear(); candidates.clear() },
  }
}
