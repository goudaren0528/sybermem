from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.resume import build_resume_checkpoint
from sybermem_core import next_step_router


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")


def write_phase_index(root: Path, lifecycle: str = "active") -> None:
    analysis = root / ".sybermem" / "analysis"
    analysis.mkdir()
    (analysis / "phase-index.md").write_text(
        "\n".join(
            [
                "# Phase Index",
                "- status: current",
                "### Phase: Continuity Trust",
                "- phase_id: phase-004",
                f"- lifecycle: {lifecycle}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_record(root: Path, subdir: str, filename: str, frontmatter: list[str], body: str) -> None:
    records = root / ".sybermem" / subdir
    records.mkdir()
    (records / filename).write_text("\n".join(["---", *frontmatter, "---", "", body]) + "\n", encoding="utf-8")


def snapshot_files(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)).replace("\\", "/"): path.read_text(encoding="utf-8") for path in sorted(root.rglob("*")) if path.is_file()}


def test_fast_resume_returns_bounded_current_state_without_full_history(tmp_path: Path) -> None:
    # Given: a project with active phase, current records, and a digest
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_phase_index(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-resume-checkpoint.md",
        ["type: change", "date: 2026-08-04", "title: Resume checkpoint", "status: implemented"],
        "## Summary\nFast resume returns bounded metadata only.\n\n## Details\nThis full body must not appear in fast mode.",
    )
    write_record(
        project_root,
        "digests",
        "2026-08-04-001-current-digest.md",
        ["type: digest", "kind: phase", "date: 2026-08-04", "number: 001", "title: current digest", "status: completed"],
        "## Core Conclusions\n- Digest coverage exists.",
    )

    # When: fast resume is built
    checkpoint = build_resume_checkpoint(project_root, mode="fast")

    # Then: the result has only bounded current-state fields
    assert checkpoint["project"] == {"project_id": "project-1", "slug": "demo", "path": str(project_root).replace("\\", "/")}
    assert checkpoint["active_phase"] == {"id": "phase-004", "name": "Continuity Trust", "lifecycle": "active"}
    assert checkpoint["progress"][0]["record_id"] == "change-001"
    assert checkpoint["progress"][0]["summary"] == "Fast resume returns bounded metadata only."
    assert checkpoint["next_action"]["action"] == "/sybermem-summary"
    assert checkpoint["confidence"] == "high"
    assert checkpoint["freshness"] == "current"
    assert checkpoint["risks"] == []
    assert "digest_coverage" not in checkpoint
    assert "read_targets" not in checkpoint
    assert "This full body must not appear" not in repr(checkpoint)


def test_resume_uses_shared_read_only_router_for_next_action(tmp_path: Path, monkeypatch) -> None:
    # Given: a project whose router seam is patched to a sentinel recommendation
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_phase_index(project_root)

    def sentinel_router(root: Path, **_signals: dict[str, str]) -> dict[str, str]:
        return {"action": "/sentinel-router-action", "reason": f"shared router used for {root.name}"}

    monkeypatch.setattr(next_step_router, "recommend_next_step_read_only", sentinel_router, raising=False)

    # When: resume builds its checkpoint
    checkpoint = build_resume_checkpoint(project_root, mode="fast")

    # Then: next_action comes from the shared router seam, not duplicate resume logic
    assert checkpoint["next_action"] == {"action": "/sentinel-router-action", "reason": "shared router used for project"}
    assert checkpoint["recommendation_reason"] == "shared router used for project"


def test_standard_resume_adds_digest_coverage_and_high_signal_risks(tmp_path: Path) -> None:
    # Given: a project with open risk records and digest coverage
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_phase_index(project_root)
    write_record(
        project_root,
        "bugs",
        "2026-08-04-001-open-risk.md",
        ["type: bug", "date: 2026-08-04", "title: Open risk", "status: open"],
        "## Summary\nResume should surface this open bug.",
    )
    write_record(
        project_root,
        "digests",
        "2026-08-04-001-current-digest.md",
        ["type: digest", "kind: phase", "date: 2026-08-04", "number: 001", "title: current digest", "status: completed"],
        "## Core Conclusions\n- Current digest coverage exists.",
    )

    # When: standard resume is built
    checkpoint = build_resume_checkpoint(project_root, mode="standard")

    # Then: digest coverage and high-signal risks are present
    assert checkpoint["digest_coverage"]["phase_digest"] == "digest-001"
    assert checkpoint["risks"] == [{"kind": "open_bug", "record_id": "bug-001"}]


def test_deep_resume_returns_read_targets_without_reading_full_history(tmp_path: Path) -> None:
    # Given: a project with several current-state source files
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_phase_index(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-target.md",
        ["type: change", "date: 2026-08-04", "title: Target", "status: implemented"],
        "## Summary\nRead targets should point here.",
    )

    # When: deep resume is explicitly requested
    checkpoint = build_resume_checkpoint(project_root, mode="deep")

    # Then: deep mode points callers at files to inspect without embedding history bodies
    assert checkpoint["mode"] == "deep"
    assert ".sybermem/analysis/phase-index.md" in checkpoint["read_targets"]
    assert ".sybermem/changes/2026-08-04-001-target.md" in checkpoint["read_targets"]
    assert "Read targets should point here" not in repr(checkpoint)


def test_resume_handles_empty_project_without_side_effects(tmp_path: Path) -> None:
    # Given: an uninitialized directory
    project_root = tmp_path / "empty"
    project_root.mkdir()
    before = snapshot_files(project_root)

    # When: resume is requested
    checkpoint = build_resume_checkpoint(project_root, mode="fast")

    # Then: a safe no-project result is returned and no files are created
    assert checkpoint["project"]["status"] == "no_project"
    assert checkpoint["next_action"]["action"] == "/sybermem-init-project"
    assert checkpoint["confidence"] == "low"
    assert snapshot_files(project_root) == before


def test_stale_phase_state_lowers_resume_confidence(tmp_path: Path) -> None:
    # Given: a project whose phase index says no analysis exists yet
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    analysis = project_root / ".sybermem" / "analysis"
    analysis.mkdir()
    (analysis / "phase-index.md").write_text("# Phase Index\n- status: not_yet_analyzed\n", encoding="utf-8")

    # When: resume is built
    checkpoint = build_resume_checkpoint(project_root, mode="fast")

    # Then: the checkpoint remains useful but signals lower trust
    assert checkpoint["confidence"] == "low"
    assert checkpoint["freshness"] == "stale"
    assert checkpoint["next_action"]["action"] == "/sybermem-phase-analyze"


def test_newer_digest_after_phase_boundary_marks_resume_stale(tmp_path: Path) -> None:
    # Given: a phase index marked current but bounded at an older record date
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    analysis = project_root / ".sybermem" / "analysis"
    analysis.mkdir()
    (analysis / "phase-index.md").write_text(
        "\n".join(
            [
                "# Phase Index",
                "- status: current",
                "- last_record_boundary: change-001 (2026-08-04)",
                "### Phase: Continuity Trust",
                "- phase_id: phase-004",
                "- lifecycle: active",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_record(
        project_root,
        "digests",
        "2026-08-05-001-newer-digest.md",
        ["type: digest", "kind: phase", "date: 2026-08-05", "number: 001", "title: Newer digest", "status: completed"],
        "## Core Conclusions\n- New material landed after phase analysis.",
    )

    # When: resume is built from the bounded project state
    checkpoint = build_resume_checkpoint(project_root, mode="standard")

    # Then: phase freshness reflects lag from newer source material
    assert checkpoint["confidence"] == "low"
    assert checkpoint["freshness"] == "stale"
    assert checkpoint["next_action"]["action"] == "/sybermem-phase-analyze"


def test_same_day_progress_ordering_is_deterministic(tmp_path: Path) -> None:
    # Given: two manual change records on the SAME date (date-only frontmatter)
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_phase_index(project_root)
    changes = project_root / ".sybermem" / "changes"
    changes.mkdir()
    for rid in ("change-00000000000000000000000000000001", "change-00000000000000000000000000000002"):
        (changes / f"2026-08-04-{rid}.md").write_text(
            "\n".join(
                [
                    "---",
                    "type: change",
                    f"record_id: {rid}",
                    "date: 2026-08-04",
                    f"title: Work {rid[-1]}",
                    "status: implemented",
                    "---",
                    "",
                    "## Change Content\nBody.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    # When: resume is built twice
    first = build_resume_checkpoint(project_root, mode="fast")
    second = build_resume_checkpoint(project_root, mode="fast")

    # Then: same-day ordering is stable and reproducible (record_id tiebreak, desc),
    # so the higher record_id leads deterministically instead of arbitrarily.
    order = [item["record_id"] for item in first["progress"]]
    assert order == [item["record_id"] for item in second["progress"]]
    assert order[:2] == [
        "change-00000000000000000000000000000002",
        "change-00000000000000000000000000000001",
    ]


def test_confidence_reasons_expose_drivers_without_expanding_enum(tmp_path: Path) -> None:
    # Given: a current project with one open bug (medium confidence)
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_phase_index(project_root)
    write_record(
        project_root,
        "bugs",
        "2026-08-04-001-open.md",
        ["type: bug", "date: 2026-08-04", "title: Open bug", "status: open"],
        "## Summary\nStill open.",
    )

    # When: resume is built
    checkpoint = build_resume_checkpoint(project_root, mode="fast")

    # Then: the label stays within the 3-level enum, and reasons explain it
    assert checkpoint["confidence"] in {"low", "medium", "high"}
    assert checkpoint["confidence"] == "medium"
    reasons = checkpoint["confidence_reasons"]
    assert "phase index is current" in reasons
    assert "active phase id present" in reasons
    assert "1 open bugs" in reasons
    assert "0 open requirements" in reasons
