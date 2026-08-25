import { describe, expect, it } from "bun:test"
import { mkdirSync, readFileSync, rmSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import { computeRecallOutcome, flushRecallOutcome } from "../src/recall_outcome"
import { getSessionActivity, recordInjectedRecords, resetSessionActivity } from "../src/session_activity"
import type { ShellCommand } from "../src/runtime"

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
    expect(outcome.measurable).toBe(1)
    expect(outcome.unmeasurable).toBe(1)
  })

  it("returns a null-precision empty outcome when nothing is measurable", () => {
    // Given: injected records but no anchors at all
    const outcome = computeRecallOutcome(["change-a"], { "change-a": [] }, new Set(["src/auth.ts"]))

    // Then
    expect(outcome.injected).toBe(0)
    expect(outcome.precision).toBe(null)
    expect(outcome.measurable).toBe(0)
    expect(outcome.unmeasurable).toBe(1)
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

  it("flushes one bounded session outcome into the existing usage journal", async () => {
    // Given: one injected record with no edited file, so recall is unmeasurable
    const root = join(tmpdir(), `sybermem-session-outcome-${crypto.randomUUID()}`)
    const sessionID = `session-${crypto.randomUUID()}`
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    recordInjectedRecords(sessionID, ["## SyberMem Recall Hints\n- [change-a] private prompt text"])
    const activity = getSessionActivity(sessionID)
    activity.memoryTurns = 1
    activity.memoryItems = 1
    activity.memoryChars = 42
    try {
      // When
      const command: ShellCommand = {
        cwd: () => command,
        text: async () => '{"records":{"change-a":[]}}',
        nothrow: () => command,
      }
      const outcome = await flushRecallOutcome(
        () => command,
        root,
        activity,
        sessionID,
        "2026-08-25T12:00:00.000Z",
      )

      // Then: measurable semantics stay unchanged, while unmeasurable is exposed
      expect(outcome.injected).toBe(0)
      expect(outcome.measurable).toBe(0)
      expect(outcome.unmeasurable).toBe(1)
      const lines = readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf-8").trim().split("\n")
      const entry: unknown = JSON.parse(lines[0] ?? "{}")
      expect(entry).toMatchObject({ schema_version: 1, host: "opencode", event: "session_outcome", session_id: sessionID, memory_turns: 1, memory_items: 1, memory_chars: 42, recall_evidence_available: true, recall_measurable: 0, recall_unmeasurable: 1, recall_hit: 0, recall_precision: null })
      expect(JSON.stringify(entry)).not.toContain("private prompt text")
    } finally {
      resetSessionActivity(sessionID)
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("does not attribute recall metrics when record-files evidence lookup fails", async () => {
    // Given: injected recall exists, but Core cannot provide related_files evidence
    const root = join(tmpdir(), `sybermem-session-outcome-unavailable-${crypto.randomUUID()}`)
    const sessionID = `session-${crypto.randomUUID()}`
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    recordInjectedRecords(sessionID, ["## SyberMem Recall Hints\n- [change-a] private prompt text"])
    const activity = getSessionActivity(sessionID)
    activity.memoryTurns = 1
    activity.memoryItems = 1
    activity.memoryChars = 42
    try {
      // When
      const command: ShellCommand = {
        cwd: () => command,
        text: async () => { throw new Error("record-files unavailable") },
        nothrow: () => command,
      }
      const outcome = await flushRecallOutcome(
        () => command,
        root,
        activity,
        sessionID,
        "2026-08-25T12:00:00.000Z",
      )

      // Then: unavailable evidence is not relabeled as anchorless evidence
      expect(outcome.recallEvidenceAvailable).toBe(false)
      expect(outcome.measurable).toBe(0)
      expect(outcome.unmeasurable).toBe(0)
      expect(outcome.hit).toBe(0)
      expect(outcome.precision).toBe(null)
      const lines = readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf-8").trim().split("\n")
      const entry: unknown = JSON.parse(lines[0] ?? "{}")
      expect(entry).toMatchObject({ schema_version: 1, host: "opencode", event: "session_outcome", session_id: sessionID, recall_evidence_available: false, recall_measurable: 0, recall_unmeasurable: 0, recall_hit: 0, recall_precision: null })
      expect(() => readFileSync(join(root, ".sybermem", ".recall-outcomes.jsonl"), "utf-8")).toThrow()
    } finally {
      resetSessionActivity(sessionID)
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("does not write an outcome for a fresh activity window", async () => {
    // Given: no activity has been recorded for this session
    const root = join(tmpdir(), `sybermem-session-outcome-empty-${crypto.randomUUID()}`)
    const sessionID = `session-${crypto.randomUUID()}`
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    const activity = getSessionActivity(sessionID)
    try {
      // When
      await flushRecallOutcome(async () => ({ text: async () => "{}", cwd: () => undefined, nothrow: () => undefined }), root, activity, sessionID)

      // Then
      expect(() => readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf-8")).toThrow()
    } finally {
      resetSessionActivity(sessionID)
      rmSync(root, { recursive: true, force: true })
    }
  })
})
