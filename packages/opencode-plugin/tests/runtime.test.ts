import { afterEach, describe, expect, it } from "bun:test"
import { mkdirSync, rmSync, writeFileSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import { resolveRoot } from "../src/runtime"

function makeTempProject(): string {
  const root = join(tmpdir(), `sybermem-opencode-${crypto.randomUUID()}`)
  mkdirSync(join(root, ".sybermem"), { recursive: true })
  mkdirSync(join(root, ".claude"), { recursive: true })
  writeFileSync(join(root, ".claude", "settings.json"), "{}\n", "utf-8")
  return root
}

describe("runtime", () => {
  let root = ""

  afterEach(() => {
    if (root) rmSync(root, { recursive: true, force: true })
  })

  it("resolves a SyberMem project root from a nested working directory", () => {
    // Given
    root = makeTempProject()
    const nested = join(root, "packages", "core")
    mkdirSync(nested, { recursive: true })

    // When / Then
    expect(resolveRoot(nested)).toBe(root)
  })
})
