import { describe, expect, it } from "bun:test"
import { mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import { boundedJsonlAppend, compactJsonlJournal, loadNudgeState } from "../src/state"

describe("boundedJsonlAppend", () => {
  it("appends without compacting on the write hot path", () => {
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
      expect(entries.map((entry) => entry.index)).toEqual([0, 1, 2, 3, 4])
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("compacts bounded journals at the lifecycle boundary", () => {
    // Given
    const root = join(tmpdir(), `sybermem-state-compact-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    try {
      for (let index = 0; index < 5; index += 1) boundedJsonlAppend(root, ".sample.jsonl", { index }, 3)

      // When
      compactJsonlJournal(root, ".sample.jsonl", 3)

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
      const content = readFileSync(join(root, ".sybermem", ".sample.jsonl"), "utf-8")
      expect(content.endsWith(`${JSON.stringify({ index: 1 })}\n`)).toBe(true)
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("does not write through a symlinked memory directory", () => {
    // Given
    const root = join(tmpdir(), `sybermem-state-symlink-dir-${crypto.randomUUID()}`)
    const outside = join(tmpdir(), `sybermem-state-outside-dir-${crypto.randomUUID()}`)
    mkdirSync(root, { recursive: true })
    mkdirSync(outside, { recursive: true })
    try {
      symlinkSync(outside, join(root, ".sybermem"), "junction")

      // When / Then: fail-open append refuses the redirected memory directory
      expect(() => boundedJsonlAppend(root, ".sample.jsonl", { index: 1 }, 3)).not.toThrow()
      expect(() => readFileSync(join(outside, ".sample.jsonl"), "utf-8")).toThrow()
    } finally {
      rmSync(root, { recursive: true, force: true })
      rmSync(outside, { recursive: true, force: true })
    }
  })

  it("does not write oversized journal entries", () => {
    // Given
    const root = join(tmpdir(), `sybermem-state-entry-cap-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    try {
      // When / Then: oversized metadata is skipped fail-open
      expect(() => boundedJsonlAppend(root, ".sample.jsonl", { payload: "x".repeat(20_000) }, 3)).not.toThrow()
      expect(() => readFileSync(join(root, ".sybermem", ".sample.jsonl"), "utf-8")).toThrow()
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
