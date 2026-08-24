export interface Norm {
  readonly recordId: string
  readonly statement: string
  readonly scope: string
}

// Parse the norms array out of `sybermem norms list --format json`. Fail-closed to []
// on any malformed/absent shape so a caller stays silent rather than injecting garbage.
export function parseNorms(json: string): Norm[] {
  const trimmed = json.trim()
  if (!trimmed) return []
  try {
    const parsed: unknown = JSON.parse(trimmed)
    if (typeof parsed !== "object" || parsed === null) return []
    const norms = Reflect.get(parsed, "norms")
    if (!Array.isArray(norms)) return []
    const out: Norm[] = []
    for (const raw of norms) {
      if (typeof raw !== "object" || raw === null) continue
      const recordId = Reflect.get(raw, "record_id")
      const statement = Reflect.get(raw, "statement")
      const scope = Reflect.get(raw, "scope")
      if (typeof recordId === "string" && typeof statement === "string" && statement) {
        out.push({ recordId, statement, scope: typeof scope === "string" ? scope : "" })
      }
    }
    return out
  } catch {
    return []
  }
}

// Render the project constitution block from active global norms. Empty string when there
// are none, so callers can append unconditionally. Bounded by the CLI's own cap.
export function constitutionSection(norms: readonly Norm[]): string {
  if (norms.length === 0) return ""
  const lines = ["\n### Project Norms (binding)"]
  for (const norm of norms) lines.push(`- [${norm.recordId}] ${norm.statement}`)
  lines.push("These are binding project norms — follow them unless the user explicitly overrides.")
  return lines.join("\n") + "\n"
}

// Render a scoped-norms block (norms relevant to the current task area). Same shape as the
// constitution block but framed as context-scoped rather than always-on.
export function scopedNormSection(norms: readonly Norm[]): string {
  if (norms.length === 0) return ""
  const lines = ["\n### Relevant Project Norms"]
  for (const norm of norms) lines.push(`- [${norm.recordId}] (${norm.scope || "scoped"}) ${norm.statement}`)
  return lines.join("\n") + "\n"
}
