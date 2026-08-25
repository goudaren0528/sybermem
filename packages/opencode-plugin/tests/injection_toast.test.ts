import { describe, expect, it } from "bun:test"
import { mkdirSync, rmSync, writeFileSync } from "fs"
import { tmpdir } from "os"
import { join } from "path"
import { buildPromptInjectionToastSummary } from "../src/injection_toast"
import { buildMemoryUsageEntry } from "../src/memory_usage"
import { SyberMemPlugin } from "../src/plugin"
import { stashPromptPackets } from "../src/prompt_context"
import { markPendingStartup } from "../src/startup_context"
import type { Shell, ShellCommand } from "../src/runtime"

function disabledShellCommand(): ShellCommand {
  return {
    cwd: () => disabledShellCommand(),
    text: async () => { throw new Error("shell disabled in test") },
    nothrow: () => disabledShellCommand(),
  }
}

const disabledShell: Shell = () => disabledShellCommand()

function createPluginRoot(): string {
  const root = join(tmpdir(), `sybermem-opencode-plugin-${crypto.randomUUID()}`)
  mkdirSync(join(root, ".sybermem"), { recursive: true })
  mkdirSync(join(root, ".claude"), { recursive: true })
  writeFileSync(join(root, ".claude", "settings.json"), "{}")
  return root
}

async function flushToasts(): Promise<void> {
  await Promise.resolve()
}

describe("prompt injection toast summary", () => {
  it("builds one structured summary from prompt-time counts and Phase 1 usage totals", () => {
    // Given
    const usageEntry = buildMemoryUsageEntry(
      {
        sessionID: "session-summary",
        packets: [
          "## SyberMem Recall Hints\n- [change-a] keep it small\n- [decision-b] prefer tests",
          "## User Habit Reminder\n- [habit-a] prefer docs",
          "## Relevant Project Norms\n- [norm-a] validate at boundary",
        ],
        startup: "## SyberMem Startup Context\n- [decision-startup] existing seam",
      },
      { timestamp: "2026-08-25T12:00:00.000Z" },
    )

    // When
    const summary = buildPromptInjectionToastSummary(
      {
        injected: true,
        recallCount: 2,
        recallChars: usageEntry.recall_chars,
        digestCount: 0,
        habitCount: 1,
        habitChars: usageEntry.habit_chars,
        habitCandidate: false,
        normCount: 1,
        normChars: usageEntry.norm_chars,
        injectedIds: ["change-a", "decision-b", "habit-a", "norm-a"],
      },
      usageEntry,
    )

    // Then
    expect(summary).toEqual({
      totalItems: 4,
      totalChars: usageEntry.recall_chars + usageEntry.habit_chars + usageEntry.norm_chars,
      laneCounts: [
        { lane: "recall", count: 2 },
        { lane: "habit", count: 1 },
        { lane: "norm", count: 1 },
      ],
    })
  })

  it("returns no summary when no prompt-time memory item was model-visible", () => {
    // Given / When / Then
    expect(buildPromptInjectionToastSummary(
      {
        injected: true,
        recallCount: 0,
        recallChars: 0,
        digestCount: 0,
        habitCount: 0,
        habitChars: 40,
        habitCandidate: true,
        normCount: 0,
        normChars: 0,
        injectedIds: [],
      },
      buildMemoryUsageEntry({ sessionID: "session-empty", packets: ["## User Habit Reminder\n- Confirm with /sybermem-habit"], startup: "" }),
    )).toBeNull()
  })

  it("emits exactly one summary toast after prompt-time memory reaches the transform", async () => {
    // Given
    const root = createPluginRoot()
    const messages: string[] = []
    try {
      const plugin = await SyberMemPlugin({
        $: disabledShell,
        directory: root,
        client: { tui: { showToast: async ({ body }) => { messages.push(body.message) } } },
      })
      stashPromptPackets("session-injected", [
        "## SyberMem Recall Hints\n- [change-a] keep it small\n- [decision-b] prefer tests",
        "## User Habit Reminder\n- [habit-a] prefer docs",
        "## Relevant Project Norms\n- [norm-a] validate at boundary",
      ])

      // When
      await plugin["experimental.chat.system.transform"]?.({ sessionID: "session-injected" }, { system: ["base"] })
      await flushToasts()

      // Then
      expect(messages).toHaveLength(1)
      expect(messages[0]).toContain("items=4")
      expect(messages[0]).toContain("chars=")
      expect(messages[0]).toContain("recall=2")
      expect(messages[0]).toContain("habit=1")
      expect(messages[0]).toContain("norm=1")
      expect(messages[0]).not.toContain("applied 1 user habit reminder")
      expect(messages[0]).not.toContain("project norm")
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })

  it("preserves the startup-context toast unchanged", async () => {
    // Given
    const root = createPluginRoot()
    const messages: string[] = []
    writeFileSync(join(root, ".sybermem", "INDEX.md"), "## Key Conclusions\n- [decision-a] Keep the existing seam\n\n## Topic Index\n- seam: decision-a\n")
    try {
      const plugin = await SyberMemPlugin({
        $: disabledShell,
        directory: root,
        client: { tui: { showToast: async ({ body }) => { messages.push(body.message) } } },
      })
      markPendingStartup("session-startup")

      // When
      await plugin["experimental.chat.system.transform"]?.({ sessionID: "session-startup" }, { system: ["base"] })
      await flushToasts()

      // Then
      expect(messages).toEqual(["⭐ SyberMem: injected project startup context into this session"])
    } finally {
      rmSync(root, { recursive: true, force: true })
    }
  })
})
