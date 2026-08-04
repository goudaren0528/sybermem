from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.search import compact_project_search, search_project


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def write_record(root: Path, subdir: str, filename: str, frontmatter: list[str], body: str) -> None:
    records = root / ".sybermem" / subdir
    records.mkdir(exist_ok=True)
    (records / filename).write_text("\n".join(["---", *frontmatter, "---", "", body]) + "\n", encoding="utf-8")


def test_compact_project_search_excludes_auto_trail_evidence_but_explicit_search_returns_it(tmp_path: Path, monkeypatch) -> None:
    # Given: an authoritative manual record and a matching auto-trail evidence record
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-authoritative.md",
        ["type: change", "date: 2026-08-04", "title: Authoritative recall fix", "status: implemented"],
        "## Summary\nManual fix for recall-token retrieval.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-04-002-auto.md",
        ["type: change", "date: 2026-08-04", "title: Auto recall trail", "status: implemented"],
        "## Change Content\nAuto-generated from workspace changes detected at session stop. recall-token",
    )
    monkeypatch.chdir(project_root)

    # When: explicit and compact automatic searches run for the same query
    explicit_rows = search_project("recall-token")
    compact_rows = compact_project_search("recall-token", limit=3)

    # Then: evidence stays visible on explicit search but is excluded from automatic recall
    assert {row["authority"] for row in explicit_rows} == {"authoritative", "evidence"}
    assert [row["record_id"] for row in compact_rows] == ["change-001"]


def test_project_search_derives_summary_and_related_digest_from_markdown(tmp_path: Path, monkeypatch) -> None:
    # Given: a manual record covered by a digest through existing source_records metadata
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-recall-contract.md",
        ["type: change", "date: 2026-08-04", "title: Recall contract", "status: implemented"],
        "## Summary\nRecall packets include bounded metadata only.\n\n## Details\nFull content should stay out of packets.",
    )
    write_record(
        project_root,
        "digests",
        "2026-08-05-001-recall-digest.md",
        [
            "type: digest",
            "kind: phase",
            "date: 2026-08-05",
            "number: 001",
            "title: recall digest",
            "status: completed",
            "source_records:",
            "  - changes/2026-08-04-001-recall-contract.md",
        ],
        "## Core Conclusions\n- Recall contract stabilized.",
    )
    monkeypatch.chdir(project_root)

    # When: project search returns the manual record
    rows = search_project("Recall packets")

    # Then: compact metadata is derived without requiring canonical format changes
    row = next(item for item in rows if item["record_id"] == "change-001")
    assert row["summary"] == "Recall packets include bounded metadata only."
    assert row["related_digest"] == "digest-001"


def test_compact_project_search_notes_historical_digest_when_newer_authoritative_record_matches(tmp_path: Path, monkeypatch) -> None:
    # Given: a historical digest and a newer authoritative record matching the same query
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "digests",
        "2026-08-04-001-old-digest.md",
        ["type: digest", "kind: phase", "date: 2026-08-04", "number: 001", "title: old digest", "status: completed"],
        "## Core Conclusions\n- conflict-token used to mean the old digest conclusion.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-05-001-new-decision.md",
        ["type: decision", "date: 2026-08-05", "title: New conflict decision", "status: decided"],
        "## Summary\nconflict-token is now governed by the newer decision.",
    )
    monkeypatch.chdir(project_root)

    # When: compact recall sees both matching rows
    rows = compact_project_search("conflict-token", limit=3)

    # Then: the digest remains present but carries deterministic conflict metadata
    digest = next(row for row in rows if row["record_id"] == "digest-001")
    assert digest["conflict_note"] == "historical digest; newer authoritative record exists"


def test_compact_project_search_matches_english_terms_across_record_fields(tmp_path: Path, monkeypatch) -> None:
    # Given: a record whose meaningful prompt terms are spread across title, topics, relations, and body
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-workspace-recall.md",
        [
            "type: requirement",
            "date: 2026-08-04",
            "title: Workspace recall behavior",
            "status: accepted",
            "topics: [search, context]",
            "implements: decision-123",
        ],
        "## Summary\nNatural prompts should retrieve concise context without exact phrase matching.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-001-workspace-only.md",
        ["type: change", "date: 2026-08-05", "title: Workspace cleanup", "status: implemented"],
        "## Summary\nA newer single-term record should not crowd out the stronger overlap.",
    )
    monkeypatch.chdir(project_root)

    # When: a natural English prompt distributes terms across record fields
    rows = compact_project_search("retrieve workspace context for search decision", limit=3)

    # Then: the authoritative record is recalled without requiring an exact phrase match
    assert [row["record_id"] for row in rows] == ["requirement-001"]
    assert rows[0]["match"] in {"relation", "topic", "keyword"}


def test_compact_project_search_matches_natural_chinese_prompt(tmp_path: Path, monkeypatch) -> None:
    # Given: a Chinese requirement record with no ASCII query terms
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-cjk-recall.md",
        ["type: requirement", "date: 2026-08-04", "title: 中文任务召回", "status: accepted", "topics: [中文, 检索]"],
        "## Summary\n自然语言提示可以检索需求上下文并完成任务召回。",
    )
    monkeypatch.chdir(project_root)

    # When: a natural CJK prompt asks for the same retrieval behavior
    rows = compact_project_search("中文提示应该检索上下文并召回相关需求", limit=3)

    # Then: compact recall returns the matching authoritative requirement
    assert [row["record_id"] for row in rows] == ["requirement-001"]


def test_compact_project_search_ignores_low_signal_prompt(tmp_path: Path, monkeypatch) -> None:
    # Given: a project with content containing common words and isolated CJK characters
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-common.md",
        ["type: change", "date: 2026-08-04", "title: Common project change record", "status: implemented"],
        "## Summary\nThe project has a change record with 中文内容 for realistic fixtures.",
    )
    monkeypatch.chdir(project_root)

    # When: the prompt contains only low-signal short/common terms
    rows = compact_project_search("please check the project change record", limit=3)

    # Then: automatic recall stays quiet
    assert rows == []
