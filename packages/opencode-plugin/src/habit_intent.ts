import { sybermemText, type Shell } from "./runtime"

export interface HabitIntentResult {
  readonly captured: boolean
  readonly habitType: string
  // Suggested routing from Core: "user" (cross-project habit), "project" (belongs in a
  // /sybermem-record decision/requirement), or "ambiguous" (ask the user). "" when uncaptured.
  readonly suggestedScope: string
}

const NO_CAPTURE: HabitIntentResult = { captured: false, habitType: "", suggestedScope: "" }

// Cheap prefilter for durable preference phrasing. Core is authoritative; this
// only prevents obvious non-preferences from spawning a CLI subprocess.
const DURABLE_PREFERENCE_RE = /(\b(always\s+(?:prefer|use|reply|respond|run|keep|write|ask|show|include|avoid)|usually\s+(?:i\s+)?(?:prefer|use|want|ask|run|keep|write)|(?:please\s+)?remember\s+(?:that\s+)?(?:i\s+)?(?:prefer|want|usually|always)|i\s+prefer\b|i\s+usually\b|by\s+default\b|make\s+this\s+the\s+default\b|from\s+now\s+on\b)|以后(?:都|请|记得|默认|一律)?|请记住|帮我记住|记住我|我(?:习惯|偏好|希望)|每次都|默认(?:用|先|都)?|一律(?:用|先|都)?|总是(?:用|先|都)?)/i
const NOISY_HABIT_DISCUSSION_RE = /(why|debug|investigate|research|review|analy[sz]e|improve|design|logic|classifier|candidate|capture|为什么|怎么|调研|研究|评审|审查|改进|设计|逻辑|候选|捕获|命中).{0,80}(habit|preference|memory|norm|习惯|偏好|记忆|规范|约定)|(habit|preference|memory|norm|习惯|偏好|记忆|规范|约定).{0,80}(why|debug|investigate|research|review|analy[sz]e|improve|design|logic|classifier|candidate|capture|为什么|怎么|调研|研究|评审|审查|改进|设计|逻辑|候选|捕获|命中)/i
const AGENT_PROMPT_PREFIX_RE = /^\s*(?:TASK|CONTEXT|AXIS|EXPECTED OUTCOME|MUST DO|MUST NOT DO|REQUEST):/i
const ONE_OFF_WORK_RE = /(fix|repair|update|submit|publish|release|commit|create\s+pr|修复|更新|提交|发布|上线).{0,80}(pr|readme|docs?|todo|ui|bug|文档|待办|规范|约定|项目|下拉|按钮)/i

export function looksLikeHabitIntent(text: string): boolean {
  return DURABLE_PREFERENCE_RE.test(text) && !isNoisyHabitCandidate(text)
}

function isNoisyHabitCandidate(text: string): boolean {
  return AGENT_PROMPT_PREFIX_RE.test(text) || NOISY_HABIT_DISCUSSION_RE.test(text) || ONE_OFF_WORK_RE.test(text)
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
