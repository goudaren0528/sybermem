import { existsSync, readFileSync } from "fs"
import { join } from "path"

function userHome(): string | null {
  return process.env.USERPROFILE ?? process.env.HOME ?? null
}

export function readInstalledVersion(): string {
  const home = userHome()
  if (!home) return ""
  const marker = join(home, ".claude", "sybermem", "VERSION")
  if (!existsSync(marker)) return ""
  try {
    return readFileSync(marker, "utf-8").trim()
  } catch {
    return ""
  }
}

export function isManagedProject(root: string): boolean {
  return existsSync(join(root, ".sybermem", "project.yaml"))
}

export function readProjectVersion(root: string): string {
  const proj = join(root, ".sybermem", "project.yaml")
  if (!existsSync(proj)) return ""
  try {
    for (const raw of readFileSync(proj, "utf-8").split("\n")) {
      const line = raw.trim()
      if (line.startsWith("sybermem_version:")) return line.split(":").slice(1).join(":").trim()
    }
  } catch {}
  return ""
}

function parse(version: string): number[] {
  return version
    .trim()
    .split(".")
    .map((raw) => {
      let digits = ""
      for (const ch of raw) {
        if (ch >= "0" && ch <= "9") digits += ch
        else break
      }
      return digits ? Number.parseInt(digits, 10) : 0
    })
}

export function compareVersions(a: string, b: string): number {
  const pa = parse(a)
  const pb = parse(b)
  const width = Math.max(pa.length, pb.length)
  for (let i = 0; i < width; i++) {
    const x = pa[i] ?? 0
    const y = pb[i] ?? 0
    if (x < y) return -1
    if (x > y) return 1
  }
  return 0
}

export function isProjectOutdated(project: string, installed: string): boolean {
  if (!project || !installed) return false
  return compareVersions(project, installed) < 0
}

// Tri-state nudge decision so OLD projects (project.yaml predates the
// sybermem_version field) still get a one-time bootstrap nudge:
// - installed unknown -> false (no VERSION marker; can't judge)
// - not a managed project -> false
// - managed but no stamp yet -> true (needs first /sybermem-update)
// - managed and stamp < installed -> true
export function projectNeedsUpdate(root: string, installed: string): boolean {
  if (!installed || !isManagedProject(root)) return false
  const project = readProjectVersion(root)
  if (!project) return true
  return compareVersions(project, installed) < 0
}

export function updateNudgeMessage(root: string): string | null {
  const installed = readInstalledVersion()
  if (!projectNeedsUpdate(root, installed)) return null
  const project = readProjectVersion(root)
  const wasRefreshed = project
    ? `this project was last refreshed with ${project}`
    : `this project predates SyberMem version tracking`
  return `\u2B50 SyberMem ${installed} is installed; ${wasRefreshed}. Run /sybermem-update to apply the latest fixes.`
}
