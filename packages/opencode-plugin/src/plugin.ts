import type { Plugin } from "@opencode-ai/plugin"
import { appendAutoTrailJournal, classifyFollowup, countCommitsSinceLastRecord, detectHighLevelAreas, getChangedFiles, overlapsRecentAutoTrails, THEME_WINDOW_SIZE, trailFiles } from "./followup"
import { buildCompactionContext } from "./compaction"
import { detectStaleSignal, parseIndex } from "./project_state"
import { digestStatusText, memoryStatsText, resolveRoot } from "./runtime"
import { digestBacklogToast, parseDigestBacklog } from "./digest_backlog_signal"
import { loadNudgeState, saveNudgeState } from "./state"
import { appendRecallDebug } from "./recall_debug"
import { captureRecordIntentWithCli } from "./record_intent"
import { classifyPackets, collectPromptPackets, extractPromptText, injectStashedPromptPackets, RECALL_STASH, stashPromptPackets, type ChatMessageOutput, type InjectionSummary, type SystemTransformOutput } from "./prompt_context"
import { buildStartupContext, consumePendingStartup, markPendingStartup, prependStartupContext } from "./startup_context"
import { lowSignalRecallToast, parseRecallHealth } from "./recall_health_signal"
import { extractEditedFile, getSessionActivity, recordEditedFile, recordInjectedRecords, recordToolExecution, recordTodoUpdate, resetSessionActivity } from "./session_activity"
import { flushRecallOutcome } from "./recall_outcome"
import { captureHabitIntentWithCli } from "./habit_intent"
import { updateNudgeMessage } from "./version_signal"
import { applyReplyMarker, armReplyMarker } from "./reply_marker"
import { appendMemoryUsage } from "./memory_usage"

interface ToastClient { readonly tui: { readonly showToast: (input: { readonly body: { readonly message: string; readonly variant: "info" } }) => Promise<void> } }
interface PluginArgs { readonly $: import("./runtime").Shell; readonly directory: string; readonly client: ToastClient }
interface EventInput { readonly event: { readonly type: string; readonly properties?: { readonly info?: { readonly id?: string } } } }

async function showToast(client: ToastClient, message: string): Promise<void> {
  try {
    await client.tui.showToast({ body: { message, variant: "info" } })
  } catch {
    // Fail open: toasts are optional UX, never block the prompt flow.
  }
}

// In-memory throttle keyed by message type so we never toast-spam the TUI. The
// plugin process lives for the session; a fresh process resets the counter.
const LAST_TOAST = new Map<string, number>()
const TOAST_COOLDOWN_MS = 30_000

function throttledToast(client: ToastClient, key: string, message: string): void {
  const now = Date.now()
  const last = LAST_TOAST.get(key) ?? 0
  if (now - last < TOAST_COOLDOWN_MS) return
  LAST_TOAST.set(key, now)
  void showToast(client, message)
}

function readSessionID(source: unknown): string {
  if (typeof source !== "object" || source === null) return ""
  for (const key of ["sessionID", "sessionId", "session"]) {
    const value = Reflect.get(source, key)
    if (typeof value === "string" && value) return value
  }
  return ""
}

function recallToastMessage(summary: InjectionSummary): string | null {
  if (summary.recallCount === 0) return null
  const n = summary.recallCount
  return `⭐ SyberMem 记忆已加入本轮回答参考：${n} 条相关记录 (recall)`
}

// Habit injection gets its own distinct, brain-marked toast so an applied user
// habit is as perceptible as recall — not buried inside a combined recall notice.
function habitToastMessage(summary: InjectionSummary): string | null {
  if (summary.habitCount === 0) return null
  const n = summary.habitCount
  // Keep the English "applied ... user habit reminder(s)" phrasing so the toast
  // stays a DISTINCT applied-habit signal (also asserted by the package guard).
  return `🧠 SyberMem 已应用你的 ${n} 条习惯 (applied ${n} user habit reminder${n === 1 ? "" : "s"})`
}

// Applied scoped-norm toast: a binding project norm relevant to this prompt's area was
// injected. Distinct marker so a governing norm is as perceptible as recall/habit.
function normToastMessage(summary: InjectionSummary): string | null {
  if (summary.normCount === 0) return null
  const n = summary.normCount
  return `📏 SyberMem 已应用 ${n} 条相关项目规范 (applied ${n} project norm${n === 1 ? "" : "s"})`
}

// Scope-aware "save this preference" hint. When Core suggests where the preference
// belongs (cross-project user habit vs a project decision/requirement record), the
// toast routes the user to the right home; otherwise it stays neutral and defers the
// user-vs-project question to the /sybermem-habit confirm step.
function habitCandidateToast(habitIntent: import("./habit_intent").HabitIntentResult): string {
  if (habitIntent.captured && habitIntent.suggestedScope === "project") {
    return "💡 SyberMem 发现一条像是本项目的约定 — 可用 /sybermem-record 记为决策/需求，或 /sybermem-habit 确认"
  }
  if (habitIntent.captured && habitIntent.suggestedScope === "user") {
    return "💡 SyberMem 发现一条可复用的个人习惯 — 需要的话用 /sybermem-habit 一步确认"
  }
  return "💡 SyberMem 发现一条可复用的偏好/规范 — 需要的话用 /sybermem-habit 一步确认（会问你记成习惯还是项目约定）"
}

async function handleSessionCreated(args: PluginArgs, root: string, sessionID: string): Promise<void> {
  // Version nudge fires independently of conclusions: an outdated project should
  // be flagged even before it has any recorded memory. Fail-open and throttled.
  const versionNudge = updateNudgeMessage(root)
  if (versionNudge) throttledToast(args.client, "version-outdated", versionNudge)

  const parsed = parseIndex(root)
  if (!parsed || parsed.conclusions.length === 0) return
  // Mark this session so the first system-transform turn injects model-visible
  // startup context (key conclusions / phase / next-step), not just a toast.
  if (sessionID) markPendingStartup(sessionID)
  const stale = await detectStaleSignal(args.$, root)
  const staleNote = stale.stale ? ` (phase-index ${stale.commitsAhead} commits behind)` : ""
  const commitsSinceRecord = await countCommitsSinceLastRecord(args.$, root)
  const recordNote = commitsSinceRecord >= 3 ? `. ${commitsSinceRecord} commits since last record — consider /sybermem-record` : ""
  const ahaMarker = stale.stale || commitsSinceRecord >= 3 ? "⭐ " : ""
  await args.client.tui.showToast({ body: { message: `${ahaMarker}SyberMem: loaded ${parsed.conclusions.length} key conclusions${staleNote}${recordNote}`, variant: "info" } })
}

async function maybeToastRecallHealth(args: PluginArgs, root: string): Promise<void> {
  try {
    const health = parseRecallHealth(await memoryStatsText(args.$, root))
    if (!health) return
    const message = lowSignalRecallToast(health)
    if (message) throttledToast(args.client, "recall-health", message)
  } catch {
    // Advisory only: recall-health must never block or reject the idle handler.
  }
}

// Proactive "you have undigested work" heads-up. Reads the same digest-governance JSON
// the compaction/startup stale-digest check uses (single source of truth in core), so
// there is no duplicated coverage logic here. Fires only above the backlog threshold,
// throttled, and fail-open so it never blocks idle handling.
async function maybeToastDigestBacklog(args: PluginArgs, root: string): Promise<void> {
  try {
    const backlog = parseDigestBacklog(await digestStatusText(args.$, root))
    if (!backlog) return
    const message = digestBacklogToast(backlog)
    if (message) throttledToast(args.client, "digest-backlog", message)
  } catch {
    // Advisory only: digest backlog must never block or reject the idle handler.
  }
}

// At idle, turn this session's accumulated recall injections + edits into one
// bounded recall-outcome journal entry, then reset the session accumulator.
// Fail-open: relevance evidence is advisory and must never block idle handling.
async function flushSessionRelevance(args: PluginArgs, root: string, sessionID: string): Promise<void> {
  if (!sessionID) return
  try {
    const activity = getSessionActivity(sessionID)
    await flushRecallOutcome(args.$, root, activity, sessionID)
  } catch {
    // Relevance measurement is best-effort; swallow all errors.
  } finally {
    resetSessionActivity(sessionID)
  }
}

function deriveActivitySignal(sessionID: string): { toolSignal: "tests_passed" | "build_ok" | null; todoCompletedBatches: number; editFocus: string | null } {
  const activity = getSessionActivity(sessionID)
  let editFocus: string | null = null
  let topCount = 1
  for (const [file, count] of activity.editedFiles) {
    if (count > topCount) {
      topCount = count
      editFocus = file
    }
  }
  return { toolSignal: activity.lastToolSignal, todoCompletedBatches: activity.todoCompletedBatches, editFocus }
}

async function handleSessionIdle(args: PluginArgs, root: string, sessionID: string): Promise<void> {
  const trail = trailFiles(await getChangedFiles(args.$, root))
  if (trail.length === 0) return
  const fingerprint = JSON.stringify(trail)
  const state = loadNudgeState(root)
  if (state.lastFingerprint === fingerprint) return
  if (overlapsRecentAutoTrails(root, trail)) {
    saveNudgeState(root, { ...state, lastFingerprint: fingerprint })
    return
  }
  const commitsSince = await countCommitsSinceLastRecord(args.$, root)
  const activity = sessionID ? deriveActivitySignal(sessionID) : undefined
  const followup = classifyFollowup(trail, commitsSince, state, activity)
  const today = new Date().toISOString().split("T")[0]
  appendAutoTrailJournal(root, today, trail, detectHighLevelAreas(trail), followup.type)
  const windows = { ...(state.theme_recent_stops ?? {}) }
  windows[followup.themeKey] = [...(windows[followup.themeKey] ?? []), today].slice(-THEME_WINDOW_SIZE)
  const digestGuard = { ...(state.digest_nudged_at_window_len ?? {}) }
  if (followup.type === "digest") digestGuard[followup.themeKey] = windows[followup.themeKey].length
  saveNudgeState(root, { ...state, lastFingerprint: fingerprint, lastNudgeCommitCount: commitsSince, theme_recent_stops: windows, digest_nudged_at_window_len: digestGuard, last_theme: followup.themeKey, last_nudge_type: followup.type, last_nudge: followup.type === "none" ? state.last_nudge : { platform: "opencode", type: followup.type, theme: followup.themeKey, date: today } })
  if (followup.type !== "none") await args.client.tui.showToast({ body: { message: followup.message ?? "SyberMem: consider recording this work.", variant: "info" } })
}

export const SyberMemPlugin: Plugin = async ({ $, directory, client }: PluginArgs) => {
  const args = { $, directory, client }
  const root = resolveRoot(directory)
  return {
    event: async ({ event }: EventInput) => {
      if (!root) return
      const sessionID = event.properties?.info?.id ?? ""
      if (event.type === "session.created") await handleSessionCreated(args, root, sessionID)
      // Edit/activity accumulation must never reject the event callback, so each
      // in-memory mutation path is independently fail-open.
      if (event.type === "file.edited") {
        try {
          const file = extractEditedFile(event.properties)
          if (file && sessionID) recordEditedFile(sessionID, file)
        } catch { /* activity capture is best-effort */ }
      }
      if (event.type === "todo.updated" && sessionID) {
        try { recordTodoUpdate(sessionID, event.properties) } catch { /* best-effort */ }
      }
      if (event.type === "session.idle") {
        // Each idle step is independently fail-open so an auto-trail/git failure
        // cannot suppress relevance flushing or the recall-health advisory.
        try { await handleSessionIdle(args, root, sessionID) } catch { /* nudge is advisory */ }
        await flushSessionRelevance(args, root, sessionID)
        await maybeToastRecallHealth(args, root)
        await maybeToastDigestBacklog(args, root)
      }
    },
    "tool.execute.after": async (input: unknown, output: unknown) => {
      if (!root) return
      try {
        const sessionID = readSessionID(input)
        if (sessionID) recordToolExecution(sessionID, input, output)
      } catch { /* tool-signal capture is best-effort */ }
    },
    "chat.message": async ({ sessionID }: { readonly sessionID: string }, output: ChatMessageOutput) => {
      if (!root) return
      const text = extractPromptText(output)
      if (!text) return
      await captureRecordIntentWithCli(args.$, root, text)
      // Passively capture a candidate-only user-habit intent (Core writes it to
      // the user-level intent file; never an active habit). This makes durable
      // preferences discoverable without the user remembering to run a command.
      const habitIntent = await captureHabitIntentWithCli(args.$, root, text)
      const packets = await collectPromptPackets(args.$, root, text)
      appendRecallDebug(root, packets)
      // Remember which records were injected this session so idle can later
      // check whether any of them lined up with edited files (relevance).
      if (sessionID) recordInjectedRecords(sessionID, packets)
      stashPromptPackets(sessionID, packets)
      // Surface the "this looks like a reusable preference" signal. Prefer the
      // Core capture (a real candidate was written), falling back to the packet
      // heuristic, so the user knows a habit candidate is ready to confirm.
      const summary = classifyPackets(packets)
      if (habitIntent.captured || summary.habitCandidate) {
        throttledToast(args.client, "habit-candidate", habitCandidateToast(habitIntent))
      }
    },
    "experimental.chat.system.transform": async ({ sessionID }: { readonly sessionID?: string }, output: SystemTransformOutput) => {
      if (!root) return
      // Inject per-prompt recall/habit packets first, THEN prepend startup context,
      // so on a fresh session's first turn the startup packet ends up on top rather
      // than being buried under recall hints.
      const packets = RECALL_STASH.get(sessionID ?? "") ?? []
      const summary = injectStashedPromptPackets(sessionID ?? "", output)
      let startup = ""
      // First turn of a freshly created session: prepend bounded startup context so
      // key conclusions/phase/next-step are model-visible, not just a toast. One-shot.
      if (consumePendingStartup(sessionID ?? "")) {
        startup = await buildStartupContext(args.$, root) ?? ""
        if (startup) {
          prependStartupContext(output, startup)
          throttledToast(args.client, "startup-context", "⭐ SyberMem: injected project startup context into this session")
        }
      }
      appendMemoryUsage(root, { sessionID: sessionID ?? "", packets, startup })
      // Toast at injection time (not capture time) so the user only sees a
      // notice when context actually reached the model. Recall and habit get
      // SEPARATE, distinctly-marked toasts so an applied user habit is as
      // perceptible as recall, instead of being merged into one notice. The
      // habit-candidate case stays on chat.message's own "save this" toast.
      if (!summary.habitCandidate) {
        const recallMessage = recallToastMessage(summary)
        if (recallMessage) throttledToast(args.client, "recall-injected", recallMessage)
        const habitMessage = habitToastMessage(summary)
        if (habitMessage) throttledToast(args.client, "habit-injected", habitMessage)
        const normMessage = normToastMessage(summary)
        if (normMessage) throttledToast(args.client, "norm-injected", normMessage)
      }
      // Arm the opt-in reply marker for this turn (no-op unless SYBERMEM_REPLY_MARKER
      // is set and material was actually injected).
      armReplyMarker(sessionID ?? "", summary.recallCount, summary.habitCount)
    },
    "experimental.text.complete": async (
      input: { readonly sessionID: string; readonly messageID: string; readonly partID: string },
      output: { text: string },
    ) => {
      if (!root) return
      // Opt-in only (default OFF). Prepends one marker line to the first assistant
      // text part of a turn that actually received injected context. Fail-open.
      try {
        output.text = applyReplyMarker(input.sessionID, input.messageID, output.text)
      } catch { /* reply marker is optional UX, never block the reply */ }
    },
    "experimental.session.compacting": async (_input: unknown, output: { readonly context: string[] }) => {
      if (!root) return
      const context = await buildCompactionContext(args.$, root)
      if (context) output.context.push(context)
    },
  }
}
