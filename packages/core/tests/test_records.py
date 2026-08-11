from __future__ import annotations

from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.records import generate_record_id, parse_record_file


def test_generate_record_id_is_exported_from_package_root() -> None:
    # The record-id helper must be importable from the package root so callers
    # (and the record skill) have a discoverable entrypoint, not a buried module.
    import sybermem_core

    from_root = sybermem_core.generate_record_id
    assert "generate_record_id" in sybermem_core.__all__
    assert re.fullmatch(r"bug-[0-9a-f]{32}", from_root("bug"))


def test_generate_record_id_returns_uuid_backed_identifier() -> None:
    # Given: a canonical SyberMem record type
    record_type = "change"

    # When: a new record id is generated
    record_id = generate_record_id(record_type)

    # Then: the id uses the expected type-prefixed UUID format
    assert re.fullmatch(r"change-[0-9a-f]{32}", record_id)


def test_parse_record_file_prefers_explicit_frontmatter_record_id_and_topics(tmp_path: Path) -> None:
    # Given: a canonical record file with explicit frontmatter identifiers
    record_path = tmp_path / "2026-08-07-001-canonical-record.md"
    record_path.write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "record_id: change-1234567890abcdef1234567890abcdef",
                "date: 2026-08-07",
                "title: Canonical UUID record",
                "status: implemented",
                "key_conclusion: Explicit canonical metadata wins over filename fallback.",
                "topics:",
                "  - canonical",
                "  - uuid",
                "---",
                "",
                "## Summary",
                "Body text with #legacy-tag that should not override explicit topics.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: the record is parsed for indexing
    record = parse_record_file(record_path, "project-1", "demo")

    # Then: canonical frontmatter wins while existing caller-facing keys remain intact
    assert record["project_id"] == "project-1"
    assert record["slug"] == "demo"
    assert record["record_id"] == "change-1234567890abcdef1234567890abcdef"
    assert record["type"] == "change"
    assert record["title"] == "Canonical UUID record"
    assert record["created_at"] == "2026-08-07"
    assert record["status"] == "implemented"
    assert record["topics"] == "canonical,uuid"
    assert record["key_conclusion"] == "Explicit canonical metadata wins over filename fallback."


def test_parse_record_file_preserves_legacy_filename_record_id_and_optional_metadata(tmp_path: Path) -> None:
    # Given: a legacy record without canonical frontmatter extensions
    record_path = tmp_path / "2026-08-07-007-legacy-record.md"
    record_path.write_text(
        "\n".join(
            [
                "---",
                "type: bug",
                "date: 2026-08-07",
                "title: Legacy bug record",
                "status: resolved",
                "---",
                "",
                "## Summary",
                "Legacy records still expose #hooks and #compatibility topics.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: the legacy record is parsed
    record = parse_record_file(record_path, "project-legacy", "demo")

    # Then: the numeric filename fallback and optional metadata compatibility remain intact
    assert record["record_id"] == "bug-007"
    assert record["topics"] == "hooks,compatibility"
    assert record["key_conclusion"] == ""
    assert record["status"] == "resolved"


def test_parse_record_file_reads_canonical_requirement_and_bug_metadata(tmp_path: Path) -> None:
    # Given: canonical requirement and bug records with new frontmatter fields
    requirement_path = tmp_path / "2026-08-07-001-requirement.md"
    requirement_path.write_text(
        "\n".join(
            [
                "---",
                "type: requirement",
                "date: 2026-08-07",
                "title: Capture canonical requirement metadata",
                "source: Product review",
                "priority: high",
                "---",
                "",
                "Requirement body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    bug_path = tmp_path / "2026-08-07-002-bug.md"
    bug_path.write_text(
        "\n".join(
            [
                "---",
                "type: bug",
                "date: 2026-08-07",
                "title: Capture canonical bug metadata",
                "severity: critical",
                "status: fixed",
                "---",
                "",
                "Bug body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: each canonical record is parsed
    requirement = parse_record_file(requirement_path, "project-1", "demo")
    bug = parse_record_file(bug_path, "project-1", "demo")

    # Then: exact frontmatter keys are preserved for downstream rendering
    assert requirement["source"] == "Product review"
    assert requirement["priority"] == "high"
    assert bug["severity"] == "critical"
