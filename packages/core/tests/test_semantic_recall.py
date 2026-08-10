from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.semantic_recall import build_vector, cosine, semantic_scores
from sybermem_core.search import compact_project_search


def test_cosine_is_one_for_identical_text_and_zero_for_disjoint() -> None:
    a = build_vector("workspace recall behavior")
    assert cosine(a, a) == 1.0 or abs(cosine(a, a) - 1.0) < 1e-9
    b = build_vector("xxxxx yyyyy zzzzz")
    assert cosine(a, b) < 0.2


def test_semantic_scores_rank_morphologically_related_text_higher() -> None:
    rows = [
        {"title": "Recall retrieval tuning", "topics": "", "content": "improving recall and retrieval"},
        {"title": "Unrelated billing invoice", "topics": "", "content": "monthly invoice totals"},
    ]
    scored = semantic_scores("retrieval recalling", rows)
    assert scored, "expected at least one semantic hit"
    assert scored[0][0] == 0  # the recall/retrieval row ranks first


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


def test_semantic_supplement_is_off_by_default(tmp_path: Path, monkeypatch) -> None:
    # Given: a record only reachable by morphological (not exact-term) overlap
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-07-001-auth.md",
        ["type: change", "date: 2026-08-07", "title: Authentication authorization redesign", "status: implemented"],
        "## Summary\nReworked the authentication and authorization boundary.",
    )
    monkeypatch.delenv("SYBERMEM_SEMANTIC_RECALL", raising=False)
    monkeypatch.chdir(project_root)

    # When: semantic recall is disabled (default) and the inflected query misses lexically
    rows = compact_project_search("authenticating and authorizing", limit=3)

    # Then: nothing is surfaced (no silent semantic supplement) — economy preserved by default
    assert rows == []


def test_semantic_supplement_surfaces_lexical_miss_when_enabled(tmp_path: Path, monkeypatch) -> None:
    # Given: a record whose terms are inflected forms the query does not contain verbatim,
    # so exact-term lexical scoring misses it, but char n-grams still overlap strongly.
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-07-001-auth.md",
        ["type: change", "date: 2026-08-07", "title: Authentication authorization redesign", "status: implemented"],
        "## Summary\nReworked the authentication and authorization boundary.",
    )
    monkeypatch.chdir(project_root)

    # Sanity: with semantic recall OFF, the inflected query misses lexically.
    monkeypatch.delenv("SYBERMEM_SEMANTIC_RECALL", raising=False)
    lexical_only = compact_project_search("authenticating and authorizing", limit=3)
    assert lexical_only == []

    # When: semantic recall is enabled for the same inflected query
    monkeypatch.setenv("SYBERMEM_SEMANTIC_RECALL", "1")
    rows = compact_project_search("authenticating and authorizing", limit=3)

    # Then: the record is surfaced via the semantic supplement
    semantic_hits = [r for r in rows if r.get("match") == "semantic"]
    assert semantic_hits, "expected a semantic supplement hit when enabled"
    assert semantic_hits[0]["record_id"] == "change-001"
    # And: a semantic hit stays below the high-signal floor so it never auto-injects
    assert float(semantic_hits[0]["score"]) < 12.0
