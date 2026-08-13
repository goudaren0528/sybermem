import { describe, expect, it } from "bun:test"
import { appendPromptPacket, extractPromptText, injectStashedPromptPackets, stashPromptPackets } from "../src/prompt_context"

describe("prompt context helpers", () => {
  it("extracts only text parts from chat.message output", () => {
    // Given / When
    const text = extractPromptText({ parts: [{ type: "tool", text: "ignore" }, { type: "text", text: "record" }, { type: "text", text: "this" }] })

    // Then
    expect(text).toBe("record this")
  })

  it("filters prompt packets by heading", () => {
    // Given
    const packets: string[] = []

    // When
    appendPromptPacket(packets, "## SyberMem Recall Hints\n- change-1", "## SyberMem Recall Hints")
    appendPromptPacket(packets, "raw prompt text", "## SyberMem Recall Hints")

    // Then
    expect(packets).toEqual(["## SyberMem Recall Hints\n- change-1"])
  })

  it("injects stashed packets into the first system block", () => {
    // Given
    stashPromptPackets("session-a", ["## SyberMem Recall Hints\n- change-1"])
    const output = { system: ["base"] }

    // When
    const injected = injectStashedPromptPackets("session-a", output)

    // Then
    expect(injected).toBe(true)
    expect(output.system[0].startsWith("## SyberMem Recall Hints")).toBe(true)
  })
})
