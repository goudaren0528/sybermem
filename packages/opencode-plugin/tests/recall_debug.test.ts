import { describe, expect, it } from "bun:test"
import { mkdirSync, readFileSync, rmSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import { appendRecallDebug, buildRecallDebugEntry } from "../src/recall_debug"
import { compactJsonlJournal } from "../src/state"

describe("recall debug", () => {
  it("builds inject entries from bounded recall packet metadata", () => {
    // Given
    const packet = "## SyberMem Recall Hints\n- 💡 [change-abc123] match: topic\nsecret-unicorn-8472"

    // When
    const entry = buildRecallDebugEntry([packet], "2026-08-14T00:00:00.000Z")

    // Then
    expect(entry.event).toBe("inject")
    expect(entry.record_ids).toEqual(["change-abc123"])
    expect(entry.match_classes).toEqual(["topic"])
    expect(JSON.stringify(entry)).not.toContain("secret-unicorn-8472")
  })

  it("builds abstain entries when recall is absent", () => {
    // Given / When
    const entry = buildRecallDebugEntry([], "2026-08-14T00:00:00.000Z")

    // Then
    expect(entry.event).toBe("abstain")
    expect(entry.reason).toBe("no-high-signal-recall")
  })

  it("caps the debug log to the newest 200 entries", () => {
    // Given
    const root = join(tmpdir(), `sybermem-recall-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    try {
      // When
      for (let index = 0; index < 205; index += 1) appendRecallDebug(root, [], `2026-08-14T00:00:${String(index).padStart(2, "0")}.000Z`)

      compactJsonlJournal(root, ".recall-debug.jsonl", 200)

      // Then
      const lines = readFileSync(join(root, ".sybermem", ".recall-debug.jsonl"), "utf-8").trim().split("\n")
      expect(lines).toHaveLength(200)
      expect(lines[0]).toContain("00:05")
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })
})
