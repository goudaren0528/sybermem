import { describe, expect, it } from "bun:test"
import { classifyFollowup } from "../src/followup"

describe("followup trigger reasons", () => {
  it("promotes to a record nudge on passing tests even below the file-count threshold", () => {
    // Given: a single edited file (below RECORD_FILE_THRESHOLD) but tests passed
    const result = classifyFollowup(["src/auth.ts"], 0, {}, { toolSignal: "tests_passed", todoCompletedBatches: 0, editFocus: null })

    // Then: it is a record nudge tagged with the semantic reason, not a file count
    expect(result.type).toBe("record")
    expect(result.triggerReason).toBe("tests_passed")
    expect(result.message).toContain("tests passed")
  })

  it("promotes on a completed todo batch", () => {
    const result = classifyFollowup(["src/util.ts"], 0, {}, { toolSignal: null, todoCompletedBatches: 1, editFocus: null })
    expect(result.type).toBe("record")
    expect(result.triggerReason).toBe("todo_batch_done")
  })

  it("falls back to the existing file-count heuristic when no activity signal is present", () => {
    // Given: five plain files, no activity signals
    const files = ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]
    const result = classifyFollowup(files, 0, {})
    expect(result.type).toBe("record")
    expect(result.triggerReason).toBe("file_count")
  })

  it("stays silent when nothing qualifies and there is no activity signal", () => {
    const result = classifyFollowup(["a.txt"], 0, {})
    expect(result.type).toBe("none")
    expect(result.triggerReason).toBe("none")
  })
})
