import { describe, expect, it } from "bun:test"
import { captureHabitIntentWithCli, looksLikeHabitIntent } from "../src/habit_intent"
import type { Shell } from "../src/runtime"

// Minimal Shell stub: records the command and returns a canned stdout.
function stubShell(stdout: string): { shell: Shell; commands: string[] } {
  const commands: string[] = []
  const shell = ((strings: TemplateStringsArray, ...values: readonly string[]) => {
    let cmd = ""
    strings.forEach((s, i) => { cmd += s; if (i < values.length) cmd += values[i] })
    commands.push(cmd)
    const chain = { cwd: () => chain, nothrow: () => chain, text: async () => stdout }
    return chain
  }) as unknown as Shell
  return { shell, commands }
}

describe("habit intent capture", () => {
  it("reports a capture with the classified habit type", async () => {
    // Given: Core returns a captured candidate
    const { shell } = stubShell(JSON.stringify({ captured: true, candidate: { candidate_only: true, habit_type: "communication" } }))

    // When
    const result = await captureHabitIntentWithCli(shell, "/root", "以后都用中文回复我")

    // Then
    expect(result.captured).toBe(true)
    expect(result.habitType).toBe("communication")
    // No suggested_scope in this canned payload → empty, not undefined
    expect(result.suggestedScope).toBe("")
  })

  it("suppresses a single-project convention before the CLI is invoked", async () => {
    // Given: a single-project convention. The prefilter rejects it, so Core's canned
    // project-scope response is never consumed and no subprocess is spawned.
    const { shell, commands } = stubShell(JSON.stringify({ captured: true, candidate: { habit_type: "workflow", suggested_scope: "project" } }))

    // When
    const result = await captureHabitIntentWithCli(shell, "/root", "以后这个项目的 PR 都要小")

    // Then: no capture, and the CLI was never called
    expect(result.captured).toBe(false)
    expect(result.suggestedScope).toBe("")
    expect(commands).toEqual([])
  })

  it("propagates suggested_scope from Core for a prompt that passes the prefilter", async () => {
    // Given: a genuine cross-project preference passes the prefilter, so the CLI runs
    // and its suggested_scope is mapped straight through.
    const { shell, commands } = stubShell(JSON.stringify({ captured: true, candidate: { habit_type: "communication", suggested_scope: "user" } }))

    // When
    const result = await captureHabitIntentWithCli(shell, "/root", "我习惯回复都用中文")

    // Then: the result mapping carries the scope, and the CLI was invoked once
    expect(result.captured).toBe(true)
    expect(result.suggestedScope).toBe("user")
    expect(commands.length).toBe(1)
  })

  it("routes through the habit intent CLI with an argparse-safe --prompt= form", async () => {
    // Given
    const { shell, commands } = stubShell(JSON.stringify({ captured: true, candidate: { habit_type: "workflow" } }))

    // When
    await captureHabitIntentWithCli(shell, "/root", "always prefer plans")

    // Then: the command uses `--prompt=` so a leading-dash prompt is not mis-parsed
    expect(commands.some((c) => c.includes("habit intent --prompt=") && c.includes("always prefer plans"))).toBe(true)
  })

  it("skips the CLI entirely for a non-preference prompt (hot-path cost guard)", async () => {
    // Given
    const { shell, commands } = stubShell(JSON.stringify({ captured: false, candidate: null }))

    // When: an ordinary work prompt with no preference language
    const result = await captureHabitIntentWithCli(shell, "/root", "fix the crash in the parser")

    // Then: no subprocess was spawned and no capture occurred
    expect(result.captured).toBe(false)
    expect(commands).toEqual([])
  })

  it("prefilter recognizes ASCII and CJK preference language only", () => {
    expect(looksLikeHabitIntent("always prefer plans")).toBe(true)
    expect(looksLikeHabitIntent("remember that I prefer plans")).toBe(true)
    expect(looksLikeHabitIntent("以后都用中文回复")).toBe(true)
    expect(looksLikeHabitIntent("fix the crash in the parser")).toBe(false)
    expect(looksLikeHabitIntent("")).toBe(false)
  })

  it("prefilter recognizes the expanded ASCII and CJK trigger vocabulary", () => {
    // Expanded ASCII triggers
    expect(looksLikeHabitIntent("usually I want tests first")).toBe(true)
    expect(looksLikeHabitIntent("make this the default going forward")).toBe(true)
    expect(looksLikeHabitIntent("from now on, follow this convention")).toBe(true)
    // Expanded CJK triggers that previously slipped through the prefilter
    expect(looksLikeHabitIntent("总是先出方案")).toBe(true)
    expect(looksLikeHabitIntent("每次都跑测试")).toBe(true)
    expect(looksLikeHabitIntent("默认用中文")).toBe(true)
    expect(looksLikeHabitIntent("以后尽量保持 PR 小而聚焦")).toBe(true)
    expect(looksLikeHabitIntent("以后这个仓库都遵守这个约定")).toBe(false)
    // Still silent for ordinary work talk
    expect(looksLikeHabitIntent("重启一下服务")).toBe(false)
  })

  it("prefilter rejects noisy habit-system and one-off task prompts", () => {
    const falsePositivePrompts = [
      "我的项目给我记录的habit看起来跟用户偏好/长期要求一点关系都没有。我想知道为什么会命中候选。",
      "TASK: Review SyberMem's current memory/habit/norm recall logic and product design for recall accuracy improvements.",
      "CONTEXT: The user wants a review of current SyberMem memory/habit/norm recall logic and product design.",
      "AXIS: SyberMem user habit and project norm recall product design.",
      "Research how to improve preference detection and habit candidate capture.",
      "Review current SyberMem memory/habit/norm recall logic and product design.",
      "还有一个问题，顶部选择项目的下拉按钮错位，然后更新todo list，及时更新相关文档，包括readme，然后提交PR发布，PR要规范。",
    ]

    for (const prompt of falsePositivePrompts) expect(looksLikeHabitIntent(prompt)).toBe(false)
  })

  it("prefilter preserves explicit durable user preferences", () => {
    expect(looksLikeHabitIntent("以后回复我都用中文")).toBe(true)
    expect(looksLikeHabitIntent("请记住我偏好先看计划再改代码")).toBe(true)
    expect(looksLikeHabitIntent("always prefer concise PR summaries")).toBe(true)
    expect(looksLikeHabitIntent("Please remember that I usually want a plan before edits")).toBe(true)
  })

  it("prefilter rejects the four observed project-discussion false positives", () => {
    const falsePositivePrompts = [
      "总结下最近sybermem遇到的bug，看下是否可以提一些通用的tuantuanrent的规范和经验，避免以后重复发生。你先分析",
      "不追求有 diff 的 PR，做好记录。以后规范有diff的pr就行，dev和main都是",
      "dev 作为长期集成分支：dev 从当前 main(bbb52b7) 建出，以后走 feature → dev → main。",
      "那以后每次更新都要这样吗，有没有通用的更新方式？太麻烦了这样",
    ]

    for (const prompt of falsePositivePrompts) expect(looksLikeHabitIntent(prompt)).toBe(false)
  })

  it("prefilter preserves explicit personal preferences across English and Chinese", () => {
    expect(looksLikeHabitIntent("以后都用中文")).toBe(true)
    expect(looksLikeHabitIntent("我习惯回复都用中文")).toBe(true)
    expect(looksLikeHabitIntent("always prefer plans before implementation")).toBe(true)
    expect(looksLikeHabitIntent("please remember that I prefer concise replies")).toBe(true)
    expect(looksLikeHabitIntent("我希望以后每次先给计划再改代码")).toBe(true)
  })

  it("prefilter preserves polite-question preferences but still rejects real questions", () => {
    // A durable preference that ends with a polite confirmation tail is still a preference.
    expect(looksLikeHabitIntent("以后每次回复都用中文，可以吗？")).toBe(true)
    expect(looksLikeHabitIntent("以后都先给计划，好吗？")).toBe(true)
    // A genuine information-seeking / complaint prompt is not.
    expect(looksLikeHabitIntent("那以后每次更新都要这样吗，有没有通用的更新方式？太麻烦了这样")).toBe(false)
  })

  it("prefilter preserves cross-project workflows but rejects single-project conventions", () => {
    // First-person cross-project workflows that merely mention PR/branch/规范 are habits.
    expect(looksLikeHabitIntent("我习惯在 PR 中遵守命名规范")).toBe(true)
    expect(looksLikeHabitIntent("always prefer PR reviews before merging branches")).toBe(true)
    expect(looksLikeHabitIntent("我偏好所有项目都使用同一套提交规范")).toBe(true)
    // A single-project convention or declarative branch topology is not a user habit.
    expect(looksLikeHabitIntent("以后这个项目的 PR 都要小而聚焦")).toBe(false)
    expect(looksLikeHabitIntent("以后这个仓库都遵守这个约定")).toBe(false)
  })

  it("prefilter preserves explicit analysis/debug habits over generic discussion words", () => {
    expect(looksLikeHabitIntent("我习惯先分析问题，以后再写代码")).toBe(true)
    expect(looksLikeHabitIntent("请记住我偏好先总结 bug，再开始修复")).toBe(true)
    expect(looksLikeHabitIntent("always prefer to analyze bugs before implementing a fix")).toBe(true)
  })

  it("fails open on empty text and on malformed CLI output", async () => {
    const empty = await captureHabitIntentWithCli(stubShell("").shell, "/root", "")
    expect(empty.captured).toBe(false)
    // Malformed output on a prompt that DOES pass the prefilter still fails open.
    const malformed = await captureHabitIntentWithCli(stubShell("not json").shell, "/root", "always do X")
    expect(malformed.captured).toBe(false)
  })
})
