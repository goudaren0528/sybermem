from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core import workspace_search as ws


def test_staleness_empty_when_indexed_head_matches(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.setattr(
        ws,
        "load_registry",
        lambda: [{"project_id": "p1", "slug": "proj", "path": str(project), "last_seen_commit": "abc123"}],
    )
    monkeypatch.setattr(ws, "current_head", lambda root: "abc123")

    assert ws.workspace_index_staleness() == []


def test_staleness_reports_project_when_head_diverged(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    monkeypatch.setattr(
        ws,
        "load_registry",
        lambda: [{"project_id": "p1", "slug": "proj", "path": str(project), "last_seen_commit": "old111"}],
    )
    monkeypatch.setattr(ws, "current_head", lambda root: "new222")

    stale = ws.workspace_index_staleness()
    assert len(stale) == 1
    assert stale[0]["slug"] == "proj"
    assert stale[0]["indexed_commit"] == "old111"
    assert stale[0]["current_commit"] == "new222"
    assert stale[0]["stale"] is True


def test_staleness_skips_missing_path_and_empty_heads(tmp_path: Path, monkeypatch) -> None:
    existing = tmp_path / "exists"
    existing.mkdir()
    monkeypatch.setattr(
        ws,
        "load_registry",
        lambda: [
            {"project_id": "gone", "slug": "gone", "path": str(tmp_path / "missing"), "last_seen_commit": "x"},
            {"project_id": "nohead", "slug": "nohead", "path": str(existing), "last_seen_commit": "x"},
            {"project_id": "noindex", "slug": "noindex", "path": str(existing), "last_seen_commit": ""},
        ],
    )
    # existing dir resolves to empty HEAD (e.g. not a git repo) -> skipped
    monkeypatch.setattr(ws, "current_head", lambda root: "")

    assert ws.workspace_index_staleness() == []
