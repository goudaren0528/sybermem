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
import { buildPromptInjectionToastSummary, habitCandidateToast, pendingHabitToast, promptInjectionToastMessage } from "./injection_toast"
import { updateNudgeMessage } from "./version_signal"
import { feedbackRpc, type FeedbackNotice, type FeedbackSummary } from "./v2_feedback"

// Structural V2 definition: Plugin.define in @opencode/plugin 2.x is an
// identity function. Avoid adding a shared runtime dependency for this bundle.
type Registration = { dispose(): Promise<void> }
type Request = { sessionID: string; system: { type: "text"; text: string }[]; messages?: { role?: string; content?: unknown }[] }
type ToolEvent = { sessionID: string; tool: string; input: any; status: string; result?: { metadata?: Record<string, unknown>; content?: unknown; error?: unknown } }
interface Context {
  location: { directory: string }
  session: {
    get(input: { sessionID: string }): Promise<{ location: { directory: string } }>
    context(input: { sessionID: string }): Promise<readonly { id: string; type: string; text?: string; parts?: readonly { type?: string; text?: string }[] }[]>
    hook(name: string, callback: (event: any) => Promise<void>): Promise<Registration>
  }
  tool: { hook(name: string, callback: (event: ToolEvent) => Promise<void>): Promise<Registration> }
  event: { subscribe(input: { signal: AbortSignal }): AsyncIterable<{ type: string; data: any }> }
  rpc?: { register(definition: typeof feedbackRpc, handlers: { status(input: { sessionID: string }): Promise<{ epoch: string; summary: FeedbackSummary | null }> }): Promise<Registration & { events: { emit(name: "notice", data: FeedbackNotice): Promise<void> } }> }
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
  const summaries = new Map<string, FeedbackSummary>()
  const sequences = new Map<string, number>()
  let feedback: (Registration & { events: { emit(name: "notice", data: FeedbackNotice): Promise<void> } }) | undefined
  const notice = (sessionID: string, kind: FeedbackNotice["kind"], message: string, messageID = "", totalItems = 0, totalChars = 0) => {
    if (stopped || !sessionID || !feedback) return
    const sequence = (sequences.get(sessionID) ?? 0) + 1
    sequences.set(sessionID, sequence)
    const data: FeedbackNotice = { epoch, sessionID, sequence, kind, message: message.slice(0, 240), messageID, totalItems, totalChars }
    if (kind === "summary") summaries.set(sessionID, { epoch, sessionID, sequence, message: data.message, messageID, totalItems, totalChars })
    void feedback.events.emit("notice", data).catch(() => { /* optional UI channel */ })
  }
  // V2 server plugins cannot display V1 TUI toasts. Preserve advisory text in
  // server diagnostics; model-visible memory remains in context hooks below.
  const diagnostic = (message: string) => { if (!stopped) console.info(message) }
  const client = { diagnostic, tui: { showToast: async ({ body }: { body: { message: string } }) => diagnostic(body.message) } }
  diagnostic("SyberMem V2: reply text markers are unavailable; a separately loaded TUI companion can display RPC notifications. Diagnostics and .sybermem/.memory-usage.jsonl remain available without it.")
  const versionNudge = updateNudgeMessage(root)
  if (versionNudge) diagnostic(versionNudge)
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
    summaries.clear()
    sequences.clear()
  }
  try {
    if (ctx.rpc) {
      feedback = await ctx.rpc.register(feedbackRpc, { status: async ({ sessionID }) => ({ epoch, summary: await belongs(sessionID) ? summaries.get(sessionID) ?? null : null }) })
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
          notice(event.sessionID, "advisory", versionNudge)
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
          const summary = buildPromptInjectionToastSummary(classifyPackets(packets), usage)
          if (summary && reported.get(event.sessionID) !== messageID) {
            reported.set(event.sessionID, messageID)
            const message = promptInjectionToastMessage(summary)
            diagnostic(message)
            if (summaries.get(event.sessionID)?.messageID !== messageID) notice(event.sessionID, "summary", message, messageID, summary.totalItems, summary.totalChars)
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
      if (event.type === "session.deleted" && (sessions.has(id) || pendingStates.has(id))) {
        resetSessionActivity(id); resetPendingHabit(id); sessions.delete(id); pendingStates.delete(id); admitted.delete(id); summaries.delete(id); reported.delete(id); sequences.delete(id); versionNotified.delete(id)
        continue
      }
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
