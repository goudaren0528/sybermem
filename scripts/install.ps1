# SyberMem - 安装脚本 (Windows)
# 将 skills 复制到 Claude Code 和 OpenCode 用户级目录

$ErrorActionPreference = "Stop"
$AdrPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillSource = Join-Path $AdrPath "packages\claude-skills"
$LauncherDir = Join-Path $env:USERPROFILE ".claude\sybermem"
$LauncherPath = Join-Path $LauncherDir "launch_record_change_on_stop.py"
$LauncherSource = Join-Path $AdrPath "scripts\global-stop-hook-launcher.py"
$SessionLauncherSource = Join-Path $AdrPath "scripts\global-session-start-launcher.py"
$SessionLauncherPath = Join-Path $LauncherDir "launch_session_start_context.py"
$PluginSource = Join-Path $AdrPath "packages\opencode-plugin\sybermem.ts"
$OpenCodePluginDir = Join-Path $env:USERPROFILE ".config\opencode\plugins"
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
    foreach ($skill in @("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-digest", "sybermem-phase-analyze", "sybermem-phase-confirm", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest")) {
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

# Claude Code: install global stop hook launcher
if (Test-Path (Join-Path $env:USERPROFILE ".claude")) {
    if (-not (Test-Path $LauncherDir)) {
        New-Item -ItemType Directory -Path $LauncherDir -Force | Out-Null
    }
    Copy-Item -Path $LauncherSource -Destination $LauncherPath -Force
    Write-Host "  [Claude Code] 已安装 stop hook launcher: $LauncherPath"
    Copy-Item -Path $SessionLauncherSource -Destination $SessionLauncherPath -Force
    Write-Host "  [Claude Code] 已安装 session start launcher: $SessionLauncherPath"
}

# OpenCode: install plugin
if (Test-Path (Join-Path $env:USERPROFILE ".config\opencode")) {
    if (-not (Test-Path $OpenCodePluginDir)) {
        New-Item -ItemType Directory -Path $OpenCodePluginDir -Force | Out-Null
    }
    Copy-Item -Path $PluginSource -Destination (Join-Path $OpenCodePluginDir "sybermem.ts") -Force
    Write-Host "  [OpenCode] 已安装 plugin: $OpenCodePluginDir\sybermem.ts"
}

Write-Host ""
Write-Host "=== 安装完成 ==="
Write-Host ""
Write-Host "可用 Skills："
Write-Host "  /sybermem-init-project  — 初始化或刷新当前项目的 SyberMem 配置"
Write-Host "  /sybermem-record        — 创建记录（自动判断类型）"
Write-Host "  /sybermem-summary       — 基于现有记录生成周报/月报"
Write-Host "  /sybermem-digest        — 基于现有记录沉淀阶段摘要"
Write-Host "  /sybermem-phase-analyze — 从项目历史构建或刷新持久化阶段索引"
Write-Host "  /sybermem-phase-confirm — 确认或调整阶段索引中的候选阶段"
Write-Host "  /using-sybermem         — 显示当前 SyberMem 状态和建议的下一步命令"
Write-Host "  /sybermem-update        — 更新全局 Skills 并重新检查当前项目"
Write-Host "  /sybermem-search        — 按关键词、topic、phase 范围、日期范围或记录 ID 检索记录"
Write-Host "  /sybermem-link          — 在两条已有记录间建立正向关系（implements / fixes / related / superseded-by）"
Write-Host "  /sybermem-theme-digest  — 为单个 topic 创建跨多个 phase 的持久化高阶摘要"
Write-Host ""
Write-Host "下一步：进入你的项目目录后执行 /sybermem-update"
Write-Host "如果你只想初始化或刷新当前项目，可执行 /sybermem-init-project"
Write-Host ""
Write-Host "注意：更新全局 Skills 不会自动刷新项目里的 AGENTS.md / CLAUDE.md；请在项目内运行 /sybermem-update 或 /sybermem-init-project"
Write-Host "注意：stop hook 的子目录兼容现在由全局 launcher 提供：~/.claude/sybermem/launch_record_change_on_stop.py"

if ((Test-Path (Join-Path $LegacyLocalSkills "sybermem-init-project")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-record")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-summary")) -or
    (Test-Path (Join-Path $LegacyLocalSkills "sybermem-update"))) {
    Write-Host ""
    Write-Host "迁移提示：当前仓库仍存在旧的项目级 SyberMem skills 副本 (.claude/skills/sybermem-*)。"
    Write-Host "这些副本会和全局 skills 重复显示；确认已切换到全局安装模式后，可以安全删除它们。"
}
