# SyberMem - Remote Install (no clone needed)
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
        foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-update")) {
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
Write-Host "  /sybermem-update        — Refresh global skills, then re-check the current project"
Write-Host ""
Write-Host "Next: open your project and run /sybermem-update"
Write-Host "If you only want the local project refresh check, run /sybermem-init-project"
Write-Host ""
Write-Host "Note: updating global skills does not automatically refresh project AGENTS.md / CLAUDE.md files"
