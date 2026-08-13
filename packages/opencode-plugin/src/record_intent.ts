import { writeFileSync } from "fs"
import { join } from "path"
import { sybermemText, type Shell } from "./runtime"

const INTENT_TYPES = ["change", "decision", "requirement", "bug"] as const
export type RecordIntentType = typeof INTENT_TYPES[number]

export interface RecordIntentMetadata {
  readonly record_intent: true
  readonly classification: RecordIntentType
  readonly action: "/sybermem-record"
  readonly reason: string
  readonly source: "opencode-chat-message"
  readonly created_at: string
  readonly matched_pattern: string
  readonly phrase: ""
}

interface IntentRule { readonly classification: RecordIntentType; readonly id: string; readonly pattern: RegExp; readonly reason: string }
interface CoreIntentCandidate { readonly classification: string; readonly action?: string; readonly reason?: string }

const BLOCKED_PATTERN = /(password\s*=|token\s*=|secret\s*=|bearer\s+[a-z0-9._-]+|api[_ -]?key\s*=|begin\s+(?:rsa\s+)?private\s+key|ignore\s+(?:all\s+)?previous|system\s+prompt|developer\s+message|<\/?(?:system|developer|tool)[^>]*>|\/sybermem-record\s+--|不要.{0,8}(记录|沉淀)|do\s+not\s+record|don'?t\s+record)/i
const RULES: readonly IntentRule[] = [
  { classification: "bug", id: "bug-fix", pattern: /(bug|fix|crash|regression|修复|缺陷|问题)/i, reason: "explicit bug record request" },
  { classification: "decision", id: "decision", pattern: /(decision|architecture decision|adr|决定|决策)/i, reason: "explicit decision record request" },
  { classification: "requirement", id: "requirement", pattern: /(requirement|需求|must|必须|should)/i, reason: "explicit requirement record request" },
  { classification: "change", id: "change", pattern: /(record|记录|沉淀|实现|完成|change)/i, reason: "explicit change record request" },
]

export function classifyRecordIntent(text: string, createdAt = new Date().toISOString()): RecordIntentMetadata | null {
  if (!/(record|记录|沉淀)/i.test(text) || isBlockedPrompt(text)) return null
  for (const rule of RULES) {
    if (rule.pattern.test(text)) {
      return { record_intent: true, classification: rule.classification, action: "/sybermem-record", reason: rule.reason, source: "opencode-chat-message", created_at: createdAt, matched_pattern: rule.id, phrase: "" }
    }
  }
  return null
}

export function isBlockedPrompt(text: string): boolean {
  return BLOCKED_PATTERN.test(text)
}

function isRecordIntentType(classification: string): classification is RecordIntentType {
  return classification === "change" || classification === "decision" || classification === "requirement" || classification === "bug"
}

function fromCoreCandidate(candidate: CoreIntentCandidate, createdAt: string): RecordIntentMetadata | null {
  if (!isRecordIntentType(candidate.classification)) return null
  return {
    record_intent: true,
    classification: candidate.classification,
    action: "/sybermem-record",
    reason: typeof candidate.reason === "string" ? candidate.reason : "bounded core classifier match",
    source: "opencode-chat-message",
    created_at: createdAt,
    matched_pattern: "core-classifier",
    phrase: "",
  }
}

async function classifyWithCli($: Shell, root: string, text: string, createdAt: string): Promise<RecordIntentMetadata | null> {
  try {
    const candidate: unknown = JSON.parse(await sybermemText($, root, ["record", "intent", "--prompt", text, "--format", "json"]))
    if (typeof candidate !== "object" || candidate === null) return null
    const classification = Reflect.get(candidate, "classification")
    const reason = Reflect.get(candidate, "reason")
    if (typeof classification !== "string") return null
    return fromCoreCandidate({ classification, reason: typeof reason === "string" ? reason : undefined }, createdAt)
  } catch {
    return null
  }
}

export function captureRecordIntent(root: string, text: string, createdAt?: string): boolean {
  const metadata = classifyRecordIntent(text, createdAt)
  if (!metadata) return false
  try {
    writeFileSync(join(root, ".sybermem", ".record-intent.json"), JSON.stringify(metadata, null, 2) + "\n", "utf-8")
    return true
  } catch {
    return false
  }
}

export async function captureRecordIntentWithCli($: Shell, root: string, text: string, createdAt = new Date().toISOString()): Promise<boolean> {
  if (isBlockedPrompt(text)) return false
  const metadata = await classifyWithCli($, root, text, createdAt) ?? classifyRecordIntent(text, createdAt)
  if (!metadata) return false
  try {
    writeFileSync(join(root, ".sybermem", ".record-intent.json"), JSON.stringify(metadata, null, 2) + "\n", "utf-8")
    return true
  } catch {
    return false
  }
}
