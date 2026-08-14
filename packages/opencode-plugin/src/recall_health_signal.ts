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

// Only the low_signal verdict is actionable in-session. no_log / no_activity /
// healthy are either not the user's problem or need no nudge, so they stay silent.
export function lowSignalRecallToast(health: RecallHealth): string | null {
  if (health.status !== "low_signal") return null
  const hint = health.hint ? ` — ${health.hint}` : ""
  return `💡 SyberMem: recall quality is low${hint}`
}
