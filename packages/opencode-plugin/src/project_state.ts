import { existsSync, readFileSync } from "fs"
import { join } from "path"

export interface ParsedIndex {
  readonly conclusions: readonly string[]
  readonly topicIndex: Readonly<Record<string, readonly string[]>>
}

export interface PhaseIndexInfo {
  readonly exists: boolean
  readonly status?: string
  readonly confirmedCount?: number
  readonly activePhase?: string | null
}

export interface ProjectIdentity {
  readonly exists: boolean
  readonly projectId?: string | null
  readonly slug?: string | null
}

export interface StaleSignal {
  readonly stale: boolean
  readonly commitsAhead: number
  readonly boundary?: string
  readonly head?: string
}

export function parseIndex(root: string): ParsedIndex | null {
  const indexPath = join(root, ".sybermem", "INDEX.md")
  if (!existsSync(indexPath)) return null
  const content = readFileSync(indexPath, "utf-8")
  const conclusionsMatch = content.match(/## Key Conclusions\s*\n([\s\S]*?)(?=\n---|\n## )/)
  const conclusions: string[] = []
  if (conclusionsMatch) {
    for (const line of conclusionsMatch[1].split("\n")) {
      const trimmed = line.trim()
      if (trimmed.startsWith("- [")) conclusions.push(trimmed)
    }
  }
  const topicMatch = content.match(/## Topic Index\s*\n([\s\S]*?)(?=\n---|\n## |$)/)
  const topicIndex: Record<string, string[]> = {}
  if (topicMatch) {
    for (const line of topicMatch[1].split("\n")) {
      const m = line.match(/^- (\S+):\s*(.+)/)
      if (m) topicIndex[m[1]] = m[2].split(",").map((s) => s.trim())
    }
  }
  return { conclusions, topicIndex }
}

function getActivePhase(root: string): string | null {
  const phasePath = join(root, ".sybermem", "analysis", "phase-index.md")
  if (!existsSync(phasePath)) return null
  const phases = [...readFileSync(phasePath, "utf-8").matchAll(/### Phase: (.+)/g)]
  return phases.length === 0 ? null : phases[phases.length - 1][1]
}

export function parsePhaseIndex(root: string): PhaseIndexInfo {
  const phasePath = join(root, ".sybermem", "analysis", "phase-index.md")
  if (!existsSync(phasePath)) return { exists: false }
  const content = readFileSync(phasePath, "utf-8")
  const statusMatch = content.match(/^- status:\s*(.+)/m)
  const phases = [...content.matchAll(/### Phase: (.+)/g)]
  return { exists: true, status: statusMatch ? statusMatch[1].trim() : "unknown", confirmedCount: phases.length, activePhase: getActivePhase(root) }
}

export function parseProjectIdentity(root: string): ProjectIdentity {
  const projPath = join(root, ".sybermem", "project.yaml")
  if (!existsSync(projPath)) return { exists: false }
  let projectId: string | null = null
  let slug: string | null = null
  for (const raw of readFileSync(projPath, "utf-8").split("\n")) {
    const line = raw.trim()
    if (line.startsWith("project_id:")) projectId = line.split(":").slice(1).join(":").trim()
    else if (line.startsWith("slug:")) slug = line.split(":").slice(1).join(":").trim()
  }
  return { exists: true, projectId, slug }
}

export async function detectStaleSignal($: import("./runtime").Shell, root: string): Promise<StaleSignal> {
  const phasePath = join(root, ".sybermem", "analysis", "phase-index.md")
  if (!existsSync(phasePath)) return { stale: false, commitsAhead: 0 }
  const boundaryMatch = readFileSync(phasePath, "utf-8").match(/^- last_git_boundary:\s*(\S+)/m)
  if (!boundaryMatch) return { stale: false, commitsAhead: 0 }
  const boundary = boundaryMatch[1]
  try {
    const head = (await $`git rev-parse HEAD`.cwd(root).text()).trim()
    if (head === boundary) return { stale: false, commitsAhead: 0 }
    const countStr = (await $`git rev-list --count ${boundary}..HEAD`.cwd(root).text()).trim()
    const count = Number.parseInt(countStr, 10) || 0
    return { stale: count >= 3, commitsAhead: count, boundary, head: head.substring(0, 7) }
  } catch {
    return { stale: false, commitsAhead: 0 }
  }
}
