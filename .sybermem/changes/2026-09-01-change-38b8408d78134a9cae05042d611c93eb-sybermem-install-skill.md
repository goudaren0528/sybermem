---
type: change
record_id: change-38b8408d78134a9cae05042d611c93eb
date: 2026-09-01
title: 新增 sybermem-install 一键安装 skill（对话内完整安装 + 三宿主验证 + CLI 优先 init）
status: completed
source: docs/prd/sybermem-install-skill.md
key_conclusion: 新增 sybermem-install skill，让新用户在 agent 对话里触发即可完成 SyberMem 完整安装——它作为薄编排层运行官方远程安装脚本落盘全部本体，再验证三宿主+CLI 就绪并 CLI 优先初始化项目；因为脚本新落盘的 skill 当前会话不热加载，项目 init 必须走 CLI（sybermem project refresh）而非 /sybermem-init-project skill
topics: [installation, skills, onboarding]
author: sisyphus
related_files: [packages/claude-skills/sybermem-install/SKILL.md, docs/prd/sybermem-install-skill.md]
---

## Change Content

新增 skill `packages/claude-skills/sybermem-install/SKILL.md`，作为面向全新机器的首次安装入口。假设用户机器上仅有这一个 skill（无 CLI、无其它 skills、无 plugin、无 hooks），但允许编排远程脚本。同时产出配套 PRD `docs/prd/sybermem-install-skill.md`。

skill 的 7 步 Flow：
1. 环境探测（host/OS/shell + python 可用性 + 是否已装）
2. 按 OS/shell 选择官方远程安装命令（Windows cmd/OpenCode → install-remote.py；PowerShell → .ps1；Unix → .sh）
3. 说明并执行远程脚本（下载→解压→落盘全部本体，不重实现）
4. 解析输出，以退出码 0 + `=== Installation Complete ===` banner 为权威完成信号（Python 路径打 `updated:`，shell/PS 打 `installed:`）
5. 三宿主 + 共享 CLI 就绪验证（Claude/OpenCode/Codex 逐一判定，含 managed-install.json、safe-managed-remove.py、5 个 Codex hooks + _codex_observability.py）
6. CLI 优先项目初始化：`sybermem project refresh --format json`；拆分回退——CLI 本身未就绪=部分安装失败，CLI 就绪但本项目 refresh 失败=全局成功仅 init 延后到下一会话
7. 输出安装摘要（版本 + 逐宿主就绪 + 项目 init 结果 + 下一步）

## Reason for Change

此前新用户首次安装 SyberMem 的唯一入口是终端一行命令（curl|bash / irm|iex / python -c），对"在 agent 对话里工作"的用户是一次上下文断裂。现有 `sybermem-update` 只覆盖已安装用户的刷新，不覆盖全新机器首次安装。需要一个可在对话里触发、由 agent 引导完成完整安装的 skill。

关键约束（决定设计）：安装脚本新落盘的 skill 通常不被当前会话热加载，所以项目初始化必须 CLI 优先（子进程装完即用），`/sybermem-init-project` 仅作下一会话回退——这与 update 的 CLI 优先模式一致。

## Impact Scope

- 新增：`packages/claude-skills/sybermem-install/SKILL.md`（分发源）、`docs/prd/sybermem-install-skill.md`（PRD）。
- 不改动任何现有脚本或 skill。
- 明确决策：新 skill **不进** 安装脚本的 `SKILLS` 清单，也不进 `managed-install.json`。经代码核实（`scripts/safe-managed-remove.py` 只按清单精确名删除）：不进清单 = 重装/更新不分发它、卸载不删它，安全共存；代价是它的分发由外部负责（符合非目标）。
- 老用户路径不变：一行命令与 `sybermem-update` 照常可用。
- 本次不涉及数据迁移：未引入持久数据结构、不改记忆格式、不碰数据库/索引。

## Implementation

薄编排层：skill 不重实现安装步骤，而是运行官方远程脚本，其最终调用与 `_install_common.install_from_checkout` 一致落盘 skills×3宿主、Codex hooks+hooks.json、Claude launchers、CLI venv、OpenCode plugin、VERSION。

经 oracle review（9 条问题全部修复）：修正 CLI 失败误报成功的 blocker（拆分部分失败/仅 init 延后两种情况）；就绪表补齐 Oracle 指出的实际落盘文件；修正"host not present skipped"逻辑（安装器自建目录，目录存在≠宿主原本在）；Step 4 改为以退出码+banner 为权威信号并区分 installed/updated 措辞；补 cmd.exe 命令示例；加不进清单的边界说明；删除脚本不存在的 `安装完成` 措辞。

## Test Verification

隔离沙箱（临时 HOME + 覆写 Path.home()）真跑 `install_from_checkout`，验证：
- 落盘 exit 0，`INSTALL_OK`。
- Step 5 就绪表 100% 准确——列出的每个路径（Claude 6 项含 managed-install.json/safe-managed-remove.py/VERSION、OpenCode skills+plugin、Codex skills+5 hooks+_codex_observability.py+hooks.json、CLI launcher）全部真实落盘 `[OK]`。
- CLI 就绪门：`sybermem.cmd project refresh --help` 退出码 0，帮助正常输出。
- Codex `hooks.json` 5 事件（UserPromptSubmit/SessionStart/SessionEnd/Stop/PostCompact）各含 sybermem managed handler。
- 异常流：坏 URL 下载 → HTTPError 404 + 退出码非零，证明 Step 4 失败判定有真实依据。
- 沙箱测试后已清理，未污染真实环境。

## Notes

PRD 遗留 4 项待确认：Q1（清理逻辑是否误删清单外 skill）已在本次实现前用代码核实关闭=安全；Q2（分发方式）、Q3（是否保留手动一行命令兜底文案，当前设计保留）、Q4（远程仓库坐标是否正式源）仍待相关负责人确认，均不阻塞本 skill 落地。
