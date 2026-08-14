from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CHECK_SCRIPT = ROOT / "scripts" / "check-plugin-package.py"


def test_package_integrity_checks_all_runtime_refresh_scripts() -> None:
    # Given: package integrity checks are the distribution contract for runtime refresh wiring
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: both local and remote install/update scripts are covered by the runtime refresh check
    assert checker["RUNTIME_REFRESH_SCRIPTS"] == [
        Path("scripts/install.sh"),
        Path("scripts/install.ps1"),
        Path("scripts/install-remote.sh"),
        Path("scripts/install-remote.ps1"),
        Path("scripts/update.sh"),
        Path("scripts/update.ps1"),
    ]


def test_package_integrity_checks_codex_runtime_distribution() -> None:
    # Given: Codex installs skills plus bounded managed lifecycle hooks
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: the integrity checker tracks Codex skill scripts, hook scripts, public docs, and metadata honesty
    assert checker["CODEX_SKILL_SCRIPTS"] == [
        Path("scripts/install.sh"),
        Path("scripts/install.ps1"),
        Path("scripts/install-remote.sh"),
        Path("scripts/install-remote.ps1"),
        Path("scripts/update.sh"),
        Path("scripts/update.ps1"),
    ]
    assert checker["CODEX_HOOK_INSTALL_SCRIPTS"] == checker["CODEX_SKILL_SCRIPTS"]
    assert Path(".codex/INSTALL.md") in checker["PUBLIC_DOCS"]
    assert Path("docs/feature_map.md") in checker["PUBLIC_DOCS"]
    assert callable(checker["check_codex_skill_install_wiring"])
    assert callable(checker["check_codex_user_prompt_hook_install_wiring"])
    assert callable(checker["check_codex_metadata_honesty"])
    assert callable(checker["check_codex_runtime_discoverability"])
    assert Path("CONTRIBUTING.md") in checker["UNSUPPORTED_CLAIM_DOCS"]
    assert Path("CHANGELOG.md") in checker["UNSUPPORTED_CLAIM_DOCS"]
    assert Path("docs/feature_map.md") in checker["UNSUPPORTED_CLAIM_DOCS"]


def test_package_integrity_calls_dedicated_codex_runtime_guards_from_main() -> None:
    # Given: Codex runtime support has dedicated integrity guards for install wiring and honest claims
    script = CHECK_SCRIPT.read_text(encoding="utf-8")

    # When / Then: main() invokes both Codex-specific guards as part of package verification
    assert "def check_codex_user_prompt_hook_install_wiring(root: Path) -> None:" in script
    assert "check_codex_user_prompt_hook_install_wiring(root)" in script
    assert "def check_codex_runtime_discoverability(root: Path) -> None:" in script
    assert "check_codex_runtime_discoverability(root)" in script


def test_codex_installers_include_user_skill_targets() -> None:
    # Given: Codex installs the canonical skills into the user-level Codex skill path
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: every install/update script names the Codex target path and label
    for relative_path in checker["CODEX_SKILL_SCRIPTS"]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        target_fragment = ".agents/skills" if relative_path.suffix == ".sh" else ".agents\\skills"
        assert target_fragment in text
        assert "Codex" in text


def test_codex_plugin_metadata_keeps_supported_scope_narrow() -> None:
    # Given: Codex metadata must honestly describe skills support without broad automation claims
    metadata = (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")

    # When / Then: it mentions Codex skills without claiming unsupported automation
    assert "Codex" in metadata
    assert "skills" in metadata
    assert "codex" in metadata
    assert "agents" in metadata
    assert "hook" not in metadata.lower()
    assert "runtime" not in metadata.lower()
    assert "prompt-time" not in metadata.lower()


def test_codex_install_documents_hook_backed_project_context_workflow() -> None:
    # Given: Codex project context is bounded to supported lifecycle hooks
    install_doc = (ROOT / ".codex" / "INSTALL.md").read_text(encoding="utf-8")

    # When / Then: the docs expose the shared context helper while preserving the unsupported boundary
    assert "sybermem context prompt --query" in install_doc
    assert "SessionStart" in install_doc
    assert "UserPromptSubmit" in install_doc
    assert "Codex support does not add broad Codex runtime automation" in install_doc
    assert "hidden auto-resume" in install_doc
    assert "background automation" in install_doc
    assert "direct compaction prompt injection" in install_doc
    assert ".codex/config.toml" in install_doc


def test_codex_user_prompt_hook_source_captures_prompt_context() -> None:
    # Given: Codex support uses one bounded user prompt hook for recall, habits, and record intent
    hook_source = (ROOT / ".codex" / "hooks" / "user_prompt.py").read_text(encoding="utf-8")

    # When / Then: the source keeps the documented Codex hook contract and bounded prompt context routes
    assert "UserPromptSubmit" in hook_source
    assert "hookSpecificOutput" in hook_source
    assert "additionalContext" in hook_source
    assert '"context"' in hook_source
    assert '"recall"' in hook_source
    assert '"habit"' in hook_source
    assert "--delivery" in hook_source
    assert "prompt-time" in hook_source
    assert "classify_record_intent" in hook_source
    assert ".record-intent.json" in hook_source
    assert "auto-resume" not in hook_source.lower()


def test_codex_session_start_hook_source_exists() -> None:
    # Given: Codex SessionStart is the supported seam for startup project context
    hook_source = (ROOT / ".codex" / "hooks" / "session_start.py").read_text(encoding="utf-8")

    # When / Then: the source emits SessionStart additionalContext from shared session context CLI
    assert "SessionStart" in hook_source
    assert "hookSpecificOutput" in hook_source
    assert "additionalContext" in hook_source
    assert '"context"' in hook_source
    assert '"session"' in hook_source
    assert "auto-resume" not in hook_source.lower()


def test_codex_stop_and_post_compact_hook_sources_exist() -> None:
    # Given: Codex uses supported Stop/PostCompact events for bounded lifecycle follow-up
    stop_source = (ROOT / ".codex" / "hooks" / "stop.py").read_text(encoding="utf-8")
    post_compact_source = (ROOT / ".codex" / "hooks" / "post_compact.py").read_text(encoding="utf-8")

    # When / Then: Stop can nudge once, while PostCompact only marks later re-seed
    assert "Stop" in stop_source
    assert "stop_hook_active" in stop_source
    assert '"decision"' in stop_source
    assert '"block"' in stop_source
    assert "/sybermem-record" in stop_source
    assert ".nudge-state.json" in stop_source
    assert "PostCompact" in post_compact_source
    assert ".codex-compact-marker.json" in post_compact_source
    assert "additionalContext" not in post_compact_source


def test_package_integrity_checks_cli_using_skills_with_fixed_launcher_guidance() -> None:
    # Given: CLI-using skills must preserve fixed-launcher guidance for deterministic resolution
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: the integrity script tracks the required CLI-using skills and guidance checker
    assert checker["CLI_USING_SKILLS"] == [
        Path("packages/claude-skills/using-sybermem/SKILL.md"),
        Path("packages/claude-skills/sybermem-record/SKILL.md"),
        Path("packages/claude-skills/sybermem-search/SKILL.md"),
        Path("packages/claude-skills/sybermem-habit/SKILL.md"),
        Path("packages/claude-skills/sybermem-team-publish/SKILL.md"),
        Path("packages/claude-skills/sybermem-team-summary/SKILL.md"),
        Path("packages/claude-skills/sybermem-init-project/SKILL.md"),
        Path("packages/claude-skills/sybermem-update/SKILL.md"),
        Path("packages/claude-skills/sybermem-summary/SKILL.md"),
        Path("packages/claude-skills/sybermem-phase-analyze/SKILL.md"),
    ]
    assert callable(checker["check_skill_cli_resolution_guidance"])
    assert callable(checker["check_project_refresh_contract"])
    assert callable(checker["check_project_memory_stats_contract"])
    assert callable(checker["check_project_phase_contract"])


def test_package_integrity_guards_cli_first_phase_contract() -> None:
    # Given: phase analysis must persist deterministically via the CLI, not a hand-written step
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: docs, skill contract, and CLI parser all carry the phase commands
    assert callable(checker["check_project_phase_contract"])
    for relative_path in [
        Path("README.md"),
        Path("README.en.md"),
        Path("docs/feature_map.md"),
        Path("packages/claude-skills/sybermem-phase-analyze/SKILL.md"),
        Path("skills/sybermem-phase-analyze/SKILL.md"),
    ]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "sybermem project phase analyze" in text

    for relative_path in [
        Path("packages/claude-skills/sybermem-phase-analyze/SKILL.md"),
        Path("skills/sybermem-phase-analyze/SKILL.md"),
    ]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "sybermem project phase confirm --from-json" in text
        assert "missing, broken, or emits invalid JSON" in text

    cli_main = (ROOT / "packages" / "cli" / "sybermem_cli" / "main.py").read_text(encoding="utf-8")
    assert "cmd_project_phase_analyze" in cli_main
    assert "cmd_project_phase_confirm" in cli_main
    assert 'project_sub.add_parser("phase")' in cli_main


def test_cli_using_skills_include_fixed_launcher_contract_fragments() -> None:
    # Given: fixed-launcher guidance is a machine-read contract for CLI-using skills
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: each tracked skill keeps the exact launcher fragments the integrity check enforces
    for relative_path in checker["CLI_USING_SKILLS"]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert ".claude\\sybermem\\cli\\sybermem.cmd" in text
        assert ".claude/sybermem/cli/sybermem" in text
        assert "Do not modify persistent PATH automatically" in text
        assert "$SyberMemCli" in text
        assert "SYBERMEM_CLI" in text


def test_package_integrity_guards_cli_first_project_refresh_contract() -> None:
    # Given: /sybermem-update must stay fast and deterministic when the CLI is healthy
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: docs, skill contract, and CLI parser all carry the project refresh command
    assert callable(checker["check_project_refresh_contract"])
    for relative_path in [
        Path("README.md"),
        Path("README.en.md"),
        Path("docs/feature_map.md"),
        Path(".opencode/INSTALL.md"),
        Path(".codex/INSTALL.md"),
        Path("packages/claude-skills/sybermem-update/SKILL.md"),
        Path("skills/sybermem-update/SKILL.md"),
    ]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "sybermem project refresh --format json" in text

    cli_main = (ROOT / "packages" / "cli" / "sybermem_cli" / "main.py").read_text(encoding="utf-8")
    assert "cmd_project_refresh" in cli_main
    assert 'project_sub.add_parser("refresh")' in cli_main


def test_package_integrity_guards_cli_first_project_memory_stats_contract() -> None:
    # Given: /sybermem-summary consumes deterministic CLI memory and recall stats when available
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: docs, skill contract, and CLI parser all carry the memory-stats command
    assert callable(checker["check_project_memory_stats_contract"])
    for relative_path in [
        Path("README.md"),
        Path("README.en.md"),
        Path("docs/feature_map.md"),
        Path("packages/cli/README.md"),
        Path("packages/claude-skills/sybermem-summary/SKILL.md"),
        Path("skills/sybermem-summary/SKILL.md"),
    ]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "sybermem project memory-stats" in text

    summary_skill = (ROOT / "packages" / "claude-skills" / "sybermem-summary" / "SKILL.md").read_text(encoding="utf-8")
    assert "missing, broken, or emits invalid JSON" in summary_skill
    assert 'recall.status == "no_log"' in summary_skill
    assert ".sybermem/.recall-debug.jsonl" in summary_skill
    assert "Try bare `sybermem` only as the final fallback" in summary_skill

    cli_main = (ROOT / "packages" / "cli" / "sybermem_cli" / "main.py").read_text(encoding="utf-8")
    assert "cmd_project_memory_stats" in cli_main
    assert 'project_sub.add_parser("memory-stats")' in cli_main


def test_local_install_and_update_scripts_force_refresh_core_and_cli_packages() -> None:
    # Given: local install/update scripts are supported runtime refresh entrypoints
    scripts = (
        ROOT / "scripts" / "install.sh",
        ROOT / "scripts" / "install.ps1",
        ROOT / "scripts" / "update.sh",
        ROOT / "scripts" / "update.ps1",
    )

    # When / Then: they force reinstall both Core and CLI packages just like remote installers
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        core_fragment = "packages/core" if script.suffix == ".sh" else "packages\\core"
        cli_fragment = "packages/cli" if script.suffix == ".sh" else "packages\\cli"
        assert core_fragment in text
        assert cli_fragment in text
        assert "--upgrade" in text
        assert "--force-reinstall" in text


def test_package_integrity_exposes_cli_wrapper_wiring_check() -> None:
    # Given: fixed launcher pollution is prevented by a package integrity guard
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: the guard is exported for the checker main path
    assert callable(checker["check_cli_wrapper_wiring"])


def test_distribution_scripts_install_fixed_sybermem_cli_wrappers() -> None:
    # Given: global install/update scripts own the fixed sybermem launcher body
    windows_scripts = (
        ROOT / "scripts" / "install.ps1",
        ROOT / "scripts" / "update.ps1",
        ROOT / "scripts" / "install-remote.ps1",
    )
    posix_scripts = (
        ROOT / "scripts" / "install.sh",
        ROOT / "scripts" / "update.sh",
        ROOT / "scripts" / "install-remote.sh",
    )

    # When / Then: Windows wrappers call venv\Scripts\sybermem.exe, never smoke output stubs
    for script in windows_scripts:
        text = script.read_text(encoding="utf-8")
        assert ".claude\\sybermem\\cli" in text
        assert "sybermem.cmd" in text
        assert "python -m venv $CliVenv" in text
        assert "venv\\Scripts\\sybermem.exe" in text
        assert "Set-Content -Path $CliWrapper -Encoding ASCII" in text
        assert "sys.stdout.write(" not in text
        assert "Smoke habit applies" not in text

    # When / Then: POSIX wrappers call venv/bin/sybermem, never smoke output stubs
    for script in posix_scripts:
        text = script.read_text(encoding="utf-8")
        assert ".claude/sybermem/cli" in text
        assert 'CLI_WRAPPER="$CLI_DIR/sybermem"' in text
        assert 'python -m venv "$CLI_VENV"' in text
        assert "venv/bin/sybermem" in text
        assert 'cat > "$CLI_WRAPPER"' in text
        assert "sys.stdout.write(" not in text
        assert "Smoke habit applies" not in text


def test_opencode_plugin_injects_user_habits_only_during_compaction() -> None:
    # Given: OpenCode support must stay inside documented compaction behavior
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: compaction keeps the inject route, and prompt-time support must not bypass it with a direct remind CLI call
    assert "experimental.session.compacting" in plugin
    assert 'sybermemText($, root, ["habit", "inject", "--context", habitContext, "--format", "markdown"])' in plugin
    assert "compaction planning review implementation coding documentation" in plugin
    assert "sybermem habit remind" not in plugin


def test_package_integrity_calls_recall_relevance_guard_from_main() -> None:
    # Given: the edit-aware recall relevance loop is a distribution contract
    script = CHECK_SCRIPT.read_text(encoding="utf-8")

    # When / Then: main() defines and invokes the dedicated relevance guard
    assert "def check_opencode_recall_relevance_wiring(root: Path) -> None:" in script
    assert "check_opencode_recall_relevance_wiring(root)" in script


def test_recall_relevance_wiring_guard_passes_on_repo() -> None:
    # Given: the guard function loaded from the checker
    checker = runpy.run_path(str(CHECK_SCRIPT))
    guard = checker["check_opencode_recall_relevance_wiring"]

    # When / Then: it passes against the real repo (bundle + core + cli are wired)
    guard(ROOT)


def test_opencode_plugin_source_modules_include_relevance_modules() -> None:
    # Given: new source modules must be tracked so the bundle stays reproducible
    checker = runpy.run_path(str(CHECK_SCRIPT))
    modules = checker["OPENCODE_PLUGIN_SOURCE_MODULES"]

    # When / Then: both edit-aware modules are enumerated
    assert Path("packages/opencode-plugin/src/session_activity.ts") in modules
    assert Path("packages/opencode-plugin/src/recall_outcome.ts") in modules


def test_package_integrity_exposes_unsupported_platform_claim_guard() -> None:
    # Given: OpenCode and Codex support must stay honest about unsupported runtime seams
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: the integrity script exposes a dedicated guard for claim honesty
    assert callable(checker["check_unsupported_platform_claims"])
    assert Path(".opencode/INSTALL.md") in checker["UNSUPPORTED_CLAIM_DOCS"]
    assert Path(".codex/INSTALL.md") in checker["UNSUPPORTED_CLAIM_DOCS"]
    assert Path("docs/feature_map.md") in checker["UNSUPPORTED_CLAIM_DOCS"]


def test_platform_docs_keep_unsupported_claims_in_limitation_sections() -> None:
    # Given: docs may mention unsupported seams only when clearly saying they are unsupported
    checker = runpy.run_path(str(CHECK_SCRIPT))
    guarded_fragments = checker["UNSUPPORTED_RUNTIME_CLAIMS"]

    # When / Then: current platform docs satisfy the machine-enforced honesty guard
    checker["check_unsupported_platform_claims"](ROOT)
    assert '"prompt" handler' in guarded_fragments
    assert "background automation" in guarded_fragments


def test_package_integrity_exposes_opencode_cli_resolution_check() -> None:
    # Given: package integrity checks must guard the OpenCode plugin's fixed-launcher fallback
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: the checker exports the dedicated OpenCode CLI resolution guard
    assert callable(checker["check_opencode_plugin_cli_resolution"])
    assert checker["OPENCODE_PLUGIN_UPDATE_SCRIPTS"] == [
        Path("scripts/install.sh"),
        Path("scripts/install.ps1"),
        Path("scripts/install-remote.sh"),
        Path("scripts/install-remote.ps1"),
        Path("scripts/update.sh"),
        Path("scripts/update.ps1"),
    ]


def test_package_integrity_exposes_opencode_source_bundle_and_privacy_guards() -> None:
    # Given: OpenCode ships one bundled plugin but keeps maintainable source modules
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: package integrity checks track the source split and prompt-free metadata guards
    assert checker["OPENCODE_PLUGIN_SOURCE_MODULES"] == [
        Path("packages/opencode-plugin/src/index.ts"),
        Path("packages/opencode-plugin/src/plugin.ts"),
        Path("packages/opencode-plugin/src/runtime.ts"),
        Path("packages/opencode-plugin/src/project_state.ts"),
        Path("packages/opencode-plugin/src/followup.ts"),
        Path("packages/opencode-plugin/src/state.ts"),
        Path("packages/opencode-plugin/src/prompt_context.ts"),
        Path("packages/opencode-plugin/src/compaction.ts"),
        Path("packages/opencode-plugin/src/record_intent.ts"),
        Path("packages/opencode-plugin/src/recall_debug.ts"),
        Path("packages/opencode-plugin/src/startup_context.ts"),
        Path("packages/opencode-plugin/src/recall_health_signal.ts"),
        Path("packages/opencode-plugin/src/session_activity.ts"),
        Path("packages/opencode-plugin/src/recall_outcome.ts"),
    ]
    assert callable(checker["check_opencode_plugin_source_bundle"])
    assert callable(checker["check_opencode_prompt_privacy"])
    assert "scripts/build-opencode-plugin.mjs" in CHECK_SCRIPT.read_text(encoding="utf-8")


def test_package_integrity_guards_opencode_first_turn_and_recall_health() -> None:
    # Given: OpenCode first-turn context and recall-health feedback are model-visible seams
    checker = runpy.run_path(str(CHECK_SCRIPT))
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: the bundled plugin wires first-turn startup injection and recall-health advisory
    assert callable(checker["check_opencode_memory_feedback_wiring"])
    assert "markPendingStartup" in plugin
    assert "consumePendingStartup" in plugin
    assert "buildStartupContext" in plugin
    assert "## SyberMem Startup Context" in plugin
    assert "project memory-stats --format json" in plugin
    assert "recall_health" in plugin
    assert "low_signal" in plugin


def test_opencode_plugin_uses_resolver_backed_cli_commands() -> None:
    # Given: OpenCode plugin commands must be routed through the resolver-backed launcher fallback
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: the plugin retains fixed-launcher resolution fragments and avoids old direct bare-CLI calls
    assert "resolveSybermemCommand" in plugin
    assert ".claude" in plugin
    assert "sybermem.cmd" in plugin
    assert '"sybermem", "cli", "sybermem"' in plugin
    assert "USERPROFILE" in plugin
    assert "HOME" in plugin
    assert "sybermemText" in plugin
    assert "$`sybermem digest status --format json`" not in plugin
    assert "$`sybermem next-step --format json`" not in plugin
    assert "$`sybermem habit inject --context ${habitContext} --format markdown`" not in plugin
    assert "args.join" not in plugin


def test_opencode_plugin_consumes_stale_digest_json_without_throwing() -> None:
    # Given: `sybermem digest status` exits nonzero when stale digests exist
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: the plugin must consume stdout without throwing away stale JSON
    assert "digestStatusText" in plugin
    assert ".nothrow()" in plugin


def test_opencode_plugin_reuses_manual_context_helper_for_compaction() -> None:
    # Given: OpenCode compaction is a supported lifecycle seam for carrying project memory forward
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: compaction uses the shared manual context helper through resolver-backed CLI calls
    assert "experimental.session.compacting" in plugin
    assert 'sybermemText($, root, ["context", "session", "--format", "markdown"])' in plugin
    assert "## SyberMem Manual Session Context" in plugin


def test_opencode_plugin_wires_prompt_time_recall_and_toasts() -> None:
    # Given: OpenCode per-prompt recall must use supported plugin hooks and the SDK toast API
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: the prompt capture/injection route and toast contract remain wired
    assert '"chat.message"' in plugin
    assert '"experimental.chat.system.transform"' in plugin
    assert "RECALL_STASH" in plugin
    assert "context recall" in plugin
    assert "context habit" in plugin
    assert "--delivery" in plugin
    assert "prompt-time" in plugin
    assert "## User Habit Reminder" in plugin
    assert "client.tui.showToast" in plugin
    assert "sybermem habit remind" not in plugin
    assert "injected only at supported compaction" not in plugin
    assert "undocumented per-prompt hook" not in plugin
    assert '"tui.toast.show"' not in plugin
    assert "level:" not in plugin


def test_opencode_plugin_bundle_keeps_single_file_installer_contract() -> None:
    # Given: installers still copy the generated single-file OpenCode plugin artifact
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: the artifact is generated and has no local source imports
    assert "SyberMem OpenCode Plugin (generated bundle)" in plugin
    assert "packages/opencode-plugin/src/index.ts" in plugin
    assert "from \"./src" not in plugin
    assert "from './src" not in plugin
    assert "from \"./plugin\"" not in plugin
    assert "--check" in (ROOT / "scripts" / "build-opencode-plugin.mjs").read_text(encoding="utf-8")
    for relative_path in [
        Path("scripts/install.sh"),
        Path("scripts/install.ps1"),
        Path("scripts/install-remote.sh"),
        Path("scripts/install-remote.ps1"),
        Path("scripts/update.sh"),
        Path("scripts/update.ps1"),
    ]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        source_fragment = "packages/opencode-plugin/sybermem.ts" if relative_path.suffix == ".sh" else "packages\\opencode-plugin\\sybermem.ts"
        assert source_fragment in text


def test_opencode_plugin_records_prompt_free_intent_and_recall_debug_metadata() -> None:
    # Given: OpenCode prompt-time behavior writes bounded metadata only
    record_intent = (ROOT / "packages" / "opencode-plugin" / "src" / "record_intent.ts").read_text(encoding="utf-8")
    recall_debug = (ROOT / "packages" / "opencode-plugin" / "src" / "recall_debug.ts").read_text(encoding="utf-8")
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: record intent and recall debug persist metadata, not raw prompt text
    assert ".record-intent.json" in record_intent
    assert "source: \"opencode-chat-message\"" in record_intent
    assert "phrase: \"\"" in record_intent
    assert "matched_pattern" in record_intent
    assert ".recall-debug.jsonl" in recall_debug
    assert "boundedJsonlAppend" in recall_debug
    assert "record_ids" in recall_debug
    assert "match_classes" in recall_debug
    assert "abstain" in recall_debug
    assert ".record-intent.json" in plugin
    assert ".recall-debug.jsonl" in plugin
    assert "opencode-chat-message" in plugin
    combined = f"{record_intent}\n{recall_debug}"
    assert "raw_prompt" not in combined
    assert "prompt_text" not in combined
    assert "phrase: text" not in combined


def test_active_docs_do_not_retain_stale_codex_or_opencode_platform_claims() -> None:
    # Given: contributor and changelog guidance are active release-facing docs
    active_text = "\n".join(
        (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in [Path("CONTRIBUTING.md"), Path("CHANGELOG.md")]
    )

    # When / Then: they no longer describe OpenCode/Codex as prompt-time/manual-only platforms
    assert "skills-only boundary" not in active_text
    assert "skills-only smoke path" not in active_text
    assert "no Codex hooks, prompt-time injection" not in active_text
    assert "supported compaction only" not in active_text
