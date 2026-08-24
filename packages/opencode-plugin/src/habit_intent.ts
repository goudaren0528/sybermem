import { sybermemText, type Shell } from "./runtime"

export interface HabitIntentResult {
  readonly captured: boolean
  readonly habitType: string
  // Suggested routing from Core: "user" (cross-project habit), "project" (belongs in a
  // /sybermem-record decision/requirement), or "ambiguous" (ask the user). "" when uncaptured.
  readonly suggestedScope: string
}

const NO_CAPTURE: HabitIntentResult = { captured: false, habitType: "", suggestedScope: "" }

// Cheap prefilter that mirrors Core's HABIT_INTENT_TERMS so ordinary prompts do
// NOT pay for an extra CLI subprocess. Only prompts that plausibly look like a
// durable preference reach the authoritative Core classifier. ASCII terms match
// on word boundaries; CJK terms match as substrings (no word boundaries there).
// Keep in sync with Core's HABIT_INTENT_TERMS (packages/core/sybermem_core/user_habits.py).
// Core is authoritative; this is only a hot-path prefilter so ordinary prompts skip the
// subprocess. If it under-matches, Core never sees the prompt, so the two MUST agree.
const HABIT_INTENT_HINT_RE = /\b(always|habit|preference|prefer|remember|usually|default|convention)\b/i
const CJK_HABIT_INTENT_HINTS = ["以后", "偏好", "习惯", "记住", "总是", "每次", "默认", "一律", "记得", "尽量", "规范", "约定"]

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
    const suggestedScope = typeof candidate === "object" && candidate !== null ? Reflect.get(candidate, "suggested_scope") : ""
    return {
      captured: true,
      habitType: typeof habitType === "string" ? habitType : "",
      suggestedScope: typeof suggestedScope === "string" ? suggestedScope : "",
    }
  } catch {
    return NO_CAPTURE
  }
}
