import { describe, expect, it } from "bun:test"
import { computeRecallOutcome } from "../src/recall_outcome"

describe("recall outcome", () => {
  it("counts a record as a hit when any related file was edited", () => {
    // Given: two injected records, one whose related file was edited
    const injected = ["change-a", "bug-b"]
    const related = { "change-a": ["src/auth.ts", "src/token.ts"], "bug-b": ["src/pay.ts"] }
    const edited = new Set(["src/auth.ts", "src/unrelated.ts"])

    // When
    const outcome = computeRecallOutcome(injected, related, edited)

    // Then
    expect(outcome.injected).toBe(2)
    expect(outcome.hit).toBe(1)
    expect(outcome.precision).toBe(0.5)
    expect(outcome.hitRecords).toEqual(["change-a"])
    expect(outcome.missRecords).toEqual(["bug-b"])
  })

  it("excludes records without a related_files anchor from the denominator", () => {
    // Given: one anchored+hit record and one anchorless record
    const injected = ["change-a", "change-noanchor"]
    const related = { "change-a": ["src/auth.ts"], "change-noanchor": [] }
    const edited = new Set(["src/auth.ts"])

    // When
    const outcome = computeRecallOutcome(injected, related, edited)

    // Then: precision is 1/1, not 1/2 — the anchorless record is not a miss
    expect(outcome.injected).toBe(1)
    expect(outcome.hit).toBe(1)
    expect(outcome.precision).toBe(1)
  })

  it("returns a null-precision empty outcome when nothing is measurable", () => {
    // Given: injected records but no anchors at all
    const outcome = computeRecallOutcome(["change-a"], { "change-a": [] }, new Set(["src/auth.ts"]))

    // Then
    expect(outcome.injected).toBe(0)
    expect(outcome.precision).toBe(null)
  })

  it("normalizes path separators on both sides before matching", () => {
    // Given: related file uses forward slashes, edited set uses backslashes
    const outcome = computeRecallOutcome(["change-a"], { "change-a": ["src/auth.ts"] }, new Set(["src\\auth.ts"]))

    // Then: they still match
    expect(outcome.hit).toBe(1)
    expect(outcome.precision).toBe(1)
  })

  it("matches injected ids case-insensitively against the related map", () => {
    // Given: injected id is upper-case, map key is lower-case
    const outcome = computeRecallOutcome(["CHANGE-A"], { "change-a": ["src/auth.ts"] }, new Set(["src/auth.ts"]))

    // Then
    expect(outcome.hit).toBe(1)
  })
})
