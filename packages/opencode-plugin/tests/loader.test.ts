import { test, expect } from "bun:test"
import { resolve } from "node:path"

test("package entrypoints match official 2.0.15 Host resolver contract", async () => {
  // The extracted official host.js imports @opencode/util, which is not part
  // of the offline contract snapshot. Assert its exact entrypoint algorithm
  // as source evidence rather than falsely claiming a working host import.
  const host = await Bun.file("C:/Users/example/AppData/Local/Temp/opencode/jev-v2-contract-2015/plugin/package/dist/host.js").text()
  expect(host).toContain('entry(["server", ""])')
  expect(host).toContain('entry(["tui"])')
  const target = resolve(import.meta.dir, "../dist-v2")
  const manifest = await Bun.file(resolve(target, "package.json")).json()
  expect(manifest.exports["./server"]).toBe("./server.js")
  expect(manifest.exports["./tui"]).toBe("./tui.js")
  const server = await import(resolve(target, "server.js"))
  const tui = await import(resolve(target, "tui.js"))
  expect(server.default.id).toBe("sybermem")
  expect(tui.default.id).toBe("sybermem-tui")
})
