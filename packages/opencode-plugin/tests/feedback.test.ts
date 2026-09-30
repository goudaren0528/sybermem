import { test, expect } from "bun:test"
import { feedbackGate, feedbackRpc, type FeedbackStatus } from "../src/v2_feedback"
import { setupSyberMemTui } from "../src/tui"

const tick = () => Bun.sleep(0)
const deferred = <T>() => {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => { resolve = done })
  return { promise, resolve }
}
const sample = (sessionID: string, sequence: number, messageID = `m${sequence}`, epoch = "one", message = "1 recall") => ({ epoch, sessionID, sequence, kind: "summary" as const, message, messageID, totalItems: 1, totalChars: 40 })
const status = (epoch: string, summary: ReturnType<typeof sample> | null): FeedbackStatus => ({ epoch, summary })
const advisory = (sessionID: string, sequence: number, message: string, epoch = "one", messageID = `v${sequence}`) => ({ epoch, sessionID, sequence, kind: "advisory" as const, message, messageID, totalItems: 0, totalChars: 0 })
const version = (type: "project" | "remote", notice: ReturnType<typeof advisory>) => ({ type, notice })
const versioned = (epoch: string, summary: ReturnType<typeof sample> | null, versionStatus: FeedbackStatus["versionStatus"]): FeedbackStatus => ({ epoch, summary, versionStatus })
const located = (data: ReturnType<typeof sample> | ReturnType<typeof advisory>) => ({ location: { directory: "D:\\project" }, data })
// Minimal controllable clock so toast-queue pacing can be advanced deterministically
// (the shared queue holds the second coalesced notice until the first finishes).
const fakeClock = () => {
  let now = 0, nextId = 1
  const timers = new Map<number, { callback: () => void; at: number }>()
  return {
    now: () => now,
    setTimeout(callback: () => void, ms: number) { const id = nextId++; timers.set(id, { callback, at: now + Math.max(0, ms) }); return id },
    clearTimeout(handle: unknown) { if (typeof handle === "number") timers.delete(handle) },
    setInterval(callback: () => void, ms: number) {
      const id = nextId++
      const repeat = () => { if (timers.has(id)) { callback(); timers.set(id, { callback: repeat, at: now + Math.max(1, ms) }) } }
      timers.set(id, { callback: repeat, at: now + Math.max(1, ms) })
      return id
    },
    clearInterval(handle: unknown) { if (typeof handle === "number") timers.delete(handle) },
    advance(ms: number) {
      const target = now + ms
      for (;;) {
        let earliest: number | null = null, at = Number.POSITIVE_INFINITY
        for (const [id, timer] of timers) if (timer.at <= target && timer.at < at) { earliest = id; at = timer.at }
        if (earliest === null) break
        const timer = timers.get(earliest)!
        timers.delete(earliest)
        now = timer.at
        timer.callback()
      }
      now = target
    },
  }
}

test("gate filters location and session, deduplicates and retires old epochs", () => {
  let sessionID = "a"
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID }), (notice) => shown.push(notice))
  gate.accept({ location: { directory: "D:\\other" }, data: sample("a", 2) })
  gate.accept(located(sample("b", 2)))
  expect(shown).toHaveLength(0)
  gate.restore(status("one", null), "a")
  gate.accept(located(sample("a", 2)))
  gate.accept(located(sample("a", 1)))
  gate.accept(located(sample("a", 2)))
  expect(shown).toHaveLength(1)
  gate.restore(status("two", sample("a", 1, "new", "two")), "a")
  gate.accept(located(sample("a", 90, "late", "one")))
  gate.restore(status("one", sample("a", 91, "late", "one")), "a")
  expect(shown.map((item) => item.messageID)).toEqual(["m2", "new"])
  sessionID = "b"
  gate.accept(located(sample("a", 3, "invisible", "two")))
  expect(shown).toHaveLength(2)
  gate.clear()
})

test("old status 4 arriving after live 5 cannot rewind or display old snapshot", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  const revision = gate.revision("a")
  gate.accept(located(sample("a", 5, "new")))
  gate.restore(status("one", sample("a", 4, "old")), "a", revision, gate.challenge("a"))
  gate.accept(located(sample("a", 6, "next")))
  expect(shown.map((item) => item.messageID)).toEqual(["new", "next"])
})

test("restart equal sequence 1 recovers new summary, but same message stays quiet and advisory resumes", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(status("one", null), "a")
  gate.accept(located(sample("a", 1, "old")))
  gate.restore(status("two", sample("a", 1, "new", "two")), "a")
  gate.restore(status("two", sample("a", 1, "new", "two")), "a")
  gate.restore(status("three", sample("a", 1, "new", "three")), "a")
  gate.accept(located({ ...sample("a", 2, "", "three"), kind: "advisory" }))
  expect(shown.map((item) => item.kind)).toEqual(["summary", "summary", "advisory"])
  gate.accept(located(sample("a", 99, "late", "one")))
  gate.restore(status("two", sample("a", 100, "late", "two")), "a")
  expect(shown).toHaveLength(3)
})

test("null snapshot advances epoch and accepts subsequent low-sequence advisory", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(status("one", null), "a")
  gate.accept(located(sample("a", 9, "old")))
  gate.restore(status("two", null), "a")
  gate.accept(located({ ...sample("a", 1, "", "two"), kind: "advisory" }))
  gate.accept(located({ ...sample("a", 10, "", "one"), kind: "advisory" }))
  expect(shown.map((item) => item.epoch)).toEqual(["one", "two"])
})

test("B null status then first old A live cannot retire B; B status and live recover", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(status("B", null), "a")
  expect(gate.accept(located(sample("a", 99, "stale", "A")))).toBe(true)
  expect(shown).toHaveLength(0)
  gate.restore(status("B", sample("a", 2, "current", "B")), "a", gate.revision("a"), gate.challenge("a"))
  gate.accept(located({ ...sample("a", 3, "", "B"), kind: "advisory" }))
  gate.accept(located(sample("a", 100, "stale", "A")))
  expect(shown.map((item) => item.epoch)).toEqual(["B", "B"])
  gate.restore(status("A", sample("a", 101, "stale", "A")), "a")
  gate.accept(located(sample("a", 4, "more", "B")))
  expect(shown.map((item) => item.messageID)).toEqual(["current", "", "more"])
})

test("first live is held until matching status confirms epoch", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  expect(gate.accept(located(sample("a", 5, "fresh", "B")))).toBe(true)
  expect(shown).toHaveLength(0)
  gate.restore(status("B", sample("a", 4, "stale", "B")), "a", 0, gate.challenge("a"))
  expect(shown.map((item) => item.messageID)).toEqual(["fresh"])
})

test("unknown live C queues status; confirmed C retires B and recovers live", async () => {
  const next = deferred<FeedbackStatus>()
  const shown: any[] = [], calls: string[] = []
  let listener!: (event: unknown) => void
  const ctx: any = { location: { directory: "D:\\project" }, ui: { router: { current: () => ({ type: "session", sessionID: "a" }) }, toast: { show: (item: unknown) => shown.push(item) } }, client: { rpc: () => ({ status: ({ sessionID }: { sessionID: string }) => { calls.push(sessionID); return calls.length === 1 ? Promise.resolve(status("B", null)) : next.promise }, events: { on: (_: string, cb: (event: unknown) => void) => { listener = cb; return () => {} } } }) } }
  const stop = setupSyberMemTui(ctx)
  await tick()
  listener(located(sample("a", 1, "new", "C")))
  await tick()
  expect(calls).toEqual(["a", "a"])
  expect(shown).toHaveLength(0)
  next.resolve(status("C", null))
  await tick()
  expect(shown.map((item) => item.message)).toEqual(["1 recall"])
  listener(located(sample("a", 9, "old", "B")))
  expect(shown).toHaveLength(1)
  stop()
})

test("TUI rechecks route and location, handles independent windows, unsubscribes on unload", async () => {
  const windows = ["D:\\project", "D:\\other"].map((directory) => {
    let selected = "a", wake!: () => void, listener!: (event: unknown) => void, removed = 0
    const shown: any[] = [], calls: string[] = []
    const ctx: any = { location: { directory }, data: { listen: (cb: () => void) => { wake = cb; return () => { removed++ } } }, ui: { router: { current: () => ({ type: "session", sessionID: selected }) }, toast: { show: (item: unknown) => shown.push(item) } }, client: { rpc: (definition: unknown) => {
      expect(definition).toBe(feedbackRpc)
      return { status: async ({ sessionID }: { sessionID: string }) => { calls.push(sessionID); return status("one", sample(sessionID, 1)) }, events: { on: (_: string, cb: (event: unknown) => void) => { listener = cb; return () => { removed++ } } } }
    } } }
    const stop = setupSyberMemTui(ctx)
    return { shown, calls, select: (id: string) => { selected = id; wake() }, emit: (event: unknown) => listener(event), stop, removed: () => removed }
  })
  await tick()
  windows[0].select("b"); windows[1].select("c")
  await tick()
  expect(windows.map((w) => w.calls)).toEqual([["a", "b"], ["a", "c"]])
  windows[0].emit({ location: { directory: "D:\\other" }, data: sample("b", 2) })
  expect(windows[0].shown).toHaveLength(2)
  for (const w of windows) { w.stop(); expect(w.removed()).toBe(2); w.emit(located(sample("b", 3))) }
  expect(windows.map((w) => w.shown.length)).toEqual([2, 2])
})

test("pending status is rejected after route or location changes and after unload", async () => {
  const pending = deferred<FeedbackStatus>()
  let selected = "a", wake!: () => void
  const shown: unknown[] = []
  const ctx: any = { location: { directory: "D:\\project" }, data: { listen: (cb: () => void) => { wake = cb; return () => {} } }, ui: { router: { current: () => ({ type: "session", sessionID: selected }) }, toast: { show: (item: unknown) => shown.push(item) } }, client: { rpc: () => ({ status: () => pending.promise, events: { on: () => () => {} } }) } }
  const stop = setupSyberMemTui(ctx)
  selected = "b"; wake()
  pending.resolve(status("one", sample("a", 1)))
  await tick()
  expect(shown).toHaveLength(0)
  stop()
  const later = deferred<FeedbackStatus>()
  ctx.client.rpc = () => ({ status: () => later.promise, events: { on: () => () => {} } })
  const unload = setupSyberMemTui(ctx)
  unload()
  later.resolve(status("one", sample("b", 1)))
  await tick()
  expect(shown).toHaveLength(0)
})

test("slow status checks coalesce without overlap or starvation", async () => {
  const first = deferred<FeedbackStatus>()
  const calls: string[] = [], shown: any[] = []
  let wake!: () => void
  const ctx: any = { location: { directory: "D:\\project" }, data: { listen: (cb: () => void) => { wake = cb; return () => {} } }, ui: { router: { current: () => ({ type: "session", sessionID: "a" }) }, toast: { show: (item: unknown) => shown.push(item) } }, client: { rpc: () => ({ status: ({ sessionID }: { sessionID: string }) => { calls.push(sessionID); return calls.length === 1 ? first.promise : Promise.resolve(status("one", sample("a", 2, "m2", "one", "2 recall"))) }, events: { on: () => () => {} } }) } }
  const clock = fakeClock()
  const stop = setupSyberMemTui(ctx, 2, { clock })
  await tick()
  for (let i = 0; i < 8; i++) wake()
  expect(calls).toEqual(["a"])
  first.resolve(status("one", sample("a", 1)))
  await tick(); await tick()
  expect(calls).toEqual(["a", "a"])
  // Distinct business identity (messageID + message) so the queue's dedupe does
  // not mask the second coalesced status; it waits its turn, then both display.
  expect(shown.map((item) => item.message)).toEqual(["1 recall"])
  clock.advance(3500)
  expect(shown.map((item) => item.message)).toEqual(["1 recall", "2 recall"])
  stop()
})

test("a throwing disposer cannot prevent the other disposer or gate cleanup", async () => {
  let listener!: (event: unknown) => void, rpcOff = 0
  const shown: unknown[] = []
  const ctx: any = { location: { directory: "D:\\project" }, data: { listen: () => () => { throw Error("bad disposer") } }, ui: { router: { current: () => ({ type: "session", sessionID: "a" }) }, toast: { show: (item: unknown) => shown.push(item) } }, client: { rpc: () => ({ status: async () => status("one", null), events: { on: (_: string, cb: (event: unknown) => void) => { listener = cb; return () => { rpcOff++ } } } }) } }
  const stop = setupSyberMemTui(ctx)
  await tick()
  stop()
  listener(located(sample("a", 1)))
  expect(rpcOff).toBe(1)
  expect(shown).toHaveLength(0)
})

test("status replays latest summary plus version hints oldest-first without dropping the summary", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  // A higher-sequence version hint must not make the lower-sequence summary look stale.
  gate.restore(versioned("one", sample("a", 1, "summary"), [version("remote", advisory("a", 5, "remote update"))]), "a")
  expect(shown.map((item) => item.messageID)).toEqual(["summary", "v5"])
  expect(shown.map((item) => item.kind)).toEqual(["summary", "advisory"])
  // And the reverse ordering still shows both, because replay is sequence-sorted.
  gate.restore(versioned("two", sample("a", 9, "late-summary", "two"), [version("project", advisory("a", 3, "project refresh", "two"))]), "a")
  expect(shown.map((item) => item.messageID)).toEqual(["summary", "v5", "v3", "late-summary"])
  gate.clear()
})

test("version hints suppress same identity or non-update but display a changed higher-sequence hint", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(versioned("one", null, [version("remote", advisory("a", 1, "hint v1"))]), "a")
  // Same identity at a higher sequence is a re-send, not an update.
  gate.restore(versioned("one", null, [version("remote", advisory("a", 2, "hint v1"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["hint v1"])
  // A changed message at a higher sequence is a genuine update and must display.
  gate.restore(versioned("one", null, [version("remote", advisory("a", 3, "hint v2"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["hint v1", "hint v2"])
  // An older sequence must never rewind to previous content.
  gate.restore(versioned("one", null, [version("remote", advisory("a", 2, "hint v1"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["hint v1", "hint v2"])
  // Another category has its own identity and sequence.
  gate.restore(versioned("one", null, [version("project", advisory("a", 4, "project v1"))]), "a")
  gate.restore(versioned("one", null, [version("project", advisory("a", 5, "project v1"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["hint v1", "hint v2", "project v1"])
  // Summary messageID dedupe is untouched: a repeated summary stays quiet.
  gate.restore(versioned("one", sample("a", 6, "s"), []), "a")
  gate.restore(versioned("one", sample("a", 7, "s"), []), "a")
  expect(shown.filter((item) => item.kind === "summary")).toHaveLength(1)
  gate.clear()
})

test("a changed version update competes with a live candidate by sequence", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(versioned("one", null, [version("remote", advisory("a", 1, "hint v1"))]), "a")
  // A live notice for an unknown epoch is held as a candidate at a higher sequence.
  expect(gate.accept(located(advisory("a", 4, "live hint", "B")))).toBe(true)
  expect(shown.map((item) => item.message)).toEqual(["hint v1"])
  // The confirming snapshot carries a changed update at a still newer sequence, so
  // the update displays and the older live candidate is dropped.
  gate.restore(versioned("B", null, [version("remote", advisory("a", 6, "hint v2", "B"))]), "a", gate.revision("a"), gate.challenge("a"))
  expect(shown.map((item) => item.message)).toEqual(["hint v1", "hint v2"])
  gate.clear()
})

test("a live candidate newer than a changed version snapshot suppresses the snapshot", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  expect(gate.accept(located(advisory("a", 7, "live hint", "B")))).toBe(true)
  gate.restore(versioned("B", null, [version("remote", advisory("a", 6, "hint v2", "B"))]), "a", 0, gate.challenge("a"))
  expect(shown.map((item) => item.message)).toEqual(["live hint"])
  gate.clear()
})

test("duplicate categories inside one status snapshot collapse to one hint", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(versioned("one", null, [
    version("remote", advisory("a", 1, "remote update")),
    version("remote", advisory("a", 2, "remote update again")),
    version("project", advisory("a", 3, "project refresh")),
  ]), "a")
  expect(shown.map((item) => item.message)).toEqual(["remote update", "project refresh"])
  gate.clear()
})

test("a stale version snapshot is not marked seen, so a later newer hint still displays", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(status("one", null), "a")
  gate.accept(located(advisory("a", 5, "live hint")))
  // Sequence 4 is below the confirmed live sequence 5: dropped by the sequence
  // gate and must NOT be remembered, or the category stays suppressed forever.
  gate.restore(versioned("one", null, [version("remote", advisory("a", 4, "remote update"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["live hint"])
  gate.restore(versioned("one", null, [version("remote", advisory("a", 6, "remote update"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["live hint", "remote update"])
  gate.clear()
})

test("version hint identity is bounded per epoch and resets on a new epoch", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(versioned("one", null, [version("project", advisory("a", 1, "project refresh"))]), "a")
  // Same epoch/category stays quiet even at a higher sequence.
  gate.restore(versioned("one", null, [version("project", advisory("a", 3, "project refresh"))]), "a")
  expect(shown).toHaveLength(1)
  // A new epoch is a new server instance: the category may announce again.
  gate.restore(versioned("two", null, [version("project", advisory("a", 2, "project refresh", "two"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["project refresh", "project refresh"])
  gate.clear()
})

test("late version snapshot cannot outrank newer confirmed live traffic", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(status("one", null), "a")
  gate.accept(located(advisory("a", 5, "live hint")))
  gate.restore(versioned("one", null, [version("remote", advisory("a", 4, "old hint"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["live hint"])
  gate.clear()
})

test("an unknown-epoch live candidate outranks an older version snapshot and is confirmed by it", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  expect(gate.accept(located(advisory("a", 5, "live hint", "B")))).toBe(true)
  expect(shown).toHaveLength(0)
  gate.restore(versioned("B", null, [version("remote", advisory("a", 4, "old snapshot", "B"))]), "a", 0, gate.challenge("a"))
  expect(shown.map((item) => item.message)).toEqual(["live hint"])
  gate.clear()
})

test("a version snapshot newer than the live candidate wins and the stale candidate stays quiet", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  expect(gate.accept(located(advisory("a", 2, "live older", "B")))).toBe(true)
  gate.restore(versioned("B", null, [version("remote", advisory("a", 6, "snapshot newer", "B"))]), "a", 0, gate.challenge("a"))
  expect(shown.map((item) => item.message)).toEqual(["snapshot newer"])
  gate.clear()
})

test("version hints ignore mis-scoped and illegal entries and accept only the confirmed session/epoch", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(versioned("one", null, [
    version("remote", advisory("b", 1, "other session")),
    version("remote", advisory("a", 2, "other epoch", "two")),
    { type: "bogus", notice: advisory("a", 3, "bad type") } as any,
    version("project", { ...advisory("a", 4, "bad kind"), kind: "summary" } as any),
    { type: "remote", notice: { ...advisory("a", 5, "bad sequence"), sequence: 0 } } as any,
    { type: "remote", notice: { ...advisory("a", 6, "empty message"), message: "" } } as any,
    version("project", advisory("a", 7, "good")),
  ]), "a")
  expect(shown.map((item) => item.message)).toEqual(["good"])
  gate.clear()
})

test("old status without versionStatus keeps replaying the latest summary", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore({ epoch: "one", summary: sample("a", 2, "old") }, "a")
  gate.restore({ epoch: "one", summary: sample("a", 3, "new") }, "a")
  expect(shown.map((item) => item.messageID)).toEqual(["old", "new"])
  gate.clear()
})

test("protocolVersion is optional and never gates status replay", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  // An old server omits protocolVersion entirely. The new capability is detected
  // by the presence of versionStatus, not by the marker, so a status carrying
  // versionStatus but no protocolVersion still replays both hints and summary.
  gate.restore(versioned("one", sample("a", 1, "old"), [version("remote", advisory("a", 2, "hint"))]), "a")
  expect(shown.map((item) => item.messageID)).toEqual(["old", "v2"])
  // A new server may add the optional marker alongside a new capability; it is
  // transport metadata the gate ignores, so replay is unchanged.
  gate.restore({ epoch: "two", summary: sample("a", 9, "late", "two"), versionStatus: [version("project", advisory("a", 4, "project hint", "two"))], protocolVersion: 2 }, "a")
  expect(shown.map((item) => item.messageID)).toEqual(["old", "v2", "v4", "late"])
  gate.clear()
})

test("a same-identity higher-sequence status hint silently advances the watermark and blocks late live replays", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  // remote seq1 is displayed normally.
  gate.restore(versioned("one", null, [version("remote", advisory("a", 1, "remote update"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["remote update"])
  // The same text re-issued at seq10 must not toast...
  gate.restore(versioned("one", null, [version("remote", advisory("a", 10, "remote update"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["remote update"])
  // ...but the snapshot raises the session watermark, so a late live seq5, which
  // sits between the old watermark and the snapshot watermark, must be rejected.
  expect(gate.accept(located(advisory("a", 5, "remote update")))).not.toBe(true)
  expect(shown.map((item) => item.message)).toEqual(["remote update"])
  // A genuinely newer live seq11 is still allowed.
  gate.accept(located(advisory("a", 11, "remote newer")))
  expect(shown.map((item) => item.message)).toEqual(["remote update", "remote newer"])
  gate.clear()
})

test("a summary below a duplicate version hint but newer than the old watermark still displays", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(versioned("one", null, [version("remote", advisory("a", 1, "remote update"))]), "a")
  // Summary seq5 outranks the old watermark 1 yet is below the duplicate hint 10;
  // replaying in sequence order must show it before the watermark advances past it.
  gate.restore(versioned("one", sample("a", 5, "summary5"), [version("remote", advisory("a", 10, "remote update"))]), "a")
  expect(shown.map((item) => item.messageID)).toEqual(["v1", "summary5"])
  // The duplicate hint still raised the watermark to 10, so seq7 late live is rejected.
  gate.accept(located(advisory("a", 7, "late")))
  expect(shown.map((item) => item.messageID)).toEqual(["v1", "summary5"])
  gate.accept(located(advisory("a", 11, "newer")))
  expect(shown.map((item) => item.messageID)).toEqual(["v1", "summary5", "v11"])
  gate.clear()
})

test("version hint watermark advances within an epoch and resets on a new epoch", () => {
  const shown: any[] = []
  const gate = feedbackGate("D:\\project", () => ({ type: "session", sessionID: "a" }), (item) => shown.push(item))
  gate.restore(versioned("one", null, [version("remote", advisory("a", 2, "remote update"))]), "a")
  gate.restore(versioned("one", null, [version("remote", advisory("a", 9, "remote update"))]), "a")
  expect(shown).toHaveLength(1)
  gate.accept(located(advisory("a", 5, "remote update")))
  expect(shown).toHaveLength(1)
  // A new epoch resets the category identity and the watermark, so the same hint
  // announces again and a lower live event is no longer blocked by the old epoch.
  gate.restore(versioned("two", null, [version("remote", advisory("a", 1, "remote update", "two"))]), "a")
  expect(shown.map((item) => item.message)).toEqual(["remote update", "remote update"])
  gate.accept(located(advisory("a", 5, "remote update", "two")))
  expect(shown).toHaveLength(3)
  gate.clear()
})


test("RPC payload contains display fields only; epoch is required even for null status", () => {
  const { input, output } = feedbackRpc.methods.status
  const event = feedbackRpc.events.notice.schema
  const summary = output.properties.summary.anyOf[0]
  const versionStatus = output.properties.versionStatus
  const versionItem = versionStatus.items
  const protocolVersion = output.properties.protocolVersion
  expect(Object.keys(input.properties)).toEqual(["sessionID"])
  expect(output.required).toEqual(["epoch", "summary"])
  expect(Object.keys(summary.properties).sort()).toEqual(["epoch", "message", "messageID", "sequence", "sessionID", "totalChars", "totalItems"])
  expect(Object.keys(event.properties).sort()).toEqual(["epoch", "kind", "message", "messageID", "sequence", "sessionID", "totalChars", "totalItems"])
  expect(summary.required).toContain("epoch")
  expect(event.required).toContain("epoch")
  expect([input, output, summary, event].every((schema) => schema.additionalProperties === false)).toBe(true)
  expect(Object.keys(sample("a", 1)).sort()).toEqual(Object.keys(event.properties).sort())
  // Optional version hints: bounded, not required, and reusing the exact notice shape.
  expect(Object.keys(output.properties).sort()).toEqual(["epoch", "protocolVersion", "summary", "versionStatus"])
  expect(output.required).not.toContain("versionStatus")
  expect(output.required).not.toContain("protocolVersion")
  expect(versionStatus.type).toBe("array")
  expect(versionStatus.maxItems).toBe(2)
  expect(versionItem.additionalProperties).toBe(false)
  expect(versionItem.required).toEqual(["type", "notice"])
  expect(Object.keys(versionItem.properties).sort()).toEqual(["notice", "type"])
  expect(versionItem.properties.type.enum).toEqual(["project", "remote"])
  expect(versionItem.properties.notice).toBe(event)
  // Optional new-capability marker: a fixed constant 2 encoded as a single-value
  // enum (the pinned 2.0.15 host validator has no `const` keyword), never required.
  expect(protocolVersion.type).toBe("integer")
  expect(protocolVersion.enum).toEqual([2])
})
