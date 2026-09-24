import { test, expect } from "bun:test"
import { readFileSync } from "node:fs"
import { resolve } from "node:path"

test("package entrypoints export loadable server and TUI modules", async () => {
  const target = resolve(import.meta.dir, "../dist-v2")
  const manifest = await Bun.file(resolve(target, "package.json")).json()
  expect(manifest.exports["./server"]).toBe("./server.js")
  expect(manifest.exports["./tui"]).toBe("./tui.js")
  const server = await import(resolve(target, "server.js"))
  const tui = await import(resolve(target, "tui.js"))
  expect(server.default.id).toBe("sybermem")
  expect(tui.default.id).toBe("sybermem-tui")
})

// Optional independent source check: supply the extracted OpenCode 2.0.15
// @opencode-ai/plugin dist/host.js via this explicit environment variable.
// Source inspection is not proof of live host loading or source provenance.
const hostSource = process.env.SYBERMEM_OPENCODE_2_0_15_HOST_SOURCE
const hostContract = hostSource === undefined ? test.skip : test
hostContract("OpenCode 2.0.15 host source contract (not verified without SYBERMEM_OPENCODE_2_0_15_HOST_SOURCE)", () => {
  let source: string
  try {
    source = readFileSync(hostSource!, "utf8")
  } catch {
    throw new Error("Configured OpenCode 2.0.15 host source cannot be read")
  }
  expect(source.includes('entry(["server", ""])')).toBe(true)
  expect(source.includes('entry(["tui"])')).toBe(true)
})
