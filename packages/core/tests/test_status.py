from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core import next_step_router
from sybermem_core.next_step_router import recommend_next_step
from sybermem_core.status import project_status


def write_project_with_team(root: Path, team_root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (sybermem / "project.yaml").write_text(
        f"project_id: project-1\nslug: demo\nteam:\n  team_id: team-1\n  team_path: {team_root.as_posix()}\n",
        encoding="utf-8",
    )
    records = sybermem / "changes"
    records.mkdir()
    (records / "2026-08-04-001-current.md").write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "date: 2026-08-04",
                "title: Current",
                "status: implemented",
                "---",
                "",
                "## Summary",
                "Current project source.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_project_status_returns_empty_snapshot_when_project_is_uninitialized(tmp_path: Path) -> None:
    # Given: a directory with no .sybermem project state
    project_root = tmp_path / "empty"
    project_root.mkdir()

    # When: current status is requested
    status = project_status(project_root)

    # Then: callers receive a bounded empty snapshot rather than an exception
    assert status["project_id"] == ""
    assert status["slug"] == "empty"
    assert status["phase"] == {"id": "", "name": "", "lifecycle": "active"}
    assert status["recent_records"] == []
    assert status["open_bugs"] == []
    assert status["open_requirements"] == []


def test_project_status_treats_fixed_bug_as_closed_but_statusless_as_open(tmp_path: Path) -> None:
    # Given: a project with one bug marked `fixed`, one marked `resolved`, and one with no status
    project_root = tmp_path / "project"
    bugs = project_root / ".sybermem" / "bugs"
    bugs.mkdir(parents=True)
    (project_root / ".sybermem" / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")

    def write_bug(name: str, status_line: str) -> None:
        frontmatter = ["---", "type: bug", "date: 2026-08-07", f"title: {name}", "severity: high"]
        if status_line:
            frontmatter.append(status_line)
        frontmatter.append("---")
        (bugs / f"2026-08-07-{name}.md").write_text("\n".join(frontmatter) + "\n\nbody\n", encoding="utf-8")

    write_bug("001-fixed", "status: fixed")
    write_bug("002-resolved", "status: resolved")
    write_bug("003-nostatus", "")

    # When: status enumerates open bugs
    status = project_status(project_root)

    # Then: fixed and resolved are closed; a status-less bug stays open (conservative)
    assert "bug-001" not in status["open_bugs"]
    assert "bug-002" not in status["open_bugs"]
    assert "bug-003" in status["open_bugs"]


def test_recommend_next_step_returns_phase_analyze_without_commit_probe(tmp_path: Path, monkeypatch) -> None:
    # Given: a SyberMem project with no phase index yet
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".sybermem").mkdir()
    (project_root / ".sybermem" / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")

    def fail_commit_probe(root: Path) -> int:
        raise AssertionError(f"commit probe should not run for {root}")

    monkeypatch.setattr(next_step_router, "_count_commits_since_last_record", fail_commit_probe)

    # When: routing decides the next step
    step = recommend_next_step(project_root)

    # Then: the structural prerequisite wins before any git-backed record gap check
    assert step["action"] == "/sybermem-phase-analyze"
    assert "phase index" in step["reason"]


def test_project_status_exposes_team_trust_metadata_for_unpublished_local_changes(tmp_path: Path) -> None:
    # Given: a project with a remembered Team publication whose source hash is outdated
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    team_project = team_root / "projects" / "demo"
    team_project.mkdir(parents=True)
    write_project_with_team(project_root, team_root)
    team_project.joinpath("meta.json").write_text(
        json.dumps(
            {
                "published_at": "2026-08-01T00:00:00+08:00",
                "source_scope": "project_records_digests_identity",
                "source_hash": "old-source-hash",
                "stale": False,
                "conflict": False,
                "review_required": True,
            }
        ),
        encoding="utf-8",
    )

    # When: project status is rendered
    status = project_status(project_root)

    # Then: Team metadata reports local changes without mutating Project truth
    assert status["publication"]["preview"]["source_hash"] != "old-source-hash"
    assert status["publication"]["team"] == {
        "team_id": "team-1",
        "team_path": str(team_root).replace("\\", "/"),
        "published_at": "2026-08-01T00:00:00+08:00",
        "source_scope": "project_records_digests_identity",
        "local_changes_after_publish": True,
        "stale": True,
        "conflict": False,
        "review_required": True,
    }
