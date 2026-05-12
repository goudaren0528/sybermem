# ADR Record System - Remote Install (no clone needed)
# Usage: irm https://raw.githubusercontent.com/goudaren0528/sybermem/main/scripts/install-remote.ps1 | iex

$ErrorActionPreference = "Stop"

$Repo = "goudaren0528/sybermem"
$Branch = "main"
$ZipUrl = "https://github.com/$Repo/archive/$Branch.zip"
$ArchivePrefix = "sybermem-$Branch"

$Targets = @(
    @{ Path = Join-Path $env:USERPROFILE ".claude\skills"; Label = "Claude Code" }
    @{ Path = Join-Path $env:USERPROFILE ".config\opencode\skills"; Label = "OpenCode" }
)

Write-Host "=== ADR Record System - Remote Install ==="
Write-Host ""

$TmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("adr-install-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null

try {
    Write-Host "Downloading from GitHub..."
    $ZipFile = Join-Path $TmpDir "repo.zip"
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipFile -UseBasicParsing

    Expand-Archive -Path $ZipFile -DestinationPath $TmpDir -Force

    $SkillsSrc = Join-Path $TmpDir "$ArchivePrefix\.claude\skills"

    if (-not (Test-Path $SkillsSrc)) {
        throw "Skills not found in archive"
    }

    foreach ($target in $Targets) {
        if (-not (Test-Path $target.Path)) {
            New-Item -ItemType Directory -Path $target.Path -Force | Out-Null
        }
        foreach ($skill in @("init-project", "record", "summary")) {
            $src = Join-Path $SkillsSrc $skill
            $dst = Join-Path $target.Path $skill
            if (Test-Path $src) {
                Copy-Item -Path $src -Destination $dst -Recurse -Force
                Write-Host "  [$($target.Label)] installed: /$skill"
            }
        }
    }
} finally {
    Remove-Item -Path $TmpDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "=== Installation Complete ==="
Write-Host ""
Write-Host "Available Skills:"
Write-Host "  /init-project  — Initialize ADR system"
Write-Host "  /record        — Create a record (auto-detects type)"
Write-Host "  /summary       — Generate weekly/monthly report"
Write-Host ""
Write-Host "Next: run /init-project in your project directory"
