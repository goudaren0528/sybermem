import { afterEach, beforeEach, describe, expect, it } from "bun:test"
import { mkdtempSync, readFileSync, rmSync, writeFileSync, mkdirSync } from "fs"
import { join } from "path"
import { tmpdir } from "os"
import {
  cacheIsStale,
  fetchRemoteVersion,
  parseRemoteVersionCache,
  readRemoteVersionCache,
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
  it("fails open when fetch throws", async () => {
    globalThis.fetch = (async () => {
      throw new Error("network down")
    }) as typeof fetch
    expect(await fetchRemoteVersion()).toBeNull()
  })
})
