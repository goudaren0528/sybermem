import { describe, expect, it } from "bun:test"
import { constitutionSection, parseNorms, scopedNormSection } from "../src/norm_signal"

describe("parseNorms", () => {
  it("parses the norms array from norms list json", () => {
    const json = JSON.stringify({
      norms: [
        { record_id: "norm-001", statement: "Use pnpm", scope: "global" },
        { record_id: "norm-002", statement: "Sessions expire in 30m", scope: "topic:auth" },
      ],
    })
    const norms = parseNorms(json)
    expect(norms).toEqual([
      { recordId: "norm-001", statement: "Use pnpm", scope: "global" },
      { recordId: "norm-002", statement: "Sessions expire in 30m", scope: "topic:auth" },
    ])
  })

  it("fails closed on malformed/absent shapes and skips empty statements", () => {
    expect(parseNorms("")).toEqual([])
    expect(parseNorms("not json")).toEqual([])
    expect(parseNorms(JSON.stringify({ other: 1 }))).toEqual([])
    expect(parseNorms(JSON.stringify({ norms: [{ record_id: "norm-x", statement: "" }] }))).toEqual([])
  })

  it("defaults missing scope to empty string", () => {
    const norms = parseNorms(JSON.stringify({ norms: [{ record_id: "n", statement: "s" }] }))
    expect(norms).toEqual([{ recordId: "n", statement: "s", scope: "" }])
  })
})

describe("constitutionSection", () => {
  it("returns empty for no norms", () => {
    expect(constitutionSection([])).toBe("")
  })

  it("renders a binding constitution block with a follow instruction", () => {
    const md = constitutionSection([{ recordId: "norm-001", statement: "Use pnpm", scope: "global" }])
    expect(md).toContain("### Project Norms (binding)")
    expect(md).toContain("[norm-001] Use pnpm")
    expect(md).toContain("binding project norms")
  })
})

describe("scopedNormSection", () => {
  it("renders scoped norms with their scope tag", () => {
    const md = scopedNormSection([{ recordId: "norm-002", statement: "Idempotent webhooks", scope: "topic:payment" }])
    expect(md).toContain("### Relevant Project Norms")
    expect(md).toContain("(topic:payment)")
    expect(md).toContain("[norm-002] (topic:payment) Idempotent webhooks")
  })

  it("returns empty for no norms", () => {
    expect(scopedNormSection([])).toBe("")
  })
})
