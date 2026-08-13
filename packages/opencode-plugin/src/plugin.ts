import type { Plugin } from "@opencode-ai/plugin"
import { appendAutoTrailJournal, classifyFollowup, countCommitsSinceLastRecord, detectHighLevelAreas, getChangedFiles, overlapsRecentAutoTrails, THEME_WINDOW_SIZE, trailFiles } from "./followup"
import { buildCompactionContext } from "./compaction"
import { detectStaleSignal, parseIndex } from "./project_state"
import { resolveRoot } from "./runtime"
import { loadNudgeState, saveNudgeState } from "./state"
import { appendRecallDebug } from "./recall_debug"
import { captureRecordIntentWithCli } from "./record_intent"
import { collectPromptPackets, extractPromptText, injectStashedPromptPackets, stashPromptPackets, type ChatMessageOutput, type SystemTransformOutput } from "./prompt_context"

interface ToastClient { readonly tui: { readonly showToast: (input: { readonly body: { readonly message: string; readonly variant: "info" } }) => Promise<void> } }
interface PluginArgs { readonly $: import("./runtime").Shell; readonly directory: string; readonly client: ToastClient }
interface EventInput { readonly event: { readonly type: string } }

async function handleSessionCreated(args: PluginArgs, root: string): Promise<void> {
  const parsed = parseIndex(root)
  if (!parsed || parsed.conclusions.length === 0) return
  const stale = await detectStaleSignal(args.$, root)
  const staleNote = stale.stale ? ` (phase-index ${stale.commitsAhead} commits behind)` : ""
  const commitsSinceRecord = await countCommitsSinceLastRecord(args.$, root)
  const recordNote = commitsSinceRecord >= 3 ? `. ${commitsSinceRecord} commits since last record — consider /sybermem-record` : ""
  const ahaMarker = stale.stale || commitsSinceRecord >= 3 ? "⭐ " : ""
  await args.client.tui.showToast({ body: { message: `${ahaMarker}SyberMem: loaded ${parsed.conclusions.length} key conclusions${staleNote}${recordNote}`, variant: "info" } })
}

async function handleSessionIdle(args: PluginArgs, root: string): Promise<void> {
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
  const followup = classifyFollowup(trail, commitsSince, state)
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
      if (event.type === "session.created") await handleSessionCreated(args, root)
      if (event.type === "session.idle") await handleSessionIdle(args, root)
    },
    "chat.message": async ({ sessionID }: { readonly sessionID: string }, output: ChatMessageOutput) => {
      if (!root) return
      const text = extractPromptText(output)
      if (!text) return
      await captureRecordIntentWithCli(args.$, root, text)
      const packets = await collectPromptPackets(args.$, root, text)
      appendRecallDebug(root, packets)
      stashPromptPackets(sessionID, packets)
    },
    "experimental.chat.system.transform": async ({ sessionID }: { readonly sessionID?: string }, output: SystemTransformOutput) => {
      if (!root) return
      injectStashedPromptPackets(sessionID ?? "", output)
    },
    "experimental.session.compacting": async (_input: unknown, output: { readonly context: string[] }) => {
      if (!root) return
      const context = await buildCompactionContext(args.$, root)
      if (context) output.context.push(context)
    },
  }
}
