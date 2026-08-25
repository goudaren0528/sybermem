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

const LAST_TOAST = new Map<string, number>()
const TOAST_COOLDOWN_MS = 30_000

export function throttledToast(client: ToastClient, key: string, message: string): void {
  const now = Date.now()
  const last = LAST_TOAST.get(key) ?? 0
  if (now - last < TOAST_COOLDOWN_MS) return
  LAST_TOAST.set(key, now)
  void showToast(client, message)
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
