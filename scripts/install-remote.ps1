# SyberMem - Remote Install (no clone needed)
# Usage: irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex

$ErrorActionPreference = "Stop"

$Repo = "goudaren0528/sybermem"
$Branch = "main"
$ZipUrl = "https://github.com/$Repo/archive/$Branch.zip"
$ArchivePrefix = "sybermem-$Branch"
$LauncherDir = Join-Path $env:USERPROFILE ".claude\sybermem"
$LauncherPath = Join-Path $LauncherDir "launch_record_change_on_stop.py"
$SessionLauncherPath = Join-Path $LauncherDir "launch_session_start_context.py"
$ManifestPath = Join-Path $LauncherDir "managed-install.json"
$RemoverPath = Join-Path $LauncherDir "safe-managed-remove.py"
$CliDir = Join-Path $LauncherDir "cli"
$CliVenv = Join-Path $CliDir "venv"
$CliWrapper = Join-Path $CliDir "sybermem.cmd"
$OpenCodePluginDir = Join-Path $env:USERPROFILE ".config\opencode\plugins"
$CodexHookDir = Join-Path $env:USERPROFILE ".codex\hooks"
$CodexHookPath = Join-Path $CodexHookDir "sybermem_user_prompt.py"
$CodexSessionHookPath = Join-Path $CodexHookDir "sybermem_session_start.py"
$CodexSessionEndHookPath = Join-Path $CodexHookDir "sybermem_session_end.py"
$CodexStopHookPath = Join-Path $CodexHookDir "sybermem_stop.py"
$CodexPostCompactHookPath = Join-Path $CodexHookDir "sybermem_post_compact.py"
$CodexObservabilityPath = Join-Path $CodexHookDir "_codex_observability.py"
$CodexHooksJson = Join-Path $env:USERPROFILE ".codex\hooks.json"

$Targets = @(
    @{ Path = Join-Path $env:USERPROFILE ".claude\skills"; Label = "Claude Code" }
    @{ Path = Join-Path $env:USERPROFILE ".config\opencode\skills"; Label = "OpenCode" }
    @{ Path = Join-Path $env:USERPROFILE ".agents\skills"; Label = "Codex" }
)

Write-Host "=== SyberMem Remote Install ==="
Write-Host ""

$TmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("sybermem-install-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null

try {
    Write-Host "Downloading from GitHub..."
    $ZipFile = Join-Path $TmpDir "repo.zip"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipFile -UseBasicParsing

    Expand-Archive -Path $ZipFile -DestinationPath $TmpDir -Force

    $SkillsSrc = Join-Path $TmpDir "$ArchivePrefix\packages\claude-skills"
    $LauncherSource = Join-Path $TmpDir "$ArchivePrefix\scripts\global-stop-hook-launcher.py"
    $SessionLauncherSource = Join-Path $TmpDir "$ArchivePrefix\scripts\global-session-start-launcher.py"
    $PluginSource = Join-Path $TmpDir "$ArchivePrefix\packages\opencode-plugin\sybermem.ts"
    $CoreSource = Join-Path $TmpDir "$ArchivePrefix\packages\core"
    $CliSource = Join-Path $TmpDir "$ArchivePrefix\packages\cli"
    $CodexHookSource = Join-Path $TmpDir "$ArchivePrefix\.codex\hooks\user_prompt.py"
    $CodexSessionHookSource = Join-Path $TmpDir "$ArchivePrefix\.codex\hooks\session_start.py"
    $CodexSessionEndHookSource = Join-Path $TmpDir "$ArchivePrefix\.codex\hooks\session_end.py"
    $CodexStopHookSource = Join-Path $TmpDir "$ArchivePrefix\.codex\hooks\stop.py"
$CodexPostCompactHookSource = Join-Path $TmpDir "$ArchivePrefix\.codex\hooks\post_compact.py"
$CodexObservabilitySource = Join-Path $TmpDir "$ArchivePrefix\.codex\hooks\_codex_observability.py"
$ManifestSource = Join-Path $TmpDir "$ArchivePrefix\scripts\managed-install.json"
$RemoverSource = Join-Path $TmpDir "$ArchivePrefix\scripts\safe-managed-remove.py"

    if (-not (Test-Path $SkillsSrc)) {
        throw "Skills not found in archive"
    }

    function Remove-ManagedDirectory {
        param([string]$Root, [string]$Target)
        & python $RemoverSource child --root $Root --name (Split-Path -Leaf $Target)
        if ($LASTEXITCODE -ne 0) { throw "Managed removal failed: $Target" }
    }

    foreach ($target in $Targets) {
        if (-not (Test-Path $target.Path)) {
            New-Item -ItemType Directory -Path $target.Path -Force | Out-Null
        }
        foreach ($retiredSkill in @("sybermem-phase-confirm", "sybermem-team-publish", "sybermem-team-summary")) {
            $retiredPath = Join-Path $target.Path $retiredSkill
            if (Test-Path $retiredPath) {
                Remove-ManagedDirectory -Root $target.Path -Target $retiredPath
            }
        }
        foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-resume", "sybermem-digest", "sybermem-phase-analyze", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest", "sybermem-habit", "sybermem-uninstall")) {
            $src = Join-Path $SkillsSrc $skill
            $dst = Join-Path $target.Path $skill
            if (Test-Path $src) {
                if (Test-Path $dst) {
                    Remove-ManagedDirectory -Root $target.Path -Target $dst
                }
                Copy-Item -Path $src -Destination $dst -Recurse -Force
                Write-Host "  [$($target.Label)] installed: /$skill"
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

    # Global launchers: only needed by the Claude Code lifecycle hooks.
    if (Test-Path (Join-Path $env:USERPROFILE ".claude")) {
        if (-not (Test-Path $LauncherDir)) {
            New-Item -ItemType Directory -Path $LauncherDir -Force | Out-Null
        }
        Copy-Item -Path $ManifestSource -Destination $ManifestPath -Force
        Copy-Item -Path $RemoverSource -Destination $RemoverPath -Force
        Copy-Item -Path $LauncherSource -Destination $LauncherPath -Force
        Write-Host "  [Claude Code] installed stop hook launcher: $LauncherPath"
        if (Test-Path $SessionLauncherSource) {
            Copy-Item -Path $SessionLauncherSource -Destination $SessionLauncherPath -Force
            Write-Host "  [Claude Code] installed session start launcher: $SessionLauncherPath"
        }
    }

    # sybermem CLI/runtime: install unconditionally. OpenCode skills (search/record/
    # using-sybermem) call the `sybermem` CLI, so gating this on ~/.claude would leave
    # OpenCode-only machines with skills that invoke a runtime that was never installed.
    if (-not (Test-Path $CliDir)) {
        New-Item -ItemType Directory -Path $CliDir -Force | Out-Null
    }
    $pipExe = Join-Path $CliVenv "Scripts\pip.exe"
    python -m venv $CliVenv
    & (Join-Path $CliVenv "Scripts\python.exe") -m pip install --upgrade pip
    & $pipExe install --upgrade --force-reinstall $CoreSource $CliSource
    # Do NOT export SYBERMEM_HOME: it used to split the user-habit store away from the
    # documented ~/.sybermem home. The launcher only locates the venv now; Core
    # resolves the canonical home so launcher and bare `sybermem` share one store.
    @'
@echo off
"%USERPROFILE%\.claude\sybermem\cli\venv\Scripts\sybermem.exe" %*
'@ | Set-Content -Path $CliWrapper -Encoding ASCII
    Write-Host "  [Global] installed sybermem CLI: $CliWrapper"

    # Installed-version marker: session-start checks this against each project's
    # .sybermem/project.yaml sybermem_version to nudge /sybermem-update when behind.
    $VersionSource = Join-Path $TmpDir "$ArchivePrefix\VERSION"
    if (Test-Path $VersionSource) {
        New-Item -ItemType Directory -Force -Path $LauncherDir | Out-Null
        Copy-Item -Path $VersionSource -Destination (Join-Path $LauncherDir "VERSION") -Force
        Write-Host "  [Global] recorded installed version marker: $(Join-Path $LauncherDir 'VERSION')"
    }


    # OpenCode: install plugin
    if (Test-Path (Join-Path $env:USERPROFILE ".config\opencode")) {
        if (-not (Test-Path $OpenCodePluginDir)) {
            New-Item -ItemType Directory -Path $OpenCodePluginDir -Force | Out-Null
        }
        if (Test-Path $PluginSource) {
            Copy-Item -Path $PluginSource -Destination (Join-Path $OpenCodePluginDir "sybermem.ts") -Force
            Write-Host "  [OpenCode] installed plugin: $OpenCodePluginDir\sybermem.ts"
        }
    }
} finally {
    Remove-Item -Path $TmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "=== Installation Complete ==="
Write-Host ""
Write-Host "Available Skills:"
Write-Host "  /sybermem-init-project  - Initialize or refresh SyberMem in the current project"
Write-Host "  /sybermem-record        - Create a record (auto-detects type)"
Write-Host "  /sybermem-summary       - Generate weekly/monthly reports"
Write-Host "  /sybermem-resume        - Build a read-only restart view for the current project"
Write-Host "  /sybermem-digest        - Create a durable phase digest from existing records"
Write-Host "  /sybermem-phase-analyze - Build or refresh the persistent phase index from project history"
Write-Host "  /using-sybermem         - Show current SyberMem status and the recommended next command"
Write-Host "  /sybermem-update        - Refresh global skills, then re-check the current project"
Write-Host "  /sybermem-search        - Search/query records by keyword, topic, phase range, date range, or record ID"
Write-Host "  /sybermem-link          - Add a forward relation between two existing records"
Write-Host "  /sybermem-theme-digest  - Create a durable topic-level digest"

Write-Host "  /sybermem-habit         - Manage user-level habit memory and reminders"
Write-Host "  /sybermem-uninstall     - Safely choose project-level or global uninstall"
Write-Host ""
# Honest PATH guidance: the wrapper lives in $CliDir, not on PATH by default on
# Windows. We do NOT modify persistent PATH automatically; detect and guide.
$sybermemOnPath = ($env:PATH -split ';' | Where-Object { $_.TrimEnd('\') -ieq $CliDir.TrimEnd('\') }).Count -gt 0
if ($sybermemOnPath) {
    Write-Host "sybermem CLI is installed and on PATH. You can now run: sybermem project init --register"
} else {
    Write-Host "sybermem CLI is installed at: $CliWrapper"
    Write-Host "To run it as ``sybermem`` from anywhere, add this directory to your PATH:"
    Write-Host "  $CliDir"
    Write-Host "  e.g. setx PATH `"$CliDir;`$env:PATH`"  (opens a new shell to take effect)"
    Write-Host "Or run it by full path: & `"$CliWrapper`" project init --register"
}
Write-Host ""
Write-Host "Next: open your project and run /sybermem-update"
Write-Host "If you only want the local project refresh check, run /sybermem-init-project"
Write-Host ""
Write-Host "Note: updating global skills does not automatically refresh project managed files; run /sybermem-update in the project (it removes legacy AGENTS.md / CLAUDE.md protocol blocks)"
Write-Host "Stop hook subdirectory compatibility is now provided by the global launcher at ~/.claude/sybermem/launch_record_change_on_stop.py"
