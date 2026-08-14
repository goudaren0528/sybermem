import type { Shell } from "./runtime"
import { recordFilesText } from "./runtime"
import { boundedJsonlAppend } from "./state"
import type { SessionActivity } from "./session_activity"

export interface RecallOutcome {
  readonly injected: number
  readonly hit: number
  readonly precision: number | null
  readonly hitRecords: readonly string[]
  readonly missRecords: readonly string[]
}

const EMPTY_OUTCOME: RecallOutcome = { injected: 0, hit: 0, precision: null, hitRecords: [], missRecords: [] }

function normalize(path: string): string {
  return path.trim().replace(/\\/g, "/")
}

// A record "hits" when any of its declared related_files was edited this
// session. Records with no related_files anchor are excluded from the
// denominator (conservative): we cannot judge relevance without an anchor, so
// they count as neither hit nor miss.
export function computeRecallOutcome(
  injected: readonly string[],
  relatedFilesByRecord: Readonly<Record<string, readonly string[]>>,
  editedFiles: ReadonlySet<string>,
): RecallOutcome {
  const edited = new Set([...editedFiles].map(normalize))
  const hitRecords: string[] = []
  const missRecords: string[] = []
  for (const rawId of injected) {
    const id = rawId.toLowerCase()
    const related = (relatedFilesByRecord[id] ?? relatedFilesByRecord[rawId] ?? []).map(normalize)
    if (related.length === 0) continue
    if (related.some((file) => edited.has(file))) hitRecords.push(id)
    else missRecords.push(id)
  }
  const injectedCount = hitRecords.length + missRecords.length
  if (injectedCount === 0) return EMPTY_OUTCOME
  return {
    injected: injectedCount,
    hit: hitRecords.length,
    precision: hitRecords.length / injectedCount,
    hitRecords,
    missRecords,
  }
}

function parseRecordFilesJson(raw: string): Record<string, readonly string[]> {
  try {
    const parsed: unknown = JSON.parse(raw.trim())
    if (typeof parsed !== "object" || parsed === null) return {}
    const records = Reflect.get(parsed, "records")
    if (typeof records !== "object" || records === null) return {}
    const mapping: Record<string, string[]> = {}
    for (const [key, value] of Object.entries(records as Record<string, unknown>)) {
      if (Array.isArray(value)) mapping[key.toLowerCase()] = value.filter((item): item is string => typeof item === "string")
    }
    return mapping
  } catch {
    return {}
  }
}

// Fetch related_files for the injected records from Core (keeps Markdown parsing
// in Core), compute the outcome, and append one bounded journal entry. Fail-open:
// any failure yields no outcome rather than throwing out of the idle handler.
export async function flushRecallOutcome($: Shell, root: string, activity: SessionActivity, sessionID: string, timestamp = new Date().toISOString()): Promise<RecallOutcome> {
  const injected = [...activity.injectedRecords]
  if (injected.length === 0 || activity.editedFiles.size === 0) return EMPTY_OUTCOME
  let mapping: Record<string, readonly string[]> = {}
  try {
    mapping = parseRecordFilesJson(await recordFilesText($, root, injected.join(",")))
  } catch {
    return EMPTY_OUTCOME
  }
  const outcome = computeRecallOutcome(injected, mapping, new Set(activity.editedFiles.keys()))
  if (outcome.injected === 0) return EMPTY_OUTCOME
  boundedJsonlAppend(root, ".recall-outcomes.jsonl", {
    timestamp,
    session: sessionID,
    injected: outcome.injected,
    hit: outcome.hit,
    precision: outcome.precision,
    hit_records: outcome.hitRecords,
    miss_records: outcome.missRecords,
  }, 200)
  return outcome
}
