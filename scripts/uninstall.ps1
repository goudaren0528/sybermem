$ErrorActionPreference = "Stop"

$claudeSkills = Join-Path $env:USERPROFILE ".claude\skills"
$opencodeSkills = Join-Path $env:USERPROFILE ".config\opencode\skills"
$codexSkills = Join-Path $env:USERPROFILE ".agents\skills"
$claudeSybermem = Join-Path $env:USERPROFILE ".claude\sybermem"
$opencodePlugin = Join-Path $env:USERPROFILE ".config\opencode\plugins\sybermem.ts"

function Remove-ManagedDirectory {
  param([string]$Root, [string]$Target)
  if (-not (Test-Path -LiteralPath $Target)) { return }
  $rootItem = Get-Item -LiteralPath $Root -Force
  if (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Refusing linked managed root: $Root" }
  $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
  $parentFull = [IO.Path]::GetFullPath((Split-Path -Parent $Target)).TrimEnd('\', '/')
  if (-not [StringComparer]::OrdinalIgnoreCase.Equals($rootFull, $parentFull)) {
    throw "Refusing to remove path outside managed root: $Target"
  }
  $item = Get-Item -LiteralPath $Target -Force
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Remove-Item -LiteralPath $Target -Force -Confirm:$false
    return
  }
  Remove-Item -LiteralPath $Target -Recurse -Force -Confirm:$false
}

foreach ($name in @(
  "sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest",
  "sybermem-resume", "sybermem-phase-analyze", "using-sybermem",
  "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest",
  "sybermem-team-publish", "sybermem-team-summary", "sybermem-habit",
  "sybermem-phase-confirm"
)) {
  Remove-ManagedDirectory -Root $claudeSkills -Target (Join-Path $claudeSkills $name)
  Remove-ManagedDirectory -Root $opencodeSkills -Target (Join-Path $opencodeSkills $name)
  Remove-ManagedDirectory -Root $codexSkills -Target (Join-Path $codexSkills $name)
}

# Remove only SyberMem-owned launcher/runtime paths. Preserve unknown user files.
Remove-ManagedDirectory -Root $claudeSybermem -Target (Join-Path $claudeSybermem "cli")
foreach ($managedFile in @("launch_record_change_on_stop.py", "launch_session_start_context.py", "VERSION")) {
  Remove-Item -LiteralPath (Join-Path $claudeSybermem $managedFile) -Force -ErrorAction SilentlyContinue
}
if (Test-Path -LiteralPath $claudeSybermem) {
  $remaining = Get-ChildItem -LiteralPath $claudeSybermem -Force
  if ($remaining.Count -eq 0) { Remove-Item -LiteralPath $claudeSybermem -Force }
}
Remove-Item -Force $opencodePlugin -ErrorAction SilentlyContinue

Write-Host "SyberMem global uninstall complete."
Write-Host "Project histories under .sybermem/ were not removed."
