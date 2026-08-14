import type { Plugin } from "@opencode-ai/plugin"
import { appendAutoTrailJournal, classifyFollowup, countCommitsSinceLastRecord, detectHighLevelAreas, getChangedFiles, overlapsRecentAutoTrails, THEME_WINDOW_SIZE, trailFiles } from "./followup"
import { buildCompactionContext } from "./compaction"
import { detectStaleSignal, parseIndex } from "./project_state"
import { memoryStatsText, resolveRoot } from "./runtime"
import { loadNudgeState, saveNudgeState } from "./state"
import { appendRecallDebug } from "./recall_debug"
import { captureRecordIntentWithCli } from "./record_intent"
import { classifyPackets, collectPromptPackets, extractPromptText, injectStashedPromptPackets, stashPromptPackets, type ChatMessageOutput, type InjectionSummary, type SystemTransformOutput } from "./prompt_context"
import { buildStartupContext, consumePendingStartup, markPendingStartup, prependStartupContext } from "./startup_context"
import { lowSignalRecallToast, parseRecallHealth } from "./recall_health_signal"
import { extractEditedFile, getSessionActivity, recordEditedFile, recordInjectedRecords, recordToolExecution, recordTodoUpdate, resetSessionActivity } from "./session_activity"
import { flushRecallOutcome } from "./recall_outcome"

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

function describeInjection(summary: InjectionSummary): string {
  const parts: string[] = []
  if (summary.recallCount > 0) parts.push(`${summary.recallCount} recall hint${summary.recallCount === 1 ? "" : "s"}`)
  if (summary.habitCount > 0) parts.push(`${summary.habitCount} habit reminder${summary.habitCount === 1 ? "" : "s"}`)
  if (parts.length === 0) return ""
  return parts.join(" + ")
}

async function handleSessionCreated(args: PluginArgs, root: string, sessionID: string): Promise<void> {
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
      if (event.type === "file.edited") {
        const file = extractEditedFile(event.properties)
        if (file && sessionID) recordEditedFile(sessionID, file)
      }
      if (event.type === "todo.updated" && sessionID) recordTodoUpdate(sessionID, event.properties)
      if (event.type === "session.idle") {
        // Recall-health advisory runs independently of the file-change nudge path,
        // so it is not suppressed by "no changed files" / duplicate-fingerprint gates.
        await handleSessionIdle(args, root, sessionID)
        await flushSessionRelevance(args, root, sessionID)
        await maybeToastRecallHealth(args, root)
      }
    },
    "tool.execute.after": async (input: unknown, output: unknown) => {
      if (!root) return
      const sessionID = readSessionID(input)
      if (sessionID) recordToolExecution(sessionID, input, output)
    },
    "chat.message": async ({ sessionID }: { readonly sessionID: string }, output: ChatMessageOutput) => {
      if (!root) return
      const text = extractPromptText(output)
      if (!text) return
      await captureRecordIntentWithCli(args.$, root, text)
      const packets = await collectPromptPackets(args.$, root, text)
      appendRecallDebug(root, packets)
      // Remember which records were injected this session so idle can later
      // check whether any of them lined up with edited files (relevance).
      if (sessionID) recordInjectedRecords(sessionID, packets)
      stashPromptPackets(sessionID, packets)
      // Make a silently dropped "this looks like a reusable preference" signal
      // visible, so the user knows they can persist it as a habit.
      const summary = classifyPackets(packets)
      if (summary.habitCandidate) {
        throttledToast(args.client, "habit-candidate", "💡 Detected a reusable preference — save it with /sybermem-habit")
      }
    },
    "experimental.chat.system.transform": async ({ sessionID }: { readonly sessionID?: string }, output: SystemTransformOutput) => {
      if (!root) return
      // Inject per-prompt recall/habit packets first, THEN prepend startup context,
      // so on a fresh session's first turn the startup packet ends up on top rather
      // than being buried under recall hints.
      const summary = injectStashedPromptPackets(sessionID ?? "", output)
      // First turn of a freshly created session: prepend bounded startup context so
      // key conclusions/phase/next-step are model-visible, not just a toast. One-shot.
      if (consumePendingStartup(sessionID ?? "")) {
        const startup = await buildStartupContext(args.$, root)
        if (startup) {
          prependStartupContext(output, startup)
          throttledToast(args.client, "startup-context", "⭐ SyberMem: injected project startup context into this session")
        }
      }
      // Toast at injection time (not capture time) so the user only sees a
      // notice when context actually reached the model — makes recall/habit
      // injection perceptible in-session, not just at session start. The
      // habit-candidate case is excluded here because chat.message already
      // surfaces that as its own "save this preference" toast.
      if (summary.injected && !summary.habitCandidate) {
        throttledToast(args.client, "recall-injected", `⭐ SyberMem: injected ${describeInjection(summary)} into this prompt`)
      }
    },
    "experimental.session.compacting": async (_input: unknown, output: { readonly context: string[] }) => {
      if (!root) return
      const context = await buildCompactionContext(args.$, root)
      if (context) output.context.push(context)
    },
  }
}
