# SyberMem - update script (Windows)
# Sync current skills to the Claude Code, OpenCode, and Codex user directories.

$ErrorActionPreference = "Stop"
$AdrPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillSource = Join-Path $AdrPath "packages\claude-skills"
$CodexHookSource = Join-Path $AdrPath ".codex\hooks\user_prompt.py"
$CodexSessionHookSource = Join-Path $AdrPath ".codex\hooks\session_start.py"
$CodexSessionEndHookSource = Join-Path $AdrPath ".codex\hooks\session_end.py"
$CodexStopHookSource = Join-Path $AdrPath ".codex\hooks\stop.py"
$CodexPostCompactHookSource = Join-Path $AdrPath ".codex\hooks\post_compact.py"
$CodexObservabilitySource = Join-Path $AdrPath ".codex\hooks\_codex_observability.py"
$CodexHookDir = Join-Path $env:USERPROFILE ".codex\hooks"
$CodexHookPath = Join-Path $CodexHookDir "sybermem_user_prompt.py"
$CodexSessionHookPath = Join-Path $CodexHookDir "sybermem_session_start.py"
$CodexSessionEndHookPath = Join-Path $CodexHookDir "sybermem_session_end.py"
$CodexStopHookPath = Join-Path $CodexHookDir "sybermem_stop.py"
$CodexPostCompactHookPath = Join-Path $CodexHookDir "sybermem_post_compact.py"
$CodexObservabilityPath = Join-Path $CodexHookDir "_codex_observability.py"
$CodexHooksJson = Join-Path $env:USERPROFILE ".codex\hooks.json"
$LauncherDir = Join-Path $env:USERPROFILE ".claude\sybermem"
$LauncherPath = Join-Path $LauncherDir "launch_record_change_on_stop.py"
$UnifiedLauncherSource = Join-Path $AdrPath "scripts\global-hook-launcher.py"
$UnifiedLauncherPath = Join-Path $LauncherDir "launch_hook.py"
$ClaudePython = $null
foreach ($candidate in @("python", "python3")) {
    $found = Get-Command $candidate -ErrorAction SilentlyContinue
    if (-not $found) { continue }
    try {
        $reported = & $candidate -c 'import os,sys; p=os.path.realpath(sys.executable); assert os.path.isabs(p) and os.path.isfile(p) and p.lower().endswith(chr(46)+chr(101)+chr(120)+chr(101)); print(p)' 2>$null
        if ($LASTEXITCODE -ne 0) { continue }
        $exe = [string]($reported | Select-Object -Last 1)
        if (-not [System.IO.Path]::IsPathRooted($exe) -or -not $exe.EndsWith(".exe", [System.StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $exe -PathType Leaf)) { continue }
        & $exe -c 'import sys; sys.exit(0)' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $ClaudePython = $exe; break }
    } catch { continue }
}
if (-not $ClaudePython) { throw "No working real Python executable (python/python3); Claude runtime not verified" }
$LauncherSource = Join-Path $AdrPath "scripts\global-stop-hook-launcher.py"
$SessionLauncherSource = Join-Path $AdrPath "scripts\global-session-start-launcher.py"
$SessionLauncherPath = Join-Path $LauncherDir "launch_session_start_context.py"
$ManifestSource = Join-Path $AdrPath "scripts\managed-install.json"
$ManifestPath = Join-Path $LauncherDir "managed-install.json"
$RemoverSource = Join-Path $AdrPath "scripts\safe-managed-remove.py"
$RemoverPath = Join-Path $LauncherDir "safe-managed-remove.py"
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

Write-Host "=== SyberMem Update ==="

function Remove-ManagedDirectory {
    param([string]$Root, [string]$Target)
    & $ClaudePython $RemoverSource child --root $Root --name (Split-Path -Leaf $Target)
    if ($LASTEXITCODE -ne 0) { throw "Managed removal failed: $Target" }
}

foreach ($target in $Targets) {
    if (-not (Test-Path $target.Path)) {
        New-Item -ItemType Directory -Path $target.Path -Force | Out-Null
    }
    foreach ($retiredSkill in @("sybermem-phase-confirm", "sybermem-team-publish", "sybermem-team-summary", "sybermem-link")) {
        $retiredPath = Join-Path $target.Path $retiredSkill
        if (Test-Path $retiredPath) {
            Remove-ManagedDirectory -Root $target.Path -Target $retiredPath
        }
    }
    foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-resume", "sybermem-digest", "sybermem-phase-analyze", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-theme-digest", "sybermem-habit", "sybermem-uninstall", "sybermem-install")) {
        $src = Join-Path $SkillSource $skill
        $dst = Join-Path $target.Path $skill
        if (Test-Path $src) {
            if (Test-Path $dst) {
                Remove-ManagedDirectory -Root $target.Path -Target $dst
            }
            Copy-Item -Path $src -Destination $dst -Recurse -Force
            Write-Host "  [$($target.Label)] updated: /$skill"
        }
    }
}

function Install-CodexUserPromptHook {
    if ((-not (Test-Path $CodexHookSource)) -or (-not (Test-Path $CodexSessionHookSource)) -or (-not (Test-Path $CodexSessionEndHookSource)) -or (-not (Test-Path $CodexStopHookSource)) -or (-not (Test-Path $CodexPostCompactHookSource))) {
        Write-Host "  [Codex] skipped hooks: one or more sources were not found"
        return
    }

    if (-not (Test-Path $CodexHookDir)) {
        New-Item -ItemType Directory -Path $CodexHookDir -Force | Out-Null
    }
    Copy-Item -Path $CodexHookSource -Destination $CodexHookPath -Force
    Copy-Item -Path $CodexSessionHookSource -Destination $CodexSessionHookPath -Force
    Copy-Item -Path $CodexSessionEndHookSource -Destination $CodexSessionEndHookPath -Force
    Copy-Item -Path $CodexStopHookSource -Destination $CodexStopHookPath -Force
    Copy-Item -Path $CodexPostCompactHookSource -Destination $CodexPostCompactHookPath -Force
    if (Test-Path $CodexObservabilitySource) {
        Copy-Item -Path $CodexObservabilitySource -Destination $CodexObservabilityPath -Force
    }

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
        statusMessage = "SyberMem：召回相关项目记忆…"
    }
    $sessionManaged = [ordered]@{
        type = "command"
        command = "python `"$CodexSessionHookPath`""
        additionalContextLimit = 6000
        statusMessage = "SyberMem：加载项目记忆与规范…"
    }
    $sessionEndManaged = [ordered]@{
        type = "command"
        command = "python `"$CodexSessionEndHookPath`""
        statusMessage = "SyberMem：结算本会话召回命中…"
    }
    $stopManaged = [ordered]@{
        type = "command"
        command = "python `"$CodexStopHookPath`""
        statusMessage = "SyberMem：检查是否需要记录本次改动…"
    }
    $postCompactManaged = [ordered]@{
        type = "command"
        command = "python `"$CodexPostCompactHookPath`""
        statusMessage = "SyberMem：标记 compaction 以便下次会话续接…"
    }
    $hooks["UserPromptSubmit"] = @((Remove-Managed (Get-Handlers "UserPromptSubmit") "sybermem_user_prompt.py") + $promptManaged)
    $hooks["SessionStart"] = @((Remove-Managed (Get-Handlers "SessionStart") "sybermem_session_start.py") + $sessionManaged)
    $hooks["SessionEnd"] = @((Remove-Managed (Get-Handlers "SessionEnd") "sybermem_session_end.py") + $sessionEndManaged)
    $hooks["Stop"] = @((Remove-Managed (Get-Handlers "Stop") "sybermem_stop.py") + $stopManaged)
    $hooks["PostCompact"] = @((Remove-Managed (Get-Handlers "PostCompact") "sybermem_post_compact.py") + $postCompactManaged)

    if (-not (Test-Path (Split-Path -Parent $CodexHooksJson))) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $CodexHooksJson) -Force | Out-Null
    }
    $data | ConvertTo-Json -Depth 20 | Set-Content -Path $CodexHooksJson -Encoding UTF8
    Write-Host "  [Codex] installed UserPromptSubmit hook: $CodexHookPath"
    Write-Host "  [Codex] installed SessionStart hook: $CodexSessionHookPath"
    Write-Host "  [Codex] installed SessionEnd hook: $CodexSessionEndHookPath"
    Write-Host "  [Codex] installed Stop hook: $CodexStopHookPath"
    Write-Host "  [Codex] installed PostCompact hook: $CodexPostCompactHookPath"
    Write-Host "  [Codex] updated hooks.json without removing unrelated hooks: $CodexHooksJson"
}

Install-CodexUserPromptHook

    & $ClaudePython (Join-Path $AdrPath "scripts\claude-runtime-deploy.py") --root $AdrPath --home $env:USERPROFILE
    if ($LASTEXITCODE -ne 0) { throw "Claude runtime deployment refused" }
if (-not (Test-Path $CliDir)) {
    New-Item -ItemType Directory -Path $CliDir -Force | Out-Null
}
& $ClaudePython -m venv $CliVenv
& (Join-Path $CliVenv "Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $CliVenv "Scripts\pip.exe") install --upgrade --force-reinstall (Join-Path $AdrPath "packages\core") (Join-Path $AdrPath "packages\cli")
# Do NOT export SYBERMEM_HOME: it used to split the user-habit store away from the
# documented ~/.sybermem home. The launcher only locates the venv now; Core resolves
# the canonical home so launcher and bare `sybermem` share one habit store.
@'
@echo off
"%USERPROFILE%\.claude\sybermem\cli\venv\Scripts\sybermem.exe" %*
'@ | Set-Content -Path $CliWrapper -Encoding ASCII
Write-Host "  [Global] installed sybermem CLI: $CliWrapper"




    # Shared transactional OpenCode deployment.
    & $ClaudePython (Join-Path $AdrPath "scripts\opencode-install.py") install --root $AdrPath --home $env:USERPROFILE
    if ($LASTEXITCODE -ne 0) { throw "OpenCode deployment failed" }

Write-Host ""
Write-Host "=== Update Complete ==="
Write-Host ""
Write-Host "Available Skills:"
Write-Host "  /sybermem-init-project  - Initialize or refresh the current project"
Write-Host "  /sybermem-record        - Create a record (auto-detects type)"
Write-Host "  /sybermem-summary       - Generate weekly/monthly reports"
Write-Host "  /sybermem-resume        - Build a read-only restart view"
Write-Host "  /sybermem-digest        - Create a durable phase digest"
Write-Host "  /sybermem-phase-analyze - Build or refresh the phase index"
Write-Host "  /using-sybermem         - Show status and the recommended next command"
Write-Host "  /sybermem-update        - Refresh global skills and the current project"
Write-Host "  /sybermem-search        - Search records by query, topic, phase, date, or ID"
Write-Host "  /sybermem-theme-digest  - Create a cross-phase topic digest"

Write-Host "  /sybermem-habit         - Manage user-level habit memory and reminders"
Write-Host "  /sybermem-uninstall     - Safely choose project-level or global uninstall"
Write-Host "  /sybermem-install       - Install the complete SyberMem system from a fresh machine (new-user entrypoint)"
Write-Host ""
$sybermemOnPath = ($env:PATH -split ';' | Where-Object { $_.TrimEnd('\') -ieq $CliDir.TrimEnd('\') }).Count -gt 0
if ($sybermemOnPath) {
    Write-Host "sybermem CLI installed and on PATH. Run: sybermem project init --register"
} else {
    Write-Host "sybermem CLI installed at: $CliWrapper"
    Write-Host "To run it as ``sybermem`` from anywhere, add this directory to your PATH: $CliDir"
    Write-Host "Or run it by full path: & `"$CliWrapper`" project init --register"
}
Write-Host ""
Write-Host "Next: open your project and run /sybermem-update"
Write-Host "For a local project refresh check, run /sybermem-init-project"
Write-Host ""
Write-Host "Note: global updates do not refresh project managed files; run /sybermem-update in the project (it removes legacy AGENTS.md / CLAUDE.md protocol blocks)"
Write-Host "Global Claude hook runtime deployed; project settings NOT migrated. Run sybermem project refresh inside each project. Host behavior is unverified."

if ((Test-Path (Join-Path $LegacyLocalSkills "sybermem-init-project")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-record")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-summary")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-update"))) {
    Write-Host ""
    Write-Host "Migration note: this repository still has old project-level SyberMem skill copies (.claude/skills/sybermem-*)."
    Write-Host "They may appear alongside global skills; delete them after switching to global installation."
}
