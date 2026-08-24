export interface DigestBacklog {
  readonly uncovered: number
  readonly daysSinceLatestDigest: number
  readonly hasDigest: boolean
}

// Parse the backlog object out of `sybermem digest status --format json`. Fail-closed
// to null on any malformed/absent field so the caller stays silent rather than guessing.
export function parseDigestBacklog(json: string): DigestBacklog | null {
  const trimmed = json.trim()
  if (!trimmed) return null
  try {
    const parsed: unknown = JSON.parse(trimmed)
    if (typeof parsed !== "object" || parsed === null) return null
    const backlog = Reflect.get(parsed, "backlog")
    if (typeof backlog !== "object" || backlog === null) return null
    const uncovered = Reflect.get(backlog, "uncovered")
    if (typeof uncovered !== "number") return null
    const days = Reflect.get(backlog, "days_since_latest_digest")
    const hasDigest = Reflect.get(backlog, "has_digest")
    return {
      uncovered,
      daysSinceLatestDigest: typeof days === "number" ? days : 0,
      hasDigest: hasDigest === true,
    }
  } catch {
    return null
  }
}

// Coarser than the record nudge: a digest compresses a whole batch, so only surface
// once a meaningful pile of uncovered records has accumulated. Keep in sync with
// DIGEST_BACKLOG_THRESHOLD in packages/core/sybermem_core/next_step_router.py.
export const DIGEST_BACKLOG_THRESHOLD = 5

export function digestBacklogToast(backlog: DigestBacklog): string | null {
  if (backlog.uncovered < DIGEST_BACKLOG_THRESHOLD) return null
  // Only add the age clause when a prior digest exists (otherwise the day count is 0
  // and meaningless). The "no digest yet" case is already served by next-step, so here
  // we lead with the accumulation the user can act on.
  const ageNote = backlog.hasDigest && backlog.daysSinceLatestDigest > 0
    ? `（距上次 digest ${backlog.daysSinceLatestDigest} 天）`
    : ""
  return `⭐ SyberMem: ${backlog.uncovered} 条记录尚未进入任何 digest${ageNote} — 考虑 /sybermem-digest 压缩这批工作`
}
