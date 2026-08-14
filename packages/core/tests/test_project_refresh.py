from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.project_refresh import refresh_project


PROTOCOL_BLOCK = """<!-- SYBERMEM_SESSION_PROTOCOL:START -->
## SyberMem Session Protocol

Current protocol body.
<!-- SYBERMEM_SESSION_PROTOCOL:END -->"""


def write_template(template_root: Path, relative_path: str, content: str) -> None:
    target = template_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def seed_templates(template_root: Path) -> None:
    write_template(template_root, "CLAUDE.md", f"# Claude Instructions\n\n{PROTOCOL_BLOCK}\n\n## Core Rule\nTemplate rule.\n")
    write_template(template_root, "AGENTS.md", f"# Agent Instructions\n\n{PROTOCOL_BLOCK}\n\n## Core Rule\nTemplate rule.\n")
    write_template(
        template_root,
        ".claude/settings.json",
        json.dumps(
            {
                "env": {"SYBERMEM_RECORD_MODE": "remind"},
                "hooks": {
                    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python .sybermem/hooks/user_prompt.py", "timeout": 10}]}],
                    "SessionStart": [{"hooks": [{"type": "command", "command": "python .sybermem/hooks/session_start_context.py", "timeout": 15}]}],
                    "Stop": [{"hooks": [{"type": "command", "command": "python .sybermem/hooks/record_change_on_stop.py", "timeout": 60}]}],
                },
            },
            indent=2,
        )
        + "\n",
    )
    write_template(template_root, ".sybermem/hooks/user_prompt.py", "# current user prompt hook\n")
    write_template(template_root, ".sybermem/templates/change-template.md", "record_id:\nkey_conclusion:\ntopics:\n")
    write_template(template_root, ".sybermem/templates/digest-template.md", "coverage_hash:\n")
    write_template(template_root, ".sybermem/analysis/phase-index.md", "# Phase Index\n")


def test_refresh_project_is_idempotent_when_project_is_fresh(tmp_path: Path) -> None:
    # Given: a project refreshed once from deterministic templates
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    seed_templates(template_root)
    first = refresh_project(project_root, template_roots=(template_root,))

    # When: the same project is refreshed again
    second = refresh_project(project_root, template_roots=(template_root,))

    # Then: the second refresh reports no changes
    assert first["overall"] == "updated"
    assert second["overall"] == "fresh"
    assert second["actions_applied"] == []
    assert second["actions_needed"] == []


def test_refresh_project_creates_missing_managed_file_from_template(tmp_path: Path) -> None:
    # Given: a template-owned hook is absent from the project
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    seed_templates(template_root)

    # When: the project is refreshed
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: the missing hook is copied from the template
    hook_path = project_root / ".sybermem" / "hooks" / "user_prompt.py"
    assert hook_path.read_text(encoding="utf-8") == "# current user prompt hook\n"
    assert ".sybermem/hooks/user_prompt.py" in report["files"]
    assert "create .sybermem/hooks/user_prompt.py from template" in report["actions_applied"]


def test_refresh_project_backs_up_and_replaces_stale_managed_file(tmp_path: Path) -> None:
    # Given: a stale SyberMem-managed hook already exists
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    seed_templates(template_root)
    stale_hook = project_root / ".sybermem" / "hooks" / "user_prompt.py"
    stale_hook.parent.mkdir(parents=True, exist_ok=True)
    stale_hook.write_text("# stale hook\n", encoding="utf-8")

    # When: the project is refreshed
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: the stale hook is backed up and replaced with the template copy
    assert stale_hook.read_text(encoding="utf-8") == "# current user prompt hook\n"
    assert stale_hook.with_suffix(".py.bak").read_text(encoding="utf-8") == "# stale hook\n"
    assert "replace .sybermem/hooks/user_prompt.py from template" in report["actions_applied"]


def test_refresh_project_preserves_custom_instruction_content_while_refreshing_protocol(tmp_path: Path) -> None:
    # Given: AGENTS.md has custom content and an obsolete SyberMem protocol block
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    seed_templates(template_root)
    agents = project_root / "AGENTS.md"
    agents.parent.mkdir(parents=True, exist_ok=True)
    agents.write_text(
        "# Custom Agent Notes\n\n"
        "Keep this local workflow.\n\n"
        "<!-- SYBERMEM_SESSION_PROTOCOL:START -->\nold protocol\n<!-- SYBERMEM_SESSION_PROTOCOL:END -->\n\n"
        "Custom footer.\n",
        encoding="utf-8",
    )

    # When: the project is refreshed
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: custom content remains and the marker-bounded block is current
    content = agents.read_text(encoding="utf-8")
    assert "Keep this local workflow." in content
    assert "Custom footer." in content
    assert PROTOCOL_BLOCK in content
    assert "old protocol" not in content
    assert report["preserved_custom"] == ["AGENTS.md"]


def test_refresh_project_preserves_custom_instruction_with_workflow_heading(tmp_path: Path) -> None:
    # Given: AGENTS.md has a user-owned Workflow section plus stale protocol text
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    seed_templates(template_root)
    agents = project_root / "AGENTS.md"
    agents.parent.mkdir(parents=True, exist_ok=True)
    agents.write_text(
        "# Team Agent Guide\n\n"
        "## Workflow\n\n"
        "Custom release workflow that must never be overwritten.\n\n"
        "<!-- SYBERMEM_SESSION_PROTOCOL:START -->\nstale\n<!-- SYBERMEM_SESSION_PROTOCOL:END -->\n",
        encoding="utf-8",
    )

    # When: the project is refreshed
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: the custom workflow remains and no whole-file replacement backup is created
    content = agents.read_text(encoding="utf-8")
    assert "Custom release workflow that must never be overwritten." in content
    assert PROTOCOL_BLOCK in content
    assert not agents.with_suffix(".md.bak").exists()
    assert report["files"]["AGENTS.md"]["status"] == "custom_preserved"


def test_refresh_project_creates_missing_claude_settings_from_template(tmp_path: Path) -> None:
    # Given: the project has no Claude settings file
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    seed_templates(template_root)

    # When: the project is refreshed
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: settings.json is created from the operational template with global launchers
    settings_path = project_root / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    session_command = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    stop_command = settings["hooks"]["Stop"][0]["hooks"][0]["command"]
    assert session_command.endswith('/.claude/sybermem/launch_session_start_context.py"')
    assert stop_command.endswith('/.claude/sybermem/launch_record_change_on_stop.py"')
    assert session_command.startswith('python "')
    assert stop_command.startswith('python "')
    assert report["files"][".claude/settings.json"]["status"] == "created"
    assert "create .claude/settings.json from template" in report["actions_applied"]


def test_refresh_project_surgically_merges_custom_claude_settings(tmp_path: Path) -> None:
    # Given: custom settings include unrelated keys/hooks plus stale SyberMem hook groups
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    seed_templates(template_root)
    settings_path = project_root / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "permissions": {"allow": ["Bash(pytest:*)"]},
                "env": {"CUSTOM_ENV": "keep", "SYBERMEM_RECORD_MODE": "auto"},
                "hooks": {
                    "PreToolUse": [{"hooks": [{"type": "command", "command": "python custom_pre.py"}]}],
                    "UserPromptSubmit": [
                        {"hooks": [{"type": "command", "command": "python custom_prompt.py"}]},
                        {"hooks": [{"type": "command", "command": "python .sybermem/hooks/detect_record_intent.py"}]},
                        {"hooks": [{"type": "command", "command": "python .sybermem/hooks/task_recall.py"}]},
                    ],
                    "SessionStart": [
                        {"hooks": [{"type": "command", "command": "python custom_session.py"}]},
                        {"hooks": [{"type": "command", "command": "python .sybermem/hooks/session_start_context.py", "timeout": 1}]},
                    ],
                    "Stop": [
                        {"hooks": [{"type": "command", "command": "python custom_stop.py"}]},
                        {"hooks": [{"type": "command", "command": "python .sybermem/hooks/record_change_on_stop.py", "timeout": 1}]},
                    ],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # When: the project is refreshed
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: unrelated settings remain and SyberMem-managed settings are repaired
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["permissions"] == {"allow": ["Bash(pytest:*)"]}
    assert settings["env"]["CUSTOM_ENV"] == "keep"
    assert settings["env"]["SYBERMEM_RECORD_MODE"] == "remind"
    assert settings["hooks"]["PreToolUse"] == [{"hooks": [{"type": "command", "command": "python custom_pre.py"}]}]

    user_prompt_commands = [hook["command"] for group in settings["hooks"]["UserPromptSubmit"] for hook in group["hooks"]]
    session_commands = [hook["command"] for group in settings["hooks"]["SessionStart"] for hook in group["hooks"]]
    stop_commands = [hook["command"] for group in settings["hooks"]["Stop"] for hook in group["hooks"]]
    assert "python custom_prompt.py" in user_prompt_commands
    assert "python .sybermem/hooks/user_prompt.py" in user_prompt_commands
    assert "python .sybermem/hooks/detect_record_intent.py" not in user_prompt_commands
    assert "python .sybermem/hooks/task_recall.py" not in user_prompt_commands
    assert session_commands[0] == "python custom_session.py"
    assert session_commands[1].startswith('python "')
    assert session_commands[1].endswith('/.claude/sybermem/launch_session_start_context.py"')
    assert stop_commands[0] == "python custom_stop.py"
    assert stop_commands[1].startswith('python "')
    assert stop_commands[1].endswith('/.claude/sybermem/launch_record_change_on_stop.py"')
    assert report["files"][".claude/settings.json"]["status"] == "updated"
    assert "merge .claude/settings.json from template" in report["actions_applied"]


def test_refresh_project_json_payload_contains_required_summary_keys(tmp_path: Path) -> None:
    # Given: a minimal project refresh fixture
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    seed_templates(template_root)

    # When: the project is refreshed
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: the machine payload includes the CLI contract keys
    assert set(report) >= {
        "root",
        "overall",
        "files",
        "actions_needed",
        "actions_applied",
        "actions_skipped",
        "preserved_custom",
    }
    assert report["root"] == str(project_root.resolve()).replace("\\", "/")
    assert isinstance(report["files"], dict)
    assert isinstance(report["actions_needed"], list)
    assert isinstance(report["actions_applied"], list)
    assert isinstance(report["actions_skipped"], list)
    assert isinstance(report["preserved_custom"], list)


def test_refresh_project_rejects_managed_symlink_targets(tmp_path: Path) -> None:
    # Given: a project managed hook path is a symlink to a file outside the project
    template_root = tmp_path / "templates"
    project_root = tmp_path / "project"
    outside = tmp_path / "outside.py"
    seed_templates(template_root)
    outside.write_text("# outside\n", encoding="utf-8")
    hook = project_root / ".sybermem" / "hooks" / "user_prompt.py"
    hook.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(outside, hook)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    # When / Then: refresh refuses to follow the symlink and leaves the outside file intact
    with pytest.raises(ValueError, match="managed path is a symlink"):
        refresh_project(project_root, template_roots=(template_root,))
    assert outside.read_text(encoding="utf-8") == "# outside\n"
