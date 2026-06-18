# OpenCode Tool Mapping

- Resolve project root → use the OpenCode plugin root-resolution logic in `packages/opencode-plugin/sybermem.ts`
- Startup diagnostics → `session.created`
- Change detection → `session.idle`
- Compaction context → `experimental.session.compacting`
- Diagnose SyberMem state → `/sybermem:using-sybermem`
