# ADR 记录系统 - 更新脚本 (Windows)
# 同步最新 skills 到 Claude Code 和 OpenCode 用户级目录

$ErrorActionPreference = "Stop"
$AdrPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillSource = Join-Path $AdrPath ".claude\skills"

$Targets = @(
    @{ Path = Join-Path $env:USERPROFILE ".claude\skills"; Label = "Claude Code" }
    @{ Path = Join-Path $env:USERPROFILE ".config\opencode\skills"; Label = "OpenCode" }
)

Write-Host "=== ADR 记录系统更新 ==="

foreach ($target in $Targets) {
    if (-not (Test-Path $target.Path)) {
        New-Item -ItemType Directory -Path $target.Path -Force | Out-Null
    }
    foreach ($skill in @("init-project", "record", "summary")) {
        $src = Join-Path $SkillSource $skill
        $dst = Join-Path $target.Path $skill
        if (Test-Path $src) {
            if (Test-Path $dst) {
                Remove-Item -Path $dst -Recurse -Force -Confirm:$false
            }
            Copy-Item -Path $src -Destination $dst -Recurse -Force
            Write-Host "  [$($target.Label)] 已更新: /$skill"
        }
    }
}

Write-Host ""
Write-Host "=== 更新完成 ==="
