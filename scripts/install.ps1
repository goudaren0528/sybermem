# ADR 记录系统 - 安装脚本 (Windows)
# 将 skills 复制到 Claude Code 和 OpenCode 用户级目录

$ErrorActionPreference = "Stop"
$AdrPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillSource = Join-Path $AdrPath ".claude\skills"

$Targets = @(
    @{ Path = Join-Path $env:USERPROFILE ".claude\skills"; Label = "Claude Code" }
    @{ Path = Join-Path $env:USERPROFILE ".config\opencode\skills"; Label = "OpenCode" }
)

Write-Host "=== ADR 记录系统安装 ==="

foreach ($target in $Targets) {
    if (-not (Test-Path $target.Path)) {
        New-Item -ItemType Directory -Path $target.Path -Force | Out-Null
    }
    foreach ($skill in @("init-project", "record", "summary")) {
        $src = Join-Path $SkillSource $skill
        $dst = Join-Path $target.Path $skill
        if (Test-Path $src) {
            Copy-Item -Path $src -Destination $dst -Recurse -Force
            Write-Host "  [$($target.Label)] 已安装: /$skill"
        }
    }
}

Write-Host ""
Write-Host "=== 安装完成 ==="
Write-Host ""
Write-Host "可用 Skills："
Write-Host "  /init-project  — 初始化 ADR 系统"
Write-Host "  /record        — 创建记录（自动判断类型）"
Write-Host "  /summary       — 生成周报/月报"
Write-Host ""
Write-Host "下一步：在项目目录中执行 /init-project"
