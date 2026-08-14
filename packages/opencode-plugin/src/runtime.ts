import { existsSync } from "fs"
import { join, resolve } from "path"

export type Shell = (strings: TemplateStringsArray, ...values: readonly string[]) => ShellCommand

export interface ShellCommand {
  cwd(path: string): ShellCommand
  text(): Promise<string>
  nothrow(): ShellCommand
}

export function resolveRoot(cwd: string): string | null {
  let current = resolve(cwd)
  while (true) {
    const hasSybermem = existsSync(join(current, ".sybermem"))
    const hasSettings = existsSync(join(current, ".claude", "settings.json"))
    const hasIndex = existsSync(join(current, ".sybermem", "INDEX.md"))
    if (hasSybermem && (hasSettings || hasIndex)) return current
    const parent = resolve(current, "..")
    if (parent === current) break
    current = parent
  }
  return null
}

function userHome(): string | null {
  return process.env.USERPROFILE ?? process.env.HOME ?? null
}

export function resolveSybermemCommand(): string {
  const home = userHome()
  if (!home) return "sybermem"
  const launcher = process.platform === "win32"
    ? join(home, ".claude", "sybermem", "cli", "sybermem.cmd")
    : join(home, ".claude", "sybermem", "cli", "sybermem")
  return existsSync(launcher) ? launcher : "sybermem"
}

export type SybermemRoute =
  | readonly ["next-step", "--format", "json"]
  | readonly ["habit", "inject", "--context", string, "--format", "markdown"]
  | readonly ["habit", "intent", "--prompt", string, "--format", "json"]
  | readonly ["habit", "awareness", "--format", "json"]
  | readonly ["context", "session", "--format", "markdown"]
  | readonly ["context", "recall", "--query", string, "--format", "markdown"]
  | readonly ["context", "habit", "--context", string, "--delivery", "prompt-time", "--format", "markdown"]
  | readonly ["record", "intent", "--prompt", string, "--format", "json"]

export async function sybermemText($: Shell, root: string, args: SybermemRoute): Promise<string> {
  const sybermem = resolveSybermemCommand()
  switch (args[0]) {
    case "next-step":
      return $`${sybermem} next-step ${args[1]} ${args[2]}`.cwd(root).text()
    case "habit":
      if (args[1] === "intent") return $`${sybermem} habit intent --prompt ${args[3]} --format json`.cwd(root).nothrow().text()
      if (args[1] === "awareness") return $`${sybermem} habit awareness --format json`.cwd(root).nothrow().text()
      return $`${sybermem} habit inject ${args[2]} ${args[3]} ${args[4]} ${args[5]}`.cwd(root).text()
    case "context":
      switch (args[1]) {
        case "session":
          return $`${sybermem} context session ${args[2]} ${args[3]}`.cwd(root).text()
        case "recall":
          return $`${sybermem} context recall --query ${args[3]} --format markdown`.cwd(root).text()
        case "habit":
          return $`${sybermem} context habit --context ${args[3]} --delivery ${args[5]} --format ${args[7]}`.cwd(root).text()
      }
      break
    case "record":
      return $`${sybermem} record intent --prompt ${args[3]} --format ${args[5]}`.cwd(root).text()
  }
  return ""
}

export async function digestStatusText($: Shell, root: string): Promise<string> {
  const sybermem = resolveSybermemCommand()
  return $`${sybermem} digest status --format json`.cwd(root).nothrow().text()
}

export async function memoryStatsText($: Shell, root: string): Promise<string> {
  const sybermem = resolveSybermemCommand()
  return $`${sybermem} project memory-stats --format json`.cwd(root).nothrow().text()
}

export async function recordFilesText($: Shell, root: string, ids: string): Promise<string> {
  const sybermem = resolveSybermemCommand()
  return $`${sybermem} project record-files --ids ${ids} --format json`.cwd(root).nothrow().text()
}
