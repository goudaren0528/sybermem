import { digestLatestText, digestStatusText, sybermemText, type Shell } from "./runtime"
import { detectStaleSignal, parseIndex, parsePhaseIndex, parseProjectIdentity } from "./project_state"

// Latest phase digest Core Conclusions for compaction carry-forward. Same rationale as
// startup: the digest flow archives source conclusions out of INDEX, so surface the
// digest's own conclusions so compaction keeps the compressed knowledge. Fail-open.
async function latestDigestSection($: Shell, root: string): Promise<string> {
  try {
    const parsed: unknown = JSON.parse(await digestLatestText($, root))
    if (typeof parsed !== "object" || parsed === null) return ""
    const conclusions = Reflect.get(parsed, "conclusions")
    if (!Array.isArray(conclusions) || conclusions.length === 0) return ""
    const title = typeof Reflect.get(parsed, "title") === "string" ? Reflect.get(parsed, "title") : ""
    const lines = conclusions.filter((c): c is string => typeof c === "string").slice(0, 5)
    if (lines.length === 0) return ""
    return `\n### Latest Digest${title ? `: ${title}` : ""}\n${lines.join("\n")}\n`
  } catch {
    return ""
  }
}

export interface CompactionOutput { readonly context: string[] }

function numberField(value: unknown, key: string): number | null {
  if (typeof value !== "object" || value === null) return null
  const field = Reflect.get(value, key)
  return typeof field === "number" ? field : null
}

function stringField(value: unknown, key: string): string {
  if (typeof value !== "object" || value === null) return ""
  const field = Reflect.get(value, key)
  return typeof field === "string" ? field.trim() : ""
}

export async function buildCompactionContext($: Shell, root: string): Promise<string | null> {
  const parsed = parseIndex(root)
  const conclusions = parsed?.conclusions ?? []
  // Digest conclusions may be the only remaining useful carry-forward when INDEX key
  // conclusions were archived into a digest, so fetch the digest section before bailing.
  const digestSection = await latestDigestSection($, root)
  if (conclusions.length === 0 && !digestSection) return null
  const phaseInfo = parsePhaseIndex(root)
  const identity = parseProjectIdentity(root)
  const stale = await detectStaleSignal($, root)
  let context = ""
  try {
    const manualContext = (await sybermemText($, root, ["context", "session", "--format", "markdown"])).trim()
    if (manualContext.startsWith("## SyberMem Manual Session Context")) context += `${manualContext}\n\n`
  } catch {
    // Old CLI or unavailable launcher: fall back to inline compaction context below.
  }
  if (!context) context = "## SyberMem Project Memory\n\n"
  if (identity.exists && identity.slug) context += `Project: ${identity.slug} (${identity.projectId ?? "no id"}).\n\n`
  if (conclusions.length > 0) {
    context += "### Key Conclusions\n"
    for (const c of conclusions) context += `${c}\n`
  }
  context += digestSection
  if (stale.stale) context += `\n⭐ Heads-up: phase index trails HEAD by ${stale.commitsAhead} commits — the conclusions above may lag your latest work. Consider /sybermem-phase-analyze before relying on phase context.\n`
  try {
    const staleDigestCount = numberField(JSON.parse(await digestStatusText($, root)), "stale")
    if (staleDigestCount !== null && staleDigestCount > 0) context += `\n⭐ Digest heads-up: ${staleDigestCount} digest(s) are stale — their source records changed. Run /sybermem-digest to regenerate, or \`sybermem digest status\` to see which sources drifted.\n`
  } catch {
    // Digest governance is advisory and must not block compaction.
  }
  if (phaseInfo.exists) {
    context += `\n### Phase Index\nStatus: ${phaseInfo.status}. ${phaseInfo.confirmedCount} confirmed phases.\n`
    if (phaseInfo.activePhase) context += `Active phase: ${phaseInfo.activePhase}.\n`
  }
  if (stale.stale) context += `\n### Stale Signal\nPhase-index last git boundary: ${stale.boundary}, current HEAD: ${stale.head} (${stale.commitsAhead} commits ahead).\n`
  const topicIndex = parsed?.topicIndex ?? {}
  if (Object.keys(topicIndex).length > 0) {
    context += "\n### Topic Index\n"
    for (const [topic, records] of Object.entries(topicIndex)) context += `- ${topic}: ${records.join(", ")}\n`
  }
  try {
    const rec: unknown = JSON.parse(await sybermemText($, root, ["next-step", "--format", "json"]))
    const action = stringField(rec, "action")
    const reason = stringField(rec, "reason")
    if (action) context += `\n### Recommended Next Step\n${action}${reason ? ` — ${reason}` : ""}\n`
  } catch {
    // Next-step routing is advisory and must not block compaction.
  }
  try {
    const habitContext = "compaction planning review implementation coding documentation"
    const habitMarkdown = (await sybermemText($, root, ["habit", "inject", "--context", habitContext, "--format", "markdown"])).trim()
    if (habitMarkdown) context += `\n${habitMarkdown}\n`
  } catch {
    // Habit injection is additive and must remain fail-open.
  }
  context += "\n### SyberMem Commands\n- /sybermem-record — create a record after meaningful work\n- /sybermem-summary — view current phase status\n- /sybermem-digest — create durable phase digest\n"
  return context.length > 3000 ? `${context.substring(0, 2997)}...` : context
}
