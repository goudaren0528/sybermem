import { test, expect, beforeEach, afterEach } from "bun:test"
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs"
import { join } from "node:path"
import { setupSyberMemV2 } from "../src/v2"
import { getSessionActivity } from "../src/session_activity"
import plugin from "../src/index"
import bundled from "../sybermem"

// The V2 setup now evaluates remote-version awareness at instance start. Keep the
// suite hermetic: no background network, no dependence on the developer's real
// ~/.claude/sybermem. Tests that specifically exercise the remote path re-enable it.
const V2_ENV_KEYS = ["USERPROFILE", "HOME", "SYBERMEM_NO_REMOTE_CHECK"] as const
let v2SavedEnv: Record<string, string | undefined>
beforeEach(() => {
  v2SavedEnv = {}
  for (const key of V2_ENV_KEYS) v2SavedEnv[key] = process.env[key]
  process.env.SYBERMEM_NO_REMOTE_CHECK = "1"
})
afterEach(() => {
  for (const key of V2_ENV_KEYS) {
    if (v2SavedEnv[key] === undefined) delete process.env[key]
    else process.env[key] = v2SavedEnv[key]
  }
})

test("V2 entrypoint is a stable default definition", () => {
  expect(plugin.id).toBe("sybermem")
  expect(plugin.setup).toBe(setupSyberMemV2)
  expect(bundled.id).toBe("sybermem")
  expect(typeof bundled.setup).toBe("function")
})

test("V2 feedback epochs are stable within setup and distinct across setups", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-epoch-"))
  // Neutral home: no installed VERSION marker, so no version hint leaks into the
  // status snapshot regardless of the developer's real ~/.claude/sybermem.
  const home = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-epoch-home-"))
  process.env.USERPROFILE = home
  process.env.HOME = home
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
    expect(first).toEqual({ epoch: first.epoch, summary: null, protocolVersion: 2 })
    expect(await handlers[0]({ sessionID: "foreign" })).toEqual(first)
    expect(await handlers[0]({ sessionID: "" })).toEqual(first)
    expect(second).toEqual({ epoch: second.epoch, summary: null, protocolVersion: 2 })
    expect(first.epoch).not.toBe(second.epoch)
  } finally { await cleanupFirst?.(); await cleanupSecond?.(); rmSync(root, { recursive: true, force: true }); rmSync(home, { recursive: true, force: true }) }
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
    expect(await statusHandler({ sessionID: "" })).toEqual({ epoch: status.epoch, summary: null, protocolVersion: 2 })
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

interface V2HarnessOptions {
  readonly history?: Array<{ id: string; type: string; text?: string }>
  readonly result?: (command: string) => string
  readonly withRpc?: boolean
}

function v2Harness(root: string, options: V2HarnessOptions = {}) {
  const hooks = new Map<string, Function>()
  const notices: any[] = []
  const calls: string[] = []
  let status: ((input: { sessionID: string }) => Promise<any>) | undefined
  const history = options.history ?? []
  const result = options.result ?? (() => "{}")
  const shell: any = (strings: TemplateStringsArray, ...values: unknown[]) => {
    const command = strings.reduce((out, part, i) => out + part + (values[i] ?? ""), "")
    calls.push(command)
    return { cwd() { return this }, nothrow() { return this }, async text() { return result(command) } }
  }
  const ctx: any = {
    location: { directory: root },
    session: {
      get: async () => ({ location: { directory: root } }),
      context: async () => [...history],
      hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => hooks.delete(name) } },
    },
    tool: { hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => hooks.delete(name) } } },
    event: { subscribe: async function* () {} },
  }
  if (options.withRpc !== false) {
    ctx.rpc = { register: async (_definition: unknown, handlers: any) => {
      status = handlers.status
      return {
        events: { emit: async (_name: string, notice: any) => { notices.push(notice) } },
        dispose: async () => { status = undefined },
      }
    } }
  }
  return { hooks, notices, calls, history, shell, ctx, status: () => status, summaries: () => notices.filter((notice) => notice.kind === "summary") }
}

function v2Fixture(prefix: string): { root: string; cleanup: () => void } {
  const root = mkdtempSync(join(process.env.TEMP!, prefix))
  mkdirSync(join(root, ".sybermem"))
  writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\n")
  return { root, cleanup: () => rmSync(root, { recursive: true, force: true }) }
}

test("V2 startup-only turn reports the injected startup context exactly once", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-startup-only-")
  const harness = v2Harness(root, {
    history: [{ id: "m1", type: "user", text: "hello" }],
    result: (command) => command.includes("digest latest") ? JSON.stringify({ conclusions: ["Startup-only conclusion"] }) : "{}",
  })
  const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
  try {
    const event = { sessionID: "s", system: [] as any[] }
    await harness.hooks.get("context")!(event)
    const summaries = harness.summaries()
    expect(summaries).toHaveLength(1)
    expect(summaries[0].message).toContain("项目启动上下文")
    expect(summaries[0].totalItems).toBe(0)
    expect(event.system.some((part) => part.text.includes("Startup-only conclusion"))).toBe(true)
    const serialized = JSON.stringify(harness.notices)
    expect(serialized).not.toContain("已记住")
    expect(serialized).not.toContain("模型已采用")
    // A continuation carries the same startup block but must not re-announce it.
    await harness.hooks.get("context")!({ sessionID: "s", system: [] })
    expect(harness.summaries()).toHaveLength(1)
    expect(existsSync(join(root, ".sybermem", ".memory-usage.jsonl"))).toBe(true)
  } finally { await cleanup(); dropRoot() }
})

test("V2 all-empty turn injects nothing, announces nothing and does not crash", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-all-empty-")
  const harness = v2Harness(root, { history: [{ id: "m1", type: "user", text: "hello" }] })
  const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
  try {
    const event = { sessionID: "s", system: [] as any[] }
    await harness.hooks.get("context")!(event)
    expect(event.system).toEqual([])
    expect(harness.summaries()).toHaveLength(0)
    expect(harness.notices.filter((notice) => notice.message.includes("启动上下文") || notice.message.includes("本轮加入"))).toHaveLength(0)
    expect(existsSync(join(root, ".sybermem", ".memory-usage.jsonl"))).toBe(false)
  } finally { await cleanup(); dropRoot() }
})

test("V2 summarizes each persisted message once and never repeats on continuations", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-multiturn-")
  const harness = v2Harness(root, {
    history: [{ id: "m1", type: "user", text: "first" }],
    result: (command) => {
      if (command.includes("digest latest")) return JSON.stringify({ conclusions: ["Startup conclusion"] })
      if (command.includes("context recall")) return "## SyberMem Recall Hints\n- change-one: relevant"
      return "{}"
    },
  })
  const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
  try {
    const first = { sessionID: "s", system: [] as any[] }
    await harness.hooks.get("context")!(first)
    await harness.hooks.get("context")!({ sessionID: "s", system: [] }) // continuation of m1
    expect(harness.summaries().map((notice) => notice.messageID)).toEqual(["m1"])
    harness.history.push({ id: "m2", type: "user", text: "second" })
    await harness.hooks.get("context")!({ sessionID: "s", system: [] })
    await harness.hooks.get("context")!({ sessionID: "s", system: [] }) // continuation of m2
    expect(harness.summaries().map((notice) => notice.messageID)).toEqual(["m1", "m2"])
    expect(first.system.some((part) => part.text.includes("change-one"))).toBe(true)
    expect(readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf8").trim().split("\n")).toHaveLength(2)
  } finally { await cleanup(); dropRoot() }
})

test("V2 unconfirmed admission captures, recalls and announces nothing", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-admission-")
  const harness = v2Harness(root, {
    history: [],
    result: (command) => command.includes("context recall") ? "## SyberMem Recall Hints\n- change-admitted: relevant" : "{}",
  })
  const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
  try {
    await harness.hooks.get("prompt")!({ sessionID: "s", messageID: "m1", prompt: { text: "remember this" } })
    const rejected = { sessionID: "s", system: [] as any[] }
    await harness.hooks.get("context")!(rejected)
    expect(rejected.system).toEqual([])
    expect(harness.summaries()).toHaveLength(0)
    expect(harness.calls.some((call) => call.includes("remember this"))).toBe(false)
    // The persisted turn wins, and only then does injection/announcement happen.
    harness.history.push({ id: "m1", type: "user", text: "canonical accepted text" })
    const accepted = { sessionID: "s", system: [] as any[] }
    await harness.hooks.get("context")!(accepted)
    expect(accepted.system.some((part) => part.text.includes("change-admitted"))).toBe(true)
    expect(harness.summaries()).toHaveLength(1)
    expect(harness.calls.some((call) => call.includes("canonical accepted text"))).toBe(true)
  } finally { await cleanup(); dropRoot() }
})

test("V2 without an RPC channel still injects and stays a no-op for notices", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-norpc-")
  const harness = v2Harness(root, {
    history: [{ id: "m1", type: "user", text: "hello" }],
    withRpc: false,
    result: (command) => command.includes("context recall") ? "## SyberMem Recall Hints\n- change-norpc: relevant" : "{}",
  })
  const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
  try {
    const event = { sessionID: "s", system: [] as any[] }
    await harness.hooks.get("context")!(event)
    expect(event.system.some((part) => part.text.includes("change-norpc"))).toBe(true)
    expect(harness.notices).toHaveLength(0)
  } finally { await cleanup(); dropRoot() }
  expect(harness.hooks.size).toBe(0)
})

test("V2 keeps the remote-outdated notice distinct from the local project-refresh notice", async () => {
  const home = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-remote-home-"))
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-remote-")
  try {
    process.env.USERPROFILE = home
    process.env.HOME = home
    delete process.env.SYBERMEM_NO_REMOTE_CHECK
    mkdirSync(join(home, ".claude", "sybermem"), { recursive: true })
    writeFileSync(join(home, ".claude", "sybermem", "VERSION"), "0.1.0\n")
    writeFileSync(join(home, ".claude", "sybermem", ".remote-version-cache.json"), JSON.stringify({ remote_version: "9.9.9", checked_at: new Date().toISOString() }))
    writeFileSync(join(root, ".sybermem", "project.yaml"), "slug: fixture\nsybermem_version: 0.0.1\n")
    const harness = v2Harness(root, { history: [{ id: "m1", type: "user", text: "hello" }] })
    const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
    try {
      await harness.hooks.get("context")!({ sessionID: "s", system: [] })
      await harness.hooks.get("context")!({ sessionID: "s", system: [] }) // once per session, not per turn
      const advisories = harness.notices.filter((notice) => notice.kind === "advisory").map((notice) => notice.message)
      expect(advisories.filter((message: string) => message.includes("available on GitHub"))).toHaveLength(1)
      expect(advisories.filter((message: string) => message.includes("/sybermem-update"))).toHaveLength(1)
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

// ---------------------------------------------------------------------------
// Server-side status effectiveness and cache-capacity ownership (PRD §6.1):
// the snapshot carries at most two currently-valid version hints (project +
// remote), reusing live sequences, re-sequencing changed hints and dropping
// hints whose condition no longer holds.
// ---------------------------------------------------------------------------

function v2RemoteHome(installed: string, remote: string | null): string {
  const home = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-vhome-"))
  process.env.USERPROFILE = home
  process.env.HOME = home
  delete process.env.SYBERMEM_NO_REMOTE_CHECK
  mkdirSync(join(home, ".claude", "sybermem"), { recursive: true })
  writeFileSync(join(home, ".claude", "sybermem", "VERSION"), `${installed}\n`)
  if (remote) writeFileSync(join(home, ".claude", "sybermem", ".remote-version-cache.json"), JSON.stringify({ remote_version: remote, checked_at: new Date().toISOString() }))
  return home
}

function v2ProjectStamp(root: string, version: string): void {
  writeFileSync(join(root, ".sybermem", "project.yaml"), `slug: fixture\nsybermem_version: ${version}\n`)
}

test("V2 status carries at most two currently valid version hints and reuses live sequences", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-status-")
  const home = v2RemoteHome("0.1.0", "9.9.9")
  v2ProjectStamp(root, "0.0.1")
  try {
    const harness = v2Harness(root, { history: [{ id: "m1", type: "user", text: "hello" }] })
    const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
    try {
      await harness.hooks.get("context")!({ sessionID: "s", system: [] })
      const snapshot = await harness.status()!({ sessionID: "s" })
      expect(snapshot.epoch).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
      expect(snapshot.versionStatus).toHaveLength(2)
      expect(snapshot.versionStatus.map((entry: any) => entry.type).sort()).toEqual(["project", "remote"])
      for (const entry of snapshot.versionStatus) {
        const notice = entry.notice
        expect(notice.kind).toBe("advisory")
        expect(notice.epoch).toBe(snapshot.epoch)
        expect(notice.sessionID).toBe("s")
        expect(notice.messageID).toBe("")
        expect(notice.totalItems).toBe(0)
        expect(notice.totalChars).toBe(0)
        // The exact same sequence was already delivered on the live stream.
        const live = harness.notices.find((candidate) => candidate.message === notice.message)
        expect(live).toBeDefined()
        expect(live.sequence).toBe(notice.sequence)
      }
      // Unchanged hints never churn the transport sequence.
      const again = await harness.status()!({ sessionID: "s" })
      expect(again.versionStatus.map((entry: any) => entry.notice.sequence)).toEqual(snapshot.versionStatus.map((entry: any) => entry.notice.sequence))
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

test("V2 status reflects remote cache changes, drops invalidated hints and re-sequences new ones", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-status-cache-")
  const home = v2RemoteHome("0.1.0", "9.9.9")
  v2ProjectStamp(root, "0.0.1")
  const cachePath = join(home, ".claude", "sybermem", ".remote-version-cache.json")
  try {
    const harness = v2Harness(root, { history: [{ id: "m1", type: "user", text: "hello" }] })
    const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
    try {
      const first = await harness.status()!({ sessionID: "s" })
      const firstRemote = first.versionStatus.find((entry: any) => entry.type === "remote")
      expect(firstRemote).toBeDefined()
      expect(firstRemote.notice.message).toContain("9.9.9")
      // A cache that is no longer ahead drops the remote hint; the project hint stays.
      writeFileSync(cachePath, JSON.stringify({ remote_version: "0.0.9", checked_at: new Date().toISOString() }))
      const dropped = await harness.status()!({ sessionID: "s" })
      expect(dropped.versionStatus.some((entry: any) => entry.type === "remote")).toBe(false)
      expect(dropped.versionStatus.some((entry: any) => entry.type === "project")).toBe(true)
      // A different newer version returns under a fresh, strictly greater sequence.
      writeFileSync(cachePath, JSON.stringify({ remote_version: "8.8.8", checked_at: new Date().toISOString() }))
      const revived = await harness.status()!({ sessionID: "s" })
      const revivedRemote = revived.versionStatus.find((entry: any) => entry.type === "remote")
      expect(revivedRemote.notice.message).toContain("8.8.8")
      expect(revivedRemote.notice.sequence).toBeGreaterThan(firstRemote.notice.sequence)
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

test("V2 status omits the remote hint when remote checks are disabled", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-status-disabled-")
  const home = v2RemoteHome("0.1.0", "9.9.9")
  process.env.SYBERMEM_NO_REMOTE_CHECK = "1"
  v2ProjectStamp(root, "0.0.1")
  try {
    const harness = v2Harness(root, { history: [{ id: "m1", type: "user", text: "hello" }] })
    const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
    try {
      const snapshot = await harness.status()!({ sessionID: "s" })
      expect(snapshot.versionStatus.some((entry: any) => entry.type === "remote")).toBe(false)
      expect(snapshot.versionStatus.some((entry: any) => entry.type === "project")).toBe(true)
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

test("V2 status scopes version hints to the owning session and omits the field when none apply", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-status-scope-"))
  const home = v2RemoteHome("0.1.0", null)
  mkdirSync(join(root, ".sybermem"))
  v2ProjectStamp(root, "0.0.1")
  let status: any
  const ctx: any = {
    location: { directory: root },
    session: {
      get: async ({ sessionID }: any) => ({ location: { directory: sessionID === "other" ? `${root}-other` : root } }),
      hook: async () => ({ dispose: async () => {} }),
    },
    tool: { hook: async () => ({ dispose: async () => {} }) },
    event: { subscribe: async function* () {} },
    rpc: { register: async (_definition: unknown, handlers: any) => { status = handlers.status; return { events: { emit: async () => {} }, dispose: async () => { status = undefined } } } },
  }
  const shell: any = () => ({ cwd() { return this }, nothrow() { return this }, async text() { return "{}" } })
  try {
    const cleanup = await setupSyberMemV2(ctx, shell)
    try {
      const owned = await status({ sessionID: "own" })
      expect(owned.versionStatus).toHaveLength(1)
      expect(owned.versionStatus[0].type).toBe("project")
      const foreign = await status({ sessionID: "other" })
      expect(foreign.summary).toBeNull()
      expect("versionStatus" in foreign).toBe(false)
    } finally { await cleanup() }
  } finally { rmSync(root, { recursive: true, force: true }); rmSync(home, { recursive: true, force: true }) }
})

test("V2 cleanup retires version hints and serves no snapshot from a disposed instance", async () => {
  const root = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-status-cleanup-"))
  const home = v2RemoteHome("0.1.0", null)
  mkdirSync(join(root, ".sybermem"))
  v2ProjectStamp(root, "0.0.1")
  let status: any
  const ctx: any = {
    location: { directory: root },
    session: { get: async () => ({ location: { directory: root } }), hook: async () => ({ dispose: async () => {} }) },
    tool: { hook: async () => ({ dispose: async () => {} }) },
    event: { subscribe: async function* () {} },
    rpc: { register: async (_definition: unknown, handlers: any) => { status = handlers.status; return { events: { emit: async () => {} }, dispose: async () => { status = undefined } } } },
  }
  const shell: any = () => ({ cwd() { return this }, nothrow() { return this }, async text() { return "{}" } })
  try {
    const cleanup = await setupSyberMemV2(ctx, shell)
    const handler = status!
    const live = await handler({ sessionID: "s" })
    expect(live.versionStatus.some((entry: any) => entry.type === "project")).toBe(true)
    await cleanup()
    const after = await handler({ sessionID: "s" })
    expect(after).toEqual({ epoch: live.epoch, summary: null, protocolVersion: 2 })
  } finally { rmSync(root, { recursive: true, force: true }); rmSync(home, { recursive: true, force: true }) }
})

test("V2 session.deleted releases per-session version state so the next turn re-announces", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-status-deleted-")
  const home = v2RemoteHome("0.1.0", "9.9.9")
  v2ProjectStamp(root, "0.0.1")
  try {
    const queue: any[] = []
    let wake: (() => void) | undefined
    let closed = false
    const hooks = new Map<string, Function>()
    const notices: any[] = []
    const ctx: any = {
      location: { directory: root },
      session: {
        get: async () => ({ location: { directory: root } }),
        context: async () => [{ id: "m1", type: "user", text: "hello" }],
        hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => hooks.delete(name) } },
      },
      tool: { hook: async (name: string, callback: Function) => { hooks.set(name, callback); return { dispose: async () => hooks.delete(name) } } },
      event: { subscribe: async function* ({ signal }: any) {
        signal.addEventListener("abort", () => { closed = true; wake?.() })
        while (!closed) {
          if (queue.length) yield queue.shift()
          else await new Promise<void>((resolve) => { wake = resolve })
        }
      } },
      rpc: { register: async (_definition: unknown, handlers: any) => ({ events: { emit: async (_name: string, notice: any) => { notices.push(notice) } }, dispose: async () => {} }) },
    }
    const shell: any = () => ({ cwd() { return this }, nothrow() { return this }, async text() { return "{}" } })
    const cleanup = await setupSyberMemV2(ctx, shell)
    try {
      const context = hooks.get("context")!
      const projectAdvisories = () => notices.filter((notice) => notice.kind === "advisory" && notice.message.includes("/sybermem-update")).length
      await context({ sessionID: "s", system: [] })
      await context({ sessionID: "s", system: [] })
      expect(projectAdvisories()).toBe(1)
      queue.push({ type: "session.deleted", data: { sessionID: "s" } })
      wake?.()
      await Bun.sleep(30)
      await context({ sessionID: "s", system: [] })
      expect(projectAdvisories()).toBe(2)
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

// ---------------------------------------------------------------------------
// Follow-up: protocol capability marker, unconditional status-only session
// cleanup, remote-cache freshness on the context path, and the bounded version
// cache (PRD §6.1/§9.3).
// ---------------------------------------------------------------------------

test("V2 status advertises protocolVersion 2 even when it carries no version hints", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-protocol-")
  const home = mkdtempSync(join(process.env.TEMP!, "sybermem-v2-protocol-home-"))
  process.env.USERPROFILE = home
  process.env.HOME = home
  try {
    const harness = v2Harness(root)
    const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
    try {
      const snapshot = await harness.status()!({ sessionID: "s" })
      expect(snapshot.protocolVersion).toBe(2)
      expect(snapshot.summary).toBeNull()
      // A capability marker is not a hint: an empty snapshot must still omit the
      // versionStatus field old TUIs treat as the V2 signal.
      expect("versionStatus" in snapshot).toBe(false)
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

test("V2 session.deleted releases a status-only session's version state under a non-regressing sequence", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-status-only-delete-")
  const home = v2RemoteHome("0.1.0", "9.9.9")
  v2ProjectStamp(root, "0.0.1")
  try {
    const queue: any[] = []
    let wake: (() => void) | undefined
    let closed = false
    let status: ((input: { sessionID: string }) => Promise<any>) | undefined
    const ctx: any = {
      location: { directory: root },
      session: { get: async () => ({ location: { directory: root } }), hook: async () => ({ dispose: async () => {} }) },
      tool: { hook: async () => ({ dispose: async () => {} }) },
      event: { subscribe: async function* ({ signal }: any) {
        signal.addEventListener("abort", () => { closed = true; wake?.() })
        while (!closed) {
          if (queue.length) yield queue.shift()
          else await new Promise<void>((resolve) => { wake = resolve })
        }
      } },
      rpc: { register: async (_definition: unknown, handlers: any) => { status = handlers.status; return { events: { emit: async () => {} }, dispose: async () => {} } } },
    }
    const shell: any = () => ({ cwd() { return this }, nothrow() { return this }, async text() { return "{}" } })
    const cleanup = await setupSyberMemV2(ctx, shell)
    try {
      // Status-only: no context turn ever runs, so sessions/pendingStates stay
      // empty and the old `sessions.has || pendingStates.has` guard skipped
      // cleanup entirely, leaking versionStatus for this session.
      const first = await status!({ sessionID: "s" })
      expect(first.protocolVersion).toBe(2)
      expect(first.versionStatus.map((entry: any) => entry.type).sort()).toEqual(["project", "remote"])
      const firstRemote = first.versionStatus.find((entry: any) => entry.type === "remote")
      queue.push({ type: "session.deleted", data: { sessionID: "s" } })
      wake?.()
      await Bun.sleep(30)
      // Same cache, so a surviving entry would be reused with its OLD sequence;
      // released state rebuilds it. The epoch-wide sequence must advance, never
      // restart, or the still-active same-epoch client would drop the notice.
      const rebuilt = await status!({ sessionID: "s" })
      const rebuiltRemote = rebuilt.versionStatus.find((entry: any) => entry.type === "remote")
      expect(rebuiltRemote.notice.message).toBe(firstRemote.notice.message)
      expect(rebuiltRemote.notice.sequence).toBeGreaterThan(firstRemote.notice.sequence)
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

test("V2 context reads the current remote cache instead of the setup-time snapshot", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-remote-current-")
  const home = v2RemoteHome("0.1.0", "0.0.9")
  const cachePath = join(home, ".claude", "sybermem", ".remote-version-cache.json")
  try {
    const harness = v2Harness(root, { history: [{ id: "m1", type: "user", text: "hello" }] })
    const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
    try {
      // The cache was not newer at setup; a background refresh lands afterwards.
      writeFileSync(cachePath, JSON.stringify({ remote_version: "9.9.9", checked_at: new Date().toISOString() }))
      await harness.hooks.get("context")!({ sessionID: "s", system: [] })
      const advisories = harness.notices.filter((notice) => notice.kind === "advisory").map((notice) => notice.message)
      expect(advisories.filter((message: string) => message.includes("9.9.9"))).toHaveLength(1)
      expect(advisories.some((message: string) => message.includes("0.0.9"))).toBe(false)
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

test("V2 evicts version-only sessions without regressing their sequence or another active session", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-version-cap-")
  const home = v2RemoteHome("0.1.0", "9.9.9")
  v2ProjectStamp(root, "0.0.1")
  const cachePath = join(home, ".claude", "sybermem", ".remote-version-cache.json")
  try {
    const harness = v2Harness(root)
    const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
    try {
      // sess-0 is a status-only session whose remote hint has already advanced.
      const first = await harness.status()!({ sessionID: "sess-0" })
      const firstRemote = first.versionStatus.find((entry: any) => entry.type === "remote")
      writeFileSync(cachePath, JSON.stringify({ remote_version: "8.8.8", checked_at: new Date().toISOString() }))
      const advanced = await harness.status()!({ sessionID: "sess-0" })
      const advancedRemote = advanced.versionStatus.find((entry: any) => entry.type === "remote")
      expect(advancedRemote.notice.sequence).toBeGreaterThan(firstRemote.notice.sequence)
      // Overflow the version cache with other status-only sessions; the oldest,
      // sess-0, is evicted. All keep the same remote cache from here on.
      for (let i = 1; i <= 256; i++) await harness.status()!({ sessionID: `sess-${i}` })
      // A peer active session polls last, so it is the most-recently touched.
      const peerBefore = await harness.status()!({ sessionID: "sess-1" })
      const peerBeforeRemote = peerBefore.versionStatus.find((entry: any) => entry.type === "remote")
      // The evicted sess-0 polls AGAIN with the SAME cache. It must rebuild under a
      // strictly higher epoch-wide sequence, never restart lower, or the still-active
      // same-epoch client would reject the notice for the same session.
      const revived = await harness.status()!({ sessionID: "sess-0" })
      const revivedRemote = revived.versionStatus.find((entry: any) => entry.type === "remote")
      expect(revivedRemote.notice.message).toBe(advancedRemote.notice.message)
      expect(revivedRemote.notice.sequence).toBeGreaterThan(advancedRemote.notice.sequence)
      // The peer session's cached notice identity is unaffected by sess-0's eviction.
      const peerAfter = await harness.status()!({ sessionID: "sess-1" })
      const peerAfterRemote = peerAfter.versionStatus.find((entry: any) => entry.type === "remote")
      expect(peerAfterRemote.notice.sequence).toBe(peerBeforeRemote.notice.sequence)
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

test("V2 repeated setups keep independent version caches across per-instance cleanup", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-repeat-setup-")
  const home = v2RemoteHome("0.1.0", null)
  v2ProjectStamp(root, "0.0.1")
  try {
    const first = v2Harness(root)
    const second = v2Harness(root)
    const cleanupFirst = await setupSyberMemV2(first.ctx, first.shell)
    const cleanupSecond = await setupSyberMemV2(second.ctx, second.shell)
    try {
      const a = await first.status()!({ sessionID: "s" })
      const b = await second.status()!({ sessionID: "s" })
      expect(a.epoch).not.toBe(b.epoch)
      expect(a.protocolVersion).toBe(2)
      expect(b.protocolVersion).toBe(2)
      expect(a.versionStatus[0].notice.sequence).toBe(1)
      expect(b.versionStatus[0].notice.sequence).toBe(1)
      await cleanupFirst()
      // Disposing one instance leaves the other's snapshot intact.
      const after = await second.status()!({ sessionID: "s" })
      expect(after.epoch).toBe(b.epoch)
      expect(after.summary).toBeNull()
      expect(after.protocolVersion).toBe(2)
      expect(after.versionStatus[0].notice.sequence).toBe(1)
    } finally { await cleanupSecond(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})

test("V2 concurrent status snapshots agree and never fabricate a lower sequence", async () => {
  const { root, cleanup: dropRoot } = v2Fixture("sybermem-v2-status-concurrent-")
  const home = v2RemoteHome("0.1.0", "9.9.9")
  v2ProjectStamp(root, "0.0.1")
  try {
    const harness = v2Harness(root)
    const cleanup = await setupSyberMemV2(harness.ctx, harness.shell)
    try {
      const snapshots = await Promise.all([
        harness.status()!({ sessionID: "s" }),
        harness.status()!({ sessionID: "s" }),
        harness.status()!({ sessionID: "s" }),
      ])
      for (const snapshot of snapshots) {
        expect(snapshot.protocolVersion).toBe(2)
        expect(snapshot.versionStatus.map((entry: any) => entry.type).sort()).toEqual(["project", "remote"])
        expect(snapshot.versionStatus.map((entry: any) => entry.notice.sessionID)).toEqual(["s", "s"])
      }
      const sequences = snapshots
        .flatMap((snapshot: any) => snapshot.versionStatus.map((entry: any) => entry.notice.sequence))
        .sort()
      // Every concurrent snapshot reused the same (type -> sequence) pairs.
      expect(sequences).toEqual([1, 1, 1, 2, 2, 2])
    } finally { await cleanup(); dropRoot() }
  } finally { rmSync(home, { recursive: true, force: true }) }
})
