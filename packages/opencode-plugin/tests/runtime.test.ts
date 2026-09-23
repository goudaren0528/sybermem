import { afterEach, describe, expect, it } from "bun:test"
import { mkdirSync, rmSync, writeFileSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import { resolveRoot } from "../src/runtime"

function makeTempProject(marker: "settings" | "project" | "index" | "empty"): string {
  const root = join(tmpdir(), `sybermem-opencode-${crypto.randomUUID()}`)
  mkdirSync(join(root, ".sybermem"), { recursive: true })
  if (marker === "settings") {
    mkdirSync(join(root, ".claude"), { recursive: true })
    writeFileSync(join(root, ".claude", "settings.json"), "{}\n", "utf-8")
  } else if (marker === "project") {
    writeFileSync(join(root, ".sybermem", "project.yaml"), "project_id: test\n", "utf-8")
  } else if (marker === "index") {
    writeFileSync(join(root, ".sybermem", "INDEX.md"), "# legacy\n", "utf-8")
  }
  return root
}

describe("runtime", () => {
  let root = ""

  afterEach(() => {
    if (root) rmSync(root, { recursive: true, force: true })
  })

  it("resolves a SyberMem project root from a nested working directory", () => {
    // Given
    root = makeTempProject("settings")
    const nested = join(root, "packages", "core")
    mkdirSync(nested, { recursive: true })

    // When / Then
    expect(resolveRoot(nested)).toBe(root)
  })

  it("resolves with project.yaml when settings.json is absent", () => {
    root = makeTempProject("project")
    expect(resolveRoot(join(root, "nested"))).toBe(root)
  })

  it("does not resolve an empty .sybermem directory", () => {
    root = makeTempProject("empty")
    // An ambient managed home may contain tmpdir; invalid child markers must
    // fall through to that ancestor rather than becoming a project themselves.
    expect(resolveRoot(root)).toBe(resolveRoot(tmpdir()))
  })

  it("does not resolve INDEX.md without a current marker", () => {
    root = makeTempProject("index")
    expect(resolveRoot(root)).toBe(resolveRoot(tmpdir()))
  })
})
