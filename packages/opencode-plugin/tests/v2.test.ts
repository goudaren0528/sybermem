import { test, expect } from "bun:test"
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs"
import { join } from "node:path"
import { setupSyberMemV2 } from "../src/v2"
import { getSessionActivity } from "../src/session_activity"
import plugin from "../src/index"
import bundled from "../sybermem"

test("V2 entrypoint is a stable default definition", () => {
  expect(plugin.id).toBe("sybermem")
  expect(plugin.setup).toBe(setupSyberMemV2)
  expect(bundled.id).toBe("sybermem")
  expect(typeof bundled.setup).toBe("function")
})

test("V2 feedback epochs are stable within setup and distinct across setups", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-epoch-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const handlers: Array<(input: { sessionID: string }) => Promise<{ epoch: string; summary: unknown }>> = []
  const ctx: any = {
    location: { directory: root },
    session: { get: async () => ({ location: { directory: root } }), hook: async () => ({ dispose: async () => {} }) },
    tool: { hook: async () => ({ dispose: async () => {} }) },
    event: { subscribe: async function* () {} },
    rpc: { register: async (_definition: unknown, callbacks: any) => {
      handlers.push(callbacks.status)
      return { events: { emit: async () => {} }, dispose: async () => {} }
    } },
  }
  const shell: any = () => ({ cwd() { return this }, nothrow() { return this }, async text() { return "{}" } })
  let cleanupFirst: (() => Promise<void>) | undefined
  let cleanupSecond: (() => Promise<void>) | undefined
  try {
    cleanupFirst = await setupSyberMemV2(ctx, shell)
    cleanupSecond = await setupSyberMemV2(ctx, shell)
    const first = await handlers[0]({ sessionID: "" })
    const second = await handlers[1]({ sessionID: "" })
    expect(first).toEqual({ epoch: first.epoch, summary: null })
    expect(await handlers[0]({ sessionID: "foreign" })).toEqual(first)
    expect(await handlers[0]({ sessionID: "" })).toEqual(first)
    expect(second).toEqual({ epoch: second.epoch, summary: null })
    expect(first.epoch).not.toBe(second.epoch)
  } finally { await cleanupFirst?.(); await cleanupSecond?.(); rmSync(root, { recursive: true, force: true }) }
})

test("V2 admitted prompt, startup, continuation, compaction, tool evidence, idle and cleanup", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-fixture-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const hooks = new Map<string, Function>()
  const calls: string[] = []
  const notices: any[] = []
  let statusHandler: any
  let stopped = false
  let unblock: (() => void) | undefined
  const queue: any[] = []
  const shell: any = (strings: TemplateStringsArray, ...values: string[]) => {
    const command = strings.reduce((out, part, i) => out + part + (values[i] ?? ""), "")
    const chain = { cwd: () => chain, nothrow: () => chain, text: async () => {
      calls.push(command)
      if (command.includes("context recall")) return "## SyberMem Recall Hints\n- change-fixture: useful context"
      if (command.includes("project record-files")) return JSON.stringify({ records: { "change-fixture": ["src/fixture.ts"] } })
      if (command.includes("digest latest")) return JSON.stringify({ conclusions: ["Fixture startup conclusion"] })
      if (command.includes("git diff --name-only")) return "src/fixture.ts"
      if (command.includes("git")) return ""
      return "{}"
    } }
    return chain
  }
  const history = [{ id: "msg_one", type: "user", text: "fix fixture" }]
  const hook = async (name: string, callback: Function) => {
    hooks.set(name, callback)
    return { dispose: async () => { hooks.delete(name) } }
  }
  const ctx: any = {
    location: { directory: root },
    session: { get: async ({ sessionID }: any) => ({ location: { directory: sessionID === "other" ? root + "-other" : root } }), context: async () => history, hook },
    tool: { hook },
    event: { subscribe: async function* ({ signal }: any) {
      signal.addEventListener("abort", () => { stopped = true; unblock?.() })
      while (!stopped) {
        if (queue.length) yield queue.shift()
        else await new Promise<void>((resolve) => { unblock = resolve })
      }
    } },
    rpc: { register: async (_definition: unknown, handlers: any) => {
      statusHandler = handlers.status
      return { events: { emit: async (_name: string, notice: any) => { notices.push(notice) } }, dispose: async () => { statusHandler = undefined } }
    } },
  }
  const cleanup = await setupSyberMemV2(ctx, shell)
  try {
    const admission = { sessionID: "one", messageID: "msg_one", prompt: { text: "fix fixture" } }
    await hooks.get("prompt")!(admission)
    expect(admission.prompt.text).toBe("fix fixture")
    expect(calls.length).toBe(0)
    const event = { sessionID: "one", system: [{ type: "text", text: "base" }] }
    await hooks.get("context")!(event)
    const usageAfterFirst = readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf8").trim().split("\n").length
    const firstInjection = event.system.map((part) => part.text)
    await hooks.get("context")!(event)
    expect(event.system.map((part) => part.text)).toEqual(firstInjection)
    expect(readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf8").trim().split("\n")).toHaveLength(usageAfterFirst)
    expect(event.system[0].text).toBe("base")
    expect(event.system.some((part) => part.text.includes("Fixture startup conclusion"))).toBe(true)
    expect(event.system.some((part) => part.text.includes("change-fixture"))).toBe(true)
    expect(existsSync(join(root, ".sybermem", ".memory-usage.jsonl"))).toBe(true)
    expect(notices.filter((notice) => notice.kind === "summary")).toHaveLength(1)
    const status = await statusHandler({ sessionID: "one" })
    expect(status.summary.totalItems).toBe(1)
    expect(status.epoch).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
    expect(status.summary.epoch).toBe(status.epoch)
    expect((await statusHandler({ sessionID: "other" })).epoch).toBe(status.epoch)
    expect((await statusHandler({ sessionID: "other" })).summary).toBeNull()
    expect(await statusHandler({ sessionID: "" })).toEqual({ epoch: status.epoch, summary: null })
    expect(notices.every((notice) => notice.epoch === status.epoch)).toBe(true)
    expect(JSON.stringify({ notices, status })).not.toContain("fix fixture")
    expect(JSON.stringify({ notices, status })).not.toContain("change-fixture: useful context")
    const recalls = calls.filter((call) => call.includes("context recall")).length
    const continuation = { sessionID: "one", system: [] }
    await hooks.get("context")!(continuation)
    expect(continuation.system).toHaveLength(event.system.length - 1)
    expect(readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf8").trim().split("\n")).toHaveLength(usageAfterFirst)
    expect(calls.filter((call) => call.includes("context recall"))).toHaveLength(recalls)
    expect(notices.filter((notice) => notice.kind === "summary")).toHaveLength(1)
    history.push({ id: "msg_two", type: "user", text: "second fixture prompt" })
    await hooks.get("context")!({ sessionID: "one", system: [] })
    expect(calls.filter((call) => call.includes("context recall"))).toHaveLength(recalls + 1)
    expect(readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf8").trim().split("\n")).toHaveLength(usageAfterFirst + 1)
    expect(notices.filter((notice) => notice.kind === "summary")).toHaveLength(2)
    expect((await statusHandler({ sessionID: "one" })).epoch).toBe(status.epoch)
    expect(notices.every((notice) => notice.epoch === status.epoch)).toBe(true)
    expect(notices.at(-1).sequence).toBeGreaterThan(notices[0].sequence)
    const compaction = { sessionID: "one", system: [] as any[] }
    await hooks.get("compaction")!(compaction)
    expect(compaction.system.length).toBeGreaterThan(0)
    const compacted = compaction.system.map((part) => part.text)
    await hooks.get("compaction")!(compaction)
    expect(compaction.system.map((part) => part.text)).toEqual(compacted)
    const after = hooks.get("execute.after")!
    await after({ sessionID: "one", tool: "shell", input: { command: "bun test" }, status: "completed", result: {} })
    expect(getSessionActivity("one").lastToolSignal).toBeNull()
    await after({ sessionID: "one", tool: "shell", input: { command: "bun test" }, status: "completed", result: { metadata: { exit: 1 } } })
    expect(getSessionActivity("one").lastToolSignal).toBeNull()
    await after({ sessionID: "one", tool: "shell", input: { command: "bun test" }, status: "completed", result: { metadata: { exit: "0" } } })
    expect(getSessionActivity("one").lastToolSignal).toBeNull()
    await after({ sessionID: "one", tool: "shell", input: { command: "bun test" }, status: "running", result: { metadata: { exit: 0 } } })
    expect(getSessionActivity("one").lastToolSignal).toBeNull()
    await after({ sessionID: "one", tool: "shell", input: { command: "bun test" }, status: "completed", result: { metadata: { exit: 0 }, error: "failed" } })
    expect(getSessionActivity("one").lastToolSignal).toBeNull()
    await after({ sessionID: "one", tool: "shell", input: { command: "bun test" }, status: "completed", result: { metadata: { exit: 0 } } })
    expect(getSessionActivity("one").lastToolSignal).toBe("tests_passed")
    await after({ sessionID: "one", tool: "shell", input: { command: "bun build" }, status: "completed", result: { metadata: { exitCode: 0 } } })
    expect(getSessionActivity("one").lastToolSignal).toBe("build_ok")
    await after({ sessionID: "one", tool: "edit", input: { filePath: join(root, "src/fixture.ts") }, status: "completed", result: {} })
    expect(getSessionActivity("one").editedFiles.has("src/fixture.ts")).toBe(true)
    const foreign = { sessionID: "other", system: [] }
    await hooks.get("context")!(foreign)
    expect(foreign.system).toEqual([])
    queue.push({ type: "session.idle", data: { sessionID: "one" } })
    unblock?.()
    for (let i = 0; i < 100 && !existsSync(join(root, ".sybermem", ".recall-outcomes.jsonl")); i++) await Bun.sleep(10)
    expect(existsSync(join(root, ".sybermem", ".recall-outcomes.jsonl"))).toBe(true)
    expect(readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf8")).toContain("one")
  } finally { await cleanup(); rmSync(root, { recursive: true, force: true }) }
  expect(stopped).toBe(true)
  expect(hooks.size).toBe(0)
    expect(getSessionActivity("one").memoryTurns).toBe(0)
})

test.each([["source", setupSyberMemV2], ["bundle", bundled.setup]] as const)("V2 %s rejected admission cannot capture intent or recall; persisted text wins", async (_name, setup) => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-admission-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const hooks = new Map<string, Function>()
  const calls: string[] = []
  const history: any[] = []
  const shell: any = (strings: TemplateStringsArray, ...values: unknown[]) => ({ cwd() { return this }, nothrow() { return this }, async text() { calls.push(strings.reduce((out, part, i) => out + part + (values[i] ?? ""), "")); return "{}" } })
  const ctx: any = {
    location: { directory: root },
    session: {
      get: async () => ({ location: { directory: root } }),
      context: async () => history,
      hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => hooks.delete(name) } },
    },
    tool: { hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => hooks.delete(name) } } },
    event: { subscribe: async function* () {} },
  }
  const cleanup = await setup(ctx, shell)
  try {
    await hooks.get("prompt")!({ sessionID: "admitted", messageID: "m1", prompt: { text: "remember this" } })
    expect(existsSync(join(root, ".sybermem", ".memory-usage.jsonl"))).toBe(false)
    const request = { sessionID: "admitted", system: [] as any[] }
    await hooks.get("context")!(request)
    expect(calls.some((call) => call.includes("remember this"))).toBe(false)
    history.push({ id: "m1", type: "user", text: "canonical accepted text" })
    await hooks.get("context")!({ sessionID: "admitted", system: [] })
    expect(calls.some((call) => call.includes("canonical accepted text"))).toBe(true)
    expect(calls.some((call) => call.includes("remember this"))).toBe(false)
  } finally { await cleanup(); rmSync(root, { recursive: true, force: true }) }
})

test("V2 no-project is a true no-op", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-no-project-"))
  try {
    const cleanup = await setupSyberMemV2({ location: { directory: "C:\\" } } as any, (() => { throw new Error("must not execute") }) as any)
    await cleanup()
    expect(existsSync(join(root, ".sybermem"))).toBe(false)
  } finally { rmSync(root, { recursive: true, force: true }) }
})

test("V2 partial setup failure disposes every acquired registration", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-cleanup-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const disposed: string[] = []
  try {
    await expect(setupSyberMemV2({
      location: { directory: root },
      session: { hook: async (name: string) => ({ dispose: async () => { disposed.push(name); if (name === "prompt") throw new Error("dispose failed") } }) },
      tool: { hook: async () => { throw new Error("registration failed") } },
    } as any)).rejects.toThrow("registration failed")
    expect(disposed).toEqual(["prompt", "context", "compaction"])
  } finally { rmSync(root, { recursive: true, force: true }) }
})

test("V2 reads persisted text parts, preserves message structure and isolates synchronous disposal", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-parts-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const hooks = new Map<string, Function>()
  const disposed: string[] = []
  const calls: string[] = []
  const shell: any = (strings: TemplateStringsArray, ...values: unknown[]) => ({ cwd() { return this }, nothrow() { return this }, async text() {
    const command = strings.reduce((out, part, i) => out + part + (values[i] ?? ""), "")
    calls.push(command)
    if (command.includes("context recall")) return "## SyberMem Recall Hints\n- fixture"
    return "{}"
  } })
  const ctx: any = {
    location: { directory: root },
    session: { get: async () => ({ location: { directory: root } }), context: async () => [{ id: "parts", type: "user", parts: [{ type: "text", text: "canonical parts text" }, { type: "image", text: "ignore image" }] }], hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: () => { disposed.push(name); if (name === "prompt") throw Error("sync disposal") } } } },
    tool: { hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => { disposed.push(name) } } } },
    event: { subscribe: async function* () {} },
  }
  const cleanup = await setupSyberMemV2(ctx, shell)
  try {
    const messages = [{ role: "user", content: "original" }]
    const result = { value: "original" }
    const event = { sessionID: "parts", system: [] as any[], messages, result }
    await hooks.get("context")!(event)
    expect(calls.some((call) => call.includes("canonical parts text"))).toBe(true)
    expect(calls.some((call) => call.includes("ignore image"))).toBe(false)
    expect(event.messages).toBe(messages)
    expect(event.result).toBe(result)
    const before = event.system.map((part) => part.text)
    await hooks.get("compaction")!(event)
    await hooks.get("compaction")!(event)
    expect(event.system.length).toBeLessThanOrEqual(before.length + 1)
    expect(event.messages).toBe(messages)
    expect(event.result).toBe(result)
  } finally { await cleanup(); rmSync(root, { recursive: true, force: true }) }
  expect(disposed).toContain("context")
  expect(disposed).toContain("execute.after")
})

test("V2 cleanup while startup is in flight cannot resurrect state or inject", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-flight-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const hooks = new Map<string, Function>()
  let release!: () => void
  let waiting!: () => void
  const reached = new Promise<void>((resolve) => { waiting = resolve })
  const gate = new Promise<void>((resolve) => { release = resolve })
  const shell: any = (strings: TemplateStringsArray, ...values: unknown[]) => ({ cwd() { return this }, nothrow() { return this }, async text() {
    const command = strings.reduce((out, part, i) => out + part + (values[i] ?? ""), "")
    if (command.includes("digest latest")) { waiting(); await gate }
    return "{}"
  } })
  const ctx: any = {
    location: { directory: root },
    session: { get: async () => ({ location: { directory: root } }), context: async () => [{ id: "m", type: "user", text: "text" }], hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => {} } } },
    tool: { hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => {} } } },
    event: { subscribe: async function* () {} },
  }
  const cleanup = await setupSyberMemV2(ctx, shell)
  try {
    const request = { sessionID: "flight", system: [] as any[] }
    const pending = hooks.get("context")!(request)
    await reached
    await cleanup()
    release()
    await pending
    expect(request.system).toEqual([])
    expect(existsSync(join(root, ".sybermem", ".memory-usage.jsonl"))).toBe(false)
  } finally { release(); await cleanup(); rmSync(root, { recursive: true, force: true }) }
})

test("V2 serializes same-message waiters and snapshots m1 before interleaved m2", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-serialized-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const hooks = new Map<string, Function>()
  const calls: string[] = []
  const history = [{ id: "m1", type: "user", text: "first unique query" }]
  let releaseRecall!: () => void
  let enteredRecall!: () => void
  const recallGate = new Promise<void>((resolve) => { releaseRecall = resolve })
  const recallEntered = new Promise<void>((resolve) => { enteredRecall = resolve })
  let releaseHabit!: () => void
  let enteredHabit!: () => void
  const habitGate = new Promise<void>((resolve) => { releaseHabit = resolve })
  const habitEntered = new Promise<void>((resolve) => { enteredHabit = resolve })
  const shell: any = (strings: TemplateStringsArray, ...values: unknown[]) => ({ cwd() { return this }, nothrow() { return this }, async text() {
    const command = strings.reduce((out, part, i) => out + part + (values[i] ?? ""), "")
    calls.push(command)
    if (command.includes("context recall") && command.includes("first unique query")) { enteredRecall(); await recallGate }
    if (command.includes("habit awareness") && calls.some((call) => call.includes("context recall") && call.includes("first unique query"))) { enteredHabit(); await habitGate }
    if (command.includes("context recall")) return `## SyberMem Recall Hints\n- ${command.includes("first unique query") ? "change-first" : "change-second"}: relevant`
    return "{}"
  } })
  const ctx: any = {
    location: { directory: root },
    session: { get: async () => ({ location: { directory: root } }), context: async () => [...history], hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => {} } } },
    tool: { hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => {} } } },
    event: { subscribe: async function* () {} },
  }
  const cleanup = await setupSyberMemV2(ctx, shell)
  try {
    const context = hooks.get("context")!
    const first = { sessionID: "s", system: [] as any[] }
    const duplicate = { sessionID: "s", system: [] as any[] }
    const pendingFirst = context(first)
    await recallEntered
    const pendingDuplicate = context(duplicate)
    await Promise.resolve()
    expect(calls.filter((call) => call.includes("context recall") && call.includes("first unique query"))).toHaveLength(1)
    releaseRecall()
    await habitEntered
    history.push({ id: "m2", type: "user", text: "second unique query" })
    const second = { sessionID: "s", system: [] as any[] }
    const pendingSecond = context(second)
    releaseHabit()
    await Promise.all([pendingFirst, pendingDuplicate, pendingSecond])
    expect(calls.filter((call) => call.includes("context recall") && call.includes("first unique query"))).toHaveLength(1)
    expect(calls.filter((call) => call.includes("context recall") && call.includes("second unique query"))).toHaveLength(1)
    expect(first.system.some((part) => part.text.includes("change-first"))).toBe(true)
    expect(first.system.some((part) => part.text.includes("change-second"))).toBe(false)
    expect(duplicate.system.some((part) => part.text.includes("change-first"))).toBe(true)
    expect(second.system.some((part) => part.text.includes("change-second"))).toBe(true)
    expect(readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf8").trim().split("\n")).toHaveLength(2)
    expect(getSessionActivity("s").memoryTurns).toBe(2)
  } finally { releaseRecall(); releaseHabit(); await cleanup(); rmSync(root, { recursive: true, force: true }) }
})

test("V2 cleanup releases context waiters while first callback is blocked", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-waiters-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const hooks = new Map<string, Function>()
  let release!: () => void
  let entered!: () => void
  const gate = new Promise<void>((resolve) => { release = resolve })
  const reached = new Promise<void>((resolve) => { entered = resolve })
  const shell: any = (strings: TemplateStringsArray, ...values: unknown[]) => ({ cwd() { return this }, nothrow() { return this }, async text() {
    const command = strings.reduce((out, part, i) => out + part + (values[i] ?? ""), "")
    if (command.includes("context recall")) { entered(); await gate }
    return "{}"
  } })
  const ctx: any = {
    location: { directory: root },
    session: { get: async () => ({ location: { directory: root } }), context: async () => [{ id: "m", type: "user", text: "intent" }], hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => {} } } },
    tool: { hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => {} } } },
    event: { subscribe: async function* () {} },
  }
  const cleanup = await setupSyberMemV2(ctx, shell)
  try {
    const first = { sessionID: "s", system: [] as any[] }
    const second = { sessionID: "s", system: [] as any[] }
    const pendingFirst = hooks.get("context")!(first)
    await reached
    const pendingSecond = hooks.get("context")!(second)
    await cleanup()
    await pendingSecond // abort wakes waiter without waiting for blocked CLI
    expect(second.system).toEqual([])
    release()
    await pendingFirst
    expect(first.system).toEqual([])
    expect(existsSync(join(root, ".sybermem", ".memory-usage.jsonl"))).toBe(false)
  } finally { release(); await cleanup(); rmSync(root, { recursive: true, force: true }) }
})

test("V2 failed context callback releases the session queue for a waiting retry", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-failure-"))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  const hooks = new Map<string, Function>()
  let release!: () => void
  let entered!: () => void
  const gate = new Promise<void>((resolve) => { release = resolve })
  const reached = new Promise<void>((resolve) => { entered = resolve })
  let fail = true
  const ctx: any = {
    location: { directory: root },
    session: {
      get: async () => ({ location: { directory: root } }),
      context: async () => { if (fail) { fail = false; entered(); await gate; throw Error("transient history failure") } return [{ id: "m", type: "user", text: "retry intent" }] },
      hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => {} } },
    },
    tool: { hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => {} } } },
    event: { subscribe: async function* () {} },
  }
  const shell: any = (strings: TemplateStringsArray, ...values: unknown[]) => ({ cwd() { return this }, nothrow() { return this }, async text() {
    const command = strings.reduce((out, part, i) => out + part + (values[i] ?? ""), "")
    return command.includes("context recall") ? "## SyberMem Recall Hints\n- change-retry: relevant" : "{}"
  } })
  const cleanup = await setupSyberMemV2(ctx, shell)
  try {
    const failed = hooks.get("context")!({ sessionID: "s", system: [] })
    await reached
    const retry = { sessionID: "s", system: [] as any[] }
    const waiting = hooks.get("context")!(retry)
    release()
    await expect(failed).rejects.toThrow("transient history failure")
    await waiting
    expect(retry.system.length).toBeGreaterThan(0)
    expect(readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf8").trim().split("\n")).toHaveLength(1)
  } finally { release(); await cleanup(); rmSync(root, { recursive: true, force: true }) }
})
