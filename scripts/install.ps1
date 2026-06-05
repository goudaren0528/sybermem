# SyberMem - 安装脚本 (Windows)
# 将 skills 复制到 Claude Code 和 OpenCode 用户级目录

$ErrorActionPreference = "Stop"
$AdrPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillSource = Join-Path $AdrPath "packages\claude-skills"
$LegacyLocalSkills = Join-Path $AdrPath ".claude\skills"

$Targets = @(
    @{ Path = Join-Path $env:USERPROFILE ".claude\skills"; Label = "Claude Code" }
    @{ Path = Join-Path $env:USERPROFILE ".config\opencode\skills"; Label = "OpenCode" }
)

Write-Host "=== SyberMem 安装 ==="

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
    foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-update")) {
        $src = Join-Path $SkillSource $skill
        $dst = Join-Path $target.Path $skill
        if (Test-Path $src) {
            if (Test-Path $dst) {
                Remove-Item -Path $dst -Recurse -Force -Confirm:$false
            }
            Copy-Item -Path $src -Destination $dst -Recurse -Force
            Write-Host "  [$($target.Label)] 已安装: /$skill"
        }
    }
}

Write-Host ""
Write-Host "=== 安装完成 ==="
Write-Host ""
Write-Host "可用 Skills："
Write-Host "  /sybermem-init-project  — 初始化或刷新当前项目的 SyberMem 配置"
Write-Host "  /sybermem-record        — 创建记录（自动判断类型）"
Write-Host "  /sybermem-summary       — 基于现有记录生成周报/月报"
Write-Host "  /sybermem-digest        — 基于现有记录沉淀阶段摘要"
Write-Host "  /sybermem-update        — 更新全局 Skills 并重新检查当前项目"
Write-Host ""
Write-Host "下一步：进入你的项目目录后执行 /sybermem-update"
Write-Host "如果你只想初始化或刷新当前项目，可执行 /sybermem-init-project"
Write-Host ""
Write-Host "注意：更新全局 Skills 不会自动刷新项目里的 AGENTS.md / CLAUDE.md；请在项目内运行 /sybermem-update 或 /sybermem-init-project"

if ((Test-Path (Join-Path $LegacyLocalSkills "sybermem-init-project")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-record")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-summary")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-update"))) {
    Write-Host ""
    Write-Host "迁移提示：当前仓库仍存在旧的项目级 SyberMem skills 副本 (.claude/skills/sybermem-*)。"
    Write-Host "这些副本会和全局 skills 重复显示；确认已切换到全局安装模式后，可以安全删除它们。"
}
