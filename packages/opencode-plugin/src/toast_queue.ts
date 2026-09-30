import type { FeedbackNotice } from "./v2_feedback"

export const SUMMARY_DURATION_MS = 3500
export const ADVISORY_DURATION_MS = 5000
export const MAX_WAITING_QUEUE = 3
export const WAITING_TTL_MS = 15_000
export const MAX_MESSAGE_CHARS = 240

export type ToastCategory = "version" | "summary" | "habit" | "idle"

export interface ToastClock {
  now(): number
  setTimeout(callback: () => void, ms: number): unknown
  clearTimeout(handle: unknown): void
  setInterval?(callback: () => void, ms: number): unknown
  clearInterval?(handle: unknown): void
}

export interface ToastPayload {
  title: string
  message: string
  variant: "info"
  duration: number
  sessionID: string
}

export interface ToastQueueOptions {
  clock?: ToastClock
  isActive: (sessionID: string) => boolean
  showToast: (input: ToastPayload) => void
}

interface QueuedToast {
  sessionID: string
  kind: FeedbackNotice["kind"]
  category: ToastCategory
  priority: number
  duration: number
  message: string
  messageID: string
  enqueuedAt: number
  order: number
}

const defaultClock: ToastClock = {
  now: () => Date.now(),
  setTimeout: (callback, ms) => setTimeout(callback, ms),
  clearTimeout: (handle) => clearTimeout(handle as ReturnType<typeof setTimeout>),
  setInterval: (callback, ms) => setInterval(callback, ms),
  clearInterval: (handle) => clearInterval(handle as ReturnType<typeof setInterval>),
}

/**
 * Classifies a notice into priority tiers using existing RPC fields (`kind` and `message`).
 * Limitation: because V2 RPC `notice` schema currently fixes `kind` to `"summary" | "advisory"`
 * with `additionalProperties: false`, advisory subtypes (`version` > `habit` > `idle`) are
 * inferred from message patterns until the server RPC adds an explicit `category` field.
 */
export function classifyNotice(notice: Pick<FeedbackNotice, "kind" | "message">): {
  category: ToastCategory
  priority: number
  duration: number
} {
  const duration = notice.kind === "summary" ? SUMMARY_DURATION_MS : ADVISORY_DURATION_MS
  if (notice.kind === "summary") {
    return { category: "summary", priority: 3, duration }
  }
  const message = notice.message ?? ""
  if (/\/sybermem-update\b|is installed;|remote main is|版本落后|最新版|更新/i.test(message)) {
    return { category: "version", priority: 4, duration }
  }
  if (/injected project startup context|项目启动上下文|已载入项目启动|注入摘要/i.test(message)) {
    return { category: "summary", priority: 3, duration }
  }
  if (/\/sybermem-habit\b|习惯|偏好\/规范|待确认的习惯候选/i.test(message)) {
    return { category: "habit", priority: 2, duration }
  }
  return { category: "idle", priority: 1, duration }
}

export function createToastQueue(options: ToastQueueOptions) {
  const clock = options.clock ?? defaultClock
  let activeItem: QueuedToast | null = null
  let activeTimer: unknown = null
  let waiting: QueuedToast[] = []
  let orderCounter = 0
  let stopped = false

  const clearTimer = () => {
    if (activeTimer !== null) {
      clock.clearTimeout(activeTimer)
      activeTimer = null
    }
  }

  const clear = () => {
    clearTimer()
    activeItem = null
    waiting = []
  }

  const purgeExpired = (now: number) => {
    if (waiting.length === 0) return
    waiting = waiting.filter((item) => now - item.enqueuedAt <= WAITING_TTL_MS)
  }

  const sortWaiting = () => {
    waiting.sort((a, b) => {
      if (b.priority !== a.priority) return b.priority - a.priority
      return a.order - b.order
    })
  }

  const isDuplicate = (candidate: QueuedToast): boolean => {
    const matches = (existing: QueuedToast) =>
      existing.sessionID === candidate.sessionID &&
      existing.kind === candidate.kind &&
      (existing.message === candidate.message ||
        (Boolean(existing.messageID) && existing.messageID === candidate.messageID))

    if (activeItem && matches(activeItem)) return true
    return waiting.some(matches)
  }

  const displayNext = () => {
    activeTimer = null
    activeItem = null
    if (stopped) return
    purgeExpired(clock.now())
    if (waiting.length === 0) return
    const next = waiting.shift()!
    if (!options.isActive(next.sessionID)) {
      clear()
      return
    }
    showNow(next)
  }

  const showNow = (item: QueuedToast) => {
    if (stopped || !options.isActive(item.sessionID)) {
      clear()
      return
    }
    activeItem = item
    try {
      options.showToast({
        title: "SyberMem",
        message: item.message,
        variant: "info",
        duration: item.duration,
        sessionID: item.sessionID,
      })
    } catch {
      // Fail-open: never block TUI if toast rendering fails.
    }
    activeTimer = clock.setTimeout(displayNext, item.duration)
  }

  return {
    enqueue(notice: FeedbackNotice) {
      if (stopped || !notice || typeof notice.sessionID !== "string" || !notice.sessionID) return
      if (typeof notice.message !== "string") return
      const trimmed = notice.message.trim().slice(0, MAX_MESSAGE_CHARS)
      if (!trimmed) return
      if (!options.isActive(notice.sessionID)) {
        clear()
        return
      }
      if (activeItem && activeItem.sessionID !== notice.sessionID) {
        clear()
      }

      const now = clock.now()
      purgeExpired(now)

      const { category, priority, duration } = classifyNotice({ kind: notice.kind, message: trimmed })
      const item: QueuedToast = {
        sessionID: notice.sessionID,
        kind: notice.kind,
        category,
        priority,
        duration,
        message: trimmed,
        messageID: typeof notice.messageID === "string" ? notice.messageID : "",
        enqueuedAt: now,
        order: ++orderCounter,
      }

      // S10: A newer summary replaces an unshown summary waiting in the queue.
      if (item.kind === "summary") {
        const existingIndex = waiting.findIndex((w) => w.kind === "summary" && w.sessionID === item.sessionID)
        if (existingIndex !== -1) {
          waiting[existingIndex] = item
          sortWaiting()
          return
        }
      }

      if (isDuplicate(item)) return

      if (!activeItem) {
        showNow(item)
        return
      }

      if (waiting.length >= MAX_WAITING_QUEUE) {
        // Overflow policy: evict lowest priority first; break ties by oldest arrival (enqueuedAt, then order).
        const pool = [...waiting, item]
        let victim = pool[0]
        for (let i = 1; i < pool.length; i++) {
          const candidate = pool[i]
          if (
            candidate.priority < victim.priority ||
            (candidate.priority === victim.priority &&
              (candidate.enqueuedAt < victim.enqueuedAt ||
                (candidate.enqueuedAt === victim.enqueuedAt && candidate.order < victim.order)))
          ) {
            victim = candidate
          }
        }
        if (victim === item) return
        waiting = waiting.filter((w) => w !== victim)
      }

      waiting.push(item)
      sortWaiting()
    },
    clear,
    dispose() {
      stopped = true
      clear()
    },
    size() {
      return waiting.length
    },
    isShowing() {
      return activeItem !== null
    },
  }
}
