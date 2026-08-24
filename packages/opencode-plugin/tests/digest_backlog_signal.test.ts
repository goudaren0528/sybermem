import { describe, expect, it } from "bun:test"
import { DIGEST_BACKLOG_THRESHOLD, digestBacklogToast, parseDigestBacklog } from "../src/digest_backlog_signal"

describe("parseDigestBacklog", () => {
  it("parses the backlog object from digest status json", () => {
    const json = JSON.stringify({
      total: 1,
      backlog: { uncovered: 7, days_since_latest_digest: 12, has_digest: true },
    })
    const backlog = parseDigestBacklog(json)
    expect(backlog).toEqual({ uncovered: 7, daysSinceLatestDigest: 12, hasDigest: true })
  })

  it("fails closed on missing/malformed backlog", () => {
    expect(parseDigestBacklog("")).toBeNull()
    expect(parseDigestBacklog("not json")).toBeNull()
    expect(parseDigestBacklog(JSON.stringify({ total: 0 }))).toBeNull()
    expect(parseDigestBacklog(JSON.stringify({ backlog: { uncovered: "x" } }))).toBeNull()
  })

  it("defaults optional fields when absent", () => {
    const backlog = parseDigestBacklog(JSON.stringify({ backlog: { uncovered: 5 } }))
    expect(backlog).toEqual({ uncovered: 5, daysSinceLatestDigest: 0, hasDigest: false })
  })
})

describe("digestBacklogToast", () => {
  it("stays silent below the threshold", () => {
    expect(digestBacklogToast({ uncovered: DIGEST_BACKLOG_THRESHOLD - 1, daysSinceLatestDigest: 30, hasDigest: true })).toBeNull()
  })

  it("fires at/above the threshold with an age note when a prior digest exists", () => {
    const msg = digestBacklogToast({ uncovered: DIGEST_BACKLOG_THRESHOLD, daysSinceLatestDigest: 12, hasDigest: true })
    expect(msg).toContain("5")
    expect(msg).toContain("12")
    expect(msg).toContain("/sybermem-digest")
  })

  it("omits the age note when no prior digest exists", () => {
    const msg = digestBacklogToast({ uncovered: 6, daysSinceLatestDigest: 0, hasDigest: false })
    expect(msg).toContain("6")
    expect(msg).not.toContain("距上次 digest")
  })
})
