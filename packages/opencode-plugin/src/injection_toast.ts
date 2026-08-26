import type { MemoryUsageEntry } from "./memory_usage"
import type { InjectionSummary } from "./prompt_context"

export interface ToastClient {
  readonly tui: {
    readonly showToast: (input: {
      readonly body: {
        readonly message: string
        readonly variant: "info"
      }
    }) => Promise<void>
  }
}

export interface PromptInjectionLaneCount {
  readonly lane: "recall" | "habit" | "norm"
  readonly count: number
}

export interface PromptInjectionToastSummary {
  readonly totalItems: number
  readonly totalChars: number
  readonly laneCounts: readonly PromptInjectionLaneCount[]
}

async function showToast(client: ToastClient, message: string): Promise<void> {
  try {
    await client.tui.showToast({ body: { message, variant: "info" } })
  } catch {
    // Fail open: toasts are optional UX, never block the prompt flow.
  }
}

// Serial toast queue with a minimum on-screen gap. OpenCode's showToast replaces
// the current toast rather than queueing, so several toasts fired in the same tick
// (e.g. idle emits nudge + recall-health + digest-backlog, or the first transform
// emits startup + prompt-memory) would clobber each other and only the last would
// be seen. We drain toasts one at a time with a gap so each is actually perceptible.
const TOAST_MIN_GAP_MS = 2_500
const TOAST_QUEUE: Array<{ readonly client: ToastClient; readonly message: string }> = []
let draining = false

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function drainToastQueue(): Promise<void> {
  if (draining) return
  draining = true
  try {
    while (TOAST_QUEUE.length > 0) {
      const next = TOAST_QUEUE.shift()
      if (!next) break
      await showToast(next.client, next.message)
      if (TOAST_QUEUE.length > 0) await sleep(TOAST_MIN_GAP_MS)
    }
  } finally {
    draining = false
  }
}

// Enqueue a toast for serial delivery. Fire-and-forget: never blocks the caller,
// and drain errors are swallowed so toasts stay optional UX.
export function enqueueToast(client: ToastClient, message: string): void {
  TOAST_QUEUE.push({ client, message })
  void drainToastQueue().catch(() => {})
}

const LAST_TOAST = new Map<string, number>()
const TOAST_COOLDOWN_MS = 30_000

export function throttledToast(client: ToastClient, key: string, message: string): void {
  const now = Date.now()
  const last = LAST_TOAST.get(key) ?? 0
  if (now - last < TOAST_COOLDOWN_MS) return
  LAST_TOAST.set(key, now)
  enqueueToast(client, message)
}

export function buildPromptInjectionToastSummary(summary: InjectionSummary, usageEntry: MemoryUsageEntry): PromptInjectionToastSummary | null {
  const laneCounts: PromptInjectionLaneCount[] = []
  if (summary.recallCount > 0) laneCounts.push({ lane: "recall", count: summary.recallCount })
  if (summary.habitCount > 0) laneCounts.push({ lane: "habit", count: summary.habitCount })
  if (summary.normCount > 0) laneCounts.push({ lane: "norm", count: summary.normCount })
  if (laneCounts.length === 0) return null
  return {
    totalItems: usageEntry.recall_items + usageEntry.habit_items + usageEntry.norm_items,
    totalChars: usageEntry.recall_chars + usageEntry.habit_chars + usageEntry.norm_chars,
    laneCounts,
  }
}

export function promptInjectionToastMessage(summary: PromptInjectionToastSummary): string {
  const laneCounts = summary.laneCounts.map(({ lane, count }) => `${lane}=${count}`).join(", ")
  return `⭐ SyberMem 注入摘要: items=${summary.totalItems}, chars=${summary.totalChars}, ${laneCounts}`
}

export function habitCandidateToast(habitIntent: import("./habit_intent").HabitIntentResult): string {
  if (habitIntent.captured && habitIntent.suggestedScope === "project") {
    return "💡 SyberMem 发现一条像是本项目的约定 — 可用 /sybermem-record 记为决策/需求，或 /sybermem-habit 确认"
  }
  if (habitIntent.captured && habitIntent.suggestedScope === "user") {
    return "💡 SyberMem 发现一条可复用的个人习惯 — 需要的话用 /sybermem-habit 一步确认"
  }
  return "💡 SyberMem 发现一条可复用的偏好/规范 — 需要的话用 /sybermem-habit 一步确认（会问你记成习惯还是项目约定）"
}
