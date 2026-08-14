import { sybermemText, type Shell } from "./runtime"

export interface HabitIntentResult {
  readonly captured: boolean
  readonly habitType: string
}

const NO_CAPTURE: HabitIntentResult = { captured: false, habitType: "" }

// Ask Core to capture a candidate-only habit intent from the prompt. Core writes
// the candidate to the USER-level ~/.sybermem/.habit-intent.json (never the
// project's .sybermem/, never an active habit) and blocks secrets/injection text.
// Fail-open: any error yields "no capture" and never rejects the chat.message hook.
export async function captureHabitIntentWithCli($: Shell, root: string, text: string): Promise<HabitIntentResult> {
  if (!text) return NO_CAPTURE
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
