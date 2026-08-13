import { describe, expect, it } from "bun:test"
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import { boundedJsonlAppend, loadNudgeState } from "../src/state"

describe("boundedJsonlAppend", () => {
  it("keeps only the newest entries", () => {
    // Given
    const root = join(tmpdir(), `sybermem-state-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    try {
      // When
      for (let index = 0; index < 5; index += 1) boundedJsonlAppend(root, ".sample.jsonl", { index }, 3)

      // Then
      const entries = readFileSync(join(root, ".sybermem", ".sample.jsonl"), "utf-8")
        .trim()
        .split("\n")
        .map((line) => JSON.parse(line))
      expect(entries.map((entry) => entry.index)).toEqual([2, 3, 4])
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("does not read oversized existing logs before appending", () => {
    // Given
    const root = join(tmpdir(), `sybermem-state-large-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    writeFileSync(join(root, ".sybermem", ".sample.jsonl"), "x".repeat(1_000_001), "utf-8")
    try {
      // When
      boundedJsonlAppend(root, ".sample.jsonl", { index: 1 }, 3)

      // Then
      const lines = readFileSync(join(root, ".sybermem", ".sample.jsonl"), "utf-8").trim().split("\n")
      expect(lines).toHaveLength(1)
      expect(JSON.parse(lines[0]).index).toBe(1)
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })
})

describe("loadNudgeState", () => {
  it("sanitizes corrupt persisted state into iterable shapes", () => {
    // Given
    const root = join(tmpdir(), `sybermem-nudge-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    writeFileSync(join(root, ".sybermem", ".nudge-state.json"), JSON.stringify({ theme_recent_stops: { docs: "bad" }, digest_nudged_at_window_len: { docs: "bad", cli: 2 }, last_nudge: { platform: "opencode", type: "record", theme: "docs", date: "2026-08-14" } }))
    try {
      // When
      const state = loadNudgeState(root)

      // Then
      expect(state.theme_recent_stops?.docs).toBeUndefined()
      expect(state.digest_nudged_at_window_len?.cli).toBe(2)
      expect(state.last_nudge?.type).toBe("record")
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })
})
