import { test, expect } from "bun:test"
import { feedbackGate, feedbackRpc, type FeedbackStatus } from "../src/v2_feedback"
import { setupSyberMemTui } from "../src/tui"

const tick = () => Bun.sleep(0)
const deferred = <T>() => {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => { resolve = done })
  return { promise, resolve }
}
const sample = (sessionID: string, sequence: number, messageID = `m${sequence}`, epoch = "one") => ({ epoch, sessionID, sequence, kind: "summary" as const, message: "1 recall", messageID, totalItems: 1, totalChars: 40 })
const status = (epoch: string, summary: ReturnType<typeof sample> | null): FeedbackStatus => ({ epoch, summary })
const located = (data: ReturnType<typeof sample>) => ({ location: { directory: "D:\\project" }, data })

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
  const ctx: any = { location: { directory: "D:\\project" }, data: { listen: (cb: () => void) => { wake = cb; return () => {} } }, ui: { router: { current: () => ({ type: "session", sessionID: "a" }) }, toast: { show: (item: unknown) => shown.push(item) } }, client: { rpc: () => ({ status: ({ sessionID }: { sessionID: string }) => { calls.push(sessionID); return calls.length === 1 ? first.promise : Promise.resolve(status("one", sample("a", 2))) }, events: { on: () => () => {} } }) } }
  const stop = setupSyberMemTui(ctx, 2)
  await tick()
  for (let i = 0; i < 8; i++) wake()
  expect(calls).toEqual(["a"])
  first.resolve(status("one", sample("a", 1)))
  await tick(); await tick()
  expect(calls).toEqual(["a", "a"])
  expect(shown.map((item) => item.message)).toEqual(["1 recall", "1 recall"])
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

test("RPC payload contains display fields only; epoch is required even for null status", () => {
  const { input, output } = feedbackRpc.methods.status
  const event = feedbackRpc.events.notice.schema
  const summary = output.properties.summary.anyOf[0]
  expect(Object.keys(input.properties)).toEqual(["sessionID"])
  expect(output.required).toEqual(["epoch", "summary"])
  expect(Object.keys(summary.properties).sort()).toEqual(["epoch", "message", "messageID", "sequence", "sessionID", "totalChars", "totalItems"])
  expect(Object.keys(event.properties).sort()).toEqual(["epoch", "kind", "message", "messageID", "sequence", "sessionID", "totalChars", "totalItems"])
  expect(summary.required).toContain("epoch")
  expect(event.required).toContain("epoch")
  expect([input, output, summary, event].every((schema) => schema.additionalProperties === false)).toBe(true)
  expect(Object.keys(sample("a", 1)).sort()).toEqual(Object.keys(event.properties).sort())
})
