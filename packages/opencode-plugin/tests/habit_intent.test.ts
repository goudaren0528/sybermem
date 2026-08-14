import { describe, expect, it } from "bun:test"
import { captureHabitIntentWithCli } from "../src/habit_intent"
import type { Shell } from "../src/runtime"

// Minimal Shell stub: records the command and returns a canned stdout.
function stubShell(stdout: string): { shell: Shell; commands: string[] } {
  const commands: string[] = []
  const shell = ((strings: TemplateStringsArray, ...values: readonly string[]) => {
    let cmd = ""
    strings.forEach((s, i) => { cmd += s; if (i < values.length) cmd += values[i] })
    commands.push(cmd)
    const chain = { cwd: () => chain, nothrow: () => chain, text: async () => stdout }
    return chain
  }) as unknown as Shell
  return { shell, commands }
}

describe("habit intent capture", () => {
  it("reports a capture with the classified habit type", async () => {
    // Given: Core returns a captured candidate
    const { shell } = stubShell(JSON.stringify({ captured: true, candidate: { candidate_only: true, habit_type: "communication" } }))

    // When
    const result = await captureHabitIntentWithCli(shell, "/root", "以后都用中文回复我")

    // Then
    expect(result.captured).toBe(true)
    expect(result.habitType).toBe("communication")
  })

  it("routes through the habit intent CLI with the prompt", async () => {
    // Given
    const { shell, commands } = stubShell(JSON.stringify({ captured: true, candidate: { habit_type: "workflow" } }))

    // When
    await captureHabitIntentWithCli(shell, "/root", "always prefer plans")

    // Then: the command targets `habit intent --prompt ... --format json`
    expect(commands.some((c) => c.includes("habit intent --prompt") && c.includes("always prefer plans"))).toBe(true)
  })

  it("returns no-capture for a non-candidate prompt", async () => {
    const { shell } = stubShell(JSON.stringify({ captured: false, candidate: null }))
    const result = await captureHabitIntentWithCli(shell, "/root", "fix the crash")
    expect(result.captured).toBe(false)
    expect(result.habitType).toBe("")
  })

  it("fails open on empty text and on malformed CLI output", async () => {
    const empty = await captureHabitIntentWithCli(stubShell("").shell, "/root", "")
    expect(empty.captured).toBe(false)
    const malformed = await captureHabitIntentWithCli(stubShell("not json").shell, "/root", "always do X")
    expect(malformed.captured).toBe(false)
  })
})
