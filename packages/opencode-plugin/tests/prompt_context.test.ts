import { describe, expect, it } from "bun:test"
import { appendPromptPacket, classifyPackets, extractPromptText, injectStashedPromptPackets, stashPromptPackets } from "../src/prompt_context"

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
    expect(injected.injected).toBe(true)
    expect(injected.recallCount).toBe(1)
    expect(injected.habitCount).toBe(0)
    expect(output.system[0].startsWith("## SyberMem Recall Hints")).toBe(true)
  })

  it("returns no injection when no packets were stashed", () => {
    // Given / When
    const injected = injectStashedPromptPackets("session-empty", { system: ["base"] })

    // Then
    expect(injected).toEqual({ injected: false, recallCount: 0, habitCount: 0, habitCandidate: false, normCount: 0 })
  })

  it("classifies recall and habit packets with counts", () => {
    // Given
    const packets = [
      "## SyberMem Recall Hints\n- change-1\n- decision-2",
      "## User Habit Reminder\n- [habit-a] This user habit may apply: prefer docs.\n- [habit-b] Also.",
    ]

    // When
    const summary = classifyPackets(packets)

    // Then
    expect(summary.recallCount).toBe(2)
    expect(summary.habitCount).toBe(2)
    expect(summary.habitCandidate).toBe(false)
    expect(summary.injected).toBe(true)
  })

  it("flags a habit packet with no concrete habit as a preference candidate", () => {
    // Given
    const packets = ["## User Habit Reminder\n- This looks like a reusable user preference. Confirm with /sybermem-habit."]

    // When
    const summary = classifyPackets(packets)

    // Then
    expect(summary.habitCount).toBe(0)
    expect(summary.habitCandidate).toBe(true)
    expect(summary.injected).toBe(true)
  })

  it("counts scoped project-norm packets", () => {
    // Given
    const packets = [
      "## Relevant Project Norms\n- [norm-001] (topic:auth) Sessions expire in 30m\n- [norm-002] (path:api) Validate at boundary",
    ]

    // When
    const summary = classifyPackets(packets)

    // Then
    expect(summary.normCount).toBe(2)
    expect(summary.injected).toBe(true)
  })
})
