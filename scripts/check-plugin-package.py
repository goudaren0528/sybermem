#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final


ROOT: Final = Path(os.environ.get("SYBERMEM_CHECK_ROOT", Path(__file__).resolve().parent.parent)).resolve()

DISTRIBUTION_SCRIPTS: Final = [
    Path("scripts/install.sh"),
    Path("scripts/install.ps1"),
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
    Path("scripts/uninstall.sh"),
    Path("scripts/uninstall.ps1"),
]
VISIBLE_SKILL_SCRIPTS: Final = [
    Path("scripts/install.sh"),
    Path("scripts/install.ps1"),
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
]
OPENCODE_PLUGIN_UPDATE_SCRIPTS: Final = [
    Path("scripts/install.sh"),
    Path("scripts/install.ps1"),
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
]
CODEX_SKILL_SCRIPTS: Final = [
    Path("scripts/install.sh"),
    Path("scripts/install.ps1"),
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
]
CODEX_HOOK_INSTALL_SCRIPTS: Final = [
    Path("scripts/install.sh"),
    Path("scripts/install.ps1"),
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
]
RUNTIME_REFRESH_SCRIPTS: Final = [
    Path("scripts/install.sh"),
    Path("scripts/install.ps1"),
    Path("scripts/install-remote.sh"),
    Path("scripts/install-remote.ps1"),
    Path("scripts/update.sh"),
    Path("scripts/update.ps1"),
]
NO_CACHE_ROOTS: Final = [
    Path("packages/claude-skills"),
    Path("packages/core"),
    Path("packages/cli"),
    Path("skills"),
]
PUBLIC_DOCS: Final = [
    Path("README.md"),
    Path("README.en.md"),
    Path("INSTALL.md"),
    Path("CHANGELOG.md"),
    Path("docs/feature_map.md"),
    Path("GEMINI.md"),
    Path(".codex/INSTALL.md"),
    Path(".opencode/INSTALL.md"),
]
PACKAGE_METADATA: Final = [
    Path(".claude-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
    Path(".cursor-plugin/plugin.json"),
    Path(".codex-plugin/plugin.json"),
    Path(".kimi-plugin/plugin.json"),
    Path("gemini-extension.json"),
    Path("hooks/hooks.json"),
    Path("packages/core/pyproject.toml"),
    Path("packages/cli/pyproject.toml"),
]
CLI_USING_SKILLS: Final = [
    Path("packages/claude-skills/using-sybermem/SKILL.md"),
    Path("packages/claude-skills/sybermem-record/SKILL.md"),
    Path("packages/claude-skills/sybermem-search/SKILL.md"),
    Path("packages/claude-skills/sybermem-habit/SKILL.md"),
    Path("packages/claude-skills/sybermem-team-publish/SKILL.md"),
    Path("packages/claude-skills/sybermem-team-summary/SKILL.md"),
    Path("packages/claude-skills/sybermem-init-project/SKILL.md"),
]
CODEX_HEALTH_CHECK_FILES: Final = [
    Path("packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py"),
    Path("skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py"),
]
UNSUPPORTED_CLAIM_DOCS: Final = [
    Path("CONTRIBUTING.md"),
    Path("CHANGELOG.md"),
    Path(".opencode/INSTALL.md"),
    Path(".codex/INSTALL.md"),
    Path("README.md"),
    Path("README.en.md"),
    Path("docs/feature_map.md"),
]
UNSUPPORTED_RUNTIME_CLAIMS: Final = [
    "hidden auto-resume",
    ".codex/config.toml",
    "background automation",
    '"agent"',
    '"prompt" handler',
]
LIMITATION_MARKERS: Final = [
    "unsupported",
    "不支持",
    "blocked",
    "限制",
    "does not",
    "does **not**",
    "do not",
    "not install",
    "not** install",
    "no hooks",
    "无 hooks",
    "没有",
    "不能",
]


def rel(path: Path, root: Path) -> str:
    """Return a stable repository-relative path for diagnostics."""
    return path.relative_to(root).as_posix()


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def check_json(path: Path, root: Path) -> None:
    if not path.is_file():
        fail(f"Missing file: {rel(path, root)}")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {rel(path, root)}: {exc}")


def check_hook_wiring(root: Path) -> None:
    hook_path = root / "hooks" / "user-prompt-submit"
    if not hook_path.is_file():
        fail("Missing file: hooks/user-prompt-submit")
    if hook_path.suffix:
        fail("hooks/user-prompt-submit must remain extensionless")

    hook_text = hook_path.read_text(encoding="utf-8")
    required_fragments = [
        "CLAUDE_PROJECT_DIR:-$(pwd)",
        "$root/.sybermem/hooks/user_prompt.py",
        "$root/.sybermem/hooks/task_recall.py",
        'python "$script" "$@"',
        "2>/dev/null || exit 0",
    ]
    for fragment in required_fragments:
        if fragment not in hook_text:
            fail(f"hooks/user-prompt-submit is missing required wiring: {fragment}")

    hooks_path = root / "hooks" / "hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))["hooks"]
    for event_name in ["SessionStart", "Stop", "UserPromptSubmit"]:
        if event_name not in hooks:
            fail(f"hooks/hooks.json is missing {event_name} hook entry")

    prompt_hooks = hooks["UserPromptSubmit"]
    commands = [
        hook["command"]
        for group in prompt_hooks
        for hook in group.get("hooks", [])
        if hook.get("type") == "command"
    ]
    expected_command = '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" user-prompt-submit'
    if expected_command not in commands:
        fail(f"hooks/hooks.json is missing command entry: {expected_command}")


def top_level_skill_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        fail(f"Missing directory: {rel(root, ROOT)}")
    return sorted(path for path in root.iterdir() if path.is_dir())


def skill_names(source_root: Path) -> list[str]:
    names = [path.name for path in top_level_skill_dirs(source_root)]
    if not names:
        fail(f"No skill directories found in {rel(source_root, ROOT)}")
    for name in names:
        skill_file = source_root / name / "SKILL.md"
        if not skill_file.is_file():
            fail(f"Skill {name} is missing {rel(skill_file, ROOT)}")
    return names


def relative_files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def check_skill_tree_parity(root: Path) -> list[str]:
    source_root = root / "packages" / "claude-skills"
    plugin_root = root / "skills"
    source_names = skill_names(source_root)
    plugin_names = skill_names(plugin_root)
    if source_names != plugin_names:
        fail(
            "Skill directory mismatch between packages/claude-skills and skills:\n"
            f"  source={source_names}\n"
            f"  plugin={plugin_names}"
        )

    for skill_name in source_names:
        source_dir = source_root / skill_name
        plugin_dir = plugin_root / skill_name
        source_files = relative_files(source_dir)
        plugin_files = relative_files(plugin_dir)
        if source_files != plugin_files:
            fail(
                f"Skill file mismatch for {skill_name}:\n"
                f"  source={','.join(path.as_posix() for path in source_files)}\n"
                f"  plugin={','.join(path.as_posix() for path in plugin_files)}"
            )
        for relative_path in source_files:
            source_file = source_dir / relative_path
            plugin_file = plugin_dir / relative_path
            if source_file.read_bytes() != plugin_file.read_bytes():
                fail(f"Skill mirror content differs: {rel(plugin_file, root)} != {rel(source_file, root)}")

    return source_names


def check_distribution_script_coverage(root: Path, names: list[str]) -> None:
    for script in DISTRIBUTION_SCRIPTS:
        script_path = root / script
        if not script_path.is_file():
            fail(f"Missing distribution script: {script.as_posix()}")
        script_text = script_path.read_text(encoding="utf-8")
        missing = [name for name in names if name not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing skill inventory entries: {', '.join(missing)}")

    for script in VISIBLE_SKILL_SCRIPTS:
        script_text = (root / script).read_text(encoding="utf-8")
        missing = [name for name in names if f"/{name}" not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing user-facing skill output: {', '.join(missing)}")


def check_opencode_plugin_update_wiring(root: Path) -> None:
    for script in OPENCODE_PLUGIN_UPDATE_SCRIPTS:
        script_text = (root / script).read_text(encoding="utf-8")
        required_fragments = [
            "packages/opencode-plugin/sybermem.ts" if script.suffix == ".sh" else "packages\\opencode-plugin\\sybermem.ts",
            ".config/opencode/plugins" if script.suffix == ".sh" else ".config\\opencode\\plugins",
            "sybermem.ts",
        ]
        missing = [fragment for fragment in required_fragments if fragment not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing OpenCode plugin update wiring: {', '.join(missing)}")


def check_codex_skill_install_wiring(root: Path) -> None:
    for script in CODEX_SKILL_SCRIPTS:
        script_text = (root / script).read_text(encoding="utf-8")
        required_fragments = [
            ".agents/skills" if script.suffix == ".sh" else ".agents\\skills",
            "Codex",
        ]
        missing = [fragment for fragment in required_fragments if fragment not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing Codex skills install wiring: {', '.join(missing)}")


def check_codex_user_prompt_hook_install_wiring(root: Path) -> None:
    hook_source = root / ".codex" / "hooks" / "user_prompt.py"
    if not hook_source.is_file():
        fail("Missing Codex user prompt hook source: .codex/hooks/user_prompt.py")

    session_hook_source = root / ".codex" / "hooks" / "session_start.py"
    if not session_hook_source.is_file():
        fail("Missing Codex session start hook source: .codex/hooks/session_start.py")
    stop_hook_source = root / ".codex" / "hooks" / "stop.py"
    if not stop_hook_source.is_file():
        fail("Missing Codex stop hook source: .codex/hooks/stop.py")
    post_compact_hook_source = root / ".codex" / "hooks" / "post_compact.py"
    if not post_compact_hook_source.is_file():
        fail("Missing Codex post compact hook source: .codex/hooks/post_compact.py")

    hook_source_text = hook_source.read_text(encoding="utf-8")
    required_source_fragments = [
        "UserPromptSubmit",
        "hookSpecificOutput",
        "additionalContext",
        "context",
        '"recall"',
        '"habit"',
        "--delivery",
        "prompt-time",
        "classify_record_intent",
        ".record-intent.json",
    ]
    missing_source = [fragment for fragment in required_source_fragments if fragment not in hook_source_text]
    if missing_source:
        fail(f".codex/hooks/user_prompt.py is missing Codex user prompt hook fragments: {', '.join(missing_source)}")

    session_source_text = session_hook_source.read_text(encoding="utf-8")
    required_session_fragments = [
        "SessionStart",
        "hookSpecificOutput",
        "additionalContext",
        "context",
        '"session"',
    ]
    missing_session = [fragment for fragment in required_session_fragments if fragment not in session_source_text]
    if missing_session:
        fail(f".codex/hooks/session_start.py is missing Codex SessionStart hook fragments: {', '.join(missing_session)}")

    stop_source_text = stop_hook_source.read_text(encoding="utf-8")
    required_stop_fragments = [
        "Stop",
        "stop_hook_active",
        '"decision"',
        '"block"',
        '"reason"',
        "/sybermem-record",
        ".nudge-state.json",
    ]
    missing_stop = [fragment for fragment in required_stop_fragments if fragment not in stop_source_text]
    if missing_stop:
        fail(f".codex/hooks/stop.py is missing Codex Stop hook fragments: {', '.join(missing_stop)}")

    post_compact_source_text = post_compact_hook_source.read_text(encoding="utf-8")
    required_post_compact_fragments = [
        "PostCompact",
        ".codex-compact-marker.json",
        "hook_event_name",
        "trigger",
    ]
    missing_post_compact = [fragment for fragment in required_post_compact_fragments if fragment not in post_compact_source_text]
    if missing_post_compact:
        fail(f".codex/hooks/post_compact.py is missing Codex PostCompact hook fragments: {', '.join(missing_post_compact)}")

    forbidden_source_fragments = [
        "auto-resume",
        "background automation",
        '"agent"',
        '"prompt" handler',
    ]
    found_source = [fragment for fragment in forbidden_source_fragments if fragment in hook_source_text.lower()]
    if found_source:
        fail(f".codex/hooks/user_prompt.py contains unsupported Codex automation behavior: {', '.join(found_source)}")

    for script in CODEX_HOOK_INSTALL_SCRIPTS:
        script_text = (root / script).read_text(encoding="utf-8")
        if script.suffix == ".sh":
            required_fragments = [
                ".codex/hooks/user_prompt.py",
                ".codex/hooks/session_start.py",
                ".codex/hooks/stop.py",
                ".codex/hooks/post_compact.py",
                ".codex/hooks",
                "sybermem_user_prompt.py",
                "sybermem_session_start.py",
                "sybermem_stop.py",
                "sybermem_post_compact.py",
                ".codex/hooks.json",
                '"UserPromptSubmit"',
                '"SessionStart"',
                '"Stop"',
                '"PostCompact"',
                '"type": "command"',
                "additionalContextLimit",
                "SyberMem prompt context adds bounded Codex recall and habit reminders when relevant.",
                "SyberMem session context adds bounded Codex startup context when available.",
                "SyberMem Stop nudge adds bounded record reminders without looping.",
                "SyberMem PostCompact marks compact re-seed for the next SessionStart.",
            ]
            forbidden_fragments = [
                ".codex/config.toml",
                '"agent"',
                '"startup"',
                '"session"',
                "background automation",
                "auto-resume",
            ]
        else:
            required_fragments = [
                ".codex\\hooks\\user_prompt.py",
                ".codex\\hooks\\session_start.py",
                ".codex\\hooks\\stop.py",
                ".codex\\hooks\\post_compact.py",
                ".codex\\hooks",
                "sybermem_user_prompt.py",
                "sybermem_session_start.py",
                "sybermem_stop.py",
                "sybermem_post_compact.py",
                ".codex\\hooks.json",
                '"UserPromptSubmit"',
                '"SessionStart"',
                '"Stop"',
                '"PostCompact"',
                'type = "command"',
                "additionalContextLimit",
                "SyberMem prompt context adds bounded Codex recall and habit reminders when relevant.",
                "SyberMem session context adds bounded Codex startup context when available.",
                "SyberMem Stop nudge adds bounded record reminders without looping.",
                "SyberMem PostCompact marks compact re-seed for the next SessionStart.",
            ]
            forbidden_fragments = [
                ".codex\\config.toml",
                'type = "agent"',
                'type = "startup"',
                'type = "session"',
                "background automation",
                "auto-resume",
            ]
        missing = [fragment for fragment in required_fragments if fragment not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing Codex UserPromptSubmit hook install wiring: {', '.join(missing)}")
        found = [fragment for fragment in forbidden_fragments if fragment.lower() in script_text.lower()]
        if found:
            fail(f"{script.as_posix()} contains unsupported Codex automation wiring: {', '.join(found)}")


def check_runtime_refresh_wiring(root: Path) -> None:
    for script in RUNTIME_REFRESH_SCRIPTS:
        script_text = (root / script).read_text(encoding="utf-8")
        required_fragments = [
            "packages/core" if script.suffix == ".sh" else "packages\\core",
            "packages/cli" if script.suffix == ".sh" else "packages\\cli",
            "--upgrade",
            "--force-reinstall",
        ]
        missing = [fragment for fragment in required_fragments if fragment not in script_text]
        if missing:
            fail(f"{script.as_posix()} is missing runtime refresh wiring: {', '.join(missing)}")


def check_no_python_cache_artifacts(root: Path) -> None:
    offenders: list[str] = []
    for relative_root in NO_CACHE_ROOTS:
        tree = root / relative_root
        if not tree.exists():
            continue
        for path in tree.rglob("*"):
            if path.name == "__pycache__" or path.name == ".pytest_cache" or path.suffix == ".pyc":
                offenders.append(rel(path, root))
    if offenders:
        fail("Python cache artifacts must not be distributed:\n  " + "\n  ".join(sorted(offenders)))


def check_required_files(root: Path) -> None:
    for path in [*PUBLIC_DOCS, *PACKAGE_METADATA]:
        full_path = root / path
        if not full_path.is_file():
            fail(f"Missing file: {path.as_posix()}")
        if full_path.suffix == ".json":
            check_json(full_path, root)


def check_skill_cli_resolution_guidance(root: Path) -> None:
    required_fragments = [
        ".claude\\sybermem\\cli\\sybermem.cmd",
        ".claude/sybermem/cli/sybermem",
        "Do not modify persistent PATH automatically",
        "$SyberMemCli",
        "SYBERMEM_CLI",
    ]
    for relative_path in CLI_USING_SKILLS:
        skill_path = root / relative_path
        if not skill_path.is_file():
            fail(f"Missing file: {relative_path.as_posix()}")
        skill_text = skill_path.read_text(encoding="utf-8")
        missing = [fragment for fragment in required_fragments if fragment not in skill_text]
        if missing:
            fail(f"{relative_path.as_posix()} is missing CLI resolution guidance: {', '.join(missing)}")


def check_opencode_plugin_cli_resolution(root: Path) -> None:
    plugin_path = root / "packages" / "opencode-plugin" / "sybermem.ts"
    if not plugin_path.is_file():
        fail("Missing file: packages/opencode-plugin/sybermem.ts")
    plugin_text = plugin_path.read_text(encoding="utf-8")

    required_fragments = [
        "resolveSybermemCommand",
        ".claude",
        "sybermem.cmd",
        '"sybermem", "cli", "sybermem"',
        "USERPROFILE",
        "HOME",
        "sybermemText",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in plugin_text]
    if missing:
        fail(f"packages/opencode-plugin/sybermem.ts is missing CLI resolution support: {', '.join(missing)}")

    forbidden_fragments = [
        "$`sybermem digest status --format json`",
        "$`sybermem next-step --format json`",
        "$`sybermem habit inject --context ${habitContext} --format markdown`",
    ]
    found = [fragment for fragment in forbidden_fragments if fragment in plugin_text]
    if found:
        fail(f"packages/opencode-plugin/sybermem.ts still contains direct bare CLI calls: {', '.join(found)}")


def check_opencode_plugin_prompt_recall(root: Path) -> None:
    """Guard the OpenCode plugin's per-prompt high-signal recall path.

    Requires the `chat.message` capture + `experimental.chat.system.transform` injection
    seam, the `client.tui.showToast` toast API (not the undocumented hook-return map),
    and the resolver-backed `sybermem context recall` + `context habit --delivery prompt-time`
    CLI routes so recall and habit reminders arrive on the same prompt turn.
    """
    plugin_path = root / "packages" / "opencode-plugin" / "sybermem.ts"
    if not plugin_path.is_file():
        fail("Missing file: packages/opencode-plugin/sybermem.ts")
    plugin_text = plugin_path.read_text(encoding="utf-8")

    required_fragments = [
        '"chat.message"',
        '"experimental.chat.system.transform"',
        "client.tui.showToast",
        "context recall",
        "context habit",
        "--delivery",
        "prompt-time",
        "## User Habit Reminder",
        "RECALL_STASH",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in plugin_text]
    if missing:
        fail(f"packages/opencode-plugin/sybermem.ts is missing per-prompt recall wiring: {', '.join(missing)}")

    forbidden_fragments = [
        '"tui.toast.show"',
        "level:",
        "sybermem habit remind",
        "injected only at supported compaction",
        "undocumented per-prompt hook",
    ]
    found = [fragment for fragment in forbidden_fragments if fragment in plugin_text]
    if found:
        fail(f"packages/opencode-plugin/sybermem.ts uses non-standard toast contract: {', '.join(found)}")


def check_codex_metadata_honesty(root: Path) -> None:
    metadata_path = root / ".codex-plugin" / "plugin.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    description = str(metadata.get("description", ""))
    keywords = metadata.get("keywords", [])
    if not isinstance(keywords, list):
        fail(".codex-plugin/plugin.json keywords must be a list")

    required_description_fragments = ["Codex", "skills"]
    missing_description = [fragment for fragment in required_description_fragments if fragment not in description]
    if missing_description:
        fail(f".codex-plugin/plugin.json description is missing Codex skills support: {', '.join(missing_description)}")

    required_keywords = ["codex", "agents"]
    keyword_values = {str(keyword).lower() for keyword in keywords}
    missing_keywords = [keyword for keyword in required_keywords if keyword not in keyword_values]
    if missing_keywords:
        fail(f".codex-plugin/plugin.json keywords are missing: {', '.join(missing_keywords)}")

    serialized = json.dumps(metadata, ensure_ascii=False).lower()
    forbidden_fragments = ["hook", "runtime", "prompt-time", "auto-resume", "background automation"]
    found = [fragment for fragment in forbidden_fragments if fragment in serialized]
    if found:
        fail(f".codex-plugin/plugin.json contains unsupported Codex automation claims: {', '.join(found)}")


def check_codex_runtime_discoverability(root: Path) -> None:
    codex_project_files_fragment = 'Path.home() / ".agents" / "skills" / "sybermem-init-project" / "project-files"'
    unsupported_codex_fragments = [
        ".codex/config.toml",
        "hidden auto-resume",
        "background automation",
        "prompt or agent handler runtime",
    ]

    health_contents: list[bytes] = []
    for relative_path in CODEX_HEALTH_CHECK_FILES:
        health_path = root / relative_path
        if not health_path.is_file():
            fail(f"Missing file: {relative_path.as_posix()}")
        health_text = health_path.read_text(encoding="utf-8")
        if codex_project_files_fragment not in health_text:
            fail(f"{relative_path.as_posix()} is missing Codex discoverability source: {codex_project_files_fragment}")
        health_contents.append(health_path.read_bytes())

    if health_contents[0] != health_contents[1]:
        fail(
            "Codex health-check copies drifted: "
            "skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py "
            "must stay byte-identical to packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py"
        )

    codex_install = root / ".codex" / "INSTALL.md"
    if not codex_install.is_file():
        fail("Missing file: .codex/INSTALL.md")
    codex_install_text = codex_install.read_text(encoding="utf-8")
    missing_doc_fragments = [fragment for fragment in unsupported_codex_fragments if fragment not in codex_install_text]
    if missing_doc_fragments:
        fail(f".codex/INSTALL.md must explicitly document unsupported Codex runtime claims: {', '.join(missing_doc_fragments)}")

    codex_config = root / ".codex" / "config.toml"
    if codex_config.exists():
        fail("Codex support must not distribute .codex/config.toml")

    metadata = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    serialized_metadata = json.dumps(metadata, ensure_ascii=False).lower()
    forbidden_metadata_fragments = ["hook", "runtime", "prompt-time", "auto-resume", "background automation"]
    found_metadata = [fragment for fragment in forbidden_metadata_fragments if fragment in serialized_metadata]
    if found_metadata:
        fail(f".codex-plugin/plugin.json contains unsupported Codex automation claims: {', '.join(found_metadata)}")


def check_unsupported_platform_claims(root: Path) -> None:
    for relative_path in UNSUPPORTED_CLAIM_DOCS:
        path = root / relative_path
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not any(claim in line for claim in UNSUPPORTED_RUNTIME_CLAIMS):
                continue
            start = max(0, line_number - 7)
            end = min(len(lines), line_number + 2)
            normalized = "\n".join(lines[start:end]).lower()
            platform_doc = relative_path.parts[0] in {".opencode", ".codex"}
            platform_context = "opencode" in normalized or "codex" in normalized
            if not platform_doc and not platform_context:
                continue
            if not any(marker in normalized for marker in LIMITATION_MARKERS):
                fail(
                    f"{relative_path.as_posix()}:{line_number} mentions unsupported platform automation without limitation framing"
                )


def claude_validate(root: Path, target: Path) -> None:
    """Run `claude plugins validate` against a manifest when the CLI is available."""
    result = subprocess.run(
        ["claude", "plugins", "validate", str(target)],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        fail(f"claude plugins validate failed for {rel(target, root)}:\n{result.stdout}{result.stderr}")


VERSION_PYPROJECT_FILES: Final = [
    Path("packages/core/pyproject.toml"),
    Path("packages/cli/pyproject.toml"),
]
VERSION_JSON_FILES: Final = [
    Path(".claude-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
    Path(".codex-plugin/plugin.json"),
    Path(".cursor-plugin/plugin.json"),
    Path(".kimi-plugin/plugin.json"),
    Path("gemini-extension.json"),
]


def check_version_consistency(root: Path) -> None:
    import re

    version_file = root / "VERSION"
    if not version_file.is_file():
        fail("Missing file: VERSION (single-source version). Run scripts/sync-version.py.")
    expected = version_file.read_text(encoding="utf-8").strip()
    if not expected:
        fail("VERSION file is empty")

    pyproject_re = re.compile(r'(?m)^version\s*=\s*"([^"]*)"')
    for rel_path in VERSION_PYPROJECT_FILES:
        text = (root / rel_path).read_text(encoding="utf-8")
        match = pyproject_re.search(text)
        if not match or match.group(1) != expected:
            found = match.group(1) if match else "(none)"
            fail(f"{rel_path.as_posix()} version {found} != VERSION {expected}; run scripts/sync-version.py")

    for rel_path in VERSION_JSON_FILES:
        data = json.loads((root / rel_path).read_text(encoding="utf-8"))
        # marketplace.json nests the version under plugins[*]; others have it top-level.
        if "plugins" in data and isinstance(data["plugins"], list):
            versions = [p.get("version") for p in data["plugins"]]
            bad = [v for v in versions if v != expected]
            if bad or not versions:
                fail(f"{rel_path.as_posix()} plugin version {bad or '(none)'} != VERSION {expected}; run scripts/sync-version.py")
        elif data.get("version") != expected:
            fail(f"{rel_path.as_posix()} version {data.get('version')} != VERSION {expected}; run scripts/sync-version.py")


def main(root: Path = ROOT) -> int:
    check_required_files(root)
    check_hook_wiring(root)
    check_no_python_cache_artifacts(root)
    check_version_consistency(root)
    check_opencode_plugin_cli_resolution(root)
    check_opencode_plugin_prompt_recall(root)
    names = check_skill_tree_parity(root)
    check_skill_cli_resolution_guidance(root)
    check_distribution_script_coverage(root, names)
    check_opencode_plugin_update_wiring(root)
    check_codex_skill_install_wiring(root)
    check_codex_user_prompt_hook_install_wiring(root)
    check_codex_metadata_honesty(root)
    check_codex_runtime_discoverability(root)
    check_unsupported_platform_claims(root)
    check_runtime_refresh_wiring(root)

    claude_cli = shutil.which("claude")
    if claude_cli:
        claude_validate(root, root / ".claude-plugin" / "plugin.json")
        claude_validate(root, root / ".claude-plugin" / "marketplace.json")
        print(f"OK ({len(names)} skills; static checks + claude plugins validate)")
    else:
        print(f"OK ({len(names)} skills; static checks only; claude CLI not found, skipped plugins validate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
