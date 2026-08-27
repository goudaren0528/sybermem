export interface RecallHealth {
  readonly status: string
  readonly hint: string
}

export function parseRecallHealth(json: string): RecallHealth | null {
  const trimmed = json.trim()
  if (!trimmed) return null
  try {
    const parsed: unknown = JSON.parse(trimmed)
    if (typeof parsed !== "object" || parsed === null) return null
    const health = Reflect.get(parsed, "recall_health")
    if (typeof health !== "object" || health === null) return null
    const status = Reflect.get(health, "status")
    const hint = Reflect.get(health, "hint")
    if (typeof status !== "string") return null
    return { status, hint: typeof hint === "string" ? hint : "" }
  } catch {
    return null
  }
}

// Only the actionable verdicts nudge in-session: low_signal (recall rarely
// fires), low_relevance (recall fires but rarely matches edited files), and
// low_measurability (recall fires but related_files anchors are too sparse).
// no_log / no_activity / healthy are either not the user's problem or need no
// nudge, so they stay silent.
export function lowSignalRecallToast(health: RecallHealth): string | null {
  if (health.status === "low_signal") {
    const hint = health.hint ? ` — ${health.hint}` : ""
    return `💡 SyberMem: recall quality is low${hint}`
  }
  if (health.status === "low_relevance") {
    const hint = health.hint ? ` — ${health.hint}` : ""
    return `💡 SyberMem: recall relevance is low${hint}`
  }
  if (health.status === "low_measurability") {
    const hint = health.hint ? ` — ${health.hint}` : ""
    return `💡 SyberMem: recall measurability is low${hint}`
  }
  return null
}
