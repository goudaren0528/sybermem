import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs"
import { dirname, join } from "path"
import { compareVersions, readInstalledVersion } from "./version_signal"

// Remote-version awareness: warn when the SyberMem published on GitHub `main`
// is newer than what is installed on this machine, so the user knows to re-run
// the install script. This is orthogonal to the existing project-vs-installed
// nudge (`updateNudgeMessage`): that one says "run /sybermem-update in this
// project"; this one says "your whole install is behind the published version".
//
// The published version's source of truth is the `VERSION` file on `main`,
// because distribution is `archive/main.zip` (not GitHub Releases). We never
// touch the network on the hot path: session-start reads a local cache and,
// only when the cache is stale, kicks off a fire-and-forget refresh that the
// CURRENT session does not await.

const REMOTE_VERSION_URL = "https://raw.githubusercontent.com/goudaren0528/sybermem/main/VERSION"
const CACHE_TTL_MS = 24 * 60 * 60 * 1000
const FETCH_TIMEOUT_MS = 3_000

export interface RemoteVersionCache {
  readonly remote_version: string
  readonly checked_at: string
}

const MAX_VERSION_LENGTH = 32

// The published VERSION is a short, strict dotted release string, optionally
// carrying a leading `v` tag and/or a semver prerelease and/or build metadata
// (e.g. `0.7.0`, `v1.2.3`, `1.2.3-rc.1`, `1.2.3-rc.1+build.5`). Anything else is
// not a version and must be rejected: HTML, embedded whitespace, control
// characters, an over-long blob, or "numeric prefix" garbage such as `9<script>`
// that compareVersions would otherwise truncate to `9` and echo into the
// user-visible nudge. Shared by the cache parser, the fetch path, and the nudge
// so a hostile remote/cache value can never reach compareVersions or the toast.
const VERSION_RE =
  /^v?\d+(?:\.\d+){1,3}(?:-[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)?(?:\+[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)?$/

export function isPlausibleVersion(value: unknown): boolean {
  if (typeof value !== "string") return false
  if (value.length === 0 || value.length > MAX_VERSION_LENGTH) return false
  return VERSION_RE.test(value)
}

function userHome(): string | null {
  return process.env.USERPROFILE ?? process.env.HOME ?? null
}

export function remoteVersionCachePath(): string | null {
  const home = userHome()
  if (!home) return null
  return join(home, ".claude", "sybermem", ".remote-version-cache.json")
}

export function remoteCheckDisabled(): boolean {
  const flag = process.env.SYBERMEM_NO_REMOTE_CHECK
  return flag === "1" || flag === "true"
}

// Parse a cache blob. Fail-safe: any malformed field yields null so callers
// treat it as "no usable cache" rather than crashing.
export function parseRemoteVersionCache(raw: string): RemoteVersionCache | null {
  try {
    const data: unknown = JSON.parse(raw)
    if (typeof data !== "object" || data === null) return null
    const remote = Reflect.get(data, "remote_version")
    const checked = Reflect.get(data, "checked_at")
    if (typeof remote !== "string" || !remote.trim()) return null
    const remoteVersion = remote.trim()
    if (!isPlausibleVersion(remoteVersion)) return null
    if (typeof checked !== "string" || !checked.trim()) return null
    return { remote_version: remoteVersion, checked_at: checked.trim() }
  } catch {
    return null
  }
}

export function readRemoteVersionCache(): RemoteVersionCache | null {
  const path = remoteVersionCachePath()
  if (!path || !existsSync(path)) return null
  try {
    return parseRemoteVersionCache(readFileSync(path, "utf-8"))
  } catch {
    return null
  }
}

export function writeRemoteVersionCache(cache: RemoteVersionCache): void {
  const path = remoteVersionCachePath()
  if (!path) return
  try {
    mkdirSync(dirname(path), { recursive: true })
    writeFileSync(path, JSON.stringify(cache, null, 2) + "\n", "utf-8")
  } catch {
    // Cache write is best-effort; a read-only home must never break session start.
  }
}

// True when the cache is missing or older than the TTL, i.e. a refresh is due.
export function cacheIsStale(cache: RemoteVersionCache | null, now: number = Date.now()): boolean {
  if (!cache) return true
  const checkedAt = Date.parse(cache.checked_at)
  if (Number.isNaN(checkedAt)) return true
  return now - checkedAt >= CACHE_TTL_MS
}

// Pure decision: does the cached remote version exceed the installed version?
// Fail-safe: unknown/implausible either side -> false (never nag on a version we
// cannot trust, and never let a malformed string reach compareVersions).
export function remoteIsNewer(remoteVersion: string, installedVersion: string): boolean {
  if (!isPlausibleVersion(remoteVersion) || !isPlausibleVersion(installedVersion)) return false
  return compareVersions(remoteVersion, installedVersion) > 0
}

// Build the session-start toast message, or null when no nudge is warranted.
export function remoteUpdateNudgeMessage(
  cache: RemoteVersionCache | null,
  installed: string,
): string | null {
  if (remoteCheckDisabled()) return null
  if (!cache || !installed) return null
  if (!remoteIsNewer(cache.remote_version, installed)) return null
  return `\u2B50 SyberMem ${cache.remote_version} is available on GitHub (you have ${installed}). Re-run the install script to upgrade this machine.`
}

// Fetch the published VERSION from `main` with a hard timeout. Returns the
// trimmed version string, or null on any failure (offline, timeout, non-200,
// empty/garbage body). Never throws.
export async function fetchRemoteVersion(): Promise<string | null> {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)
    try {
      const response = await fetch(REMOTE_VERSION_URL, {
        signal: controller.signal,
        headers: { Accept: "text/plain" },
      })
      if (!response.ok) return null
      const body = (await response.text()).trim()
      // A VERSION file is a short dotted string; reject anything that looks like
      // an HTML error page, carries whitespace/control characters, is implausibly
      // long, or is numeric-prefix garbage (e.g. `9<script>`).
      const firstLine = body.split("\n")[0]?.trim() ?? ""
      if (!isPlausibleVersion(firstLine)) return null
      return firstLine
    } finally {
      clearTimeout(timer)
    }
  } catch {
    return null
  }
}

// Fire-and-forget refresh: when enabled and the cache is stale, fetch the
// published version and update the cache. The current session never awaits this;
// the fresh value is only used on the NEXT session-start. Fully fail-open.
//
// Single-flight: several setups/locations may observe the same stale cache in the
// same tick. Share one in-flight refresh so the network is hit at most once per
// cold window; the promise is cleared as soon as it settles so a later session can
// retry after a failure.
let refreshInFlight: Promise<void> | null = null

export function refreshRemoteVersionCache(now: number = Date.now()): Promise<void> {
  if (remoteCheckDisabled()) return Promise.resolve()
  if (refreshInFlight) return refreshInFlight
  refreshInFlight = (async () => {
    try {
      const remote = await fetchRemoteVersion()
      if (remote) writeRemoteVersionCache({ remote_version: remote, checked_at: new Date(now).toISOString() })
    } catch {
      // Best-effort background refresh; a failure must never surface.
    } finally {
      refreshInFlight = null
    }
  })()
  return refreshInFlight
}

// Convenience for the plugin: return the nudge message (from cache) and, when
// the cache is stale, kick off a non-awaited refresh for next time.
export function evaluateRemoteVersion(): string | null {
  if (remoteCheckDisabled()) return null
  const cache = readRemoteVersionCache()
  const installed = readInstalledVersion()
  if (cacheIsStale(cache)) {
    // Fire-and-forget: do not block session start on the network.
    void refreshRemoteVersionCache().catch(() => {})
  }
  return remoteUpdateNudgeMessage(cache, installed)
}
