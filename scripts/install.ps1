# SyberMem - install script (Windows)
# Copy skills to the Claude Code, OpenCode, and Codex user directories.

$ErrorActionPreference = "Stop"
$AdrPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillSource = Join-Path $AdrPath "packages\claude-skills"
$CodexHookSource = Join-Path $AdrPath ".codex\hooks\user_prompt.py"
$CodexSessionHookSource = Join-Path $AdrPath ".codex\hooks\session_start.py"
$CodexStopHookSource = Join-Path $AdrPath ".codex\hooks\stop.py"
$CodexPostCompactHookSource = Join-Path $AdrPath ".codex\hooks\post_compact.py"
$CodexHookDir = Join-Path $env:USERPROFILE ".codex\hooks"
$CodexHookPath = Join-Path $CodexHookDir "sybermem_user_prompt.py"
$CodexSessionHookPath = Join-Path $CodexHookDir "sybermem_session_start.py"
$CodexStopHookPath = Join-Path $CodexHookDir "sybermem_stop.py"
$CodexPostCompactHookPath = Join-Path $CodexHookDir "sybermem_post_compact.py"
$CodexHooksJson = Join-Path $env:USERPROFILE ".codex\hooks.json"
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
    @{ Path = Join-Path $env:USERPROFILE ".agents\skills"; Label = "Codex" }
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
    foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-resume", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest", "sybermem-team-publish", "sybermem-team-summary", "sybermem-habit")) {
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

function Install-CodexUserPromptHook {
    if ((-not (Test-Path $CodexHookSource)) -or (-not (Test-Path $CodexSessionHookSource)) -or (-not (Test-Path $CodexStopHookSource)) -or (-not (Test-Path $CodexPostCompactHookSource))) {
        Write-Host "  [Codex] skipped hooks: one or more sources were not found"
        return
    }

    if (-not (Test-Path $CodexHookDir)) {
        New-Item -ItemType Directory -Path $CodexHookDir -Force | Out-Null
    }
    Copy-Item -Path $CodexHookSource -Destination $CodexHookPath -Force
    Copy-Item -Path $CodexSessionHookSource -Destination $CodexSessionHookPath -Force
    Copy-Item -Path $CodexStopHookSource -Destination $CodexStopHookPath -Force
    Copy-Item -Path $CodexPostCompactHookSource -Destination $CodexPostCompactHookPath -Force

    $data = [ordered]@{}
    if (Test-Path $CodexHooksJson) {
        try {
            $loaded = Get-Content -Path $CodexHooksJson -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
            if ($loaded -is [System.Collections.IDictionary]) {
                $data = [ordered]@{}
                foreach ($key in $loaded.Keys) {
                    $data[$key] = $loaded[$key]
                }
            }
        } catch {
            $data = [ordered]@{}
        }
    }

    if (($data["hooks"] -isnot [System.Collections.IDictionary])) {
        $data["hooks"] = [ordered]@{}
    }
    $hooks = $data["hooks"]
    function Get-Handlers($eventName) {
        $event = $hooks[$eventName]
        if ($event -is [System.Collections.IList]) {
            return @($event)
        }
        if ($null -eq $event) {
            return @()
        }
        return @($event)
    }

    function Remove-Managed($handlers, $marker) {
        return @($handlers | Where-Object {
            -not (($_ -is [System.Collections.IDictionary]) -and ([string]($_["command"]) -like "*$marker*"))
        })
    }

    $promptManaged = [ordered]@{
        type = "command"
        command = "python `"$CodexHookPath`""
        additionalContextLimit = 6000
        message = "SyberMem prompt context adds bounded Codex recall and habit reminders when relevant."
    }
    $sessionManaged = [ordered]@{
        type = "command"
        command = "python `"$CodexSessionHookPath`""
        additionalContextLimit = 6000
        message = "SyberMem session context adds bounded Codex startup context when available."
    }
    $stopManaged = [ordered]@{
        type = "command"
        command = "python `"$CodexStopHookPath`""
        message = "SyberMem Stop nudge adds bounded record reminders without looping."
    }
    $postCompactManaged = [ordered]@{
        type = "command"
        command = "python `"$CodexPostCompactHookPath`""
        message = "SyberMem PostCompact marks compact re-seed for the next SessionStart."
    }
    $hooks["UserPromptSubmit"] = @((Remove-Managed (Get-Handlers "UserPromptSubmit") "sybermem_user_prompt.py") + $promptManaged)
    $hooks["SessionStart"] = @((Remove-Managed (Get-Handlers "SessionStart") "sybermem_session_start.py") + $sessionManaged)
    $hooks["Stop"] = @((Remove-Managed (Get-Handlers "Stop") "sybermem_stop.py") + $stopManaged)
    $hooks["PostCompact"] = @((Remove-Managed (Get-Handlers "PostCompact") "sybermem_post_compact.py") + $postCompactManaged)

    if (-not (Test-Path (Split-Path -Parent $CodexHooksJson))) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $CodexHooksJson) -Force | Out-Null
    }
    $data | ConvertTo-Json -Depth 20 | Set-Content -Path $CodexHooksJson -Encoding UTF8
    Write-Host "  [Codex] installed UserPromptSubmit hook: $CodexHookPath"
    Write-Host "  [Codex] installed SessionStart hook: $CodexSessionHookPath"
    Write-Host "  [Codex] installed Stop hook: $CodexStopHookPath"
    Write-Host "  [Codex] installed PostCompact hook: $CodexPostCompactHookPath"
    Write-Host "  [Codex] updated hooks.json without removing unrelated hooks: $CodexHooksJson"
}

Install-CodexUserPromptHook

# Global launchers: only needed by the Claude Code lifecycle hooks.
if (Test-Path (Join-Path $env:USERPROFILE ".claude")) {
    if (-not (Test-Path $LauncherDir)) {
        New-Item -ItemType Directory -Path $LauncherDir -Force | Out-Null
    }
    Copy-Item -Path $LauncherSource -Destination $LauncherPath -Force
    Write-Host "  [Claude Code] installed stop hook launcher: $LauncherPath"
    Copy-Item -Path $SessionLauncherSource -Destination $SessionLauncherPath -Force
    Write-Host "  [Claude Code] installed session start launcher: $SessionLauncherPath"
}

# sybermem CLI/runtime: install unconditionally. OpenCode skills (search/record/
# using-sybermem) call the `sybermem` CLI, so gating this on ~/.claude would leave
# OpenCode-only machines with skills that invoke a runtime that was never installed.
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
Write-Host "  [Global] installed sybermem CLI: $CliWrapper"

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
Write-Host "  /sybermem-habit         - Manage user-level habit memory and reminders"
Write-Host ""
# Honest PATH guidance: the wrapper lives in $CliDir, which is not on PATH by
# default on Windows. We do NOT modify the user's persistent PATH automatically
# (that is a visible, persistent change); we detect and guide instead.
$sybermemOnPath = ($env:PATH -split ';' | Where-Object { $_.TrimEnd('\') -ieq $CliDir.TrimEnd('\') }).Count -gt 0
if ($sybermemOnPath) {
    Write-Host "sybermem CLI installed and on PATH. Run: sybermem project init --register"
} else {
    Write-Host "sybermem CLI installed at: $CliWrapper"
    Write-Host "To run it as ``sybermem`` from anywhere, add this directory to your PATH:"
    Write-Host "  $CliDir"
    Write-Host "  e.g. setx PATH `"$CliDir;`$env:PATH`"  (opens a new shell to take effect)"
    Write-Host "Or run it by full path: & `"$CliWrapper`" project init --register"
}
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
