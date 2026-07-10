$ErrorActionPreference = "Stop"

$claudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
$opencodeSkills = Join-Path $env:USERPROFILE ".config\opencode\skills"
$claudeSybermem = Join-Path $env:USERPROFILE ".claude\sybermem"
$opencodePlugin = Join-Path $env:USERPROFILE ".config\opencode\plugins\sybermem.ts"

foreach ($name in @(
  "sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest",
  "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem",
  "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest",
  "sybermem-team-publish", "sybermem-team-summary"
)) {
  Remove-Item -Recurse -Force (Join-Path $claudeSkills $name) -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force (Join-Path $opencodeSkills $name) -ErrorAction SilentlyContinue
}

Remove-Item -Recurse -Force $claudeSybermem -ErrorAction SilentlyContinue
Remove-Item -Force $opencodePlugin -ErrorAction SilentlyContinue

Write-Host "SyberMem global uninstall complete."
Write-Host "Project histories under .sybermem/ were not removed."