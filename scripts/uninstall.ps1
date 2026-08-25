$ErrorActionPreference = "Stop"

$claudeSybermem = Join-Path $env:USERPROFILE ".claude\sybermem"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifest = Join-Path $claudeSybermem "managed-install.json"
$remover = Join-Path $claudeSybermem "safe-managed-remove.py"
if (-not (Test-Path -LiteralPath $manifest)) { $manifest = Join-Path $scriptDir "managed-install.json" }
if (-not (Test-Path -LiteralPath $remover)) { $remover = Join-Path $scriptDir "safe-managed-remove.py" }
& python $remover uninstall --home $env:USERPROFILE --manifest $manifest
if ($LASTEXITCODE -ne 0) { throw "SyberMem managed uninstall failed" }

$localBinLink = Join-Path $env:USERPROFILE ".local\bin\sybermem"
if (Test-Path -LiteralPath $localBinLink) {
    try {
        $target = (Get-Item -LiteralPath $localBinLink).Target
        if ($target -like "*\.claude\sybermem\cli\sybermem") {
            Remove-Item -LiteralPath $localBinLink -Force
        }
    } catch {
        # Windows installs do not create this link; cleanup is best-effort parity with uninstall.sh.
    }
}

Write-Host "SyberMem global uninstall complete."
Write-Host "Project histories under .sybermem/ were not removed."
