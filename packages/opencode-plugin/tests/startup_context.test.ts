import { describe, expect, it } from "bun:test"
import { consumePendingStartup, markPendingStartup, prependStartupContext } from "../src/startup_context"
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

  it("prepends startup context ahead of existing system blocks", () => {
    // Given: a system prompt that already has recall content
    const output = { system: ["## SyberMem Recall Hints\n- change-1\n\nbase"] }

    // When: startup context is prepended
    prependStartupContext(output, "## SyberMem Startup Context\n- key conclusion")

    // Then: startup context comes first and existing content is preserved
    expect(output.system[0].startsWith("## SyberMem Startup Context")).toBe(true)
    expect(output.system[0]).toContain("## SyberMem Recall Hints")
  })

  it("creates the system array when none exists", () => {
    // Given: no system prompt yet
    const output: { system?: string[] } = {}

    // When: startup context is prepended
    prependStartupContext(output, "## SyberMem Startup Context\n- key conclusion")

    // Then: the startup context becomes the only system block
    expect(output.system).toEqual(["## SyberMem Startup Context\n- key conclusion"])
  })

  it("does nothing when startup context is empty", () => {
    // Given: an empty startup context
    const output = { system: ["base"] }

    // When
    prependStartupContext(output, "")

    // Then: the system prompt is untouched
    expect(output.system).toEqual(["base"])
  })

  it("keeps startup context above recall packets when both apply on the first turn", () => {
    // Given: a first turn with stashed recall packets and a pending startup context
    stashPromptPackets("session-first", ["## SyberMem Recall Hints\n- change-1"])
    const output: { system?: string[] } = { system: ["base"] }

    // When: recall packets inject first, then startup context is prepended (plugin order)
    injectStashedPromptPackets("session-first", output)
    prependStartupContext(output, "## SyberMem Startup Context\n- key conclusion")

    // Then: startup context is on top, with recall hints still present below it
    const first = output.system?.[0] ?? ""
    expect(first.startsWith("## SyberMem Startup Context")).toBe(true)
    const startupIdx = first.indexOf("## SyberMem Startup Context")
    const recallIdx = first.indexOf("## SyberMem Recall Hints")
    expect(recallIdx).toBeGreaterThan(startupIdx)
  })
})
