import type { Plugin } from "@opencode-ai/plugin"
import { appendAutoTrailJournal, classifyFollowup, countCommitsSinceLastRecord, detectHighLevelAreas, getChangedFiles, overlapsRecentAutoTrails, THEME_WINDOW_SIZE, trailFiles } from "./followup"
import { buildCompactionContext } from "./compaction"
import { detectStaleSignal, parseIndex } from "./project_state"
import { digestStatusText, memoryStatsText, resolveRoot } from "./runtime"
import { digestBacklogToast, parseDigestBacklog } from "./digest_backlog_signal"
import { compactJsonlJournal, loadNudgeState, saveNudgeState } from "./state"
import { appendRecallDebug } from "./recall_debug"
import { captureRecordIntentWithCli } from "./record_intent"
import { classifyPackets, collectPromptPackets, extractPromptText, injectStashedPromptPackets, RECALL_STASH, stashPromptPackets, type ChatMessageOutput, type SystemTransformOutput } from "./prompt_context"
import { appendStartupContext, buildStartupContext, consumePendingStartup, markPendingStartup } from "./startup_context"
import { lowSignalRecallToast, parseRecallHealth } from "./recall_health_signal"
import { extractEditedFile, getSessionActivity, recordEditedFile, recordInjectedRecords, recordMemoryUsage, recordToolExecution, recordTodoUpdate, resetSessionActivity } from "./session_activity"
import { flushRecallOutcome } from "./recall_outcome"
import { captureHabitIntentWithCli } from "./habit_intent"
import { updateNudgeMessage } from "./version_signal"
import { evaluateRemoteVersion } from "./remote_version"
import { applyReplyMarker, armReplyMarker } from "./reply_marker"
import { appendMemoryUsage } from "./memory_usage"
import { buildPromptInjectionToastSummary, enqueueToast, habitCandidateToast, promptInjectionToastMessage, throttledToast, type ToastClient } from "./injection_toast"

interface PluginArgs { readonly $: import("./runtime").Shell; readonly directory: string; readonly client: ToastClient }
interface EventInput { readonly event: { readonly type: string; readonly properties?: { readonly info?: { readonly id?: string } } } }

function readSessionID(source: unknown): string {
  if (typeof source !== "object" || source === null) return ""
  for (const key of ["sessionID", "sessionId", "session"]) {
    const value = Reflect.get(source, key)
    if (typeof value === "string" && value) return value
  }
  return ""
}

async function handleSessionCreated(args: PluginArgs, root: string, sessionID: string): Promise<void> {
  // Version nudge fires independently of conclusions: an outdated project should
  // be flagged even before it has any recorded memory. Fail-open and throttled.
  const versionNudge = updateNudgeMessage(root)
  if (versionNudge) throttledToast(args.client, "version-outdated", versionNudge)

  // Remote-version awareness: warn when GitHub `main` publishes a newer SyberMem
  // than is installed here. Reads a local cache (never blocks) and kicks off a
  // fire-and-forget refresh when the cache is stale. Distinct key/semantics from
  // the project-vs-installed nudge above. Fail-open.
  const remoteNudge = evaluateRemoteVersion()
  if (remoteNudge) throttledToast(args.client, "remote-outdated", remoteNudge)

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
  enqueueToast(args.client, `${ahaMarker}SyberMem: loaded ${parsed.conclusions.length} key conclusions${staleNote}${recordNote}`)
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
    compactJsonlJournal(root, ".memory-usage.jsonl", 200)
    compactJsonlJournal(root, ".recall-outcomes.jsonl", 200)
    compactJsonlJournal(root, ".recall-debug.jsonl", 200)
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
  if (followup.type !== "none") enqueueToast(args.client, followup.message ?? "SyberMem: consider recording this work.")
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
      // Prompt-cache-friendly injection: both blocks are APPENDED as trailing system
      // blocks (never mutating system[0], OpenCode's stable base header). Append the
      // more stable startup context FIRST, then the per-turn recall, so volatile
      // recall lands at the very end and the cacheable prefix stays byte-identical.
      const packets = RECALL_STASH.get(sessionID ?? "") ?? []
      let startup = ""
      // First turn of a freshly created session: append bounded startup context so
      // key conclusions/phase/next-step are model-visible, not just a toast. One-shot.
      if (consumePendingStartup(sessionID ?? "")) {
        startup = await buildStartupContext(args.$, root) ?? ""
        if (startup) {
          appendStartupContext(output, startup)
          throttledToast(args.client, "startup-context", "⭐ SyberMem: injected project startup context into this session")
        }
      }
      const summary = injectStashedPromptPackets(sessionID ?? "", output)
      const usageEntry = appendMemoryUsage(root, { sessionID: sessionID ?? "", packets, startup })
      if (sessionID) recordMemoryUsage(sessionID, usageEntry)
      const promptInjectionToast = buildPromptInjectionToastSummary(summary, usageEntry)
      if (promptInjectionToast) {
        throttledToast(args.client, "prompt-memory-injected", promptInjectionToastMessage(promptInjectionToast))
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
