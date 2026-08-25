from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core import portfolio as portfolio_module
from sybermem_core.portfolio import build_portfolio


def _make_project(root: Path, slug: str) -> None:
    sybermem = root / ".sybermem"
    (sybermem / "bugs").mkdir(parents=True)
    (sybermem / "changes").mkdir()
    (sybermem / "project.yaml").write_text(f"project_id: {slug}-id\nslug: {slug}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    # one open bug + one recent change record
    (sybermem / "bugs" / "2026-08-20-b.md").write_text(
        "---\ntype: bug\nrecord_id: bug-001\ndate: 2026-08-20\nstatus: open\n---\n\nx\n", encoding="utf-8"
    )
    (sybermem / "changes" / "2026-08-22-c.md").write_text(
        "---\ntype: change\nrecord_id: change-001\ndate: 2026-08-22\n---\n\nx\n", encoding="utf-8"
    )


def test_portfolio_enriches_projects_with_local_attention_signals(tmp_path: Path, monkeypatch) -> None:
    # Given: a registry with one accessible project and one missing path
    proj = tmp_path / "proj"
    proj.mkdir()
    _make_project(proj, "demo")
    registry = [
        {"project_id": "demo-id", "slug": "demo", "path": str(proj)},
        {"project_id": "gone-id", "slug": "gone", "path": str(tmp_path / "nope")},
    ]
    monkeypatch.setattr(portfolio_module, "load_registry", lambda: registry)

    # When
    result = build_portfolio()
    by_slug = {p["slug"]: p for p in result["projects"]}

    # Then: accessible project carries local-only signals; no Team publish trust envelope
    demo = by_slug["demo"]
    assert demo["open_bugs"] == 1
    assert demo["open_requirements"] == 0
    assert demo["digest_uncovered"] == 2  # bug + change, no digest covers them
    assert demo["latest_record_date"] == "2026-08-22"
    assert "publication" not in demo  # portfolio is a projection, not a publish record

    # Missing project degrades gracefully
    assert by_slug["gone"]["status"] == "missing"
    assert by_slug["gone"]["open_bugs"] == 0


def test_portfolio_shows_existing_but_uninitialized_project(tmp_path: Path, monkeypatch) -> None:
    # Given: a registry entry whose PATH EXISTS but has no .sybermem/INDEX.md yet
    proj = tmp_path / "raw"
    proj.mkdir()  # exists, but not a SyberMem project
    registry = [{"project_id": "raw-id", "slug": "raw", "path": str(proj)}]
    monkeypatch.setattr(portfolio_module, "load_registry", lambda: registry)

    # When
    result = build_portfolio()

    # Then: the entry is NOT silently dropped — it appears with an explicit status/reason
    assert len(result["projects"]) == 1
    entry = result["projects"][0]
    assert entry["slug"] == "raw"
    assert entry["status"] == "uninitialized"
    assert "INDEX.md" in entry["reason"]


def test_portfolio_is_read_only(tmp_path: Path, monkeypatch) -> None:
    # Given: a valid registered project
    proj = tmp_path / "proj"
    proj.mkdir()
    _make_project(proj, "demo")
    before = sorted(p.name for p in (proj / ".sybermem").rglob("*"))
    registry = [{"project_id": "demo-id", "slug": "demo", "path": str(proj)}]
    monkeypatch.setattr(portfolio_module, "load_registry", lambda: registry)

    # When
    build_portfolio()

    # Then: the portfolio never writes to project files (read-only projection)
    after = sorted(p.name for p in (proj / ".sybermem").rglob("*"))
    assert before == after
