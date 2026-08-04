from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.next_step_router import recommend_next_step_read_only, route_record_candidate


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (sybermem / "analysis").mkdir()
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    (sybermem / "analysis" / "phase-index.md").write_text(
        "\n".join(
            [
                "# Phase Index",
                "- status: current",
                "### Phase: Current",
                "- phase_id: phase-001",
                "- lifecycle: active",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_record_candidate_wins_before_digest_and_team_publish(tmp_path: Path) -> None:
    # Given: a project that also has digest and Team-publish signals
    project_root = tmp_path / "project"
    team_root = tmp_path / "team"
    project_root.mkdir()
    team_root.mkdir()
    write_project(project_root)
    (project_root / ".sybermem" / "project.yaml").write_text(
        f"project_id: project-1\nslug: demo\nteam_path: {team_root.as_posix()}\n",
        encoding="utf-8",
    )
    meta_dir = team_root / "projects" / "demo"
    meta_dir.mkdir(parents=True)
    meta_dir.joinpath("meta.json").write_text(
        json.dumps({"published_at": (datetime.now() - timedelta(days=7)).isoformat()}),
        encoding="utf-8",
    )
    candidate = {"classification": "decision", "action": "/sybermem-record", "reason": "decision needs durable rationale"}

    # When: the shared read-only router chooses one next action
    step = recommend_next_step_read_only(
        project_root,
        readiness={"enough_material": True},
        phase_digest=None,
        theme_digest=None,
        commit_gap=5,
        record_candidate=candidate,
    )

    # Then: record still wins over digest and Team publish
    assert step == {"action": "/sybermem-record", "reason": "decision needs durable rationale"}


def test_record_candidate_no_write_and_blocked_never_route_to_write(tmp_path: Path) -> None:
    # Given: side-effect-free record candidates that are not safe writes
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)

    # When: the candidates are routed
    no_write = route_record_candidate({"classification": "no_write", "reason": "explicit no-record request"})
    blocked = route_record_candidate({"classification": "blocked", "reason": "sensitive payload blocked"})

    # Then: neither candidate can produce a durable write command
    assert no_write == {"action": "/sybermem-summary", "reason": "explicit no-record request"}
    assert blocked == {"action": "blocked", "reason": "sensitive payload blocked"}


def test_router_returns_only_one_action_for_digest_candidate(tmp_path: Path) -> None:
    # Given: an explicit digest candidate and a simultaneous commit-gap signal
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    candidate = {"classification": "digest", "action": "/sybermem-digest", "reason": "phase appears stable"}

    # When: routing evaluates all signals
    step = recommend_next_step_read_only(project_root, commit_gap=9, record_candidate=candidate)

    # Then: callers receive one safe next action, not competing commands
    assert set(step) == {"action", "reason"}
    assert step == {"action": "/sybermem-digest", "reason": "phase appears stable"}
