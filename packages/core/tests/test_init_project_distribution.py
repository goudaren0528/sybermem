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


def test_shipped_digest_template_carries_coverage_hash() -> None:
    # Given: the authoritative digest template shipped to fresh projects
    template = (PROJECT_FILES / ".sybermem" / "templates" / "digest-template.md").read_text(encoding="utf-8")

    # Then: it declares the coverage_hash field that powers mechanical stale-digest detection
    assert "coverage_hash:" in template
    # And: the never-computed legacy fingerprint field has been retired
    assert "fingerprint:" not in template


def test_health_check_replaces_legacy_digest_template_missing_coverage_hash(tmp_path: Path) -> None:
    # Given: an existing project whose digest template predates coverage_hash (legacy fingerprint)
    project = tmp_path / "project"
    templates = project / ".sybermem" / "templates"
    templates.mkdir(parents=True)
    legacy_digest = templates / "digest-template.md"
    legacy_digest.write_text(
        "---\n"
        "type: digest\n"
        "kind: phase\n"
        "date: {{date}}\n"
        "source_records:\n"
        "{{source_records}}\n"
        "fingerprint: {{fingerprint}}\n"
        "---\n",
        encoding="utf-8",
    )

    # When: the distributed health checker classifies the digest template and derives actions
    health = runpy.run_path(str(HEALTH_SCRIPT))
    check_digest_template = health["check_digest_template"]
    generate_actions = health["generate_actions"]
    files = {".sybermem/templates/digest-template.md": check_digest_template(legacy_digest)}
    actions = generate_actions(files)

    # Then: the coverage_hash capability propagates as a replace action, not a silent no-op
    assert files[".sybermem/templates/digest-template.md"]["status"] == "stale"
    assert "replace .sybermem/templates/digest-template.md from template" in actions


def test_managed_file_copies_stay_byte_identical_across_distribution() -> None:
    # Given: managed files that exist as multiple distributed copies which must not drift
    mirror_project_files = ROOT / "skills" / "sybermem-init-project" / "project-files"
    managed_relative = (
        Path(".sybermem") / "templates" / "digest-template.md",
        Path(".sybermem") / "hooks" / "check_project_health.py",
        Path(".sybermem") / "hooks" / "task_recall.py",
        Path(".sybermem") / "hooks" / "session_start_context.py",
        Path(".sybermem") / "hooks" / "user_prompt.py",
    )

    # Then: every canonical/mirror pair is byte-identical so improvements reach both channels
    for rel in managed_relative:
        canonical = (PROJECT_FILES / rel).read_text(encoding="utf-8")
        mirror = (mirror_project_files / rel).read_text(encoding="utf-8")
        assert canonical == mirror, f"distribution drift in {rel.as_posix()}"


def test_merged_prompt_hook_applies_high_signal_recall_gate() -> None:
    # Given: user_prompt.py is the merged hook actually wired into settings (it reuses
    # task_recall's helpers). The high-signal gate (E1) and inject/abstain logging (E6)
    # must run on THIS production path, not only in the standalone task_recall.main.
    for base in (PROJECT_FILES, ROOT / "skills" / "sybermem-init-project" / "project-files"):
        hook = (base / ".sybermem" / "hooks" / "user_prompt.py").read_text(encoding="utf-8")
        # It must route recall through the high-signal contract, not the raw compact search.
        assert "high_signal_recall_hints" in hook, "merged hook must apply the E1 high-signal gate"
        assert "compact_project_search" not in hook, "merged hook must not bypass the gate via raw compact search"
        # And it must emit E6 observability events.
        assert "log_recall_event" in hook, "merged hook must log recall inject/abstain events"


def test_skill_definitions_stay_byte_identical_across_distribution() -> None:
    # Given: skills exist as a canonical tree (packages/claude-skills) and a mirror (skills/)
    canonical_skills = ROOT / "packages" / "claude-skills"
    mirror_skills = ROOT / "skills"

    # Then: every canonical SKILL.md has a byte-identical mirror so slash-command behavior
    # never diverges between the two distribution channels.
    for skill_md in sorted(canonical_skills.glob("*/SKILL.md")):
        rel = skill_md.relative_to(canonical_skills)
        mirror = mirror_skills / rel
        assert mirror.is_file(), f"missing mirror skill: {rel.as_posix()}"
        assert skill_md.read_text(encoding="utf-8") == mirror.read_text(encoding="utf-8"), f"skill drift in {rel.as_posix()}"
