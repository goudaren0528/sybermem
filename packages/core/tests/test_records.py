from __future__ import annotations

from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.records import (
    generate_record_id,
    parse_project_yaml,
    parse_project_yaml_full,
    parse_record_file,
    unwrap_scalar,
)
from sybermem_core.retrieval import derive_continuity_metadata


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


def test_parse_record_file_reads_norm_type_and_scope(tmp_path: Path) -> None:
    # Given: a norm record with scope frontmatter
    record_path = tmp_path / "2026-08-24-norm-abc.md"
    record_path.write_text(
        "\n".join([
            "---", "type: norm", "record_id: norm-abcdef1234567890abcdef1234567890",
            "date: 2026-08-24", "title: Use pnpm", "authority: authoritative",
            "status: active", "scope: global", "key_conclusion: Use pnpm in this repo",
            "---", "", "## Norm Statement", "Use pnpm.",
        ]) + "\n",
        encoding="utf-8",
    )

    record = parse_record_file(record_path, "project-1", "demo")
    assert record["type"] == "norm"
    assert record["scope"] == "global"
    assert record["authority"] == "authoritative"
    assert record["key_conclusion"] == "Use pnpm in this repo"


def test_parse_record_file_tolerates_utf8_bom(tmp_path: Path) -> None:
    # Given: a record whose file begins with a UTF-8 BOM (e.g. written by some editors)
    record_path = tmp_path / "2026-08-24-norm-bom.md"
    record_path.write_text(
        "\ufeff" + "\n".join([
            "---", "type: norm", "record_id: norm-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "date: 2026-08-24", "title: BOM norm", "scope: global",
            "key_conclusion: BOM must not break frontmatter parsing",
            "---", "", "## Norm Statement", "x",
        ]) + "\n",
        encoding="utf-8",
    )

    record = parse_record_file(record_path, "", "")
    # Without BOM tolerance these would all be empty
    assert record["type"] == "norm"
    assert record["scope"] == "global"
    assert record["key_conclusion"] == "BOM must not break frontmatter parsing"


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


def test_parse_record_file_reads_declared_source_kind(tmp_path: Path) -> None:
    # Given: a record that declares source_kind in frontmatter
    record_path = tmp_path / "2026-08-11-001-declared-source-kind.md"
    record_path.write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "record_id: change-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "date: 2026-08-11",
                "title: Declared source_kind",
                "source_kind: digest",
                "---",
                "",
                "## Change Content",
                "Body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: the record is parsed and continuity metadata is derived
    record = parse_record_file(record_path, "project-1", "demo")
    metadata = derive_continuity_metadata(record, match_reason="")

    # Then: the declared source_kind is both parsed and honored by classification
    assert record["source_kind"] == "digest"
    assert metadata["source_kind"] == "digest"


def test_declared_source_kind_falls_back_when_invalid(tmp_path: Path) -> None:
    # Given: a record whose declared source_kind is not a recognized value
    record_path = tmp_path / "2026-08-11-002-invalid-source-kind.md"
    record_path.write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "record_id: change-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "date: 2026-08-11",
                "title: Invalid source_kind",
                "source_kind: nonsense",
                "---",
                "",
                "## Change Content",
                "Body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: parsed and classified
    record = parse_record_file(record_path, "project-1", "demo")
    metadata = derive_continuity_metadata(record, match_reason="")

    # Then: the raw value is preserved by the parser but ignored by validation
    # (parse, don't trust blindly), so classification falls back to inference.
    assert record["source_kind"] == "nonsense"
    assert metadata["source_kind"] == "manual"


def test_parse_record_file_unwraps_quoted_scalars_and_topics(tmp_path: Path) -> None:
    # Given: a record with quoted title (containing a colon) and quoted inline topics
    record_path = tmp_path / "2026-08-11-003-quoted.md"
    record_path.write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "record_id: change-cccccccccccccccccccccccccccccccc",
                "date: 2026-08-11",
                'title: "Fix: quoted title with colon"',
                'topics: ["arch", "quality"]',
                "---",
                "",
                "## Change Content",
                "Body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: parsed
    record = parse_record_file(record_path, "project-1", "demo")

    # Then: quotes are stripped and the colon-bearing title survives intact
    assert record["title"] == "Fix: quoted title with colon"
    assert record["topics"] == "arch,quality"


def test_parse_record_file_reads_inline_related_files(tmp_path: Path) -> None:
    # Given: a record declaring related_files as an inline list (the common shape)
    record_path = tmp_path / "2026-08-15-001-inline-related.md"
    record_path.write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "record_id: change-dddddddddddddddddddddddddddddddd",
                "date: 2026-08-15",
                "title: Inline related files",
                "related_files: [packages/core/sybermem_core/memory_stats.py, packages/core/sybermem_core/records.py]",
                "---",
                "",
                "## Change Content",
                "Body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: parsed
    record = parse_record_file(record_path, "project-1", "demo")

    # Then: related_files becomes a comma-joined path string, distinct from `related`
    assert record["related_files"] == "packages/core/sybermem_core/memory_stats.py,packages/core/sybermem_core/records.py"
    assert record["related"] == ""


def test_parse_record_file_reads_multiline_related_files(tmp_path: Path) -> None:
    # Given: a record declaring related_files as a multiline YAML list
    record_path = tmp_path / "2026-08-15-002-multiline-related.md"
    record_path.write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "record_id: change-eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "date: 2026-08-15",
                "title: Multiline related files",
                "related_files:",
                "  - src/auth.ts",
                "  - src/token.ts",
                "topics:",
                "  - auth",
                "---",
                "",
                "## Change Content",
                "Body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: parsed
    record = parse_record_file(record_path, "project-1", "demo")

    # Then: multiline entries are collected and a following field still parses
    assert record["related_files"] == "src/auth.ts,src/token.ts"
    assert record["topics"] == "auth"


def test_parse_record_file_defaults_related_files_to_empty_for_legacy_records(tmp_path: Path) -> None:
    # Given: a legacy record with no related_files field
    record_path = tmp_path / "2026-08-15-003-no-related.md"
    record_path.write_text(
        "\n".join(
            [
                "---",
                "type: bug",
                "date: 2026-08-15",
                "title: No related files",
                "---",
                "",
                "## Summary",
                "Body.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: parsed
    record = parse_record_file(record_path, "project-1", "demo")

    # Then: the field defaults to empty so old records simply do not participate in relevance
    assert record["related_files"] == ""


def test_unwrap_scalar_strips_only_matching_quote_pairs() -> None:
    assert unwrap_scalar("  'hi'  ") == "hi"
    assert unwrap_scalar('"hi"') == "hi"
    assert unwrap_scalar("plain") == "plain"
    # Mismatched surrounding quotes must be left untouched.
    assert unwrap_scalar("'mismatch\"") == "'mismatch\""


def test_parse_project_yaml_handles_nested_repository_and_quotes(tmp_path: Path) -> None:
    # Given: a project.yaml with a nested repository map and a quoted scalar
    syb = tmp_path / ".sybermem"
    syb.mkdir()
    (syb / "project.yaml").write_text(
        "\n".join(
            [
                "schema_version: 1",
                "project_id: 01J-ABC",
                "slug: sybermem",
                'name: "sybermem"',
                "created_at: 2026-08-11T10:00:00",
                "repository:",
                "  remote: git@github.com:goudaren0528/sybermem.git",
                "  default_branch: main",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: parsed via the flat (back-compat) and full views
    flat = parse_project_yaml(tmp_path)
    full = parse_project_yaml_full(tmp_path)

    # Then: the flat view exposes only scalars (quoted values unwrapped) and never
    # leaks nested children as bogus top-level keys.
    assert flat["name"] == "sybermem"
    assert flat["slug"] == "sybermem"
    assert flat["project_id"] == "01J-ABC"
    assert "remote" not in flat and "default_branch" not in flat
    # And: the full view surfaces the nested repository map.
    assert isinstance(full["repository"], dict)
    assert full["repository"]["remote"] == "git@github.com:goudaren0528/sybermem.git"
    assert full["repository"]["default_branch"] == "main"
