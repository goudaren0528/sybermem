# Claude Code Tool Mapping

- Resolve project root → use file-system tools and current working directory
- Run hook helper → SessionStart / Stop hooks via `hooks/hooks.json`
- Diagnose SyberMem state → `/sybermem:using-sybermem`
- Refresh project files → `/sybermem:update` or `/sybermem:init-project`
