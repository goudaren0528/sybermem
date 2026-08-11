from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.digest_coverage import compute_coverage_hash
from sybermem_core.digest_governance import (
    build_digest_governance_report,
    stale_digest_count,
)


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


def write_digest(root: Path, name: str, record_id: str, source_records: list[str], coverage_hash: str | None) -> None:
    frontmatter = [
        "type: digest",
        "kind: phase",
        "date: 2026-08-05",
        "number: 001",
        f"title: {record_id} title",
        f"record_id: {record_id}",
        "status: completed",
        "source_records:",
        *[f"  - {rel}" for rel in source_records],
    ]
    if coverage_hash is not None:
        frontmatter.append(f"coverage_hash: {coverage_hash}")
    text = "\n".join(["---", *frontmatter, "---", "", "## Core Conclusions\n- summary"]) + "\n"
    write_file(root, f"digests/{name}", text)


def test_report_classifies_current_stale_and_unknown(tmp_path: Path) -> None:
    # Given: three digests — one current, one stale (source mutated), one legacy (no hash)
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\noriginal\n")
    write_file(root, "changes/b.md", "---\ntype: change\n---\n\noriginal\n")
    write_file(root, "changes/c.md", "---\ntype: change\n---\n\noriginal\n")

    current_hash = compute_coverage_hash(root, ["changes/a.md"])
    write_digest(root, "d-current.md", "digest-current", ["changes/a.md"], current_hash)

    stale_hash = compute_coverage_hash(root, ["changes/b.md"])
    write_digest(root, "d-stale.md", "digest-stale", ["changes/b.md"], stale_hash)
    write_file(root, "changes/b.md", "---\ntype: change\n---\n\nMUTATED\n")

    write_digest(root, "d-legacy.md", "digest-legacy", ["changes/c.md"], coverage_hash=None)

    # When
    report = build_digest_governance_report(root)

    # Then: counts and verdicts are correct
    assert report["total"] == 3
    assert report["current"] == 1
    assert report["stale"] == 1
    assert report["unknown"] == 1

    by_id = {d["record_id"]: d for d in report["digests"]}
    assert by_id["digest-current"]["verdict"] == "current"
    assert by_id["digest-stale"]["verdict"] == "stale"
    assert by_id["digest-legacy"]["verdict"] == "unknown"

    # And: worst-first ordering — stale leads, current trails
    assert report["digests"][0]["verdict"] == "stale"
    assert report["digests"][-1]["verdict"] == "current"


def test_stale_report_pinpoints_changed_and_missing_sources(tmp_path: Path) -> None:
    # Given: a digest over two sources; one is mutated, one is deleted after the hash
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/keep.md", "---\ntype: change\n---\n\noriginal\n")
    write_file(root, "changes/gone.md", "---\ntype: change\n---\n\noriginal\n")
    hash_before = compute_coverage_hash(root, ["changes/keep.md", "changes/gone.md"])
    write_digest(root, "d1.md", "digest-x", ["changes/keep.md", "changes/gone.md"], hash_before)

    # When: one source mutates and the other is removed
    write_file(root, "changes/keep.md", "---\ntype: change\n---\n\nMUTATED\n")
    (root / ".sybermem" / "changes" / "gone.md").unlink()

    report = build_digest_governance_report(root)
    digest = report["digests"][0]

    # Then: missing is definitive, mutated present source is a changed candidate
    assert digest["verdict"] == "stale"
    states = {d["path"]: d["state"] for d in digest["drifted_sources"]}
    assert states["changes/gone.md"] == "missing"
    assert states["changes/keep.md"] == "changed"
    assert "missing" in digest["reason"]


def test_current_digest_reports_no_drift(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\noriginal\n")
    current_hash = compute_coverage_hash(root, ["changes/a.md"])
    write_digest(root, "d1.md", "digest-ok", ["changes/a.md"], current_hash)

    report = build_digest_governance_report(root)
    assert report["digests"][0]["drifted_sources"] == []
    assert report["stale"] == 0


def test_stale_digest_count_matches_report(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\noriginal\n")
    stale_hash = compute_coverage_hash(root, ["changes/a.md"])
    write_digest(root, "d1.md", "digest-stale", ["changes/a.md"], stale_hash)
    write_file(root, "changes/a.md", "---\ntype: change\n---\n\nMUTATED\n")

    assert stale_digest_count(root) == 1


def test_empty_project_has_zero_digests(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    write_project(root)
    report = build_digest_governance_report(root)
    assert report == {"total": 0, "current": 0, "stale": 0, "unknown": 0, "digests": []}
    assert stale_digest_count(root) == 0
