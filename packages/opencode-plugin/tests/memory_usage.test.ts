import { describe, expect, it } from "bun:test"
import { mkdirSync, readFileSync, rmSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import { appendMemoryUsage, buildMemoryUsageEntry } from "../src/memory_usage"
import { compactJsonlJournal } from "../src/state"

function readSessionEntry(raw: string): { readonly session_id: string } {
  const parsed: unknown = JSON.parse(raw)
  if (typeof parsed !== "object" || parsed === null) throw new Error("expected usage entry object")
  const sessionID = Reflect.get(parsed, "session_id")
  if (typeof sessionID !== "string") throw new Error("expected usage session id")
  return { session_id: sessionID }
}

describe("memory usage journal", () => {
  it("builds lane measurements from model-visible rendered packets", () => {
    // Given: rendered recall, habit, norm, and startup packets
    const entry = buildMemoryUsageEntry(
      {
        sessionID: "session-usage",
        packets: [
          "## SyberMem Recall Hints\n- [change-a] keep it small",
          "## User Habit Reminder\n- [habit-a] prefer tests",
          "## Relevant Project Norms\n- [norm-a] validate at boundary",
        ],
        startup: "## SyberMem Startup Context\n- [decision-a] use the existing seam",
      },
      { timestamp: "2026-08-25T12:00:00.000Z" },
    )

    // Then: only bounded measurements and IDs are retained
    expect(entry).toEqual({
      schema_version: 1,
      timestamp: "2026-08-25T12:00:00.000Z",
      host: "opencode",
      session_id: "session-usage",
      total_items: 4,
      total_chars: 219,
      recall_items: 1,
      recall_chars: 51,
      habit_items: 1,
      habit_chars: 47,
      norm_items: 1,
      norm_chars: 57,
      startup_items: 1,
      startup_chars: 64,
      injected_ids: ["change-a", "habit-a", "norm-a", "decision-a"],
      startup_present: true,
    })
    expect(JSON.stringify(entry)).not.toContain("keep it small")
    expect(JSON.stringify(entry)).not.toContain("prefer tests")
  })

  it("records no model-visible usage when all lanes are empty", () => {
    // Given: a transform with no inserted packets or startup context
    const entry = buildMemoryUsageEntry(
      { sessionID: "session-empty", packets: [], startup: "" },
      { timestamp: "2026-08-25T12:00:00.000Z" },
    )

    // Then: the journal entry remains a zero-cost abstention measurement
    expect(entry.total_items).toBe(0)
    expect(entry.total_chars).toBe(0)
    expect(entry.startup_present).toBe(false)
    expect(entry.injected_ids).toEqual([])
  })

  it("appends metadata for model-visible memory", () => {
    // Given: a project memory directory and one model-visible packet
    const root = join(tmpdir(), `sybermem-memory-usage-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    try {
      // When: usage metadata is appended
      appendMemoryUsage(root, {
        sessionID: "session-write",
        packets: ["## SyberMem Recall Hints\n- [change-a] private content"],
        startup: "",
      }, { timestamp: "2026-08-25T12:00:00.000Z" })

      // Then: the persisted line has measurements and IDs, never packet content
      const line = readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf-8").trim()
      expect(line).toContain('"schema_version":1')
      expect(line).toContain('"injected_ids":["change-a"]')
      expect(line).not.toContain("private content")
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("extracts ids only from structured memory item lines", () => {
    // Given: body text contains ID-shaped strings that are not item anchors
    const entry = buildMemoryUsageEntry(
      {
        sessionID: "session-structured-ids",
        packets: [
          "## SyberMem Recall Hints\n- [change-real] body mentions bug-forged and norm-forged\nplain decision-forged",
          "## User Habit Reminder\n- [habit-real] body mentions habit-forged",
          "## Relevant Project Norms\n- [norm-real] body mentions requirement-forged",
        ],
        startup: "## SyberMem Startup Context\n- [digest-real] body mentions change-forged",
      },
      { timestamp: "2026-08-25T12:00:00.000Z" },
    )

    // Then: only structured bracket ids are retained
    expect(entry.injected_ids).toEqual(["change-real", "habit-real", "norm-real", "digest-real"])
  })

  it("bounds session id and injected id cardinality", () => {
    // Given: a long session id and many structured recall items
    const packet = ["## SyberMem Recall Hints", ...Array.from({ length: 60 }, (_, index) => `- [change-${String(index).padStart(2, "0")}] item`)].join("\n")

    // When
    const entry = buildMemoryUsageEntry(
      { sessionID: `session-${"x".repeat(200)}`, packets: [packet], startup: "" },
      { timestamp: "2026-08-25T12:00:00.000Z" },
    )

    // Then
    expect(entry.session_id.length).toBeLessThanOrEqual(80)
    expect(entry.injected_ids).toHaveLength(40)
    expect(entry.injected_ids[0]).toBe("change-00")
    expect(entry.injected_ids[39]).toBe("change-39")
  })

  it("keeps only the newest 200 usage entries", () => {
    // Given: a project memory directory and 201 model-visible injections
    const root = join(tmpdir(), `sybermem-memory-usage-cap-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    try {
      // When: all injections are appended through the production journal writer
      for (let index = 0; index < 201; index += 1) {
        appendMemoryUsage(root, {
          sessionID: `session-${index}`,
          packets: ["## SyberMem Recall Hints\n- [change-a] private content"],
          startup: "",
        }, { timestamp: `2026-08-25T12:00:${String(index).padStart(2, "0")}.000Z` })
      }

      compactJsonlJournal(root, ".memory-usage.jsonl", 200)

      // Then: lifecycle compaction keeps only the newest 200 entries
      const entries = readFileSync(join(root, ".sybermem", ".memory-usage.jsonl"), "utf-8")
        .trim()
        .split("\n")
        .map(readSessionEntry)
      expect(entries).toHaveLength(200)
      expect(entries[0]?.session_id).toBe("session-1")
      expect(entries[199]?.session_id).toBe("session-200")
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("does not throw when the bounded journal cannot be written", () => {
    // Given: a missing project memory directory
    const root = join(tmpdir(), `sybermem-memory-usage-missing-${crypto.randomUUID()}`)

    // When / Then: fail-open logging does not reject the transform-adjacent call
    expect(() => appendMemoryUsage(root, { sessionID: "session-fail-open", packets: ["## SyberMem Recall Hints\n- [change-a] content"], startup: "" })).not.toThrow()
  })
})
