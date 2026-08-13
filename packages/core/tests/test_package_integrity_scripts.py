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


def test_package_integrity_checks_codex_phase_one_point_five_distribution() -> None:
    # Given: Codex Phase 1.5 installs skills plus a bounded UserPromptSubmit reminder hook
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
    assert callable(checker["check_codex_phase_one_point_five_discoverability"])
    assert Path("CONTRIBUTING.md") in checker["UNSUPPORTED_CLAIM_DOCS"]
    assert Path("CHANGELOG.md") in checker["UNSUPPORTED_CLAIM_DOCS"]
    assert Path("docs/feature_map.md") in checker["UNSUPPORTED_CLAIM_DOCS"]


def test_package_integrity_calls_dedicated_codex_phase_one_point_five_guards_from_main() -> None:
    # Given: Codex Phase 1.5 has dedicated integrity guards for install wiring and honest claims
    script = CHECK_SCRIPT.read_text(encoding="utf-8")

    # When / Then: main() invokes both Codex-specific guards as part of package verification
    assert "def check_codex_user_prompt_hook_install_wiring(root: Path) -> None:" in script
    assert "check_codex_user_prompt_hook_install_wiring(root)" in script
    assert "def check_codex_phase_one_point_five_discoverability(root: Path) -> None:" in script
    assert "check_codex_phase_one_point_five_discoverability(root)" in script


def test_codex_phase_one_installers_include_user_skill_targets() -> None:
    # Given: Codex Phase 1 installs the canonical skills into the user-level Codex skill path
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


def test_codex_install_documents_manual_project_context_workflow() -> None:
    # Given: Codex project context remains manual even though bounded habit reminders use UserPromptSubmit
    install_doc = (ROOT / ".codex" / "INSTALL.md").read_text(encoding="utf-8")

    # When / Then: the docs expose the shared context helper while preserving the unsupported boundary
    assert "sybermem context prompt --query" in install_doc
    assert "manual" in install_doc.lower()
    assert "Codex support does not add broad Codex runtime automation" in install_doc
    assert "hidden auto-resume" in install_doc
    assert "background automation" in install_doc
    assert "prompt-time injection" in install_doc
    assert ".codex/config.toml" in install_doc


def test_codex_user_prompt_hook_source_stays_habit_only() -> None:
    # Given: Codex support uses one bounded user prompt hook for habit reminders only
    hook_source = (ROOT / ".codex" / "hooks" / "user_prompt.py").read_text(encoding="utf-8")

    # When / Then: the source keeps the documented Codex hook contract and avoids project recall automation
    assert "UserPromptSubmit" in hook_source
    assert "hookSpecificOutput" in hook_source
    assert "additionalContext" in hook_source
    assert '"context"' in hook_source
    assert '"habit"' in hook_source
    assert "--delivery" in hook_source
    assert "prompt-time" in hook_source
    assert "context recall" not in hook_source
    assert "project recall" not in hook_source.lower()
    assert "auto-resume" not in hook_source.lower()


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
    ]
    assert callable(checker["check_skill_cli_resolution_guidance"])


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


def test_opencode_plugin_injects_user_habits_only_during_compaction() -> None:
    # Given: OpenCode support must stay inside documented compaction behavior
    plugin = (ROOT / "packages" / "opencode-plugin" / "sybermem.ts").read_text(encoding="utf-8")

    # When / Then: compaction keeps the inject route, and prompt-time support must not bypass it with a direct remind CLI call
    assert "experimental.session.compacting" in plugin
    assert 'sybermemText($, root, ["habit", "inject", "--context", habitContext, "--format", "markdown"])' in plugin
    assert "compaction planning review implementation coding documentation" in plugin
    assert "sybermem habit remind" not in plugin


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
    assert "per-prompt additionalContext" in guarded_fragments
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
