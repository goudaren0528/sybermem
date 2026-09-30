import { test, expect, describe } from "bun:test"
import { createToastQueue, classifyNotice, type ToastClock, type ToastPayload } from "../src/toast_queue"
import { setupSyberMemTui } from "../src/tui"
import { feedbackRpc, type FeedbackNotice } from "../src/v2_feedback"

class FakeClock implements ToastClock {
  private currentTime = 0
  private nextTimerId = 1
  private timers = new Map<number, { callback: () => void; triggerTime: number }>()

  constructor() {
    this.now = this.now.bind(this)
    this.setTimeout = this.setTimeout.bind(this)
    this.clearTimeout = this.clearTimeout.bind(this)
    this.setInterval = this.setInterval.bind(this)
    this.clearInterval = this.clearInterval.bind(this)
  }

  now(): number {
    return this.currentTime
  }

  setTimeout(callback: () => void, ms: number): number {
    const id = this.nextTimerId++
    this.timers.set(id, { callback, triggerTime: this.currentTime + Math.max(0, ms) })
    return id
  }

  clearTimeout(handle: unknown): void {
    if (typeof handle === "number") {
      this.timers.delete(handle)
    }
  }

  setInterval(callback: () => void, ms: number): number {
    const id = this.nextTimerId++
    const repeat = () => {
      if (this.timers.has(id)) {
        callback()
        this.timers.set(id, { callback: repeat, triggerTime: this.currentTime + Math.max(1, ms) })
      }
    }
    this.timers.set(id, { callback: repeat, triggerTime: this.currentTime + Math.max(1, ms) })
    return id
  }

  clearInterval(handle: unknown): void {
    if (typeof handle === "number") {
      this.timers.delete(handle)
    }
  }

  advance(ms: number) {
    const targetTime = this.currentTime + ms
    while (true) {
      let earliestId: number | null = null
      let earliestTime = Number.POSITIVE_INFINITY
      for (const [id, timer] of this.timers.entries()) {
        if (timer.triggerTime <= targetTime && timer.triggerTime < earliestTime) {
          earliestId = id
          earliestTime = timer.triggerTime
        }
      }
      if (earliestId === null) break
      const timer = this.timers.get(earliestId)!
      this.timers.delete(earliestId)
      this.currentTime = timer.triggerTime
      timer.callback()
    }
    this.currentTime = targetTime
  }

  pendingTimers(): number {
    return this.timers.size
  }
}

const sampleNotice = (
  sessionID: string,
  kind: "summary" | "advisory",
  message: string,
  messageID = "m1",
  sequence = 1,
): FeedbackNotice => ({
  epoch: "epoch-1",
  sessionID,
  sequence,
  kind,
  message,
  messageID,
  totalItems: 1,
  totalChars: 30,
})

describe("Toast Queue and TUI Pacing", () => {
  test("classifyNotice accurately parses priority and duration from notice fields", () => {
    // Summary
    const summary = classifyNotice({ kind: "summary", message: "⭐ SyberMem 注入摘要: items=2" })
    expect(summary.category).toBe("summary")
    expect(summary.priority).toBe(3)
    expect(summary.duration).toBe(3500)

    // Version advisory
    const version = classifyNotice({
      kind: "advisory",
      message: "⭐ SyberMem 0.7.0 is installed; Run /sybermem-update to apply the latest fixes.",
    })
    expect(version.category).toBe("version")
    expect(version.priority).toBe(4)
    expect(version.duration).toBe(5000)

    // Habit advisory
    const habit = classifyNotice({
      kind: "advisory",
      message: "💡 SyberMem 有一条待确认的习惯候选 — 用 /sybermem-habit 确认",
    })
    expect(habit.category).toBe("habit")
    expect(habit.priority).toBe(2)
    expect(habit.duration).toBe(5000)

    // Idle / other advisory
    const idle = classifyNotice({
      kind: "advisory",
      message: "SyberMem: consider recording this work.",
    })
    expect(idle.category).toBe("idle")
    expect(idle.priority).toBe(1)
    expect(idle.duration).toBe(5000)
  })

  test("Pacing: summary lasts 3.5s, next toast never displays before previous finishes", () => {
    const clock = new FakeClock()
    const shown: Array<{ message: string; duration: number; time: number }> = []
    let activeSession = "session-1"

    const queue = createToastQueue({
      clock,
      isActive: (s) => s === activeSession,
      showToast: (p) => shown.push({ message: p.message, duration: p.duration, time: clock.now() }),
    })

    // Notice 1: summary (3500ms)
    queue.enqueue(sampleNotice("session-1", "summary", "Summary 1", "m1"))
    expect(shown).toHaveLength(1)
    expect(shown[0].message).toBe("Summary 1")
    expect(shown[0].duration).toBe(3500)
    expect(shown[0].time).toBe(0)

    // Notice 2: advisory arrives at t = 1000 while Notice 1 is still showing
    clock.advance(1000)
    queue.enqueue(sampleNotice("session-1", "advisory", "Habit tip: /sybermem-habit", "m2"))
    // Still only 1 shown; Notice 2 must wait
    expect(shown).toHaveLength(1)

    // Advance to t = 3499 (just before Notice 1 finishes)
    clock.advance(2499)
    expect(shown).toHaveLength(1)

    // Advance 1ms to t = 3500: Notice 1 duration finishes, Notice 2 immediately displays
    clock.advance(1)
    expect(shown).toHaveLength(2)
    expect(shown[1].message).toBe("Habit tip: /sybermem-habit")
    expect(shown[1].duration).toBe(5000)
    expect(shown[1].time).toBe(3500)

    // Notice 2 finishes at t = 8500
    clock.advance(5000)
    expect(queue.isShowing()).toBe(false)
  })

  test("Priority ordering: higher priority notice in queue jumps ahead but does NOT interrupt active toast", () => {
    const clock = new FakeClock()
    const shown: Array<{ message: string; time: number }> = []

    const queue = createToastQueue({
      clock,
      isActive: () => true,
      showToast: (p) => shown.push({ message: p.message, time: clock.now() }),
    })

    // Active toast: Idle (P3, 5000ms)
    queue.enqueue(sampleNotice("s1", "advisory", "SyberMem: consider recording this work.", "m1"))
    expect(shown.map((s) => s.message)).toEqual(["SyberMem: consider recording this work."])

    // While Idle is active at t = 500, Summary (P1) arrives
    clock.advance(500)
    queue.enqueue(sampleNotice("s1", "summary", "Summary packet", "m2"))

    // At t = 1000, Version update (P0) arrives
    clock.advance(500)
    queue.enqueue(sampleNotice("s1", "advisory", "Run /sybermem-update for version v2", "m3"))

    // Active toast is NOT interrupted at t = 1000
    expect(shown).toHaveLength(1)

    // At t = 5000, Idle finishes. Version (P0) has higher priority than Summary (P1), so Version displays next
    clock.advance(4000)
    expect(shown).toHaveLength(2)
    expect(shown[1].message).toBe("Run /sybermem-update for version v2")
    expect(shown[1].time).toBe(5000)

    // At t = 10000, Version finishes (5000ms duration). Summary displays
    clock.advance(5000)
    expect(shown).toHaveLength(3)
    expect(shown[2].message).toBe("Summary packet")
    expect(shown[2].time).toBe(10000)

    // At t = 13500, Summary finishes (3500ms duration)
    clock.advance(3500)
    expect(queue.isShowing()).toBe(false)
  })

  test("Summary replacement: newer summary replaces unshown summary waiting in queue (S10)", () => {
    const clock = new FakeClock()
    const shown: string[] = []

    const queue = createToastQueue({
      clock,
      isActive: () => true,
      showToast: (p) => shown.push(p.message),
    })

    // Active toast: version notice (5000ms)
    queue.enqueue(sampleNotice("s1", "advisory", "Run /sybermem-update", "v1"))
    expect(shown).toEqual(["Run /sybermem-update"])

    // Summary 1 arrives while version notice is showing
    clock.advance(1000)
    queue.enqueue(sampleNotice("s1", "summary", "Summary turn 1", "s1"))
    expect(queue.size()).toBe(1)

    // Summary 2 arrives before Summary 1 is shown
    clock.advance(1000)
    queue.enqueue(sampleNotice("s1", "summary", "Summary turn 2 (updated)", "s2"))
    // Queue size should still be 1 (replaced, not accumulated)
    expect(queue.size()).toBe(1)

    // When version notice completes at t = 5000, Summary 2 is shown; Summary 1 is never displayed
    clock.advance(3000)
    expect(shown).toEqual(["Run /sybermem-update", "Summary turn 2 (updated)"])
  })

  test("Queue capacity limit (<= 3) and eviction of lowest priority/stale items", () => {
    const clock = new FakeClock()
    const shown: string[] = []

    const queue = createToastQueue({
      clock,
      isActive: () => true,
      showToast: (p) => shown.push(p.message),
    })

    // Toast 1 displays immediately (5000ms)
    queue.enqueue(sampleNotice("s1", "advisory", "Active advisory", "a0"))

    // Fill waiting queue with 3 items of differing priorities
    // 1. Habit (P2)
    queue.enqueue(sampleNotice("s1", "advisory", "Habit candidate A /sybermem-habit", "h1"))
    // 2. Idle (P3 / Priority 1, oldest idle)
    clock.advance(100)
    queue.enqueue(sampleNotice("s1", "advisory", "Idle diagnostic 1", "i1"))
    // 3. Idle (P3 / Priority 1, newer idle)
    clock.advance(100)
    queue.enqueue(sampleNotice("s1", "advisory", "Idle diagnostic 2", "i2"))

    expect(queue.size()).toBe(3)

    // A higher priority Version notice (P0 / Priority 4) arrives -> overflow!
    // The lowest priority items are i1 and i2 (priority 1). i1 is older (enqueued earlier) -> i1 must be evicted!
    clock.advance(100)
    queue.enqueue(sampleNotice("s1", "advisory", "Run /sybermem-update now", "v1"))

    // Size stays bounded at 3
    expect(queue.size()).toBe(3)

    // Advance clock and verify play order: Version (P0) -> Habit (P2) -> Idle 2 (P3)
    clock.advance(4700) // t = 5000, active advisory finishes
    expect(shown[1]).toBe("Run /sybermem-update now")

    clock.advance(5000) // t = 10000, Version finishes
    expect(shown[2]).toBe("Habit candidate A /sybermem-habit")

    clock.advance(5000) // t = 15000, Habit finishes
    expect(shown[3]).toBe("Idle diagnostic 2")
    expect(shown).not.toContain("Idle diagnostic 1")
  })

  test("Waiting live TTL 15s: items that wait longer than 15s expire and are not displayed", () => {
    const clock = new FakeClock()
    const shown: string[] = []

    const queue = createToastQueue({
      clock,
      isActive: () => true,
      showToast: (p) => shown.push(p.message),
    })

    // Active toast (5000ms, t = 0..5000)
    queue.enqueue(sampleNotice("s1", "advisory", "Active toast", "a1"))

    // Habit 1 enqueued at t = 0
    queue.enqueue(sampleNotice("s1", "advisory", "Habit 1 /sybermem-habit", "h1"))

    // Habit 2 enqueued at t = 100
    clock.advance(100)
    queue.enqueue(sampleNotice("s1", "advisory", "Habit 2 /sybermem-habit", "h2"))

    // At t = 1000, high-priority Version 1 arrives (Waiting: Version 1, Habit 1, Habit 2)
    clock.advance(900)
    queue.enqueue(sampleNotice("s1", "advisory", "Version 1 /sybermem-update", "v1"))

    // Active finishes at t = 5000 -> Version 1 displays (5000..10000)
    clock.advance(4000)
    expect(shown[1]).toBe("Version 1 /sybermem-update")

    // At t = 6000, another high-priority Version 2 arrives (Waiting: Version 2, Habit 1, Habit 2)
    clock.advance(1000)
    queue.enqueue(sampleNotice("s1", "advisory", "Version 2 /sybermem-update", "v2"))

    // Version 1 finishes at t = 10000 -> Version 2 displays (10000..15000)
    clock.advance(4000)
    expect(shown[2]).toBe("Version 2 /sybermem-update")

    // Version 2 finishes at t = 15000:
    // Habit 1 was enqueued at t = 0 (waited 15000ms <= 15000ms TTL) -> displays (15000..20000)!
    clock.advance(5000)
    expect(shown[3]).toBe("Habit 1 /sybermem-habit")

    // Habit 1 finishes at t = 20000:
    // Habit 2 was enqueued at t = 100 (waited 19900ms > 15000ms TTL) -> expired and dropped!
    clock.advance(5000)
    expect(shown).toHaveLength(4)
    expect(shown).not.toContain("Habit 2 /sybermem-habit")
  })

  test("Route & location switching: clears waiting queue and active display timer, rechecks scope", () => {
    const clock = new FakeClock()
    const shown: Array<{ message: string; sessionID: string }> = []
    let currentSession: string | undefined = "session-A"
    let currentRouteType = "session"

    const queue = createToastQueue({
      clock,
      isActive: (id) => currentRouteType === "session" && currentSession === id,
      showToast: (p) => shown.push({ message: p.message, sessionID: p.sessionID }),
    })

    // Session A active toast + waiting item
    queue.enqueue(sampleNotice("session-A", "advisory", "Toast A1", "a1"))
    queue.enqueue(sampleNotice("session-A", "advisory", "Toast A2 (waiting)", "a2"))

    expect(shown).toHaveLength(1)
    expect(shown[0].message).toBe("Toast A1")

    // User switches to Session B at t = 1000
    clock.advance(1000)
    currentSession = "session-B"
    queue.clear()

    // Session B toast arrives
    queue.enqueue(sampleNotice("session-B", "summary", "Summary B1", "b1"))
    expect(shown).toHaveLength(2)
    expect(shown[1].message).toBe("Summary B1")
    expect(shown[1].sessionID).toBe("session-B")

    // Advance past Session A's original duration
    clock.advance(5000)
    // Toast A2 should NEVER appear
    expect(shown.map((s) => s.message)).not.toContain("Toast A2 (waiting)")
  })

  test("TUI setupSyberMemTui lifecycle: route changes and disposer clean up timers and state", async () => {
    const clock = new FakeClock()
    const shown: ToastPayload[] = []
    let currentRoute = { type: "session", sessionID: "sess-1" }
    let directory = "D:\\workspace"
    let noticeListener!: (event: { location?: { directory?: string }; data: FeedbackNotice }) => void

    const ctx: any = {
      location: { directory },
      ui: {
        router: { current: () => currentRoute },
        toast: { show: (item: ToastPayload) => shown.push(item) },
      },
      client: {
        rpc: () => ({
          status: async () => ({ epoch: "epoch-1", summary: null }),
          events: {
            on: (_: string, cb: typeof noticeListener) => {
              noticeListener = cb
              return () => {}
            },
          },
        }),
      },
    }

    const stop = setupSyberMemTui(ctx, 2000, { clock })
    await Bun.sleep(0)

    // Emit live notice for active session (sequence 1)
    noticeListener({
      location: { directory },
      data: sampleNotice("sess-1", "summary", "Summary 1", "m1", 1),
    })

    expect(shown).toHaveLength(1)
    expect(shown[0].message).toBe("Summary 1")

    // Emit second notice while first is active (sequence 2)
    noticeListener({
      location: { directory },
      data: sampleNotice("sess-1", "advisory", "Advisory 2", "m2", 2),
    })
    // Second notice is waiting in queue
    expect(shown).toHaveLength(1)

    // Advance time by 3500ms -> second notice displays
    clock.advance(3500)
    expect(shown).toHaveLength(2)
    expect(shown[1].message).toBe("Advisory 2")

    // Emit third notice while second is active (sequence 3), then switch route before it displays
    noticeListener({
      location: { directory },
      data: sampleNotice("sess-1", "advisory", "Should be cleared on route switch", "m3", 3),
    })
    currentRoute = { type: "session", sessionID: "sess-2" }
    clock.advance(2000) // triggers refresh which detects route switch and clears queue
    clock.advance(5000) // past Advisory 2's 5000ms duration
    expect(shown.map((s) => s.message)).not.toContain("Should be cleared on route switch")

    // Unload TUI
    stop()
    expect(clock.pendingTimers()).toBe(0)

    // Notices after unload are ignored
    noticeListener({
      location: { directory },
      data: sampleNotice("sess-2", "summary", "Summary after stop", "m4", 1),
    })
    expect(shown).toHaveLength(2)
  })

  test("Deduplication & safety: suppresses duplicate notices and truncates overlong messages", () => {
    const clock = new FakeClock()
    const shown: ToastPayload[] = []

    const queue = createToastQueue({
      clock,
      isActive: () => true,
      showToast: (p) => shown.push(p),
    })

    // Duplicate of currently active advisory is ignored
    queue.enqueue(sampleNotice("s1", "advisory", "Same advisory", "m1", 1))
    queue.enqueue(sampleNotice("s1", "advisory", "Same advisory", "m2", 2))
    expect(queue.size()).toBe(0)

    // Duplicate of waiting advisory is ignored
    queue.enqueue(sampleNotice("s1", "advisory", "Waiting advisory", "m3", 3))
    queue.enqueue(sampleNotice("s1", "advisory", "Waiting advisory", "m4", 4))
    expect(queue.size()).toBe(1)

    // Empty / whitespace message is ignored
    queue.enqueue(sampleNotice("s1", "advisory", "   ", "m5", 5))
    expect(queue.size()).toBe(1)

    // Overlong message (> 240 chars) is safely truncated
    const longText = "x".repeat(300)
    queue.enqueue(sampleNotice("s1", "advisory", longText, "m6", 6))
    clock.advance(5000) // plays "Waiting advisory"
    clock.advance(5000) // plays truncated longText
    expect(shown).toHaveLength(3)
    expect(shown[2].message.length).toBe(240)
  })
})
