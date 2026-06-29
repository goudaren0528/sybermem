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
$OpenCodePluginDir = Join-Path $env:USERPROFILE ".config\opencode\plugins"

$Targets = @(
    @{ Path = Join-Path $env:USERPROFILE ".claude\skills"; Label = "Claude Code" }
    @{ Path = Join-Path $env:USERPROFILE ".config\opencode\skills"; Label = "OpenCode" }
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

    if (-not (Test-Path $SkillsSrc)) {
        throw "Skills not found in archive"
    }

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
        foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest")) {
            $src = Join-Path $SkillsSrc $skill
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
        if (Test-Path $SessionLauncherSource) {
            Copy-Item -Path $SessionLauncherSource -Destination $SessionLauncherPath -Force
            Write-Host "  [Claude Code] installed session start launcher: $SessionLauncherPath"
        }
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
Write-Host "  /sybermem-init-project  — Initialize or refresh SyberMem in the current project"
Write-Host "  /sybermem-record        — Create a record (auto-detects type)"
Write-Host "  /sybermem-summary       — Generate weekly/monthly reports"
Write-Host "  /sybermem-digest        — Create a durable phase digest from existing records"
Write-Host "  /sybermem-phase-analyze — Build or refresh the persistent phase index from project history"
Write-Host "  /sybermem-phase-confirm — Confirm or adjust candidate phases in the phase index"
Write-Host "  /using-sybermem         — Show current SyberMem status and the recommended next command"
Write-Host "  /sybermem-update        — Refresh global skills, then re-check the current project"
Write-Host "  /sybermem-search        — Search/query records by keyword, topic, phase range, date range, or record ID"
Write-Host "  /sybermem-link          — Add a forward relation between two existing records (implements / fixes / related / superseded-by)"
Write-Host "  /sybermem-theme-digest  — Create a durable topic-level digest that compresses one theme across multiple related phases or records"
Write-Host ""
Write-Host "Next: open your project and run /sybermem-update"
Write-Host "If you only want the local project refresh check, run /sybermem-init-project"
Write-Host ""
Write-Host "Note: updating global skills does not automatically refresh project AGENTS.md / CLAUDE.md files"
Write-Host "Stop hook subdirectory compatibility is now provided by the global launcher at ~/.claude/sybermem/launch_record_change_on_stop.py"
