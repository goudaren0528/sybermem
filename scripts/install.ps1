# SyberMem - install script (Windows)
# Copy skills to the Claude Code and OpenCode user directories.

$ErrorActionPreference = "Stop"
$AdrPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillSource = Join-Path $AdrPath "packages\claude-skills"
$LauncherDir = Join-Path $env:USERPROFILE ".claude\sybermem"
$LauncherPath = Join-Path $LauncherDir "launch_record_change_on_stop.py"
$LauncherSource = Join-Path $AdrPath "scripts\global-stop-hook-launcher.py"
$SessionLauncherSource = Join-Path $AdrPath "scripts\global-session-start-launcher.py"
$SessionLauncherPath = Join-Path $LauncherDir "launch_session_start_context.py"
$CliDir = Join-Path $env:USERPROFILE ".claude\sybermem\cli"
$CliVenv = Join-Path $CliDir "venv"
$CliWrapper = Join-Path $CliDir "sybermem.cmd"
$PluginSource = Join-Path $AdrPath "packages\opencode-plugin\sybermem.ts"
$OpenCodePluginDir = Join-Path $env:USERPROFILE ".config\opencode\plugins"
$LegacyLocalSkills = Join-Path $AdrPath ".claude\skills"

$Targets = @(
    @{ Path = Join-Path $env:USERPROFILE ".claude\skills"; Label = "Claude Code" }
    @{ Path = Join-Path $env:USERPROFILE ".config\opencode\skills"; Label = "OpenCode" }
)

Write-Host "=== SyberMem Install ==="

foreach ($target in $Targets) {
    if (-not (Test-Path $target.Path)) {
        New-Item -ItemType Directory -Path $target.Path -Force | Out-Null
    }
    foreach ($legacySkill in @("init-project", "record", "summary")) {
        $legacyPath = Join-Path $target.Path $legacySkill
        if (Test-Path $legacyPath) {
            Remove-Item -Path $legacyPath -Recurse -Force -Confirm:$false
        }
    }
    foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-resume", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest", "sybermem-team-publish", "sybermem-team-summary")) {
        $src = Join-Path $SkillSource $skill
        $dst = Join-Path $target.Path $skill
        if (Test-Path $src) {
            if (Test-Path $dst) {
                Remove-Item -Path $dst -Recurse -Force -Confirm:$false
            }
            Copy-Item -Path $src -Destination $dst -Recurse -Force
            Write-Host "  [$($target.Label)] installed: /$skill"
        }
    }
}

# Claude Code: install global stop hook launcher
if (Test-Path (Join-Path $env:USERPROFILE ".claude")) {
    if (-not (Test-Path $LauncherDir)) {
        New-Item -ItemType Directory -Path $LauncherDir -Force | Out-Null
    }
    Copy-Item -Path $LauncherSource -Destination $LauncherPath -Force
    Write-Host "  [Claude Code] installed stop hook launcher: $LauncherPath"
    Copy-Item -Path $SessionLauncherSource -Destination $SessionLauncherPath -Force
    Write-Host "  [Claude Code] installed session start launcher: $SessionLauncherPath"
    if (-not (Test-Path $CliDir)) {
        New-Item -ItemType Directory -Path $CliDir -Force | Out-Null
    }
    python -m venv $CliVenv
    & (Join-Path $CliVenv "Scripts\python.exe") -m pip install --upgrade pip
    & (Join-Path $CliVenv "Scripts\pip.exe") install --upgrade --force-reinstall (Join-Path $AdrPath "packages\core") (Join-Path $AdrPath "packages\cli")
    @'
@echo off
set "SYBERMEM_HOME=%USERPROFILE%\.claude\sybermem\cli"
"%SYBERMEM_HOME%\venv\Scripts\sybermem.exe" %*
'@ | Set-Content -Path $CliWrapper -Encoding ASCII
    Write-Host "  [Claude Code] installed sybermem CLI: $CliWrapper"
}

# OpenCode: install plugin
if (Test-Path (Join-Path $env:USERPROFILE ".config\opencode")) {
    if (-not (Test-Path $OpenCodePluginDir)) {
        New-Item -ItemType Directory -Path $OpenCodePluginDir -Force | Out-Null
    }
    Copy-Item -Path $PluginSource -Destination (Join-Path $OpenCodePluginDir "sybermem.ts") -Force
    Write-Host "  [OpenCode] installed plugin: $OpenCodePluginDir\sybermem.ts"
}

Write-Host ""
Write-Host "=== Install Complete ==="
Write-Host ""
Write-Host "Available Skills:"
Write-Host "  /sybermem-init-project  - Initialize or refresh the current project"
Write-Host "  /sybermem-record        - Create a record (auto-detects type)"
Write-Host "  /sybermem-summary       - Generate weekly/monthly reports"
Write-Host "  /sybermem-resume        - Build a read-only restart view"
Write-Host "  /sybermem-digest        - Create a durable phase digest"
Write-Host "  /sybermem-phase-analyze - Build or refresh the phase index"
Write-Host "  /sybermem-phase-confirm - Confirm or adjust phase candidates"
Write-Host "  /using-sybermem         - Show status and the recommended next command"
Write-Host "  /sybermem-update        - Refresh global skills and the current project"
Write-Host "  /sybermem-search        - Search records by query, topic, phase, date, or ID"
Write-Host "  /sybermem-link          - Link existing records"
Write-Host "  /sybermem-theme-digest  - Create a cross-phase topic digest"
Write-Host "  /sybermem-team-publish  - Publish the current project to Team memory"
Write-Host "  /sybermem-team-summary  - Generate the Team management summary"
Write-Host ""
Write-Host "sybermem CLI installed. Run: sybermem project init --register"
Write-Host ""
Write-Host "Next: open your project and run /sybermem-update"
Write-Host "For initialization only, run /sybermem-init-project"
Write-Host ""
Write-Host "Note: global updates do not refresh project AGENTS.md / CLAUDE.md; run /sybermem-update in the project"
Write-Host "Note: subdirectory stop-hook support is provided by ~/.claude/sybermem/launch_record_change_on_stop.py"

if ((Test-Path (Join-Path $LegacyLocalSkills "sybermem-init-project")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-record")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-summary")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-update"))) {
    Write-Host ""
    Write-Host "Migration note: this repository still has old project-level SyberMem skill copies (.claude/skills/sybermem-*)."
    Write-Host "They may appear alongside global skills; delete them after switching to global installation."
}
