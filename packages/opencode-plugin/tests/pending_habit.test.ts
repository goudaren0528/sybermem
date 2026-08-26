import { describe, expect, it, beforeEach } from "bun:test"
import { injectPendingHabitReminder, readPendingHabitReminder, resetPendingHabit } from "../src/pending_habit"
import type { Shell } from "../src/runtime"

// A minimal fake Shell that returns a fixed stdout for any command. The plugin only
// reads the CLI stdout, so returning the awareness JSON is enough to drive the module.
function fakeShell(stdout: string): Shell {
  const cmd = {
    cwd() { return cmd },
    nothrow() { return cmd },
    async text() { return stdout },
  }
  return (() => cmd) as unknown as Shell
}

const AWARENESS_WITH_CANDIDATE = JSON.stringify({
  active: 0,
  by_type: {},
  latest_confirmed_at: "",
  pending_intent: true,
  pending_reminder: {
    pending: true,
    scope: "user",
    created_at: "2026-01-01T00:00:00+00:00",
    message: "SyberMem captured a reusable personal preference. Confirm it with /sybermem-habit.",
  },
})

const AWARENESS_NO_CANDIDATE = JSON.stringify({ active: 0, by_type: {}, latest_confirmed_at: "", pending_intent: false })

describe("pending habit reminder", () => {
  beforeEach(() => {
    resetPendingHabit("s1")
    resetPendingHabit("s2")
  })

  it("reads a scope-aware reminder from awareness JSON", async () => {
    const reminder = await readPendingHabitReminder(fakeShell(AWARENESS_WITH_CANDIDATE), "/root")
    expect(reminder).not.toBeNull()
    expect(reminder?.message).toContain("/sybermem-habit")
    expect(reminder?.createdAt).toBe("2026-01-01T00:00:00+00:00")
  })

  it("returns null when no candidate is pending", async () => {
    expect(await readPendingHabitReminder(fakeShell(AWARENESS_NO_CANDIDATE), "/root")).toBeNull()
  })

  it("fails open (null) on malformed CLI output", async () => {
    expect(await readPendingHabitReminder(fakeShell("not json"), "/root")).toBeNull()
  })

  it("injects a model-visible trailing block once per candidate per session", async () => {
    const $ = fakeShell(AWARENESS_WITH_CANDIDATE)
    const output: { system?: string[] } = { system: ["base header"] }

    // First turn: injects the candidate block as a trailing block.
    const first = await injectPendingHabitReminder($, "/root", "s1", output)
    expect(first).not.toBeNull()
    expect(output.system?.[0]).toBe("base header") // stable prefix preserved
    expect(output.system?.some((b) => b.startsWith("## SyberMem Habit Candidate"))).toBe(true)

    // Second turn (same candidate): deduped — no re-injection, returns null.
    const output2: { system?: string[] } = { system: ["base header"] }
    const second = await injectPendingHabitReminder($, "/root", "s1", output2)
    expect(second).toBeNull()
    expect(output2.system?.some((b) => b.startsWith("## SyberMem Habit Candidate"))).toBe(false)
  })

  it("re-injects for a different session (dedup is per session)", async () => {
    const $ = fakeShell(AWARENESS_WITH_CANDIDATE)
    const outA: { system?: string[] } = {}
    const outB: { system?: string[] } = {}
    expect(await injectPendingHabitReminder($, "/root", "s1", outA)).not.toBeNull()
    expect(await injectPendingHabitReminder($, "/root", "s2", outB)).not.toBeNull()
  })

  it("re-injects after a NEW candidate (different created_at) in the same session", async () => {
    const first = fakeShell(AWARENESS_WITH_CANDIDATE)
    const out1: { system?: string[] } = {}
    expect(await injectPendingHabitReminder(first, "/root", "s1", out1)).not.toBeNull()

    const newerCandidate = JSON.stringify({
      pending_intent: true,
      pending_reminder: { pending: true, scope: "user", created_at: "2026-02-02T00:00:00+00:00", message: "Confirm with /sybermem-habit." },
    })
    const out2: { system?: string[] } = {}
    const again = await injectPendingHabitReminder(fakeShell(newerCandidate), "/root", "s1", out2)
    expect(again).not.toBeNull()
    expect(out2.system?.some((b) => b.startsWith("## SyberMem Habit Candidate"))).toBe(true)
  })
})
