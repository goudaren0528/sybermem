from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.next_step_router import (
    compute_phase_state,
    recommend_next_step,
    recommend_next_step_read_only,
    route_record_candidate,
)
from sybermem_core.resume import build_resume_checkpoint


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


def test_record_candidate_wins_before_digest(tmp_path: Path) -> None:
    # Given: a project with a pending record candidate plus digest/commit-gap signals
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    candidate = {"classification": "decision", "action": "/sybermem-record", "reason": "decision needs durable rationale"}

    # When: the shared read-only router chooses one next action
    step = recommend_next_step_read_only(
        project_root,
        phase_digest=None,
        theme_digest=None,
        commit_gap=5,
        record_candidate=candidate,
    )

    # Then: an explicit record candidate wins over digest/summary routing
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


def _write_stale_phase_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    (sybermem / "analysis").mkdir(parents=True)
    (sybermem / "changes").mkdir()
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    # Phase index bounded at an OLD record date...
    (sybermem / "analysis" / "phase-index.md").write_text(
        "\n".join(
            [
                "# Phase Index",
                "- status: current",
                "- last_record_boundary: change-001 (2026-08-01)",
                "### Phase: Current",
                "- phase_id: phase-001",
                "- lifecycle: active",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    # ...while a NEWER authoritative record exists after that boundary.
    (sybermem / "changes" / "2026-08-09-001-newer-work.md").write_text(
        "\n".join(
            [
                "---",
                "type: change",
                "record_id: change-001",
                "date: 2026-08-09",
                "title: Newer work after boundary",
                "status: implemented",
                "---",
                "",
                "## Change Content\nNew material landed after phase analysis.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_stale_phase_index_makes_next_step_recommend_phase_analyze(tmp_path: Path) -> None:
    # Given: a project whose phase index lags newer source material
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_stale_phase_project(project_root)

    # When: the CLI next-step entry runs (it must compute phase_state itself)
    assert compute_phase_state(project_root) == "stale"
    step = recommend_next_step(project_root)

    # Then: it steers to phase-analyze instead of a later-stage action
    assert step["action"] == "/sybermem-phase-analyze"


def test_next_step_and_resume_agree_on_stale_phase(tmp_path: Path) -> None:
    # Given: the same stale-phase project
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_stale_phase_project(project_root)

    # When: both the CLI router and resume are asked for the next action
    router_action = recommend_next_step(project_root)["action"]
    resume_action = build_resume_checkpoint(project_root, mode="fast")["next_action"]["action"]

    # Then: the two entrypoints no longer disagree (regression guard)
    assert router_action == resume_action == "/sybermem-phase-analyze"


def test_backlog_rerecommends_digest_on_already_digested_project(tmp_path: Path) -> None:
    # Given: a healthy, already-digested project that has since accumulated uncovered records
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)

    # When: a phase digest already exists but backlog is at/above the threshold
    step = recommend_next_step_read_only(
        project_root,
        phase_digest="digests/2026-08-01-001-first.md",
        theme_digest=None,
        commit_gap=0,
        phase_state="current",
        backlog_uncovered=5,
    )

    # Then: it re-recommends a digest (the old 'no digest yet' gate would have stayed silent)
    assert step["action"] == "/sybermem-digest"
    assert "not covered by any digest" in step["reason"]


def test_first_digest_uses_digest_record_threshold(tmp_path: Path) -> None:
    # Given: a project with no digest and enough total records to be worth compressing
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)

    # When: no phase digest and backlog_total >= the digest-specific threshold
    step = recommend_next_step_read_only(
        project_root,
        phase_digest=None,
        theme_digest=None,
        commit_gap=0,
        phase_state="current",
        backlog_uncovered=6,
        backlog_total=6,
    )

    # Then: recommends the first digest based on record accumulation
    assert step["action"] == "/sybermem-digest"
    assert "no digest yet" in step["reason"]


def test_first_digest_not_recommended_below_digest_threshold(tmp_path: Path) -> None:
    # Given: a project with no digest but only a couple of records
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)

    # When: total records are below the digest threshold
    step = recommend_next_step_read_only(
        project_root,
        phase_digest=None,
        theme_digest=None,
        commit_gap=0,
        phase_state="current",
        backlog_uncovered=2,
        backlog_total=2,
    )

    # Then: no premature digest recommendation (decoupled from publish's low threshold)
    assert step["action"] != "/sybermem-digest"


def test_backlog_below_threshold_does_not_rerecommend_digest(tmp_path: Path) -> None:
    # Given: an already-digested project with only a small uncovered backlog
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)

    # When: backlog is below the threshold
    step = recommend_next_step_read_only(
        project_root,
        phase_digest="digests/2026-08-01-001-first.md",
        theme_digest=None,
        commit_gap=0,
        phase_state="current",
        backlog_uncovered=4,
    )

    # Then: no digest re-recommendation (falls through to the healthy summary)
    assert step["action"] != "/sybermem-digest"
