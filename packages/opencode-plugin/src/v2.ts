import { $ } from "bun"
import { randomUUID } from "node:crypto"
import { relative, resolve, win32 } from "node:path"
import { resolveRoot, type Shell } from "./runtime"
import { buildStartupContext } from "./startup_context"
import { buildCompactionContext } from "./compaction"
import { classifyPackets, collectPromptPackets } from "./prompt_context"
import { captureRecordIntentWithCli } from "./record_intent"
import { captureHabitIntentWithCli } from "./habit_intent"
import { appendRecallDebug } from "./recall_debug"
import { appendMemoryUsage } from "./memory_usage"
import { recordEditedFile, recordInjectedRecords, recordMemoryUsage, recordToolExecution, recordTodoUpdate, resetSessionActivity } from "./session_activity"
import { resetPendingHabit, injectPendingHabitReminder } from "./pending_habit"
import { flushSessionRelevance, handleSessionIdle, maybeToastRecallHealth, maybeToastDigestBacklog } from "./plugin"
import { buildPromptInjectionToastSummary, habitCandidateToast, pendingHabitToast, type PromptInjectionToastSummary } from "./injection_toast"
import { updateNudgeMessage, readInstalledVersion } from "./version_signal"
import { evaluateRemoteVersion, readRemoteVersionCache, remoteUpdateNudgeMessage } from "./remote_version"
import { feedbackRpc, type FeedbackNotice, type FeedbackSummary, type VersionStatus } from "./v2_feedback"

// One accurate summary per persisted user message, covering both halves of what a
// V2 turn can actually inject: the one-shot project startup context and this
// turn's dynamic packets (recall / habit / norm). A startup-only turn still gets a
// summary (project context was added even with zero dynamic entries); a turn where
// nothing was injected returns null so no misleading notice is emitted. Wording
// states what was ADDED to the request, never that the model used/remembered it.
function injectionSummary(startupPresent: boolean, dynamic: PromptInjectionToastSummary | null): { message: string; totalItems: number; totalChars: number } | null {
  if (!startupPresent && !dynamic) return null
  const segments: string[] = []
  if (startupPresent) segments.push("已向本轮请求加入项目启动上下文")
  if (dynamic) {
    const lanes = dynamic.laneCounts.map(({ lane, count }) => `${lane}=${count}`).join(", ")
    segments.push(`本轮加入 ${dynamic.totalItems} 条上下文（${lanes}）`)
  }
  return { message: `⭐ SyberMem: ${segments.join("；")}`, totalItems: dynamic?.totalItems ?? 0, totalChars: dynamic?.totalChars ?? 0 }
}

// Structural V2 definition: Plugin.define in @opencode/plugin 2.x is an
// identity function. Avoid adding a shared runtime dependency for this bundle.
type Registration = { dispose(): Promise<void> }
type Request = { sessionID: string; system: { type: "text"; text: string }[]; messages?: { role?: string; content?: unknown }[] }
type ToolEvent = { sessionID: string; tool: string; input: any; status: string; result?: { metadata?: Record<string, unknown>; content?: unknown; error?: unknown } }
// Version hints are categorized so the TUI can tell a project-refresh nudge from
// a whole-install GitHub nudge. Each category holds at most one current hint.
type VersionKind = "project" | "remote"
interface Context {
  location: { directory: string }
  session: {
    get(input: { sessionID: string }): Promise<{ location: { directory: string } }>
    context(input: { sessionID: string }): Promise<readonly { id: string; type: string; text?: string; parts?: readonly { type?: string; text?: string }[] }[]>
    hook(name: string, callback: (event: any) => Promise<void>): Promise<Registration>
  }
  tool: { hook(name: string, callback: (event: ToolEvent) => Promise<void>): Promise<Registration> }
  event: { subscribe(input: { signal: AbortSignal }): AsyncIterable<{ type: string; data: any }> }
  rpc?: { register(definition: typeof feedbackRpc, handlers: { status(input: { sessionID: string }): Promise<{ epoch: string; summary: FeedbackSummary | null; versionStatus?: VersionStatus[]; protocolVersion?: number }> }): Promise<Registration & { events: { emit(name: "notice", data: FeedbackNotice): Promise<void> } }> }
}

export async function setupSyberMemV2(ctx: Context, shell: Shell = $): Promise<() => Promise<void>> {
  const root = resolveRoot(ctx.location.directory)
  if (!root) return async () => {}
  const epoch = randomUUID()
  let stopped = false
  const controller = new AbortController()
  const aborted = new Promise<void>((resolve) => controller.signal.addEventListener("abort", () => resolve(), { once: true }))
  const registrations: Registration[] = []
  type SessionState = { startup: string; messageID?: string; packets: readonly string[]; recalled: Map<string, readonly string[]>; accounted: Set<string> }
  const sessions = new Map<string, SessionState>()
  const reported = new Map<string, string>()
  const pendingStates = new Map<string, Promise<SessionState>>()
  const contextQueues = new Map<string, Promise<void>>()
  const injected = new WeakSet<Request>()
  const compacted = new WeakSet<Request>()
  const admitted = new Map<string, { id: string; text: string }>()
  const versionNotified = new Set<string>()
  const remoteVersionNotified = new Set<string>()
  const summaries = new Map<string, FeedbackSummary>()
  // One monotonic sequence per setup epoch (server instance), not per session.
  // The TUI client keeps the highest sequence it has seen for a session and
  // drops non-advancing notices, so a per-session counter is unsafe: when a
  // status-only session's version cache is evicted and the SAME still-active
  // session polls again, a per-session counter would restart at 1 and the client
  // (same epoch) would reject the notice. A single epoch-wide counter is O(1)
  // state, never regresses across eviction/deletion/reconnect, and still only
  // increases within any one session, so live/status ordering is preserved.
  // Unchanged version hints still reuse their existing notice (and sequence).
  let feedbackSequence = 0
  // Version hints currently valid for a session, one slot per category
  // (project/remote), so at most two per session. Unlike the older
  // sessions/reported/... maps, this NEW state is explicitly bounded (PRD
  // §6.1/§9.3 require a concrete non-queue cap): `versionTouched` is an LRU
  // touch order and MAX_VERSION_SESSIONS caps how many sessions retain hints.
  // Eviction only targets "version-only" sessions (no sessions/pending/
  // queue/summary/admission evidence), so it can never drop a live session's
  // accounting; a version hint is advisory and is rebuilt from the current
  // project stamp / remote cache on the next status or context under the same
  // epoch-wide sequence (never a regression). The still-unbounded older maps are
  // out of this change.
  const MAX_VERSION_SESSIONS = 256
  const versionStatus = new Map<string, Map<VersionKind, FeedbackNotice>>()
  const versionTouched = new Map<string, number>()
  let versionTick = 0
  let feedback: (Registration & { events: { emit(name: "notice", data: FeedbackNotice): Promise<void> } }) | undefined
  const nextNotice = (sessionID: string, kind: FeedbackNotice["kind"], message: string, messageID: string, totalItems: number, totalChars: number): FeedbackNotice => {
    const sequence = ++feedbackSequence
    return { epoch, sessionID, sequence, kind, message: message.slice(0, 240), messageID, totalItems, totalChars }
  }
  const emitNotice = (data: FeedbackNotice) => { if (feedback) void feedback.events.emit("notice", data).catch(() => { /* optional UI channel */ }) }
  const notice = (sessionID: string, kind: FeedbackNotice["kind"], message: string, messageID = "", totalItems = 0, totalChars = 0) => {
    if (stopped || !sessionID || !feedback) return
    const data = nextNotice(sessionID, kind, message, messageID, totalItems, totalChars)
    if (kind === "summary") summaries.set(sessionID, { epoch, sessionID, sequence: data.sequence, message: data.message, messageID, totalItems, totalChars })
    emitNotice(data)
  }
  // Bound the new version cache. Touch order is refreshed on every version
  // lookup so an actively polled session is never the eviction victim. Eviction
  // is restricted to "version-only" sessions: any session with a session/pending
  // entry, a queued turn, a summary or a pending admission is skipped, so live
  // accounting and the shared notice sequence are never disturbed. If every
  // tracked session is live the cap is a soft one for that window; the older
  // maps remain under the separate PRD §9 item.
  const touchVersion = (sessionID: string) => {
    versionTouched.delete(sessionID)
    versionTouched.set(sessionID, ++versionTick)
  }
  const releaseVersionSession = (sessionID: string) => { versionStatus.delete(sessionID); versionTouched.delete(sessionID) }
  const versionOnly = (sessionID: string) => !sessions.has(sessionID) && !pendingStates.has(sessionID) && !contextQueues.has(sessionID) && !reported.has(sessionID) && !summaries.has(sessionID) && !admitted.has(sessionID)
  const pruneVersionSessions = (keep: string) => {
    if (versionTouched.size <= MAX_VERSION_SESSIONS) return
    for (const id of [...versionTouched.keys()]) {
      if (versionTouched.size <= MAX_VERSION_SESSIONS) break
      // Never evict the session whose hint is being computed right now.
      if (id === keep) continue
      if (!versionOnly(id)) continue
      releaseVersionSession(id)
      versionNotified.delete(id)
      remoteVersionNotified.delete(id)
    }
  }
  // Remember the currently valid hint for a category. An unchanged message reuses
  // the exact object already sent over the live stream, so its sequence stays
  // authoritative; a CHANGED message takes the next sequence from the same
  // counter (never a fabricated lower one); a hint that no longer applies is
  // dropped. This never emits: a status snapshot must not backfill a hint whose
  // condition has gone away.
  const rememberVersion = (sessionID: string, kind: VersionKind, message: string | null): FeedbackNotice | null => {
    const kinds = versionStatus.get(sessionID)
    if (!message) {
      kinds?.delete(kind)
      if (kinds && kinds.size === 0) releaseVersionSession(sessionID)
      return null
    }
    touchVersion(sessionID)
    const text = message.slice(0, 240)
    if (kinds) {
      const existing = kinds.get(kind)
      if (existing && existing.message === text) return existing
    }
    const target = kinds ?? new Map<VersionKind, FeedbackNotice>()
    if (!kinds) versionStatus.set(sessionID, target)
    const data = nextNotice(sessionID, "advisory", text, "", 0, 0)
    target.set(kind, data)
    pruneVersionSessions(sessionID)
    return data
  }
  const liveVersionNotice = (sessionID: string, kind: VersionKind, message: string) => {
    const data = rememberVersion(sessionID, kind, message)
    if (data) emitNotice(data)
  }
  // Current, condition-checked hints for a status snapshot (≤2). The local project
  // freshness is derived live from the project stamp; the remote hint reads the
  // cache NOW instead of reusing the setup-time value, so a background refresh
  // that landed after setup is reflected. Disabled remote checks yield null and
  // drop the entry.
  const currentRemoteNudge = () => remoteUpdateNudgeMessage(readRemoteVersionCache(), readInstalledVersion())
  const currentVersionStatus = (sessionID: string): VersionStatus[] => {
    const entries: readonly { type: VersionKind; message: string | null }[] = [
      { type: "project", message: updateNudgeMessage(root) },
      { type: "remote", message: currentRemoteNudge() },
    ]
    const out: VersionStatus[] = []
    for (const { type, message } of entries) {
      const data = rememberVersion(sessionID, type, message)
      if (data) out.push({ type, notice: data })
    }
    return out
  }
  // V2 server plugins cannot display V1 TUI toasts. Preserve advisory text in
  // server diagnostics; model-visible memory remains in context hooks below.
  const diagnostic = (message: string) => { if (!stopped) console.info(message) }
  const client = { diagnostic, tui: { showToast: async ({ body }: { body: { message: string } }) => diagnostic(body.message) } }
  diagnostic("SyberMem V2: reply text markers are unavailable; a separately loaded TUI companion can display RPC notifications. Diagnostics and .sybermem/.memory-usage.jsonl remain available without it.")
  const versionNudge = updateNudgeMessage(root)
  if (versionNudge) diagnostic(versionNudge)
  // Remote-version awareness is orthogonal to the local project-vs-installed nudge:
  // this one says "your whole install is behind GitHub main" (re-run the installer),
  // the one above says "this project should be refreshed" (/sybermem-update).
  // evaluateRemoteVersion reads the 24h cache synchronously and, only when stale,
  // kicks off one shared non-awaited refresh; it never blocks setup and never throws.
  // It is used here only to trigger that refresh and emit the setup diagnostic; the
  // live/context and status paths both recompute from the CURRENT cache via
  // currentRemoteNudge(), so a refresh that lands after setup is never replayed as
  // the stale setup-time version.
  const remoteVersionNudge = evaluateRemoteVersion()
  if (remoteVersionNudge) diagnostic(remoteVersionNudge)
  const args = { $: shell, directory: root, client }
  const sessionArgs = (sessionID: string) => ({ ...args, client: { diagnostic: (message: string) => { diagnostic(message); notice(sessionID, "advisory", message) }, tui: { showToast: async ({ body }: { body: { message: string } }) => { diagnostic(body.message); notice(sessionID, "advisory", body.message) } } } })
  async function belongs(sessionID: string): Promise<boolean> {
    if (stopped || !sessionID) return false
    try {
      const directory = (await ctx.session.get({ sessionID })).location.directory
      if (stopped) return false
      const canonical = (path: string) => process.platform === "win32" ? win32.normalize(win32.resolve(path)).toLowerCase() : resolve(path)
      return canonical(directory) === canonical(ctx.location.directory)
    }
    catch { return false }
  }
  async function state(sessionID: string) {
    let value = sessions.get(sessionID)
    if (!value) {
      let pending = pendingStates.get(sessionID)
      if (!pending) {
        pending = (async (): Promise<SessionState> => ({ startup: await buildStartupContext(shell, root!) ?? "", packets: [], recalled: new Map(), accounted: new Set() }))()
        pendingStates.set(sessionID, pending)
      }
      try {
        value = await pending
        if (!stopped && pendingStates.get(sessionID) === pending) sessions.set(sessionID, value)
      } finally {
        if (pendingStates.get(sessionID) === pending) pendingStates.delete(sessionID)
      }
    }
    return value
  }
  const active = (sessionID: string, value: SessionState) => !stopped && sessions.get(sessionID) === value
  // Serialize the entire consume/inject/account operation per session. Waiters
  // wake on abort even if an external CLI operation never resolves.
  async function consume(sessionID: string, work: () => Promise<void>) {
    const previous = contextQueues.get(sessionID) ?? Promise.resolve()
    let release!: () => void
    const done = new Promise<void>((resolve) => { release = resolve })
    contextQueues.set(sessionID, done)
    try {
      await Promise.race([previous, aborted])
      if (!stopped) await work()
    } finally {
      release()
      if (contextQueues.get(sessionID) === done) contextQueues.delete(sessionID)
    }
  }
  // Release every per-session structure this instance owns. Runs
  // UNCONDITIONALLY on `session.deleted`: a status-only session (a TUI poll that
  // never had a context turn) creates versionStatus but no
  // sessions/pendingStates entry, so the old guarded branch leaked them. The
  // module-global activity/habit stores are reset only when some internal map
  // still proves THIS instance tracked the session, so a peer instance sharing
  // the global store is not clobbered by a delete event it does not own.
  const releaseSession = (sessionID: string) => {
    if (!sessionID) return
    const known = sessions.has(sessionID) || pendingStates.has(sessionID) || contextQueues.has(sessionID) || admitted.has(sessionID) || reported.has(sessionID) || summaries.has(sessionID) || versionStatus.has(sessionID) || versionNotified.has(sessionID) || remoteVersionNotified.has(sessionID)
    if (known) { resetSessionActivity(sessionID); resetPendingHabit(sessionID) }
    sessions.delete(sessionID)
    reported.delete(sessionID)
    pendingStates.delete(sessionID)
    contextQueues.delete(sessionID)
    admitted.delete(sessionID)
    versionNotified.delete(sessionID)
    remoteVersionNotified.delete(sessionID)
    summaries.delete(sessionID)
    versionStatus.delete(sessionID)
    versionTouched.delete(sessionID)
  }
  const cleanup = async () => {
    stopped = true
    controller.abort()
    await Promise.allSettled(registrations.splice(0).map(async (item) => { await item.dispose() }))
    for (const id of sessions.keys()) { resetSessionActivity(id); resetPendingHabit(id) }
    sessions.clear()
    reported.clear()
    pendingStates.clear()
    contextQueues.clear()
    admitted.clear()
    versionNotified.clear()
    remoteVersionNotified.clear()
    summaries.clear()
    versionStatus.clear()
    versionTouched.clear()
  }
  try {
    if (ctx.rpc) {
      feedback = await ctx.rpc.register(feedbackRpc, { status: async ({ sessionID }) => {
        // The protocol capability marker is server-wide and always advertised,
        // even when there is no summary and no currently valid version hint (or
        // for a session this instance does not own). Old servers omit it.
        if (!await belongs(sessionID)) return { epoch, summary: null, protocolVersion: 2 }
        const summary = summaries.get(sessionID) ?? null
        const versions = currentVersionStatus(sessionID)
        return versions.length ? { epoch, summary, protocolVersion: 2, versionStatus: versions } : { epoch, summary, protocolVersion: 2 }
      } })
      registrations.push(feedback)
    }
    // Admission is retryable. Cache only; never write evidence until a model
    // context actually consumes this prompt.
    registrations.push(await ctx.session.hook("prompt", async (event: { sessionID: string; messageID: string; prompt: { text: string } }) => {
      if (!await belongs(event.sessionID)) return
      if (!stopped) admitted.set(event.sessionID, { id: event.messageID, text: event.prompt.text })
    }))
    registrations.push(await ctx.session.hook("context", async (event: Request) => {
      if (!await belongs(event.sessionID)) return
      // Read this request's persisted turn before waiting behind another
      // request: a later turn must not replace an earlier waiter's identity.
      const history = await ctx.session.context({ sessionID: event.sessionID })
      if (stopped) return
      await consume(event.sessionID, async () => {
        const current = await state(event.sessionID)
        if (!active(event.sessionID, current) || injected.has(event)) return
        if (versionNudge && !versionNotified.has(event.sessionID)) {
          versionNotified.add(event.sessionID)
          liveVersionNotice(event.sessionID, "project", versionNudge)
        }
        const remoteNudge = currentRemoteNudge()
        if (remoteNudge && !remoteVersionNotified.has(event.sessionID)) {
          remoteVersionNotified.add(event.sessionID)
          liveVersionNotice(event.sessionID, "remote", remoteNudge)
        }
        // Admission can fail or remain queued. Only persisted user messages may
        // trigger capture/recall; never use an unconfirmed admission fallback.
        const prompt = [...history].reverse().find((message) => message.type === "user")
        if (prompt?.id === admitted.get(event.sessionID)?.id) admitted.delete(event.sessionID)
        if (prompt && !current.recalled.has(prompt.id)) {
          const text = prompt.text || prompt.parts?.filter((part) => part.type === "text" && typeof part.text === "string").map((part) => part.text).join("\n") || ""
          await captureRecordIntentWithCli(shell, root, text)
          if (!active(event.sessionID, current)) return
          const habitIntent = await captureHabitIntentWithCli(shell, root, text)
          if (!active(event.sessionID, current)) return
          const packets = await collectPromptPackets(shell, root, text)
          if (!active(event.sessionID, current)) return
          current.packets = packets
          current.messageID = prompt.id
          current.recalled.set(prompt.id, packets)
          if (habitIntent.captured || classifyPackets(packets).habitCandidate) {
            const message = habitCandidateToast(habitIntent)
            diagnostic(message); notice(event.sessionID, "advisory", message, prompt.id)
          }
          appendRecallDebug(root, packets)
        }
        if (!active(event.sessionID, current)) return
        // Keep request-local identity and packets paired even if a later turn
        // has already been consumed by this session.
        const startup = current.startup
        const messageID = prompt?.id ?? current.messageID
        const packets = (messageID && current.recalled.get(messageID)) ?? current.packets
        const output = { system: [startup, ...packets].filter(Boolean) }
        if (await injectPendingHabitReminder(shell, root, event.sessionID, output)) {
          const message = pendingHabitToast()
          if (active(event.sessionID, current)) { diagnostic(message); notice(event.sessionID, "advisory", message, messageID) }
        }
        if (!active(event.sessionID, current)) return
        injected.add(event)
        event.system.push(...output.system.map((text) => ({ type: "text" as const, text })))
        // Usage and business activity describe a persisted user intent, not each
        // independent model request/continuation which still gets the injection.
        if (messageID && !current.accounted.has(messageID)) {
          current.accounted.add(messageID)
          recordInjectedRecords(event.sessionID, packets)
          const usage = appendMemoryUsage(root, { sessionID: event.sessionID, packets, startup })
          recordMemoryUsage(event.sessionID, usage)
          // One summary per persisted user message, covering both the one-shot
          // startup context and this turn's dynamic packets. A startup-only turn
          // (no recall/habit/norm) still reports the startup context; a turn that
          // injected nothing emits no notice at all.
          const dynamic = buildPromptInjectionToastSummary(classifyPackets(packets), usage)
          const summary = injectionSummary(Boolean(startup), dynamic)
          if (summary && reported.get(event.sessionID) !== messageID) {
            reported.set(event.sessionID, messageID)
            diagnostic(summary.message)
            if (summaries.get(event.sessionID)?.messageID !== messageID) notice(event.sessionID, "summary", summary.message, messageID, summary.totalItems, summary.totalChars)
          }
        }
      })
    }))
    registrations.push(await ctx.session.hook("compaction", async (event: Request) => {
      if (!await belongs(event.sessionID) || compacted.has(event)) return
      let text: string | null = null
      try { text = await buildCompactionContext(shell, root) } catch { /* advisory: preserve request unchanged */ }
      if (text && !stopped && !compacted.has(event)) {
        compacted.add(event)
        if (!event.system.some((part) => part.type === "text" && part.text === text)) event.system.push({ type: "text", text })
      }
    }))
    registrations.push(await ctx.tool.hook("execute.after", async (event) => {
      if (event.status !== "completed" || !await belongs(event.sessionID)) return
      const current = await state(event.sessionID)
      if (!active(event.sessionID, current)) return
      const input = typeof event.input === "object" && event.input !== null ? event.input : {}
      if (["edit", "write"].includes(event.tool) && typeof input.filePath === "string") {
        recordEditedFile(event.sessionID, relative(root, resolve(ctx.location.directory, input.filePath)))
      }
      if (event.tool === "todowrite") recordTodoUpdate(event.sessionID, input)
      // Completion alone does not prove shell success (nonzero commands can
      // complete normally). Require explicit exit evidence, never infer zero.
      const metadata = event.result?.metadata
      const exit = metadata?.exit ?? metadata?.exitCode
      if (event.tool === "shell" && exit === 0 && !event.result?.error) {
        recordToolExecution(event.sessionID, { tool: "bash", args: input }, { exit })
      }
    }))
  } catch (error) { await cleanup(); throw error }
  const events = (async () => {
    for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
      if (stopped) break
      const id = event.data?.sessionID
      if (event.type === "session.deleted") { releaseSession(id); continue }
      if (event.type !== "session.idle" || !await belongs(id)) continue
      const scoped = sessionArgs(id)
      try { await handleSessionIdle(scoped, root, id) } catch { /* advisory */ }
      if (stopped) break
      await flushSessionRelevance(args, root, id)
      if (stopped) break
      await maybeToastRecallHealth(scoped, root)
      if (stopped) break
      await maybeToastDigestBacklog(scoped, root)
    }
  })().catch(() => { if (!stopped) console.warn("SyberMem V2 event subscription ended unexpectedly") })
  return async () => { await cleanup(); await Promise.race([events, aborted]) }
}

export default { id: "sybermem", setup: setupSyberMemV2 }
