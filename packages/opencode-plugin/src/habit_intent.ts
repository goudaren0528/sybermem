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
// "我习惯/我偏好" are durable markers; bare "我希望" is a generic one-off request so it only
// counts with a standing-time word. "默认" must be followed by a verb (bare "默认" is a noun).
const DURABLE_PREFERENCE_RE = /(\b(always\s+(?:prefer|use|reply|respond|run|keep|write|ask|show|include|avoid)|usually\s+(?:i\s+)?(?:prefer|use|want|ask|run|keep|write)|(?:please\s+)?remember\s+(?:that\s+)?(?:i\s+)?(?:prefer|want|usually|always)|i\s+prefer\b|i\s+usually\b|by\s+default\b|make\s+this\s+the\s+default\b|from\s+now\s+on\b)|以后(?:都|请|记得|默认|一律)?|请记住|帮我记住|记住我|我(?:习惯|偏好)|我希望(?:以后|每次|默认|一律|总是)|每次都|默认(?:用|先|都)|一律(?:用|先|都)?|总是(?:用|先|都)?)/i
const NOISY_HABIT_DISCUSSION_RE = /(why|debug|investigate|research|review|analy[sz]e|improve|design|logic|classifier|candidate|capture|为什么|怎么|调研|研究|评审|审查|改进|设计|逻辑|候选|捕获|命中).{0,80}(habit|preference|memory|norm|习惯|偏好|记忆|规范|约定)|(habit|preference|memory|norm|习惯|偏好|记忆|规范|约定).{0,80}(why|debug|investigate|research|review|analy[sz]e|improve|design|logic|classifier|candidate|capture|为什么|怎么|调研|研究|评审|审查|改进|设计|逻辑|候选|捕获|命中)/i
const AGENT_PROMPT_PREFIX_RE = /^\s*(?:TASK|CONTEXT|AXIS|EXPECTED OUTCOME|MUST DO|MUST NOT DO|REQUEST):/i
const ONE_OFF_WORK_RE = /(fix|repair|update|submit|publish|release|commit|create\s+pr|修复|更新|提交|发布|上线).{0,80}(pr|readme|docs?|todo|ui|bug|文档|待办|规范|约定|项目|下拉|按钮)/i
const ANALYSIS_OR_NORM_REQUEST_RE = /(分析|总结|通用|经验|规范|约定).{0,100}(bug|问题|以后|避免|重复|习惯|偏好|要求)|(bug|问题|规范|约定|习惯|偏好).{0,100}(分析|总结|通用|经验|以后|避免|重复)|(analy[sz]e|summari[sz]e|generaliz|lessons? learned|norms?|conventions?).{0,100}(habit|preference|bug|project|memory)/i
const PROJECT_CONVENTION_RE = /(\b(?:dev|main|branch(?:es)?|diff|pull request|pr)\b|项目|仓库|代码库|分支|规范|约定).{0,100}(\b(?:dev|main|branch(?:es)?|diff|pull request|pr)\b|项目|仓库|代码库|分支|规范|约定)|\b(?:dev|main)\b.{0,100}\b(?:dev|main)\b|(?:this\s+(?:project|repo|repository|codebase)|本项目|这个项目|本仓库|这个仓库|该项目|该仓库).{0,100}(?:always|usually|prefer|remember|以后|每次|总是|默认|规范|约定|pr|branch|commit)/i
// Actual information-seeking / complaint phrasing — NOT a durable word plus a
// polite question mark. Mirrors Core's _INFORMATION_SEEKING_OR_COMPLAINT_RE.
const INFORMATION_SEEKING_OR_COMPLAINT_RE = /(?:有没有|是否(?:可以|要)|怎么(?:办|做|更新)|为什么|有通用的|不追求|太麻烦|麻烦).{0,100}(?:方式|办法|更新|规范|约定|这样|那样|怎么)|(?:以后|每次).{0,100}(?:有没有通用的|太麻烦|麻烦这样)/i
// A polite confirmation tail ("可以吗/好吗") does not make an explicit preference noise.
const POLITE_PREFERENCE_QUESTION_RE = /(?:可以吗|好吗|行吗|好不好)[\s？！!?。]*$/i
// First-person / remember phrasing is stronger evidence than generic analysis/debug words.
const EXPLICIT_PERSONAL_PREFERENCE_RE = /(?:我(?:习惯|偏好|喜欢|希望)|请记住我|帮我记住|remember that i|please remember that i|always prefer|i prefer|i usually)/i
// Explicit SINGLE-project scope: keeps "这个项目/this repo" phrasing a project convention
// even under a first-person marker. Mirrors Core's PROJECT_SCOPE_HINTS.
const SINGLE_PROJECT_SCOPE_RE = /(?:this\s+(?:project|repo|repository|codebase)|in\s+this\s+repo|本项目|这个项目|本仓库|这个仓库|该项目|该仓库|这个代码库)/i

export function looksLikeHabitIntent(text: string): boolean {
  return DURABLE_PREFERENCE_RE.test(text) && !isNoisyHabitCandidate(text)
}

function isNoisyHabitCandidate(text: string): boolean {
  // An explicit first-person / remember preference overrides a polite confirmation
  // question or a generic analysis/norm mention — it is still a durable preference.
  const explicitPersonal = EXPLICIT_PERSONAL_PREFERENCE_RE.test(text)
  if (explicitPersonal && (POLITE_PREFERENCE_QUESTION_RE.test(text) || ANALYSIS_OR_NORM_REQUEST_RE.test(text))) return false
  // A first-person cross-project preference that merely mentions project terms is a
  // durable habit, unless it explicitly scopes to a single project.
  if (explicitPersonal && PROJECT_CONVENTION_RE.test(text) && !SINGLE_PROJECT_SCOPE_RE.test(text)) {
    // A first-person standing preference is not one-off work even when it names
    // commit/PR "规范"; only agent-prompt/discussion/info-seeking noise still bars it.
    return (
      AGENT_PROMPT_PREFIX_RE.test(text) ||
      NOISY_HABIT_DISCUSSION_RE.test(text) ||
      INFORMATION_SEEKING_OR_COMPLAINT_RE.test(text)
    )
  }
  return (
    AGENT_PROMPT_PREFIX_RE.test(text) ||
    NOISY_HABIT_DISCUSSION_RE.test(text) ||
    ONE_OFF_WORK_RE.test(text) ||
    ANALYSIS_OR_NORM_REQUEST_RE.test(text) ||
    PROJECT_CONVENTION_RE.test(text) ||
    INFORMATION_SEEKING_OR_COMPLAINT_RE.test(text)
  )
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
