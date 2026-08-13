from __future__ import annotations

from argparse import Namespace
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli.main import cmd_publish_status
import sybermem_core.publish_bootstrap as publish_bootstrap


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


def write_project_shell(root: Path, *, with_identity: bool) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    if with_identity:
        (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\nname: Demo\n", encoding="utf-8")
    (sybermem / "analysis").mkdir()
    (sybermem / "analysis" / "phase-index.md").write_text(
        "# Phase Index\n- status: current\n### Phase: Trust Envelope\n- phase_id: phase-006\n- lifecycle: active\n",
        encoding="utf-8",
    )


def write_record(root: Path, subdir: str, filename: str, frontmatter: list[str], body: str) -> None:
    records_dir = root / ".sybermem" / subdir
    records_dir.mkdir(exist_ok=True)
    records_dir.joinpath(filename).write_text("\n".join(["---", *frontmatter, "---", "", body]) + "\n", encoding="utf-8")


def write_publishable_project(root: Path) -> None:
    write_project_shell(root, with_identity=True)
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


def test_cli_preview_missing_project_yaml_is_structured_and_read_only(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a SyberMem shell without project.yaml identity
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    write_project_shell(project_root, with_identity=False)
    init_team_repo(team_root)
    before = sorted(path.relative_to(project_root).as_posix() for path in project_root.rglob("*"))
    monkeypatch.chdir(project_root)

    # When: JSON preview is requested through the CLI
    exit_code = cmd_publish_status(
        Namespace(team_path=str(team_root), preview=True, preview_source_hash=None, format="json")
    )

    # Then: the command returns a structured blocked result and does not create project.yaml
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert exit_code == 1
    assert payload["status"] == "blocked"
    assert payload["reason"] == "missing_project_identity"
    assert payload["project"]["path"] == str(project_root).replace("\\", "/")
    assert sorted(path.relative_to(project_root).as_posix() for path in project_root.rglob("*")) == before
    assert not (project_root / ".sybermem" / "project.yaml").exists()


def test_cli_preview_without_project_reports_invoked_path(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: the command is invoked from a directory with no SyberMem project ancestors
    invoked_path = tmp_path / "standalone" / "child"
    invoked_path.mkdir(parents=True)
    monkeypatch.chdir(invoked_path)
    monkeypatch.setattr(publish_bootstrap, "resolve_project_root", lambda: None)

    # When: JSON preview is requested
    exit_code = cmd_publish_status(
        Namespace(team_path=None, preview=True, preview_source_hash=None, format="json")
    )

    # Then: the structured blocked result names the exact invocation directory
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert exit_code == 1
    assert payload["status"] == "blocked"
    assert payload["project"]["path"] == str(invoked_path).replace("\\", "/")


def test_team_publish_skill_requires_preview_review_publish_hash_flow() -> None:
    # Given: both distributed skill copies document the Team publish workflow
    skill_paths = [
        Path(__file__).resolve().parents[3] / "skills" / "sybermem-team-publish" / "SKILL.md",
        Path(__file__).resolve().parents[3] / "packages" / "claude-skills" / "sybermem-team-publish" / "SKILL.md",
    ]

    for skill_path in skill_paths:
        # When: the skill instructions are inspected
        text = skill_path.read_text(encoding="utf-8")

        # Then: the default path binds publish to a reviewed preview source hash
        assert "$SyberMemCli publish status --preview --format json" in text
        assert "--preview-source-hash <source_hash_from_preview> --format json" in text
        assert "preview -> review -> publish" in text
        assert "Do not modify persistent PATH automatically" in text
        assert "sybermem publish status --format json" not in text


def test_cli_json_publish_stdout_is_valid_json_without_git_commit_noise(tmp_path: Path, monkeypatch, capfd) -> None:
    # Given: a publishable project whose Team publish will create a git commit
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    write_publishable_project(project_root)
    init_team_repo(team_root)
    monkeypatch.chdir(project_root)

    # When: JSON publish is executed
    exit_code = cmd_publish_status(
        Namespace(team_path=str(team_root), preview=False, preview_source_hash=None, format="json")
    )

    # Then: stdout is parseable JSON only, not prefixed by git commit summary text
    captured = capfd.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert payload["status"] == "published"
    assert payload["slug"] == "demo"
