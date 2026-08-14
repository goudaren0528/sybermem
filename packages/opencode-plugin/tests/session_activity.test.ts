import { describe, expect, it } from "bun:test"
import {
  classifyToolSignal,
  extractEditedFile,
  getSessionActivity,
  isTodoBatchComplete,
  recordEditedFile,
  recordInjectedRecords,
  recordToolExecution,
  resetSessionActivity,
} from "../src/session_activity"

describe("session activity", () => {
  it("accumulates edit frequency per tracked file and normalizes separators", () => {
    // Given
    const id = `s-${crypto.randomUUID()}`
    try {
      // When
      recordEditedFile(id, "src\\auth.ts")
      recordEditedFile(id, "src/auth.ts")
      recordEditedFile(id, "src/util.ts")

      // Then
      const activity = getSessionActivity(id)
      expect(activity.editedFiles.get("src/auth.ts")).toBe(2)
      expect(activity.editedFiles.get("src/util.ts")).toBe(1)
    } finally {
      resetSessionActivity(id)
    }
  })

  it("ignores SyberMem-internal and VCS paths", () => {
    // Given
    const id = `s-${crypto.randomUUID()}`
    try {
      // When
      recordEditedFile(id, ".sybermem/INDEX.md")
      recordEditedFile(id, ".git/HEAD")

      // Then
      expect(getSessionActivity(id).editedFiles.size).toBe(0)
    } finally {
      resetSessionActivity(id)
    }
  })

  it("extracts an edited file from several plausible payload shapes and none when absent", () => {
    expect(extractEditedFile({ file: "src\\a.ts" })).toBe("src/a.ts")
    expect(extractEditedFile({ path: "src/b.ts" })).toBe("src/b.ts")
    expect(extractEditedFile({ filePath: "src/c.ts" })).toBe("src/c.ts")
    expect(extractEditedFile({ unknown: 1 })).toBe("")
    expect(extractEditedFile(null)).toBe("")
  })

  it("detects a completed todo batch only when every item is done", () => {
    expect(isTodoBatchComplete({ todos: [{ status: "completed" }, { status: "done" }] })).toBe(true)
    expect(isTodoBatchComplete({ todos: [{ status: "completed" }, { status: "pending" }] })).toBe(false)
    expect(isTodoBatchComplete({ todos: [] })).toBe(false)
    expect(isTodoBatchComplete({})).toBe(false)
    expect(isTodoBatchComplete(null)).toBe(false)
  })

  it("classifies passing tests and clean builds, ignoring non-bash and failing exits", () => {
    expect(classifyToolSignal({ tool: "bash", args: { command: "pytest -q" } }, { exit: 0 })).toBe("tests_passed")
    expect(classifyToolSignal({ tool: "bash", args: { command: "tsc --noEmit" } }, { exitCode: 0 })).toBe("build_ok")
    expect(classifyToolSignal({ tool: "bash", args: { command: "pytest" } }, { exit: 1 })).toBe(null)
    expect(classifyToolSignal({ tool: "read", args: { command: "pytest" } }, {})).toBe(null)
    expect(classifyToolSignal({ tool: "bash", args: { command: "ls" } }, {})).toBe(null)
  })

  it("records injected record ids from the recall packet only", () => {
    // Given
    const id = `s-${crypto.randomUUID()}`
    try {
      // When
      recordInjectedRecords(id, ["## SyberMem Recall Hints\n- 💡 [change-ABC123] match: topic\n- ⭐ [bug-def456] match: relation"])
      recordInjectedRecords(id, ["## User Habit Reminder\n- [habit-xyz] do the thing"])

      // Then: habit packet contributes nothing; recall ids are lowercased and deduped
      const activity = getSessionActivity(id)
      expect([...activity.injectedRecords].sort()).toEqual(["bug-def456", "change-abc123"])
    } finally {
      resetSessionActivity(id)
    }
  })

  it("records tool execution into the session accumulator", () => {
    // Given
    const id = `s-${crypto.randomUUID()}`
    try {
      // When
      recordToolExecution(id, { tool: "bash", args: { command: "bun test" } }, { exit: 0 })

      // Then
      expect(getSessionActivity(id).lastToolSignal).toBe("tests_passed")
    } finally {
      resetSessionActivity(id)
    }
  })
})
