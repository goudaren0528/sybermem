import { describe, expect, it } from "bun:test"
import { lowSignalRecallToast, parseRecallHealth } from "../src/recall_health_signal"

describe("recall health signal", () => {
  it("parses a low_signal recall health verdict from memory-stats json", () => {
    // Given
    const json = JSON.stringify({ recall_health: { status: "low_signal", recall_rate: 0.1, hint: "add topics" } })

    // When
    const health = parseRecallHealth(json)

    // Then
    expect(health?.status).toBe("low_signal")
    expect(health?.hint).toBe("add topics")
  })

  it("returns null for missing or malformed json", () => {
    // Given / When / Then
    expect(parseRecallHealth("")).toBeNull()
    expect(parseRecallHealth("not json")).toBeNull()
    expect(parseRecallHealth("{}")).toBeNull()
  })

  it("builds a toast for low_signal and low_relevance, but stays silent otherwise", () => {
    // Given / When / Then
    expect(lowSignalRecallToast({ status: "low_signal", hint: "add topics" })).toContain("quality is low")
    const relevance = lowSignalRecallToast({ status: "low_relevance", hint: "stale related_files" })
    expect(relevance).toContain("relevance is low")
    expect(relevance).toContain("stale related_files")
    expect(lowSignalRecallToast({ status: "healthy", hint: "ok" })).toBeNull()
    expect(lowSignalRecallToast({ status: "no_log", hint: "no log" })).toBeNull()
    expect(lowSignalRecallToast({ status: "no_activity", hint: "quiet" })).toBeNull()
  })
})
