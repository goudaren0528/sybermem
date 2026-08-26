import { describe, expect, it } from "bun:test"
import { appendStartupContext, consumePendingStartup, markPendingStartup } from "../src/startup_context"
import { injectStashedPromptPackets, stashPromptPackets } from "../src/prompt_context"

describe("startup context helpers", () => {
  it("marks and consumes a one-shot pending startup flag per session", () => {
    // Given: a session that was just created
    markPendingStartup("session-x")

    // When: the flag is consumed on the first transform
    const first = consumePendingStartup("session-x")
    const second = consumePendingStartup("session-x")

    // Then: only the first consume sees the pending flag
    expect(first).toBe(true)
    expect(second).toBe(false)
  })

  it("reports no pending startup for an unknown session", () => {
    // Given / When / Then
    expect(consumePendingStartup("never-marked")).toBe(false)
  })

  it("appends startup context as a trailing block, keeping the stable header at system[0]", () => {
    // Given: a system prompt whose first block is OpenCode's stable base header
    const output = { system: ["base header"] }

    // When: startup context is appended
    appendStartupContext(output, "## SyberMem Startup Context\n- key conclusion")

    // Then: the stable header stays at system[0] (cacheable prefix preserved) and
    // startup context is a new trailing block.
    expect(output.system[0]).toBe("base header")
    expect(output.system[output.system.length - 1].startsWith("## SyberMem Startup Context")).toBe(true)
  })

  it("creates the system array when none exists", () => {
    // Given: no system prompt yet
    const output: { system?: string[] } = {}

    // When: startup context is appended
    appendStartupContext(output, "## SyberMem Startup Context\n- key conclusion")

    // Then: the startup context becomes the only system block
    expect(output.system).toEqual(["## SyberMem Startup Context\n- key conclusion"])
  })

  it("does nothing when startup context is empty", () => {
    // Given: an empty startup context
    const output = { system: ["base"] }

    // When
    appendStartupContext(output, "")

    // Then: the system prompt is untouched
    expect(output.system).toEqual(["base"])
  })

  it("orders startup context before per-turn recall in the trailing blocks (plugin order)", () => {
    // Given: a first turn with stashed recall packets and a pending startup context
    stashPromptPackets("session-first", ["## SyberMem Recall Hints\n- change-1"])
    const output: { system?: string[] } = { system: ["base header"] }

    // When: startup appends first, then recall appends (matching plugin.ts order),
    // so the more stable startup block precedes the volatile recall block.
    appendStartupContext(output, "## SyberMem Startup Context\n- key conclusion")
    injectStashedPromptPackets("session-first", output)

    // Then: system[0] stays the stable header; startup precedes recall in the tail.
    const system = output.system ?? []
    expect(system[0]).toBe("base header")
    const startupIdx = system.findIndex((b) => b.startsWith("## SyberMem Startup Context"))
    const recallIdx = system.findIndex((b) => b.startsWith("## SyberMem Recall Hints"))
    expect(startupIdx).toBeGreaterThan(0)
    expect(recallIdx).toBeGreaterThan(startupIdx)
  })
})
