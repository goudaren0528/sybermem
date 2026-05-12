# SyberMem - 更新脚本 (Windows)
# 同步最新 skills 到 Claude Code 和 OpenCode 用户级目录

$ErrorActionPreference = "Stop"
$AdrPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillSource = Join-Path $AdrPath ".claude\skills"

$Targets = @(
    @{ Path = Join-Path $env:USERPROFILE ".claude\skills"; Label = "Claude Code" }
    @{ Path = Join-Path $env:USERPROFILE ".config\opencode\skills"; Label = "OpenCode" }
)

Write-Host "=== SyberMem 更新 ==="

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
Write-Host ""
Write-Host "下一步：进入你的项目目录后执行 /sybermem-update"
Write-Host "如果你只想检查项目本地文档是否需要刷新，可执行 /sybermem-init-project"
Write-Host ""
Write-Host "注意：更新全局 Skills 不会自动刷新项目里的 AGENTS.md / CLAUDE.md；请在项目内运行 /sybermem-update 或 /sybermem-init-project"
