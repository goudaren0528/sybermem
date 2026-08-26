import type { Shell } from "./runtime"
import { sybermemText } from "./runtime"
import type { SystemTransformOutput } from "./prompt_context"

// A passively captured habit candidate (.habit-intent.json) is NOT an active habit
// and is never injected on its own — the user must confirm it via /sybermem-habit.
// The old surfacing was a per-key throttled toast that was swallowed after its first
// fire, so users never learned a candidate was waiting and never confirmed one,
// leaving habit injection permanently silent. This module surfaces the candidate as a
// bounded, MODEL-VISIBLE trailing system block so the assistant itself can remind the
// user to confirm — injected at most ONCE per candidate per session (deduped by the
// candidate's created_at) to avoid nagging and prompt-cache thrash.

export interface PendingHabitReminder {
  readonly message: string
  readonly createdAt: string
  // Stable fingerprint of the whole candidate SET (all candidate ids), so the per-session
  // dedup re-fires when the set changes (a new candidate is captured) but not every turn.
  readonly fingerprint: string
}

// Per-session record of which candidate (by created_at) we have already surfaced, so
// the same pending candidate is not re-injected every turn. A NEW candidate (different
// created_at) becomes eligible again. Session-scoped: the plugin instance lives for
// the session, so a module-level map is naturally cleared when the session ends.
const SURFACED_CANDIDATE = new Map<string, string>()

export function resetPendingHabit(sessionID: string): void {
  SURFACED_CANDIDATE.delete(sessionID)
}

// Read the durable pending-candidate reminder from Core (single source of truth).
// Fail-open: any launcher/CLI/parse error yields no reminder.
export async function readPendingHabitReminder($: Shell, root: string): Promise<PendingHabitReminder | null> {
  try {
    const parsed: unknown = JSON.parse(await sybermemText($, root, ["habit", "awareness", "--format", "json"]))
    if (typeof parsed !== "object" || parsed === null) return null
    const reminder = Reflect.get(parsed, "pending_reminder")
    if (typeof reminder !== "object" || reminder === null) return null
    const message = Reflect.get(reminder, "message")
    const createdAt = Reflect.get(reminder, "created_at")
    const fingerprint = Reflect.get(reminder, "fingerprint")
    if (typeof message !== "string" || !message.trim()) return null
    return {
      message: message.trim(),
      createdAt: typeof createdAt === "string" ? createdAt : "",
      fingerprint: typeof fingerprint === "string" ? fingerprint : "",
    }
  } catch {
    return null
  }
}

// Inject the pending-candidate reminder as a trailing model-visible system block,
// once per candidate per session. Returns the reminder when it was injected (so the
// caller can also fire a supplementary toast), or null when nothing was injected
// (no candidate, or this candidate was already surfaced this session).
export async function injectPendingHabitReminder(
  $: Shell,
  root: string,
  sessionID: string,
  output: SystemTransformOutput,
): Promise<PendingHabitReminder | null> {
  const reminder = await readPendingHabitReminder($, root)
  if (!reminder) return null
  // Dedup by the candidate-SET fingerprint so a newly captured candidate re-surfaces the
  // reminder, but an unchanged set is not re-injected every turn.
  const key = reminder.fingerprint || reminder.createdAt || reminder.message
  if (SURFACED_CANDIDATE.get(sessionID) === key) return null
  SURFACED_CANDIDATE.set(sessionID, key)
  const block = `## SyberMem Habit Candidate\n\n${reminder.message}`
  // Trailing system block only — never mutate system[0] (the cacheable base prefix).
  if (output.system) output.system.push(block)
  else output.system = [block]
  return reminder
}
