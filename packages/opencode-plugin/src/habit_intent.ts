import { sybermemText, type Shell } from "./runtime"

export interface HabitIntentResult {
  readonly captured: boolean
  readonly habitType: string
}

const NO_CAPTURE: HabitIntentResult = { captured: false, habitType: "" }

// Cheap prefilter that mirrors Core's HABIT_INTENT_TERMS so ordinary prompts do
// NOT pay for an extra CLI subprocess. Only prompts that plausibly look like a
// durable preference reach the authoritative Core classifier. ASCII terms match
// on word boundaries; CJK terms match as substrings (no word boundaries there).
const HABIT_INTENT_HINT_RE = /\b(always|habit|preference|prefer|remember)\b/i
const CJK_HABIT_INTENT_HINTS = ["以后", "偏好", "习惯", "记住"]

export function looksLikeHabitIntent(text: string): boolean {
  return HABIT_INTENT_HINT_RE.test(text) || CJK_HABIT_INTENT_HINTS.some((hint) => text.includes(hint))
}

// Ask Core to capture a candidate-only habit intent from the prompt. Core writes
// the candidate to the USER-level ~/.sybermem/.habit-intent.json (never the
// project's .sybermem/, never an active habit) and blocks secrets/injection text.
// Fail-open: any error yields "no capture" and never rejects the chat.message hook.
export async function captureHabitIntentWithCli($: Shell, root: string, text: string): Promise<HabitIntentResult> {
  // Skip the subprocess entirely unless the prompt looks like a preference. Core
  // still re-checks authoritatively (this is only a hot-path cost guard).
  if (!text || !looksLikeHabitIntent(text)) return NO_CAPTURE
  try {
    const parsed: unknown = JSON.parse(await sybermemText($, root, ["habit", "intent", "--prompt", text, "--format", "json"]))
    if (typeof parsed !== "object" || parsed === null) return NO_CAPTURE
    if (Reflect.get(parsed, "captured") !== true) return NO_CAPTURE
    const candidate = Reflect.get(parsed, "candidate")
    const habitType = typeof candidate === "object" && candidate !== null ? Reflect.get(candidate, "habit_type") : ""
    return { captured: true, habitType: typeof habitType === "string" ? habitType : "" }
  } catch {
    return NO_CAPTURE
  }
}
