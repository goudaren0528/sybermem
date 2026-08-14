import { describe, expect, it } from "bun:test"
import { captureHabitIntentWithCli, looksLikeHabitIntent } from "../src/habit_intent"
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

  it("routes through the habit intent CLI with an argparse-safe --prompt= form", async () => {
    // Given
    const { shell, commands } = stubShell(JSON.stringify({ captured: true, candidate: { habit_type: "workflow" } }))

    // When
    await captureHabitIntentWithCli(shell, "/root", "always prefer plans")

    // Then: the command uses `--prompt=` so a leading-dash prompt is not mis-parsed
    expect(commands.some((c) => c.includes("habit intent --prompt=") && c.includes("always prefer plans"))).toBe(true)
  })

  it("skips the CLI entirely for a non-preference prompt (hot-path cost guard)", async () => {
    // Given
    const { shell, commands } = stubShell(JSON.stringify({ captured: false, candidate: null }))

    // When: an ordinary work prompt with no preference language
    const result = await captureHabitIntentWithCli(shell, "/root", "fix the crash in the parser")

    // Then: no subprocess was spawned and no capture occurred
    expect(result.captured).toBe(false)
    expect(commands).toEqual([])
  })

  it("prefilter recognizes ASCII and CJK preference language only", () => {
    expect(looksLikeHabitIntent("always prefer plans")).toBe(true)
    expect(looksLikeHabitIntent("remember this")).toBe(true)
    expect(looksLikeHabitIntent("以后都用中文回复我")).toBe(true)
    expect(looksLikeHabitIntent("fix the crash in the parser")).toBe(false)
    expect(looksLikeHabitIntent("")).toBe(false)
  })

  it("fails open on empty text and on malformed CLI output", async () => {
    const empty = await captureHabitIntentWithCli(stubShell("").shell, "/root", "")
    expect(empty.captured).toBe(false)
    // Malformed output on a prompt that DOES pass the prefilter still fails open.
    const malformed = await captureHabitIntentWithCli(stubShell("not json").shell, "/root", "always do X")
    expect(malformed.captured).toBe(false)
  })
})
