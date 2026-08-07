from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROJECT_FILES = ROOT / "packages" / "claude-skills" / "sybermem-init-project" / "project-files"
HEALTH_SCRIPT = PROJECT_FILES / ".sybermem" / "hooks" / "check_project_health.py"


def test_init_project_index_template_uses_id_columns_and_derived_wording() -> None:
    # Given: the authoritative init-project INDEX template shipped to fresh projects
    index = (PROJECT_FILES / ".sybermem" / "INDEX.md").read_text(encoding="utf-8")

    # When / Then: record sections use canonical IDs and describe derived maintenance
    assert "| ID | Date | Title | Status | Link |" in index
    assert "| ID | Date | Title | Source | Priority | Link |" in index
    assert "| ID | Date | Title | Severity | Link |" in index
    assert "| Number | Date | Title | Status | Link |" not in index
    assert "sybermem project index build" in index
    assert "When adding records, update this index file accordingly." not in index


def test_init_project_record_templates_include_uuid_index_metadata() -> None:
    # Given: the authoritative project-files template tree distributed by init-project
    expected_fields = {
        "change-template.md": ("record_id", "key_conclusion", "topics", "source"),
        "decision-template.md": ("record_id", "key_conclusion", "topics", "source"),
        "requirement-template.md": ("record_id", "key_conclusion", "topics", "source", "priority"),
        "bug-template.md": ("record_id", "key_conclusion", "topics", "source", "severity"),
    }

    # When / Then: all four runtime record templates exist and carry derived-index metadata fields
    for template_name, fields in expected_fields.items():
        template = PROJECT_FILES / ".sybermem" / "templates" / template_name
        text = template.read_text(encoding="utf-8")
        for field in fields:
            assert f"{field}:" in text


def test_health_check_detects_missing_record_templates(tmp_path: Path) -> None:
    # Given: an existing project missing the four record templates required for UUID-backed records
    project = tmp_path / "project"
    templates = project / ".sybermem" / "templates"
    templates.mkdir(parents=True)
    (project / ".claude").mkdir()
    (project / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (project / ".sybermem" / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")

    # When: the distributed health checker classifies managed files
    health = runpy.run_path(str(HEALTH_SCRIPT))
    check_record_template = health["check_record_template"]
    generate_actions = health["generate_actions"]
    files = {
        f".sybermem/templates/{name}": check_record_template(templates / name)
        for name in ("change-template.md", "decision-template.md", "requirement-template.md", "bug-template.md")
    }
    actions = generate_actions(files)

    # Then: update propagation will create the missing record templates
    expected_actions = {
        "create .sybermem/templates/change-template.md from template",
        "create .sybermem/templates/decision-template.md from template",
        "create .sybermem/templates/requirement-template.md from template",
        "create .sybermem/templates/bug-template.md from template",
    }
    assert expected_actions.issubset(actions)


def test_health_check_replaces_stale_record_template(tmp_path: Path) -> None:
    # Given: an existing project with one old numeric record template still present on disk
    project = tmp_path / "project"
    templates = project / ".sybermem" / "templates"
    templates.mkdir(parents=True)
    old_change_template = templates / "change-template.md"
    old_change_template.write_text(
        "---\n"
        "type: change\n"
        "number: XXX\n"
        "date: {{date}}\n"
        "title: {{title}}\n"
        "status: {{status}}\n"
        "author: {{author}}\n"
        "related_files: {{related_files}}\n"
        "---\n",
        encoding="utf-8",
    )

    # When: the distributed health checker evaluates that template and derives follow-up actions
    health = runpy.run_path(str(HEALTH_SCRIPT))
    check_record_template = health["check_record_template"]
    generate_actions = health["generate_actions"]
    files = {
        ".sybermem/templates/change-template.md": check_record_template(old_change_template),
    }
    actions = generate_actions(files)

    # Then: present legacy numeric templates are stale and propagate as replace actions
    assert files[".sybermem/templates/change-template.md"]["status"] == "stale"
    assert "replace .sybermem/templates/change-template.md from template" in actions
