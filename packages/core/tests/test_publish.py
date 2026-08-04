from __future__ import annotations

import json
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.publish import publish_status, publish_status_preview
from sybermem_core.team_summary import build_team_management_summary


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\nname: Demo\n", encoding="utf-8")
    (sybermem / "analysis").mkdir()
    (sybermem / "analysis" / "phase-index.md").write_text(
        "\n".join(
            [
                "# Phase Index",
                "- status: current",
                "### Phase: Trust Envelope",
                "- phase_id: phase-006",
                "- lifecycle: active",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_record(
        root,
        "changes",
        "2026-08-04-001-trust-envelope.md",
        ["type: change", "date: 2026-08-04", "title: Trust envelope", "status: implemented"],
        "## Summary\nPublish preview should describe this change.",
    )
    write_record(
        root,
        "decisions",
        "2026-08-04-001-reviewable-publish.md",
        ["type: decision", "date: 2026-08-04", "title: Reviewable publish", "status: accepted"],
        "## Decision\nHigh-impact publish uses a source hash.",
    )
    write_record(
        root,
        "digests",
        "2026-08-04-001-current-phase.md",
        ["type: digest", "kind: phase", "date: 2026-08-04", "number: 001", "title: Current phase", "status: completed"],
        "## Core Conclusions\n- Current digest exists.",
    )


def write_record(root: Path, subdir: str, filename: str, frontmatter: list[str], body: str) -> None:
    records_dir = root / ".sybermem" / subdir
    records_dir.mkdir(exist_ok=True)
    records_dir.joinpath(filename).write_text("\n".join(["---", *frontmatter, "---", "", body]) + "\n", encoding="utf-8")


def init_team_repo(team_root: Path) -> None:
    team_root.mkdir()
    subprocess.run(["git", "init"], cwd=team_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=team_root, check=True)
    subprocess.run(["git", "config", "user.name", "SyberMem Test"], cwd=team_root, check=True)
    (team_root / "team.yaml").write_text("schema_version: 1\nteam_id: team-1\nname: Team\nrepository:\n  remote: \n", encoding="utf-8")
    (team_root / "projects").mkdir()
    (team_root / "dashboards").mkdir()
    subprocess.run(["git", "add", "."], cwd=team_root, check=True)
    subprocess.run(["git", "commit", "-m", "init team"], cwd=team_root, check=True, capture_output=True)


def snapshot_files(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }


def test_publish_status_characterizes_current_output_contract(tmp_path: Path, monkeypatch) -> None:
    # Given: a publishable project and an isolated Team Git repo
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    write_project(project_root)
    init_team_repo(team_root)
    monkeypatch.chdir(project_root)

    # When: status is published without a remote
    payload = publish_status(team_root)

    # Then: the existing result still reports the published files and digest sources
    assert payload["status"] == "published"
    assert payload["team_id"] == "team-1"
    assert payload["project_id"] == "project-1"
    assert payload["slug"] == "demo"
    assert str(payload["source_phase_digest"]).endswith(".sybermem/digests/2026-08-04-001-current-phase.md")
    assert payload["source_theme_digest"] == ""
    assert payload["pushed"] is False
    assert (team_root / "projects" / "demo" / "project.md").is_file()
    assert (team_root / "projects" / "demo" / "current-status.md").is_file()
    assert (team_root / "projects" / "demo" / "meta.json").is_file()
    assert (team_root / "dashboards" / "current-overview.md").is_file()


def test_publish_preview_is_read_only_and_deterministic(tmp_path: Path, monkeypatch) -> None:
    # Given: a publishable project and Team repo
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    write_project(project_root)
    init_team_repo(team_root)
    before_project = snapshot_files(project_root)
    before_team = snapshot_files(team_root)
    monkeypatch.chdir(project_root)

    # When: preview is requested twice
    first = publish_status_preview(team_root)
    second = publish_status_preview(team_root)

    # Then: the payload is stable and no Project or Team files are written
    assert first == second
    assert first["status"] == "preview"
    assert first["source_scope"] == "project_records_digests_identity"
    assert first["source_revision"]
    assert first["source_hash"]
    assert first["selected_records"] == ["change-001", "decision-001"]
    assert first["selected_digests"] == ["digest-001"]
    assert first["freshness"] == "current"
    assert first["conflicts"] == []
    assert first["review_required"] is True
    assert snapshot_files(project_root) == before_project
    assert snapshot_files(team_root) == before_team


def test_publish_accepts_unchanged_preview_and_writes_trust_metadata(tmp_path: Path, monkeypatch) -> None:
    # Given: a preview generated from the current Project canonical records
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    write_project(project_root)
    init_team_repo(team_root)
    monkeypatch.chdir(project_root)
    preview = publish_status_preview(team_root)
    preview_hash = str(preview["source_hash"])

    # When: publish receives the matching source hash
    payload = publish_status(team_root, preview_source_hash=preview_hash)

    # Then: publish succeeds and Team metadata carries the trust envelope
    assert payload["status"] == "published"
    assert isinstance(payload["preview"], dict)
    assert payload["preview"]["source_hash"] == preview_hash
    meta = json.loads((team_root / "projects" / "demo" / "meta.json").read_text(encoding="utf-8"))
    assert meta["source_hash"] == preview_hash
    assert meta["source_revision"] == preview["source_revision"]
    assert meta["source_scope"] == "project_records_digests_identity"
    assert meta["local_changes_after_publish"] is False
    assert meta["stale"] is False
    assert meta["conflict"] is False
    assert meta["review_required"] is True
    assert meta["published_at"]


def test_team_management_summary_exposes_publish_trust_envelope(tmp_path: Path, monkeypatch) -> None:
    # Given: a reviewed publish writes Team trust metadata into the isolated Team repo
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    write_project(project_root)
    init_team_repo(team_root)
    monkeypatch.chdir(project_root)
    preview = publish_status_preview(team_root)
    preview_hash = str(preview["source_hash"])
    preview_revision = str(preview["source_revision"])
    published = publish_status(team_root, preview_source_hash=preview_hash)
    meta = json.loads((team_root / "projects" / "demo" / "meta.json").read_text(encoding="utf-8"))

    # When: the management summary is generated from Team memory
    result = build_team_management_summary(team_root)
    payload = result["payload"]
    assert isinstance(payload, dict)

    # Then: managers can inspect the publication trust envelope without reading meta.json by hand
    assert payload["projects"] == [
        {
            "slug": "demo",
            "source_revision": preview_revision,
            "source_hash": preview_hash,
            "published_at": meta["published_at"],
            "source_scope": "project_records_digests_identity",
            "local_changes_after_publish": False,
            "stale": False,
            "conflict": False,
            "review_required": True,
            "recommended_next_action": "/sybermem-team-summary",
        }
    ]
    assert isinstance(published["team_metadata"], dict)
    assert published["team_metadata"]["published_at"] == meta["published_at"]
    summary_markdown = result["summary_markdown"]
    assert isinstance(summary_markdown, Path)
    markdown = summary_markdown.read_text(encoding="utf-8")
    assert "## Publish Trust Envelope" in markdown
    assert "source hash" in markdown
    assert "source_scope=project_records_digests_identity" in markdown
    assert "local_changes_after_publish=False" in markdown


def test_publish_preview_marks_missing_phase_index_stale(tmp_path: Path, monkeypatch) -> None:
    # Given: publishable Project records exist but the phase index is missing
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    write_project(project_root)
    (project_root / ".sybermem" / "analysis" / "phase-index.md").unlink()
    init_team_repo(team_root)
    monkeypatch.chdir(project_root)

    # When: a read-only publish preview is built
    preview = publish_status_preview(team_root)

    # Then: missing structural phase truth is not presented as current freshness
    assert preview["freshness"] == "stale"


def test_publish_rejects_stale_preview_before_any_write(tmp_path: Path, monkeypatch) -> None:
    # Given: a preview that becomes stale after a new Project record is added
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    write_project(project_root)
    init_team_repo(team_root)
    monkeypatch.chdir(project_root)
    preview = publish_status_preview(team_root)
    preview_hash = str(preview["source_hash"])
    before_project = snapshot_files(project_root)
    before_team = snapshot_files(team_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-new-requirement.md",
        ["type: requirement", "date: 2026-08-04", "title: New requirement", "status: open"],
        "## Requirement\nThis record was not reviewed in the preview.",
    )
    after_record_project = snapshot_files(project_root)

    # When: publish is attempted with the old source hash
    payload = publish_status(team_root, preview_source_hash=preview_hash)

    # Then: stale_preview is returned before Team/project association writes or git staging
    assert payload["status"] == "stale_preview"
    assert payload["expected_source_hash"] == preview_hash
    assert isinstance(payload["preview"], dict)
    assert payload["preview"]["source_hash"] != preview_hash
    assert snapshot_files(project_root) == after_record_project
    assert snapshot_files(team_root) == before_team
    assert before_project[".sybermem/project.yaml"] == after_record_project[".sybermem/project.yaml"]


def test_publish_failure_preserves_project_canonical_records_and_team_association(tmp_path: Path, monkeypatch) -> None:
    # Given: a project and a path that is not a valid Team Git repo
    project_root = tmp_path / "project"
    bad_team = tmp_path / "bad-team"
    project_root.mkdir()
    bad_team.mkdir()
    write_project(project_root)
    before_project = snapshot_files(project_root)
    monkeypatch.chdir(project_root)

    # When / Then: publish fails before any Project canonical or association mutation
    try:
        publish_status(bad_team)
    except ValueError as exc:
        assert "Team Git repo" in str(exc)
    else:
        raise AssertionError("publish_status should reject a non-Team Git repo")
    assert snapshot_files(project_root) == before_project
