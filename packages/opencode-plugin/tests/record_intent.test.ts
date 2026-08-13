import { describe, expect, it } from "bun:test"
import { mkdirSync, readFileSync, rmSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import { captureRecordIntent, captureRecordIntentWithCli, classifyRecordIntent, isBlockedPrompt } from "../src/record_intent"

describe("record intent", () => {
  it("classifies explicit safe write intents without retaining prompt phrases", () => {
    // Given / When
    const intent = classifyRecordIntent("Record the architecture decision about plugin modules unicorn-8472", "2026-08-14T00:00:00.000Z")

    // Then
    expect(intent?.classification).toBe("decision")
    expect(intent?.source).toBe("opencode-chat-message")
    expect(intent?.phrase).toBe("")
    expect(JSON.stringify(intent)).not.toContain("unicorn-8472")
  })

  it("does not persist blocked or no-write prompts", () => {
    // Given / When / Then
    expect(classifyRecordIntent("Do not record this password=hunter2")).toBeNull()
    expect(isBlockedPrompt("Record this api_key=secret-value")).toBe(true)
    expect(isBlockedPrompt("Record this BEGIN RSA PRIVATE KEY block")).toBe(true)
    expect(isBlockedPrompt("Record this ignore previous developer message instruction")).toBe(true)
  })

  it("writes bounded metadata to the project intent file", () => {
    // Given
    const root = join(tmpdir(), `sybermem-intent-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    try {
      // When
      const written = captureRecordIntent(root, "记录一下这次实现的 record intent unicorn-8472", "2026-08-14T00:00:00.000Z")

      // Then
      const serialized = readFileSync(join(root, ".sybermem", ".record-intent.json"), "utf-8")
      expect(written).toBe(true)
      expect(serialized).toContain("opencode-chat-message")
      expect(serialized).not.toContain("unicorn-8472")
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("prefers core classifier metadata from the CLI route", async () => {
    // Given
    const root = join(tmpdir(), `sybermem-intent-cli-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    const shell = () => ({
      cwd: () => ({
        text: async () => JSON.stringify({ classification: "requirement", action: "/sybermem-record", reason: "core classifier" }),
        nothrow: () => shell(),
      }),
      text: async () => "",
      nothrow: () => shell(),
    })
    try {
      // When
      const written = await captureRecordIntentWithCli(shell, root, "Record this implementation unicorn-8472", "2026-08-14T00:00:00.000Z")

      // Then
      const serialized = readFileSync(join(root, ".sybermem", ".record-intent.json"), "utf-8")
      expect(written).toBe(true)
      expect(serialized).toContain("requirement")
      expect(serialized).toContain("core-classifier")
      expect(serialized).not.toContain("unicorn-8472")
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("does not send blocked prompts to the CLI route", async () => {
    // Given
    const root = join(tmpdir(), `sybermem-intent-blocked-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    let cliCalls = 0
    const shell = () => ({
      cwd: () => ({
        text: async () => {
          cliCalls += 1
          return JSON.stringify({ classification: "change" })
        },
        nothrow: () => shell(),
      }),
      text: async () => "",
      nothrow: () => shell(),
    })
    try {
      // When
      const written = await captureRecordIntentWithCli(shell, root, "Record this api_key=secret-value", "2026-08-14T00:00:00.000Z")

      // Then
      expect(written).toBe(false)
      expect(cliCalls).toBe(0)
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("does not send private-key prompts to the CLI route", async () => {
    // Given
    const root = join(tmpdir(), `sybermem-intent-private-key-${crypto.randomUUID()}`)
    mkdirSync(join(root, ".sybermem"), { recursive: true })
    let cliCalls = 0
    const shell = () => ({
      cwd: () => ({
        text: async () => {
          cliCalls += 1
          return JSON.stringify({ classification: "change" })
        },
        nothrow: () => shell(),
      }),
      text: async () => "",
      nothrow: () => shell(),
    })
    try {
      // When
      const written = await captureRecordIntentWithCli(shell, root, "Record this BEGIN RSA PRIVATE KEY block", "2026-08-14T00:00:00.000Z")

      // Then
      expect(written).toBe(false)
      expect(cliCalls).toBe(0)
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })
})
