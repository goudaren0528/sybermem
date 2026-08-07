from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.project_index import (
    DuplicateRecordIdError,
    build_project_index,
    check_project_index,
    write_project_index,
)


def write_record(root: Path, folder: str, filename: str, frontmatter: list[str], body: str = "") -> None:
    records = root / ".sybermem" / folder
    records.mkdir(parents=True, exist_ok=True)
    (records / filename).write_text(
        "\n".join(["---", *frontmatter, "---", "", body]) + "\n",
        encoding="utf-8",
    )


def write_index(root: Path, lines: list[str]) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir(exist_ok=True)
    (sybermem / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_build_project_index_includes_uuid_records_with_id_columns(tmp_path: Path) -> None:
    # Given: canonical records with explicit UUID-backed identifiers and metadata
    write_record(
        tmp_path,
        "changes",
        "2026-08-07-add-derived-index.md",
        ["type: change", "record_id: change-1234567890abcdef1234567890abcdef", "date: 2026-08-07", "title: Add derived project index", "status: implemented", "key_conclusion: Derived project indexes come from canonical records.", "topics: [index, canonical]"],
    )
    write_record(
        tmp_path,
        "decisions",
        "2026-08-06-derived-index-source.md",
        ["type: decision", "record_id: decision-fedcba0987654321fedcba0987654321", "date: 2026-08-06", "title: Use record files as index source", "status: decided", "key_conclusion: INDEX identity must not override record identity.", "topics:", "  - index", "  - identity"],
    )

    # When: the project index is built from canonical Markdown records
    index = build_project_index(tmp_path)

    # Then: generated tables use ID columns and include UUID-backed records deterministically
    assert "| ID | Date | Title | Status | Link |" in index
    assert "| Number | Date | Title | Status | Link |" not in index
    assert "| change-1234567890abcdef1234567890abcdef | 2026-08-07 | Add derived project index | implemented | [link](changes/2026-08-07-add-derived-index.md) |" in index
    assert "| decision-fedcba0987654321fedcba0987654321 | 2026-08-06 | Use record files as index source | decided | [link](decisions/2026-08-06-derived-index-source.md) |" in index
    assert "- [change-1234567890abcdef1234567890abcdef] #index #canonical — Derived project indexes come from canonical records. (2026-08-07)" in index
    assert "- index: change-1234567890abcdef1234567890abcdef, decision-fedcba0987654321fedcba0987654321" in index


def test_build_project_index_uses_legacy_overlay_for_missing_record_metadata(tmp_path: Path) -> None:
    # Given: a legacy record missing canonical conclusion/topics plus an INDEX overlay with old metadata
    write_index(tmp_path, ["# SyberMem Index", "", "## Key Conclusions", "", "- [requirement-001] #architecture #foundation — Adopted ADR system from existing INDEX metadata (2026-05-08)", "", "---", "", "## Requirements / Discussions", "", "| Number | Date | Title | Source | Priority | Link |", "|--------|------|-------|--------|----------|------|", "| 001 | 2026-05-08 | Old title | Internal discussion | high | [link](requirements/2026-05-08-001-old.md) |", "", "---", "", "## Topic Index", "", "- architecture: requirement-001", "- foundation: requirement-001"])
    write_record(tmp_path, "requirements", "2026-05-08-001-old.md", ["type: requirement", "date: 2026-05-08", "title: Create ADR Project Record System"])

    # When: the project index is rebuilt
    index = build_project_index(tmp_path)

    # Then: legacy-only conclusion, topics, Source, and Priority remain available
    assert "- [requirement-001] #architecture #foundation — Adopted ADR system from existing INDEX metadata (2026-05-08)" in index
    assert "| ID | Date | Title | Source | Priority | Link |" in index
    assert "| requirement-001 | 2026-05-08 | Create ADR Project Record System | Internal discussion | high | [link](requirements/2026-05-08-001-old.md) |" in index
    assert "- foundation: requirement-001" in index


def test_project_index_round_trips_generated_overlay_metadata_and_check_state(tmp_path: Path) -> None:
    # Given: legacy numeric table rows provide metadata that canonical records do not fully carry
    sybermem = tmp_path / ".sybermem"
    write_index(tmp_path, ["# SyberMem Index", "", "## Requirements / Discussions", "", "| Number | Date | Title | Source | Priority | Link |", "|--------|------|-------|--------|----------|------|", "| 001 | 2026-05-08 | Legacy requirement title | Internal discussion | high | [link](requirements/2026-05-08-001-old.md) |", "", "## Bug Fix Records", "", "| Number | Date | Title | Severity | Link |", "|--------|------|-------|----------|------|", "| 004 | 2026-08-05 | Legacy bug title | critical | [link](bugs/2026-08-05-004-old.md) |"])
    write_record(tmp_path, "requirements", "2026-05-08-001-old.md", ["type: requirement", "date: 2026-05-08", "title: Canonical requirement title"])
    write_record(tmp_path, "bugs", "2026-08-05-004-old.md", ["type: bug", "status: fixed"])

    # When: the first derived build is written and then parsed again on a second build
    assert write_project_index(tmp_path) is True
    first = (sybermem / "INDEX.md").read_text(encoding="utf-8")
    second = build_project_index(tmp_path)

    # Then: generated prefixed IDs still preserve legacy table metadata and the written file is current
    assert first == second
    assert check_project_index(tmp_path) is True
    assert "| requirement-001 | 2026-05-08 | Canonical requirement title | Internal discussion | high | [link](requirements/2026-05-08-001-old.md) |" in second
    assert "| bug-004 | 2026-08-05 | Legacy bug title | critical | [link](bugs/2026-08-05-004-old.md) |" in second


def test_build_project_index_backfills_missing_title_and_date_from_legacy_generated_tables(tmp_path: Path) -> None:
    # Given: a generated-style INDEX row retains title/date that the canonical bug frontmatter omits
    write_index(tmp_path, ["# SyberMem Index", "", "## Bug Fix Records", "", "| ID | Date | Title | Severity | Link |", "|----|------|-------|----------|------|", "| bug-004 | 2026-08-05 | Legacy bug title | critical | [link](bugs/2026-08-05-004-old.md) |"])
    write_record(tmp_path, "bugs", "2026-08-05-004-old.md", ["type: bug", "status: fixed"])

    # When: the project index is rebuilt from canonical records plus the generated overlay
    index = build_project_index(tmp_path)

    # Then: missing canonical title/date are backfilled from the legacy table overlay
    assert "| bug-004 | 2026-08-05 | Legacy bug title | critical | [link](bugs/2026-08-05-004-old.md) |" in index


def test_build_project_index_preserves_static_sections_and_replaces_derived_sections(tmp_path: Path) -> None:
    # Given: an existing INDEX with static prose, digest sections, and stale derived content
    write_index(tmp_path, ["# Custom Memory Index", "", "Static introduction that must stay.", "", "## Key Conclusions", "", "- [change-999] #stale — stale content (2026-01-01)", "", "## Phase Digests", "", "| Number | Date | Title | Status | Coverage | Link |", "|--------|------|-------|--------|----------|------|", "| 001 | 2026-01-02 | Keep this digest | completed | 1 record | [link](digests/one.md) |", "", "## Feature Changes", "", "stale table", "", "## Usage", "", "Keep usage instructions intact."])
    write_record(tmp_path, "changes", "2026-08-07-001-fresh.md", ["type: change", "date: 2026-08-07", "title: Fresh change", "status: implemented", "key_conclusion: Fresh derived content replaces stale generated content.", "topics: [fresh]"])

    # When: the INDEX is rebuilt
    index = build_project_index(tmp_path)

    # Then: static sections stay while derived sections are regenerated
    assert "# Custom Memory Index" in index
    assert "Static introduction that must stay." in index
    assert "| 001 | 2026-01-02 | Keep this digest | completed | 1 record | [link](digests/one.md) |" in index
    assert "Keep usage instructions intact." in index
    assert "change-999" not in index
    assert "stale table" not in index
    assert "| change-001 | 2026-08-07 | Fresh change | implemented | [link](changes/2026-08-07-001-fresh.md) |" in index


def test_build_project_index_output_is_deterministic(tmp_path: Path) -> None:
    # Given: records created in an order that differs from their canonical sort order
    write_record(
        tmp_path,
        "bugs",
        "2026-08-08-002-second.md",
        ["type: bug", "date: 2026-08-08", "title: Second bug", "status: fixed", "topics: [stability]"],
    )
    write_record(
        tmp_path,
        "changes",
        "2026-08-07-001-first.md",
        ["type: change", "date: 2026-08-07", "title: First change", "status: implemented", "topics: [stability]"],
    )

    # When: the same project index is built twice
    first = build_project_index(tmp_path)
    second = build_project_index(tmp_path)

    # Then: output is byte-stable and sorted by generated record id within derived topic rows
    assert first == second
    assert "- stability: bug-002, change-001" in first


def test_build_project_index_rejects_duplicate_non_empty_record_ids(tmp_path: Path) -> None:
    # Given: two canonical files claim the same non-empty record id
    frontmatter = ["type: change", "record_id: change-duplicate", "date: 2026-08-07", "title: Duplicate ID", "status: implemented"]
    write_record(tmp_path, "changes", "2026-08-07-a.md", frontmatter)
    write_record(tmp_path, "decisions", "2026-08-07-b.md", [*frontmatter, "type: decision"])

    # When / Then: duplicate canonical identity fails loudly instead of renumbering
    with pytest.raises(DuplicateRecordIdError) as error:
        build_project_index(tmp_path)
    assert error.value.record_id == "change-duplicate"


def test_write_and_check_project_index_are_change_aware_and_read_only(tmp_path: Path) -> None:
    # Given: a project with a canonical record and no INDEX yet
    write_record(tmp_path, "changes", "2026-08-07-001-derived.md", ["type: change", "date: 2026-08-07", "title: Derived index writer", "status: implemented", "topics: [index]"])
    index_path = tmp_path / ".sybermem" / "INDEX.md"

    # When / Then: check is read-only and reports missing, while write reports actual changes only
    assert check_project_index(tmp_path) is False
    assert not index_path.exists()
    assert write_project_index(tmp_path) is True
    first_content = index_path.read_text(encoding="utf-8")
    assert check_project_index(tmp_path) is True
    assert write_project_index(tmp_path) is False

    index_path.write_text(first_content.replace("Derived index writer", "Stale title"), encoding="utf-8")
    assert check_project_index(tmp_path) is False
    assert write_project_index(tmp_path) is True
    assert index_path.read_text(encoding="utf-8") == first_content
