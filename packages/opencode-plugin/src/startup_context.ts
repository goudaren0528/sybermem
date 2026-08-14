import type { Shell } from "./runtime"
import { digestStatusText, sybermemText } from "./runtime"
import { detectStaleSignal, parseIndex, parsePhaseIndex, parseProjectIdentity } from "./project_state"
import type { SystemTransformOutput } from "./prompt_context"

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

export function prependStartupContext(output: SystemTransformOutput, startup: string): void {
  const trimmed = startup.trim()
  if (!trimmed) return
  if (output.system && output.system.length > 0) output.system[0] = `${trimmed}\n\n${output.system[0]}`
  else output.system = [trimmed, ...(output.system ?? [])]
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
  if (!parsed || parsed.conclusions.length === 0) return null
  const phaseInfo = parsePhaseIndex(root)
  const identity = parseProjectIdentity(root)
  const stale = await detectStaleSignal($, root)
  let context = "## SyberMem Startup Context\n\n"
  if (identity.exists && identity.slug) context += `Project: ${identity.slug} (${identity.projectId ?? "no id"}).\n\n`
  context += "### Key Conclusions\n"
  for (const c of parsed.conclusions) context += `${c}\n`
  if (phaseInfo.exists) {
    context += `\n### Phase Index\nStatus: ${phaseInfo.status}. ${phaseInfo.confirmedCount} confirmed phases.\n`
    if (phaseInfo.activePhase) context += `Active phase: ${phaseInfo.activePhase}.\n`
  }
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
  return context.length > 2500 ? `${context.substring(0, 2497)}...` : context
}
