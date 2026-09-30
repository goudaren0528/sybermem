import { afterEach, beforeEach, describe, expect, it } from "bun:test"
import { mkdtempSync, readFileSync, rmSync, writeFileSync, mkdirSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import {
  cacheIsStale,
  evaluateRemoteVersion,
  fetchRemoteVersion,
  isPlausibleVersion,
  parseRemoteVersionCache,
  readRemoteVersionCache,
  refreshRemoteVersionCache,
  remoteCheckDisabled,
  remoteIsNewer,
  remoteUpdateNudgeMessage,
  remoteVersionCachePath,
  writeRemoteVersionCache,
  type RemoteVersionCache,
} from "../src/remote_version"

const ENV_KEYS = ["USERPROFILE", "HOME", "SYBERMEM_NO_REMOTE_CHECK"] as const
let saved: Record<string, string | undefined>
let home: string

beforeEach(() => {
  saved = {}
  for (const k of ENV_KEYS) saved[k] = process.env[k]
  home = mkdtempSync(join(tmpdir(), "sybermem-remote-"))
  process.env.USERPROFILE = home
  process.env.HOME = home
  delete process.env.SYBERMEM_NO_REMOTE_CHECK
})

afterEach(() => {
  for (const k of ENV_KEYS) {
    if (saved[k] === undefined) delete process.env[k]
    else process.env[k] = saved[k]
  }
  rmSync(home, { recursive: true, force: true })
})

describe("isPlausibleVersion", () => {
  it("accepts the project's strict dotted form and legal prerelease/build", () => {
    expect(isPlausibleVersion("0.7.0")).toBe(true)
    expect(isPlausibleVersion("0.1.0")).toBe(true)
    expect(isPlausibleVersion("10.20.30")).toBe(true)
    expect(isPlausibleVersion("1.2.3-rc.1")).toBe(true)
    expect(isPlausibleVersion("v0.7.0")).toBe(true)
    expect(isPlausibleVersion("1.2.3-rc.1+build.5")).toBe(true)
  })
  it("rejects numeric-prefix garbage, HTML, whitespace, control chars and over-long input", () => {
    expect(isPlausibleVersion("9<script>alert(1)</script>")).toBe(false)
    expect(isPlausibleVersion("v9<script>")).toBe(false)
    expect(isPlausibleVersion("9 garbage")).toBe(false)
    expect(isPlausibleVersion("9.0.0 extra")).toBe(false)
    expect(isPlausibleVersion("<b>9</b>")).toBe(false)
    expect(isPlausibleVersion("0.1.0\n")).toBe(false)
    expect(isPlausibleVersion("0.1.0\r0")).toBe(false)
    expect(isPlausibleVersion("9")).toBe(false)
    expect(isPlausibleVersion("")).toBe(false)
    expect(isPlausibleVersion("0.1.0".padEnd(33, "0"))).toBe(false)
    expect(isPlausibleVersion(undefined)).toBe(false)
    expect(isPlausibleVersion(9)).toBe(false)
  })
})

describe("remoteIsNewer", () => {
  it("is true only when remote strictly exceeds installed", () => {
    expect(remoteIsNewer("0.2.0", "0.1.1")).toBe(true)
    expect(remoteIsNewer("0.1.1", "0.1.1")).toBe(false)
    expect(remoteIsNewer("0.1.0", "0.2.0")).toBe(false)
  })
  it("fails safe on empty/unknown versions", () => {
    expect(remoteIsNewer("", "0.1.1")).toBe(false)
    expect(remoteIsNewer("0.2.0", "")).toBe(false)
  })
  it("rejects implausible remote/installed values instead of truncating them", () => {
    expect(remoteIsNewer("9<script>alert(1)</script>", "0.1.0")).toBe(false)
    expect(remoteIsNewer("9.9.9.9.9", "0.1.0")).toBe(false)
    expect(remoteIsNewer("9.9.9", "0.1.0 garbage")).toBe(false)
    expect(remoteIsNewer("9.9.9", "9")).toBe(false)
  })
})

describe("cacheIsStale", () => {
  it("treats missing cache as stale", () => {
    expect(cacheIsStale(null)).toBe(true)
  })
  it("treats fresh cache (<24h) as not stale", () => {
    const now = Date.parse("2026-08-26T12:00:00Z")
    const cache: RemoteVersionCache = { remote_version: "0.2.0", checked_at: "2026-08-26T06:00:00Z" }
    expect(cacheIsStale(cache, now)).toBe(false)
  })
  it("treats cache older than 24h as stale", () => {
    const now = Date.parse("2026-08-26T12:00:00Z")
    const cache: RemoteVersionCache = { remote_version: "0.2.0", checked_at: "2026-08-24T06:00:00Z" }
    expect(cacheIsStale(cache, now)).toBe(true)
  })
  it("treats an unparseable timestamp as stale", () => {
    const cache: RemoteVersionCache = { remote_version: "0.2.0", checked_at: "not-a-date" }
    expect(cacheIsStale(cache)).toBe(true)
  })
})

describe("parseRemoteVersionCache", () => {
  it("parses a valid cache blob", () => {
    const parsed = parseRemoteVersionCache('{"remote_version":"0.2.0","checked_at":"2026-08-26T00:00:00Z"}')
    expect(parsed).toEqual({ remote_version: "0.2.0", checked_at: "2026-08-26T00:00:00Z" })
  })
  it("fails safe on garbage / missing fields", () => {
    expect(parseRemoteVersionCache("not json")).toBeNull()
    expect(parseRemoteVersionCache("{}")).toBeNull()
    expect(parseRemoteVersionCache('{"remote_version":""}')).toBeNull()
    expect(parseRemoteVersionCache('{"remote_version":"0.2.0"}')).toBeNull()
  })
  it("rejects a malicious/implausible remote_version instead of trusting it", () => {
    const at = '"checked_at":"2026-08-26T00:00:00Z"'
    expect(parseRemoteVersionCache(`{"remote_version":"9<script>alert(1)</script>",${at}}`)).toBeNull()
    expect(parseRemoteVersionCache(`{"remote_version":"9 garbage",${at}}`)).toBeNull()
    expect(parseRemoteVersionCache(`{"remote_version":"9.0.0\tx",${at}}`)).toBeNull()
    expect(parseRemoteVersionCache(`{"remote_version":"${"0".repeat(33)}",${at}}`)).toBeNull()
    expect(parseRemoteVersionCache(`{"remote_version":"<b>9</b>",${at}}`)).toBeNull()
  })
})

describe("remoteUpdateNudgeMessage", () => {
  it("returns a message when remote > installed", () => {
    const cache: RemoteVersionCache = { remote_version: "0.2.0", checked_at: "2026-08-26T00:00:00Z" }
    const msg = remoteUpdateNudgeMessage(cache, "0.1.1")
    expect(msg).toContain("0.2.0")
    expect(msg).toContain("0.1.1")
  })
  it("returns null when up to date, no cache, or unknown installed", () => {
    const cache: RemoteVersionCache = { remote_version: "0.1.1", checked_at: "2026-08-26T00:00:00Z" }
    expect(remoteUpdateNudgeMessage(cache, "0.1.1")).toBeNull()
    expect(remoteUpdateNudgeMessage(null, "0.1.1")).toBeNull()
    expect(remoteUpdateNudgeMessage(cache, "")).toBeNull()
  })
  it("returns null when remote check is disabled", () => {
    process.env.SYBERMEM_NO_REMOTE_CHECK = "1"
    expect(remoteCheckDisabled()).toBe(true)
    const cache: RemoteVersionCache = { remote_version: "0.2.0", checked_at: "2026-08-26T00:00:00Z" }
    expect(remoteUpdateNudgeMessage(cache, "0.1.1")).toBeNull()
  })
  it("never echoes a malicious cached version into the toast", () => {
    const cache: RemoteVersionCache = { remote_version: "9<script>alert(1)</script>", checked_at: "2026-08-26T00:00:00Z" }
    expect(remoteUpdateNudgeMessage(cache, "0.1.0")).toBeNull()
  })
})

describe("cache round-trip", () => {
  it("writes and reads the cache under the resolved home", () => {
    const path = remoteVersionCachePath()
    expect(path).not.toBeNull()
    writeRemoteVersionCache({ remote_version: "0.3.0", checked_at: "2026-08-26T00:00:00Z" })
    const back = readRemoteVersionCache()
    expect(back).toEqual({ remote_version: "0.3.0", checked_at: "2026-08-26T00:00:00Z" })
  })
  it("returns null when no cache file exists", () => {
    expect(readRemoteVersionCache()).toBeNull()
  })
  it("returns null on a corrupt cache file", () => {
    const path = remoteVersionCachePath()!
    mkdirSync(join(path, ".."), { recursive: true })
    writeFileSync(path, "{ broken", "utf-8")
    expect(readRemoteVersionCache()).toBeNull()
  })
  it("returns null on a cache file holding a malicious/implausible version", () => {
    const path = remoteVersionCachePath()!
    mkdirSync(join(path, ".."), { recursive: true })
    writeFileSync(
      path,
      JSON.stringify({ remote_version: "9<script>alert(1)</script>", checked_at: "2026-08-26T00:00:00Z" }),
      "utf-8",
    )
    expect(readRemoteVersionCache()).toBeNull()
  })
  it("fails open when the cache path is not writable (read-only/occupied)", () => {
    // A directory where the cache file should be makes the write throw; it must
    // be swallowed so a read-only home never breaks session start.
    mkdirSync(remoteVersionCachePath()!, { recursive: true })
    expect(() =>
      writeRemoteVersionCache({ remote_version: "0.2.0", checked_at: "2026-08-26T00:00:00Z" }),
    ).not.toThrow()
    expect(readRemoteVersionCache()).toBeNull()
  })
})

describe("fetchRemoteVersion", () => {
  const realFetch = globalThis.fetch
  afterEach(() => {
    globalThis.fetch = realFetch
  })
  it("returns a plausible dotted version from a 200 body", async () => {
    globalThis.fetch = (async () => new Response("0.4.0\n", { status: 200 })) as typeof fetch
    expect(await fetchRemoteVersion()).toBe("0.4.0")
  })
  it("returns null on non-200", async () => {
    globalThis.fetch = (async () => new Response("nope", { status: 404 })) as typeof fetch
    expect(await fetchRemoteVersion()).toBeNull()
  })
  it("rejects an HTML error page body", async () => {
    globalThis.fetch = (async () => new Response("<!DOCTYPE html><html>404</html>", { status: 200 })) as typeof fetch
    expect(await fetchRemoteVersion()).toBeNull()
  })
  it("rejects numeric-prefix garbage and whitespace bodies", async () => {
    globalThis.fetch = (async () => new Response("9<script>alert(1)</script>\n", { status: 200 })) as typeof fetch
    expect(await fetchRemoteVersion()).toBeNull()
    globalThis.fetch = (async () => new Response("9 garbage\n", { status: 200 })) as typeof fetch
    expect(await fetchRemoteVersion()).toBeNull()
  })
  it("fails open on 403/429/5xx without reading the response body", async () => {
    for (const status of [403, 429, 500, 503]) {
      let bodyRead = false
      globalThis.fetch = (async () => ({
        ok: false,
        status,
        text: async () => {
          bodyRead = true
          return "SECRET-ERROR-BODY"
        },
      })) as unknown as typeof fetch
      expect(await fetchRemoteVersion()).toBeNull()
      expect(bodyRead).toBe(false)
    }
  })
  it("fails open on timeout/abort", async () => {
    globalThis.fetch = (async () => {
      throw Object.assign(new Error("The operation was aborted"), { name: "AbortError" })
    }) as typeof fetch
    expect(await fetchRemoteVersion()).toBeNull()
  })
  it("fails open when fetch throws", async () => {
    globalThis.fetch = (async () => {
      throw new Error("network down")
    }) as typeof fetch
    expect(await fetchRemoteVersion()).toBeNull()
  })
})

describe("evaluateRemoteVersion and single-flight refresh", () => {
  const realFetch = globalThis.fetch
  afterEach(() => {
    globalThis.fetch = realFetch
  })
  const waitFor = async (done: () => boolean, ticks = 200) => {
    for (let i = 0; i < ticks && !done(); i++) await Bun.sleep(1)
  }
  const versionMarker = (version: string) => {
    mkdirSync(join(home, ".claude", "sybermem"), { recursive: true })
    writeFileSync(join(home, ".claude", "sybermem", "VERSION"), `${version}\n`)
  }

  it("does not touch the network when the cache is fresh", async () => {
    let calls = 0
    globalThis.fetch = (async () => { calls++; return new Response("9.9.9\n", { status: 200 }) }) as typeof fetch
    writeRemoteVersionCache({ remote_version: "9.9.9", checked_at: new Date().toISOString() })
    expect(evaluateRemoteVersion()).toBeNull()
    await Bun.sleep(5)
    expect(calls).toBe(0)
  })

  it("returns a fresh-cache nudge without ever touching the network", async () => {
    versionMarker("0.1.0")
    let calls = 0
    globalThis.fetch = (async () => { calls++; return new Response("9.9.9\n", { status: 200 }) }) as typeof fetch
    writeRemoteVersionCache({ remote_version: "9.9.9", checked_at: new Date().toISOString() })
    const message = evaluateRemoteVersion()
    expect(message).toContain("9.9.9")
    expect(message).toContain("0.1.0")
    await Bun.sleep(5)
    expect(calls).toBe(0)
  })

  it("returns the cached nudge immediately and refreshes without blocking", async () => {
    versionMarker("0.1.0")
    writeRemoteVersionCache({ remote_version: "0.2.0", checked_at: "2000-01-01T00:00:00Z" })
    let release!: (response: Response) => void
    const gate = new Promise<Response>((resolve) => { release = resolve })
    let calls = 0
    globalThis.fetch = (async () => { calls++; return gate }) as typeof fetch
    const message = evaluateRemoteVersion()
    // The stale cache is still what the current session sees; the fetch is pending.
    expect(message).toContain("0.2.0")
    expect(calls).toBe(1)
    release(new Response("0.3.0\n", { status: 200 }))
    await waitFor(() => readRemoteVersionCache()?.remote_version === "0.3.0")
    expect(readRemoteVersionCache()?.remote_version).toBe("0.3.0")
    await Bun.sleep(2)
  })

  it("does not fetch when remote check is disabled", async () => {
    process.env.SYBERMEM_NO_REMOTE_CHECK = "1"
    let calls = 0
    globalThis.fetch = (async () => { calls++; return new Response("9.9.9\n", { status: 200 }) }) as typeof fetch
    versionMarker("0.1.0")
    writeRemoteVersionCache({ remote_version: "9.9.9", checked_at: "2000-01-01T00:00:00Z" })
    expect(remoteCheckDisabled()).toBe(true)
    expect(evaluateRemoteVersion()).toBeNull()
    await Bun.sleep(5)
    expect(calls).toBe(0)
  })

  it("shares a single fetch across concurrent stale refreshes", async () => {
    let release!: (response: Response) => void
    const gate = new Promise<Response>((resolve) => { release = resolve })
    let calls = 0
    globalThis.fetch = (async () => { calls++; return gate }) as typeof fetch
    const first = refreshRemoteVersionCache()
    const second = refreshRemoteVersionCache()
    expect(calls).toBe(1)
    release(new Response("0.5.0\n", { status: 200 }))
    await Promise.all([first, second])
    expect(calls).toBe(1)
    expect(readRemoteVersionCache()?.remote_version).toBe("0.5.0")
  })

  it("fails open on an unreadable cache and still refreshes at most once", async () => {
    mkdirSync(remoteVersionCachePath()!, { recursive: true }) // a directory where the cache file should be
    let calls = 0
    globalThis.fetch = (async () => { calls++; return new Response("0.6.0\n", { status: 200 }) }) as typeof fetch
    expect(() => evaluateRemoteVersion()).not.toThrow()
    await waitFor(() => calls === 1)
    expect(calls).toBe(1)
    await Bun.sleep(2)
  })
})
