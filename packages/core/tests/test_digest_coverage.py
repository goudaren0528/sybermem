from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.digest_coverage import compute_coverage_hash, digest_coverage_verdict, parse_digest_coverage
from sybermem_core.search import search_project


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def write_file(root: Path, rel: str, text: str) -> None:
    path = root / ".sybermem" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_digest(root: Path, name: str, source_records: list[str], coverage_hash: str | None, body_terms: str) -> None:
    frontmatter = [
        "type: digest",
        "kind: phase",
        "date: 2026-08-05",
        "number: 001",
        "title: coverage digest",
        "status: completed",
        "source_records:",
        *[f"  - {rel}" for rel in source_records],
    ]
    if coverage_hash is not None:
        frontmatter.append(f"coverage_hash: {coverage_hash}")
    text = "\n".join(["---", *frontmatter, "---", "", f"## Core Conclusions\n- {body_terms}"]) + "\n"
    write_file(root, f"digests/{name}", text)


def test_parse_digest_coverage_reads_sources_and_hash() -> None:
    text = (
        "---\n"
        "type: digest\n"
        "source_records:\n"
        "  - changes/a.md\n"
        "  - bugs/b.md\n"
        "coverage_hash: abc123\n"
        "---\n\n## Core Conclusions\n- x\n"
    )
    sources, stored = parse_digest_coverage(text)
    assert sources == ["changes/a.md", "bugs/b.md"]
    assert stored == "abc123"


def test_digest_without_coverage_hash_is_unknown_not_stale(tmp_path: Path) -> None:
    # Given: a legacy digest that predates the coverage_hash field
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\nbody\n")
    write_digest(root, "d1.md", ["changes/a.md"], coverage_hash=None, body_terms="legacy")

    # Then: it is never falsely flagged stale
    digest_text = (root / ".sybermem" / "digests" / "d1.md").read_text(encoding="utf-8")
    assert digest_coverage_verdict(root, digest_text) == "unknown"


def test_digest_coverage_current_then_stale_after_source_change(tmp_path: Path) -> None:
    # Given: a digest whose coverage_hash matches its current source files
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\noriginal body\n")
    current_hash = compute_coverage_hash(root, ["changes/a.md"])
    write_digest(root, "d1.md", ["changes/a.md"], coverage_hash=current_hash, body_terms="covered")
    digest_text = (root / ".sybermem" / "digests" / "d1.md").read_text(encoding="utf-8")

    # Then: it reads current
    assert digest_coverage_verdict(root, digest_text) == "current"

    # When: the source record changes after the digest was written
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\nMUTATED body\n")

    # Then: coverage is mechanically stale
    assert digest_coverage_verdict(root, digest_text) == "stale"


def test_search_marks_stale_covered_digest_historical(tmp_path: Path, monkeypatch) -> None:
    # Given: a digest covering a source record, with a coverage_hash captured before mutation
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(
        root,
        "changes/2026-08-04-001-covered.md",
        "---\ntype: change\ndate: 2026-08-04\ntitle: Covered change\nstatus: implemented\n---\n\n## Summary\ncoveragetoken original.\n",
    )
    stale_hash = compute_coverage_hash(root, ["changes/2026-08-04-001-covered.md"])
    write_digest(root, "2026-08-05-001-cover.md", ["changes/2026-08-04-001-covered.md"], coverage_hash=stale_hash, body_terms="coveragetoken digest")

    # When: the covered source changes, then search surfaces the digest
    write_file(
        root,
        "changes/2026-08-04-001-covered.md",
        "---\ntype: change\ndate: 2026-08-04\ntitle: Covered change\nstatus: implemented\n---\n\n## Summary\ncoveragetoken MUTATED.\n",
    )
    monkeypatch.chdir(root)
    rows = search_project("coveragetoken")

    # Then: the digest row is mechanically demoted to stale/historical with a conflict note
    digest_row = next(row for row in rows if row["source_kind"] == "digest")
    assert digest_row["freshness"] == "stale"
    assert "source records changed" in digest_row["conflict_note"]
