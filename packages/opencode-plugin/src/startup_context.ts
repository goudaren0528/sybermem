import type { Shell } from "./runtime"
import { digestLatestText, digestStatusText, normsListText, sybermemText } from "./runtime"
import { detectStaleSignal, parseIndex, parsePhaseIndex, parseProjectIdentity } from "./project_state"
import { constitutionSection, parseNorms } from "./norm_signal"
import type { SystemTransformOutput } from "./prompt_context"

// The project constitution: active GLOBAL norms, injected once per session at startup so
// binding rules govern work regardless of prompt relevance. Bounded by the CLI cap. Fail-open.
async function constitutionBlock($: Shell, root: string): Promise<string> {
  try {
    return constitutionSection(parseNorms(await normsListText($, root, "global", "")))
  } catch {
    return ""
  }
}

// Pull the latest phase digest's Core Conclusions into a bounded startup section. The
// digest flow archives source-record conclusions out of INDEX Key Conclusions, so
// without this the startup context loses exactly what the digest compressed. Fail-open.
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

// One-shot pending flag per session. A plugin instance lives for the session, so
// a module-level set is session-scoped; we only need to guarantee startup context
// reaches the FIRST system-transform turn and never repeats.
const PENDING_STARTUP = new Set<string>()

export function markPendingStartup(sessionID: string): void {
  PENDING_STARTUP.add(sessionID)
}

export function consumePendingStartup(sessionID: string): boolean {
  return PENDING_STARTUP.delete(sessionID)
}

export function appendStartupContext(output: SystemTransformOutput, startup: string): void {
  const trimmed = startup.trim()
  if (!trimmed) return
  // Prompt cache is a prefix match: never mutate system[0] (OpenCode's stable base
  // header). Append the one-shot startup block as a trailing system block so the
  // cacheable prefix stays byte-identical. The caller pushes this BEFORE per-turn
  // recall, keeping the more stable startup context ahead of volatile recall.
  if (output.system) output.system.push(trimmed)
  else output.system = [trimmed]
}

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

// Build a bounded first-turn context so the model actually sees project memory on
// the opening prompt. Habit reminders are intentionally excluded: the same first
// prompt triggers chat.message -> prompt-time habit injection, so including habits
// here would duplicate them in the identical system transform.
export async function buildStartupContext($: Shell, root: string): Promise<string | null> {
  const parsed = parseIndex(root)
  const conclusions = parsed?.conclusions ?? []
  // Fetch the latest digest section up front: when INDEX has no key conclusions (e.g.
  // they were all archived into a digest), the digest's own conclusions may be the ONLY
  // useful startup context — so we must not bail before checking for it.
  const digestSection = await latestDigestSection($, root)
  // The project constitution (binding global norms) is highest-priority governing context
  // and, like digests, may be the only useful startup content when INDEX conclusions are empty.
  const constitution = await constitutionBlock($, root)
  // Habit awareness (a count + any pending candidate) may be the ONLY useful startup
  // content — e.g. a project with no conclusions/digest/norms but a habit candidate the
  // user still needs to confirm. So compute it up front and include it in the "is there
  // anything worth injecting" decision, otherwise the early-return below would drop it.
  const habitAwareness = await habitAwarenessSection($, root)
  if (conclusions.length === 0 && !digestSection && !constitution && !habitAwareness) return null
  const phaseInfo = parsePhaseIndex(root)
  const identity = parseProjectIdentity(root)
  const stale = await detectStaleSignal($, root)
  let context = "## SyberMem Startup Context\n\n"
  if (identity.exists && identity.slug) context += `Project: ${identity.slug} (${identity.projectId ?? "no id"}).\n\n`
  // Norms first: they govern the work, so they lead the startup context.
  context += constitution
  if (conclusions.length > 0) {
    context += "### Key Conclusions\n"
    for (const c of conclusions) context += `${c}\n`
  }
  if (phaseInfo.exists) {
    context += `\n### Phase Index\nStatus: ${phaseInfo.status}. ${phaseInfo.confirmedCount} confirmed phases.\n`
    if (phaseInfo.activePhase) context += `Active phase: ${phaseInfo.activePhase}.\n`
  }
  context += digestSection
  if (stale.stale) context += `\n⭐ Heads-up: phase index trails HEAD by ${stale.commitsAhead} commits — conclusions may lag your latest work. Consider /sybermem-phase-analyze.\n`
  try {
    const staleDigestCount = numberField(JSON.parse(await digestStatusText($, root)), "stale")
    if (staleDigestCount !== null && staleDigestCount > 0) context += `\n⭐ Digest heads-up: ${staleDigestCount} digest(s) are stale — run /sybermem-digest to regenerate.\n`
  } catch {
    // Digest governance is advisory and must not block startup context.
  }
  try {
    const rec: unknown = JSON.parse(await sybermemText($, root, ["next-step", "--format", "json"]))
    const action = stringField(rec, "action")
    const reason = stringField(rec, "reason")
    if (action) context += `\n### Recommended Next Step\n${action}${reason ? ` — ${reason}` : ""}\n`
  } catch {
    // Next-step routing is advisory and must not block startup context.
  }
  if (habitAwareness) context += habitAwareness
  return context.length > 2500 ? `${context.substring(0, 2497)}...` : context
}

// Habit AWARENESS only (a count + any pending candidate, never the statements): tells
// the model that user habits exist / a candidate is waiting, without duplicating the
// prompt-time habit reminder. Returned as an appendable section (or "") so the caller
// can factor it into the "is there anything worth injecting" decision. Fail-open.
async function habitAwarenessSection($: Shell, root: string): Promise<string> {
  try {
    const awareness: unknown = JSON.parse(await sybermemText($, root, ["habit", "awareness", "--format", "json"]))
    const activeHabits = numberField(awareness, "active") ?? 0
    const pendingIntent = typeof awareness === "object" && awareness !== null && Reflect.get(awareness, "pending_intent") === true
    if (activeHabits === 0 && !pendingIntent) return ""
    // Prefer Core's single-source pending-candidate wording when present.
    let pendingNote = ""
    if (pendingIntent) {
      const reminder = typeof awareness === "object" && awareness !== null ? Reflect.get(awareness, "pending_reminder") : null
      const message = typeof reminder === "object" && reminder !== null ? Reflect.get(reminder, "message") : null
      pendingNote = typeof message === "string" && message.trim()
        ? ` ${message.trim()}`
        : " A reusable preference is pending — confirm with /sybermem-habit."
    }
    return `\n### User Habits\n${activeHabits} active user habit${activeHabits === 1 ? "" : "s"} may apply; manage with /sybermem-habit.${pendingNote}\n`
  } catch {
    // Habit awareness is advisory and must not block startup context.
    return ""
  }
}
