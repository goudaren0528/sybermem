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


def test_compact_project_search_stales_digest_when_related_newer_authoritative_record_matches(tmp_path: Path, monkeypatch) -> None:
    # Given: a historical digest and a related newer authoritative record matching the same query
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
        ["type: decision", "date: 2026-08-05", "title: New conflict decision", "status: decided", "related: digest-001"],
        "## Summary\nconflict-token is now governed by the newer decision.",
    )
    monkeypatch.chdir(project_root)

    # When: compact recall sees both matching rows
    rows = compact_project_search("conflict-token", limit=3)

    # Then: the digest remains present but carries deterministic conflict metadata
    digest = next(row for row in rows if row["record_id"] == "digest-001")
    assert digest["freshness"] == "stale"
    assert digest["conflict_note"] == "historical digest; newer authoritative record exists"


def test_compact_project_search_keeps_digest_historical_when_newer_match_is_unrelated(tmp_path: Path, monkeypatch) -> None:
    # Given: a digest and an unrelated newer decision happen to share the same query token
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "digests",
        "2026-08-04-001-current-digest.md",
        ["type: digest", "kind: phase", "date: 2026-08-04", "number: 001", "title: unrelated digest", "status: completed"],
        "## Core Conclusions\n- overlap-token summarized the digest-covered work.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-05-001-unrelated-decision.md",
        ["type: decision", "date: 2026-08-05", "title: Unrelated overlap decision", "status: decided"],
        "## Summary\noverlap-token is used here for an unrelated decision.",
    )
    monkeypatch.chdir(project_root)

    # When: compact recall sees both keyword matches
    rows = compact_project_search("overlap-token", limit=3)

    # Then: an unrelated newer authoritative record does not stale the digest
    digest = next(row for row in rows if row["record_id"] == "digest-001")
    assert digest["freshness"] == "historical"
    assert digest["conflict_note"] == ""


def test_project_search_ignores_low_signal_substring_query(tmp_path: Path, monkeypatch) -> None:
    # Given: a record containing incidental substrings that include a short manual query
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-incidental.md",
        ["type: change", "date: 2026-08-04", "title: Shipping search history", "status: implemented"],
        "## Summary\nThis record has historical content that should not match a low-signal hi query.",
    )
    monkeypatch.chdir(project_root)

    # When: a manual query has no meaningful search terms
    rows = search_project("hi")

    # Then: explicit search does not return substring-noise hits
    assert rows == []
