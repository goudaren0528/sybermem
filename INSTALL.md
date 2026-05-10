# Sybermem 安装指南

## 安装步骤

### 1. Fork 本仓库

在 GitHub 上 Fork sybermem 仓库到你的账户。

### 2. Clone 到本地

```bash
git clone https://github.com/YOUR_USERNAME/sybermem.git
cd sybermem
```

### 3. 运行安装脚本

```bash
./scripts/install.sh
```

安装脚本会执行以下操作：

1. **合入 `~/.claude/CLAUDE.md`**
   - 保留原有内容
   - 在末尾追加 sybermem 配置
   - 添加分隔标记区分用户内容和 sybermem 内容

2. **合入 `~/.claude/settings.json`**
   - 保留原有配置
   - 追加 sybermem 相关配置
   - 添加注释标记

3. **复制 Skills 到用户级目录**
   - 将 skills 目录下的 Skills 复制到 `~/.claude/skills/`

### 4. 配置开发者层

编辑以下文件，填入你的个人偏好：

- `developer/preferences.md` - 编码风格、工具偏好等
- `developer/values.md` - 开发价值观、优先级偏好等

示例：

```markdown
# developer/preferences.md

## 编码风格
- 使用 2 空格缩进
- 变量命名使用 camelCase
- 优先使用 const 而非 let

## 工具偏好
- 包管理器：pnpm
- 测试框架：Vitest
- CI/CD：GitHub Actions
```

### 5. 在项目中使用

在新项目中初始化记忆系统：

```
/init-project
```

为已有项目适配记忆系统：

```
/adapt-project
```

## 更新

更新 sybermem 到最新版本：

```bash
cd sybermem
git pull origin main
./scripts/update.sh
```

更新脚本会：
1. 拉取最新代码
2. 更新用户级注入内容（保留用户原有内容）
3. 更新 Skills

## 非侵入性保证

sybermem 保证不破坏用户原有内容：

### 合入已有文件

当用户已有 `~/.claude/CLAUDE.md` 时，sybermem 采用**追加 + 分隔标记**的方式：

```markdown
# 用户原有内容（完整保留）
...用户自己的配置...

---

<!--
  ╔═══════════════════════════════════════════════════════════╗
  ║  Sybermem 记忆系统注入（以下内容由 sybermem 管理）        ║
  ║  请勿手动修改此部分，运行 `sybermem update` 可更新        ║
  ╚═══════════════════════════════════════════════════════════╝
-->

# Sybermem 记忆系统
...
```

### 项目层独立目录

项目层使用独立的 `.sybermem/` 目录：
- 不修改项目原有文件
- 不影响项目结构
- 可以安全删除而不影响项目

### 用户内容完整保留

所有更新操作只替换 sybermem 标记区域，用户原有内容始终保留。

## 手动安装（可选）

如果需要手动安装，请执行以下步骤：

### 手动合入 CLAUDE.md

1. 打开 `~/.claude/CLAUDE.md`（如不存在则创建）
2. 在文件末尾添加分隔标记
3. 追加 `sybermem/developer/preferences.md` 和 `sybermem/developer/values.md` 内容
4. 追加 `sybermem/team/conventions.md` 和 `sybermem/team/team-values.md` 内容

### 手动合入 settings.json

1. 打开 `~/.claude/settings.json`（如不存在则创建）
2. 添加 sybermem 配置项：

```json
{
  "sybermem": {
    "path": "/path/to/your/sybermem",
    "version": "2.0.0"
  }
}
```

### 手动复制 Skills

```bash
cp -r sybermem/skills/* ~/.claude/skills/
```

## 团队协作

团队成员可以通过 PR 同步团队层内容：

1. 在 `team/` 目录下添加或修改文件
2. 创建 PR 提交到主仓库
3. 团队成员 review 后合并
4. 其他成员运行 `./scripts/update.sh` 获取更新

团队层包含：
- `team/conventions.md` - 团队编码约定
- `team/team-values.md` - 团队价值观
- `team/shared-experiences/` - 共享经验积累

## 下一步

安装完成后：

1. 阅读 [设计文档](docs/superpowers/specs/2026-05-09-sybermem-design.md) 了解系统架构
2. 在你的项目中运行 `/init-project` 或 `/adapt-project`
3. 开始积累项目记忆